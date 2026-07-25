# 🧭 Voyager — Autonomous Trip Planning Agent

An agentic AI system that autonomously researches, budgets, and self-corrects to produce a realistic, specific travel itinerary — not a fine-tuned model, but a tool-using agent built on top of an LLM.

**Live app:** [trip-planner-agent-b3vsdidmvapn4frvfzhbed.streamlit.app](https://trip-planner-agent-b3vsdidmvapn4frvfzhbed.streamlit.app)

## What makes this "agentic"

Most LLM apps are single-turn: one prompt in, one answer out. Voyager instead runs a full **reason → act → observe → repeat** loop. Given only a destination, trip length, budget, and interests, the agent decides for itself:

- When to check the weather
- What to search for (and how many times)
- How to estimate and verify a realistic budget
- Whether its own plan needs revision before it's allowed to answer

No part of the itinerary is hardcoded or templated — the agent researches real, named hotels, restaurants, and attractions for whichever destination it's given.

## Architecture

**LLM:** Llama 3.3 70B, served via [Groq](https://groq.com) (free tier, fast inference)

**Tools available to the agent:**
| Tool | Purpose |
|---|---|
| `get_weather` | 7-day forecast via Open-Meteo (free, no API key) |
| `web_search` | Live search via DuckDuckGo, used to find named hotels, restaurants, and attraction prices |
| `check_budget` | Compares a running cost estimate against the user's stated budget |

**Agent loop:** implemented as a manual tool-calling loop (no framework like LangChain) — the model's tool calls are executed, results are fed back into the conversation, and this repeats for up to 12 iterations until the model produces a final answer.

**Self-correction:** the system prompt requires the agent to run a *mandatory final budget check* against its own itemized breakdown before answering — if the numbers don't add up within budget, it must revise the plan (cheaper hotel, cheaper food, fewer paid attractions) and re-check, rather than presenting an over-budget plan with a caveat attached.

## Example output

For a 5-day, $500 trip to Tokyo with interests in food and temples, the agent independently:
1. Checked Tokyo's weather
2. Searched for and named a specific budget hotel (with real nightly price)
3. Searched for real neighborhood/restaurant recommendations
4. Searched for real attractions (Senso-ji, Meiji Shrine, teamLab Borderless, Ghibli Museum) with entry costs
5. Converted all local currency to USD
6. Verified its final itemized total ($364) came in under the $500 budget before answering

## Project Structure

```
trip-planner-agent/
├── agent.py            # Core agent loop, tools, and system prompt
├── app.py               # Streamlit UI
├── requirements.txt
└── .gitignore
```

## Running It Yourself

```bash
git clone https://github.com/abbas004tech/trip-planner-agent.git
cd trip-planner-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with:
```
GROQ_API_KEY=your_key_here
```

Then run:
```bash
streamlit run app.py
```

## Tech Stack

- **Groq** — free, fast LLM inference (Llama 3.3 70B)
- **DuckDuckGo Search (`ddgs`)** — free web search, no API key
- **Open-Meteo** — free weather API, no API key
- **Streamlit** — UI and free permanent hosting via Streamlit Community Cloud

## Author

Built by: ~Ali Abbas~ — AI Engineering student, 3rd semester.
