import streamlit as st
from agent import plan_trip

st.set_page_config(page_title="Voyager — AI Trip Planner", page_icon="🧭", layout="centered")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 20% 0%, #1e2a4a 0%, #0f1524 45%, #0a0e1a 100%);
    }

    #MainMenu, footer, header {visibility: hidden;}

    .hero {
        text-align: center;
        padding: 2.2rem 1rem 1.2rem 1rem;
    }
    .hero h1 {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #7dd3fc, #a78bfa, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .hero p {
        color: #94a3b8;
        font-size: 1.05rem;
        max-width: 480px;
        margin: 0 auto;
    }

    .glass-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 1.8rem 1.6rem;
        backdrop-filter: blur(12px);
        margin-bottom: 1.2rem;
    }

    .stTextInput input, .stNumberInput input {
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        color: #f1f5f9 !important;
        padding: 0.7rem 0.9rem !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border: 1px solid #a78bfa !important;
        box-shadow: 0 0 0 1px #a78bfa !important;
    }
    label, .stTextInput label, .stNumberInput label {
        color: #cbd5e1 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }

    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(90deg, #7dd3fc, #a78bfa) !important;
        color: #0a0e1a !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.7rem 1.5rem !important;
        width: 100%;
        transition: transform 0.15s ease;
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        transform: scale(1.01);
    }

    .step-badge {
        display: inline-block;
        background: rgba(167, 139, 250, 0.15);
        border: 1px solid rgba(167, 139, 250, 0.35);
        color: #c4b5fd;
        border-radius: 999px;
        padding: 0.35rem 0.9rem;
        font-size: 0.85rem;
        margin: 0.2rem 0.3rem 0.2rem 0;
    }

    .result-card {
        background: rgba(255, 255, 255, 0.035);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 2rem;
        color: #e2e8f0 !important;
        line-height: 1.65;
    }
    .result-card h2 {
        color: #a78bfa !important;
        font-size: 1.3rem !important;
        margin-top: 1.4rem !important;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        padding-bottom: 0.4rem;
    }
    .result-card h2:first-child { margin-top: 0 !important; }
    .result-card strong { color: #7dd3fc; }

    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>🧭 Voyager</h1>
        <p>An autonomous agent that researches real hotels, food, and attractions — then builds a budget-aware itinerary, correcting itself until it fits.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    with st.form("trip_form"):
        col1, col2 = st.columns(2)
        with col1:
            destination = st.text_input("Destination", placeholder="Bangkok, Thailand")
        with col2:
            dates = st.text_input("Trip length", placeholder="7 days")

        budget = st.number_input("Budget in USD (excluding flights)", min_value=10, value=500, step=10)
        interests = st.text_input("Interests", placeholder="street food, temples, nightlife")

        submitted = st.form_submit_button("✨ Plan my trip")
    st.markdown('</div>', unsafe_allow_html=True)

if submitted:
    if not destination or not dates or not interests:
        st.warning("Please fill in all fields.")
    else:
        progress_placeholder = st.empty()
        steps = []

        def log_callback(msg):
            clean = msg.replace("🔧 Using tool: ", "").replace("⚠️ ", "")
            if "get_weather" in clean:
                label = "🌤️ Checking weather"
            elif "web_search" in clean:
                label = "🔍 Researching options"
            elif "check_budget" in clean:
                label = "💰 Verifying budget"
            else:
                label = "🔄 Adjusting plan"
            steps.append(label)
            badges = "".join(f'<span class="step-badge">{s}</span>' for s in steps)
            progress_placeholder.markdown(badges, unsafe_allow_html=True)

        with st.spinner("Voyager is researching your trip..."):
            result = plan_trip(destination, dates, budget, interests, log_callback=log_callback)

        st.markdown("### ")
        safe_result = result.replace("$", "\\$")
        st.markdown(f'<div class="result-card">{safe_result}</div>', unsafe_allow_html=True)
