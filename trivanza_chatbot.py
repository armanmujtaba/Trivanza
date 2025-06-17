import streamlit as st
from openai import OpenAI
import re
from datetime import date, timedelta

st.set_page_config(page_title="Trivanza Travel Assistant", layout="centered")
client = OpenAI()

def is_greeting_or_planning(text):
    greetings = [
        "hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings",
        "plan", "itinerary", "plan my trip", "journey", "my journey", "trip planning",
        "plan itinerary", "plan my itinerary", "trip", "travel"
    ]
    text_lower = text.lower()
    return any(greet in text_lower for greet in greetings)

SYSTEM_PROMPT = """
You are Trivanza, an expert AI travel assistant. 
For every itinerary, perform ALL calculations yourself.
For each day, list each item (flight, hotel, meal, activity, transport, etc.) with a cost.
At the end of each day, calculate and show the exact daily total (sum of all items).
After the last day, provide an overall cost breakdown with the grand total.
Format the ENTIRE output in Markdown, using headings, bullet points, and cost tables if needed.
NEVER leave calculations or formatting to the user or to code. Do not skip any calculations.
If the user requests a modification, recalculate and reformat everything as above.
Always ask after generating an itinerary: "Would you like any modifications or changes to your itinerary? If yes, please specify and I'll update it accordingly."
Example format:

## Day 1: Arrival in Paris (2025-08-01)
✈️ Flight: Delhi to Paris, ₹35,000 [Book](https://...)
🚕 Airport transfer, ₹2,000 [Book](https://...)
🏨 Hotel: Ibis Paris, ₹6,000 [Book](https://...)
🍽️ Dinner at Le Relais, ₹1,500 [Book](https://...)
🎯 Daily Total: ₹44,500

*(Sum = 35000 + 2000 + 6000 + 1500 = 44,500)*

After all days, provide:
- Cost breakdown by category
- Packing checklist for the destination/month
- Budget analysis
- Destination Pro Tip
- **Grand Total: ₹sum**
"""

greeting_message = """Hello Traveler! Welcome to Trivanza - I'm Your Smart Travel Companion  
I'm excited to help you with your travel plans.
- Submit Plan My Trip form for customised itinerary  
- Use chat box for your other travel related queries"""

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

            days = (to_date - from_date).days + 1
            month = from_date.strftime("%B")
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

            trip_context = {
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
            st.session_state.trip_context = trip_context
            st.session_state.user_history.append(trip_context)
            st.session_state.pending_form_response = True
            st.session_state.form_submitted = True
            st.rerun()

# Render chat history above input
for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Chat input at the bottom
user_input = st.chat_input(placeholder="How may I help you today?")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if is_greeting_or_planning(user_input):
        assistant_response = greeting_message
    else:
        N = 8
        chat_history = st.session_state.messages[-N:]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_history
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
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
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
