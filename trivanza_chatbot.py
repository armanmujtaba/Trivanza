import streamlit as st
from openai import OpenAI
from datetime import date, timedelta

st.set_page_config(page_title="Trivanza Travel Assistant", layout="centered")
client = OpenAI()

STRICT_SYSTEM_PROMPT = """
You are Trivanza, an expert AI travel assistant.

You MUST follow all these instructions STRICTLY:
1. Always begin with a warm, one-line greeting (e.g., "Hello Traveler! Let's plan your adventure!").
2. For every itinerary output:
    - Use Markdown, but never use heading levels higher than `###`.
    - Each day should be started with a heading: `### Day N: <activity/city> (<YYYY-MM-DD>)`.
    - Every single itinerary item (flight, hotel, meal, activity, transportation, etc.) MUST be in a separate paragraph. That is, after each item, output **two line breaks** (an empty line) so that in Markdown each item is always in its own block and never merged into the same line.
    - For every flight, hotel, and restaurant/meal, suggest a REALISTIC option by NAME (e.g., "Air India AI-123", "Ibis Paris Montmartre", "Le Relais Restaurant").
    - Each major item (flight, hotel, meal, and main activity) MUST include a real, working, direct booking or info link. Always use a plausible link (e.g., [Book](https://www.booking.com/hotel/fr/ibis-paris-montmartre), [Book Flight](https://www.airindia.in/) or [Menu](https://www.zomato.com/)). Never use placeholder or fake links.
    - Show the cost for each item and sum exact costs for each day: `🎯 Daily Total: ₹<amount>`.
    - After all days, give a cost breakdown (bulleted), a packing checklist, a budget analysis, and one pro tip for the destination.
    - At the end, always ask: "Would you like any modifications or changes to your itinerary? If yes, please specify and I'll update it accordingly."
3. Never use heading sizes above `###`.
4. Never put more than one itinerary item on a single line or paragraph. Never use bullet points, commas, or grouping for itinerary items—**each must be in its own paragraph, separated by TWO line breaks.**
5. Never leave out booking/info links for major items.
6. Do not add, change, or fix formatting in code. All formatting MUST be performed by you, the AI.
7. If a user requests a modification, recalculate and reformat as above.
8. Greet the user at the start of every new itinerary.

Example:

Hello Traveler! Here is your Paris trip itinerary:

### Day 1: Arrival in Paris (2025-08-01)

✈️ Flight: Air India AI-123, Delhi to Paris, ₹35,000 [Book](https://www.airindia.in/)

🚕 Airport transfer: Welcome Pickups, ₹2,000 [Book](https://www.welcomepickups.com/)

🏨 Hotel: Ibis Paris Montmartre, ₹6,000 [Book](https://www.booking.com/hotel/fr/ibis-paris-montmartre)

🍽️ Dinner: Le Relais Restaurant, ₹1,500 [Menu](https://www.zomato.com/paris/le-relais)

🎯 Daily Total: ₹44,500

### Day 2: Explore Paris (2025-08-02)

...

- Cost Breakdown:
    - Flights: ₹35,000
    - Accommodation: ₹6,000
    ...
- Packing Checklist:
    - Passport, power adapter, ...
- Budget Analysis: Well within your budget.
- Paris Pro Tip: Use metro for fast travel!

Would you like any modifications or changes to your itinerary? If yes, please specify and I'll update it accordingly.
"""

greeting_message = """Hello Traveler! Welcome to Trivanza - I'm Your Smart Travel Companion  
I'm excited to help you with your travel plans.
- Submit Plan My Trip form for a customised itinerary  
- Use chat box for your other travel related queries"""

def is_greeting_or_planning(text):
    greetings = [
        "hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings",
        "plan", "itinerary", "plan my trip", "journey", "my journey", "trip planning",
        "plan itinerary", "plan my itinerary", "trip", "travel"
    ]
    text_lower = text.lower()
    return any(greet in text_lower for greet in greetings)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "trip_context" not in st.session_state:
    st.session_state.trip_context = None
if "pending_form_response" not in st.session_state:
    st.session_state.pending_form_response = False
if "user_history" not in st.session_state:
    st.session_state.user_history = []
if "pending_llm_prompt" not in st.session_state:
    st.session_state.pending_llm_prompt = None

st.markdown("""
<style>
.logo-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 10px;
}
.logo {
    width: 300px;
}
@media (min-width: 601px) {
    .logo {
        width: 350px;
    }
}
.chat-entry { margin-top: 10px; }
.stChatInputContainer { position: fixed; bottom: 0; left: 0; right: 0; background: white; z-index: 1001; }
.stChatInputContainer textarea { min-height: 2.5em; }
.appview-container .main { padding-bottom: 8em !important; }
</style>
<div class="logo-container">
    <img class="logo" src="https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/Trivanza.png?raw=true">
</div>
""", unsafe_allow_html=True)

with st.expander("📋 Plan My Trip", expanded=False):
    with st.form("travel_form", clear_on_submit=False):
        st.markdown("### 🧳 Let's plan your perfect trip!")

        col1, col2 = st.columns(2)
        with col1:
            traveler_type = st.selectbox("🧍 Traveler Type", ["Solo", "Couple", "Family", "Group"], key="traveler_type")
            group_size = st.number_input("👥 Group Size", min_value=1, value=2, key="group_size")
        with col2:
            origin = st.text_input("🌍 Origin", placeholder="e.g., Delhi", key="origin")
            destination = st.text_input("📍 Destination", placeholder="e.g., Paris", key="destination")
        col3, col4 = st.columns(2)
        with col3:
            from_date = st.date_input("📅 From Date", min_value=date.today(), key="from_date")
        with col4:
            to_date = st.date_input("📅 To Date", min_value=from_date, key="to_date")

        st.markdown("#### 💰 Budget & Stay")
        col5, col6 = st.columns(2)
        with col5:
            budget_amount = st.number_input("💰 Budget", min_value=1000, step=1000, key="budget_amount")
        with col6:
            currency_type = st.selectbox("💱 Currency", ["₹ INR", "$ USD", "€ EUR", "£ GBP", "¥ JPY"], key="currency_type")
        stay = st.selectbox("🏨 Stay Type", ["Hotel", "Hostel", "Airbnb", "Resort"], key="stay")

        st.markdown("#### 🎯 Preferences & Interests")
        dietary_pref = st.multiselect("🥗 Dietary", ["Vegetarian", "Vegan", "Gluten-Free", "Halal", "Kosher"], key="dietary_pref")
        sustainability = st.selectbox("🌱 Sustainability", ["None", "Eco-Friendly Stays", "Carbon Offset Flights", "Zero-Waste Activities"], key="sustainability")
        language_pref = st.selectbox("🌐 Language", ["English", "Hindi", "French", "Spanish", "Mandarin", "Local Phrases"], key="language_pref")
        cultural_pref = st.selectbox("👗 Cultural Sensitivity", ["Standard", "Conservative Dress", "Religious Holidays", "Gender Norms"], key="cultural_pref")
        custom_activities = st.multiselect("🎨 Interests", [
            "Beaches", "Hiking", "Shopping", "Nightlife",
            "Cultural Immersion", "Foodie Tour", "Adventure Sports"
        ], key="custom_activities")

        submit = st.form_submit_button("🚀 Generate Itinerary")

        if submit:
            st.success("✅ Generating your personalized itinerary...")

            short_prompt = (
                f"Plan a trip from {origin} to {destination} from {from_date} to {to_date} for a {traveler_type.lower()} of {group_size} people. "
                f"Budget: {currency_type} {budget_amount}. "
                f"Dietary: {', '.join(dietary_pref) if dietary_pref else 'None'}, Language: {language_pref}, Sustainability: {sustainability}, "
                f"Cultural: {cultural_pref}, Interests: {', '.join(custom_activities) if custom_activities else 'None'}. Stay: {stay}. "
                f"Please ensure all costs are shown in Indian Rupees (₹, INR)."
            )

            st.session_state.messages.append({
                "role": "user",
                "content": short_prompt
            })
            st.session_state["pending_llm_prompt"] = short_prompt
            st.session_state.trip_context = {
                "origin": origin.strip(),
                "destination": destination.strip(),
                "from_date": from_date,
                "to_date": to_date,
                "traveler_type": traveler_type,
                "group_size": group_size,
                "dietary_pref": dietary_pref,
                "language_pref": language_pref,
                "sustainability": sustainability,
                "cultural_pref": cultural_pref,
                "custom_activities": custom_activities,
                "budget_amount": budget_amount,
                "currency_type": currency_type,
                "stay": stay
            }
            st.session_state.user_history.append(st.session_state.trip_context)
            st.session_state.pending_form_response = True
            st.session_state.form_submitted = True
            st.rerun()

# Render chat history above input
for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

user_input = st.chat_input(placeholder="How may I help you today?")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if is_greeting_or_planning(user_input):
        assistant_response = greeting_message
    else:
        N = 8
        chat_history = st.session_state.messages[-N:]
        messages = [{"role": "system", "content": STRICT_SYSTEM_PROMPT}] + chat_history
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=1800
            )
            assistant_response = response.choices[0].message.content
        except Exception as e:
            print("OpenAI API error:", e)
            st.error(f"OpenAI API error: {e}")
            assistant_response = "I'm unable to assist with creating itineraries at the moment. Let me know if you need help with anything else."

    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.rerun()

if st.session_state.pending_form_response:
    try:
        prompt = st.session_state["pending_llm_prompt"]
        messages = [{"role": "system", "content": STRICT_SYSTEM_PROMPT}]
        messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=1800
        )
        assistant_response = response.choices[0].message.content
    except Exception as e:
        print("OpenAI API error:", e)
        st.error(f"OpenAI API error: {e}")
        assistant_response = "I'm unable to assist with creating itineraries at the moment. Let me know if you need help with anything else."

    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.session_state.pending_form_response = False
    st.rerun()
