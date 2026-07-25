import os
import json
import requests
from dotenv import load_dotenv
from groq import Groq
from ddgs import DDGS

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"


# ---------- TOOL 1: Weather ----------
def get_weather(city: str) -> str:
    """Fetch a 7-day weather forecast for a city using Open-Meteo (free, no API key needed)."""
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo_resp = requests.get(geo_url, timeout=10).json()
        if not geo_resp.get("results"):
            return f"Could not find location data for {city}."

        result = geo_resp["results"][0]
        lat, lon = result["latitude"], result["longitude"]

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
            f"&timezone=auto&forecast_days=7"
        )
        weather_resp = requests.get(weather_url, timeout=10).json()
        daily = weather_resp.get("daily", {})

        forecast_lines = []
        for i, date in enumerate(daily.get("time", [])):
            high = daily["temperature_2m_max"][i]
            low = daily["temperature_2m_min"][i]
            rain_chance = daily["precipitation_probability_max"][i]
            forecast_lines.append(f"{date}: High {high}C, Low {low}C, Rain chance {rain_chance}%")

        return f"7-day forecast for {city}:\n" + "\n".join(forecast_lines)
    except Exception as e:
        return f"Error fetching weather for {city}: {str(e)}"


# ---------- TOOL 2: Budget calculator ----------
def check_budget(estimated_cost: float, budget: float) -> str:
    """Compare an estimated trip cost against the user's stated budget."""
    if estimated_cost <= budget:
        remaining = budget - estimated_cost
        return f"Within budget. Estimated cost ${estimated_cost:.2f} vs budget ${budget:.2f}. ${remaining:.2f} remaining."
    else:
        over = estimated_cost - budget
        return f"OVER BUDGET by ${over:.2f}. Estimated cost ${estimated_cost:.2f} exceeds budget ${budget:.2f}. Consider cheaper options."


# ---------- TOOL 3: Free web search (DuckDuckGo via ddgs) ----------
def web_search(query: str) -> str:
    """Search the web for current information using DuckDuckGo (free, no API key needed)."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=6))
        if not results:
            return f"No search results found for: {query}"

        lines = []
        for r in results:
            lines.append(f"- {r.get('title', '')}: {r.get('body', '')}")
        return f"Search results for '{query}':\n" + "\n".join(lines)
    except Exception as e:
        return f"Error searching for '{query}': {str(e)}"


# ---------- Tool definitions (Groq uses OpenAI-style function calling format) ----------
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get a 7-day weather forecast for a city, to help plan what activities and packing make sense for the trip dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The city name to get weather for."}
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_budget",
            "description": "Check whether an estimated total trip cost fits within the user's stated budget. Use this after estimating costs for lodging, food, activities, and transport.",
            "parameters": {
                "type": "object",
                "properties": {
                    "estimated_cost": {"type": "number", "description": "The total estimated cost of the trip in USD."},
                    "budget": {"type": "number", "description": "The user's stated budget in USD."},
                },
                "required": ["estimated_cost", "budget"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current, real information about named hotels, restaurants, attractions, or prices for a destination.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"],
            },
        },
    },
]


def run_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "get_weather":
        return get_weather(tool_input["city"])
    elif tool_name == "check_budget":
        return check_budget(tool_input["estimated_cost"], tool_input["budget"])
    elif tool_name == "web_search":
        return web_search(tool_input["query"])
    return f"Unknown tool: {tool_name}"


# ---------- Main agent loop ----------
def plan_trip(destination: str, dates: str, budget: float, interests: str, log_callback=None):
    """
    Runs the agent loop: the model decides which tools to call, we execute them,
    feed results back, and repeat until it produces a final itinerary.
    log_callback: optional function to report progress (for UI streaming).
    """
    system_prompt = (
        "You are an autonomous trip planning agent. Given a destination, travel dates, "
        "a budget, and interests, you must research and produce a highly specific, "
        "actionable day-by-day itinerary. Generic advice like 'stay at a budget-friendly "
        "hotel' or 'try local street food' is NOT acceptable — you must name actual, "
        "real hotels, restaurants, and attractions with realistic prices for each.\n\n"
        "CRITICAL: The trip duration is given in the 'dates' field (e.g. '5 days' means "
        "exactly 5 days and 4 nights — do not invent a different number of days or nights). "
        "Your day-by-day itinerary must contain exactly the number of days specified, no more "
        "and no fewer, and your hotel cost must be calculated using the correct number of nights "
        "(days minus one, unless exact check-in/check-out dates are given).\n\n"
        "Follow this process:\n"
        "1. Use get_weather to check conditions for the destination and plan activities accordingly.\n"
        "2. Use web_search to find SPECIFIC named hotels or guesthouses in the destination with "
        "their approximate nightly price (search something like 'best budget hotels in "
        "[destination] with prices'). Recommend at least one specific hotel with its name and price.\n"
        "3. Use web_search to find SPECIFIC named restaurants, food streets, or dishes with "
        "approximate prices (search something like '[destination] restaurant prices' or "
        "'[destination] must try food cost'). Recommend specific places to eat with prices, "
        "for both a budget option and a slightly nicer option if it fits.\n"
        "4. Use web_search to find SPECIFIC named attractions, markets, or activities matching "
        "the user's interests, with entry fees or costs if any (search '[destination] "
        "attraction ticket prices' or similar). Recommend specific places, not vague categories.\n"
        "5. Add up a realistic total cost using the CORRECT trip duration: hotel (nights x price), "
        "food (meals x days), attractions/activities, and local transport. Use check_budget to "
        "verify this fits the user's budget. If it doesn't fit, silently swap in cheaper named "
        "alternatives (a cheaper hotel, cheaper food spots) and call check_budget again, repeating "
        "until it fits.\n\n"
        "IMPORTANT: Your final answer must be the single, already-corrected plan that fits the "
        "budget. Never present an over-budget plan followed by 'however, consider these changes' — "
        "do all revision internally across multiple check_budget calls, and only output the final, "
        "confirmed within-budget version. The final answer should read as one clean, confident plan, "
        "not a first draft with a patch note attached.\n\n"
        "CURRENCY RULE: Always express every single price in the final answer in USD only. If "
        "search results give prices in a local currency (e.g. Rs., PKR, INR, EUR), convert them "
        "to an approximate USD equivalent using a reasonable exchange rate, and state that "
        "conversion rate once near the top of your answer. Never mix currencies within the "
        "itinerary or budget breakdown — every number the user sees must be a dollar amount.\n\n"
        "You may use web_search up to 8 times total if needed to gather enough specific, named "
        "recommendations — thorough research matters more than speed here.\n\n"
        "Format your final answer with these sections:\n"
        "## Where to Stay\n"
        "(Named hotel/guesthouse recommendation with price per night and total for the correct number of nights)\n\n"
        "## Where to Eat\n"
        "(Named restaurants/food spots with approximate price per meal, covering breakfast/lunch/dinner style options)\n\n"
        "## Day-by-Day Itinerary\n"
        "(Exactly the requested number of days: named attractions/activities with entry costs, organized by morning/afternoon/evening)\n\n"
        "## Budget Breakdown\n"
        "(Clear line-item total: hotel, food, attractions, local transport, and remaining buffer against the budget — this must already be within budget)"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"Plan a trip to {destination} for these dates: {dates}. "
                f"Budget: ${budget} USD (excluding flights). "
                f"Interests: {interests}."
            ),
        },
    ]

    max_iterations = 12
    for _ in range(max_iterations):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=2500,
            )
        except Exception as e:
            if log_callback:
                log_callback(f"⚠️ Model call failed, retrying with a nudge: {e}")
            messages.append({
                "role": "user",
                "content": "That tool call was malformed. Please try again with a properly formatted function call, or just give your final answer if you have enough information.",
            })
            continue

        message = response.choices[0].message

        if not message.tool_calls:
            return message.content

        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": message.tool_calls,
        })

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_input = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                result = "Error: could not parse tool arguments. Please try again with valid JSON arguments."
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
                continue

            if log_callback:
                log_callback(f"🔧 Using tool: {tool_name}({json.dumps(tool_input)})")

            result = run_tool(tool_name, tool_input)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    return "The agent reached the maximum number of steps. Here's what it gathered so far — try a simpler or more specific request for a complete itinerary."


if __name__ == "__main__":
    result = plan_trip(
        destination="Lahore, Pakistan",
        dates="5 days",
        budget=600,
        interests="food, history, local markets",
        log_callback=print,
    )
    print("\n\n=== FINAL ITINERARY ===\n")
    print(result)