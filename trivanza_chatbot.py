import streamlit as st
import openai
import re
from datetime import date

# --------- CONFIG ---------
st.set_page_config(page_title="Trivanza Travel Assistant", layout="centered")
openai.api_key = st.secrets.get("OPENAI_API_KEY")

# --------- SESSION INIT ---------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "trip_context" not in st.session_state:
    st.session_state.trip_context = None
if "pending_form_response" not in st.session_state:
    st.session_state.pending_form_response = False

# --------- CUSTOM HEADER ---------
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
</style>
<div class="logo-container">
    <img class="logo" src="https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/Trivanza.png?raw=true">
</div>
""", unsafe_allow_html=True)

# --------- SYSTEM PROMPT ---------
system_content = (
    "You are TRIVANZA Travel Assistant. Only answer travel-related questions within the following topics: "
    "travel problem-solving (cancellations, theft, health issues), personalized itineraries (day-by-day, by budget, by interests, events), "
    "real-time alerts (weather, political unrest, flight delays), smart packing (checklists by weather & activity), "
    "culture & language (local etiquette, translations), health & insurance (local medical help, insurance), "
    "sustainable travel (eco-friendly stays, eco-transport), live translation (signs, speech, receipts), "
    "budget & currency planning, and expense categories (flight, hotel, food, transport). "
    "If the user asks anything outside these topics, reply with: \"This chat is strictly about Travel and TRIVANZA’s features. Please ask Travel-related questions.\"\n"
    "Always provide intelligent, personalized, budget-aware travel planning assistance. "
    "Give real cost estimates for every element (flight, hotel, food, transport), daily plans, and booking links for key components. "
    "When providing itineraries, break them down by day (Day 1, Day 2, etc.) with Morning/Afternoon/Evening blocks. "
    "Include the cost per day and total cost. "
    "If the user's budget is too low, calculate the true cost of the trip and suggest trade-offs or alternatives."
)

# --------- CHAT HELPER ---------
def get_chat_response():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": system_content}] + st.session_state.messages,
            temperature=0.7,
            max_tokens=1800
        )
        return response.choices[0].message['content']
    except Exception as e:
        return f"Sorry, I couldn't generate your itinerary right now.\n\nError: {str(e)}"

# --------- FORM ---------
with st.expander("📋 Plan My Trip", expanded=not st.session_state.form_submitted):
    with st.form("travel_form", clear_on_submit=False):
        st.markdown("### 🧳 Let's plan your perfect trip!")

        col1, col2 = st.columns(2)
        with col1:
            traveler_type = st.selectbox("🧍 Traveler Type", ["Solo", "Couple", "Family", "Group"])
            group_size = st.number_input("👥 Group Size", min_value=1, value=2)
        with col2:
            origin = st.text_input("🌍 Origin", placeholder="e.g., Delhi")
            destination = st.text_input("📍 Destination", placeholder="e.g., Paris")
        col3, col4 = st.columns(2)
        with col3:
            from_date = st.date_input("📅 From Date", min_value=date.today())
        with col4:
            to_date = st.date_input("📅 To Date", min_value=from_date)

        st.markdown("#### 💰 Budget & Stay")
        col5, col6 = st.columns(2)
        with col5:
            budget_amount = st.number_input("💰 Budget", min_value=1000, step=1000)
        with col6:
            currency_type = st.selectbox("💱 Currency", ["₹ INR", "$ USD", "€ EUR", "£ GBP", "¥ JPY"])
        stay = st.selectbox("🏨 Stay Type", ["Hotel", "Hostel", "Airbnb", "Resort"])

        st.markdown("#### 🎯 Preferences & Interests")
        dietary_pref = st.multiselect("🥗 Dietary", ["Vegetarian", "Vegan", "Gluten-Free", "Halal", "Kosher"])
        sustainability = st.selectbox("🌱 Sustainability", ["None", "Eco-Friendly Stays", "Carbon Offset Flights", "Zero-Waste Activities"])
        language_pref = st.selectbox("🌐 Language", ["English", "Hindi", "French", "Spanish", "Mandarin", "Local Phrases"])
        cultural_pref = st.selectbox("👗 Cultural Sensitivity", ["Standard", "Conservative Dress", "Religious Holidays", "Gender Norms"])
        custom_activities = st.multiselect("🎨 Interests", [
            "Beaches", "Hiking", "Shopping", "Nightlife", 
            "Cultural Immersion", "Foodie Tour", "Adventure Sports"
        ])

        submit = st.form_submit_button("🚀 Generate Itinerary")

        if submit:
            if not origin.strip():
                st.error("❌ Enter your origin city!")
            elif not destination.strip():
                st.error("❌ Enter your destination!")
            elif to_date < from_date:
                st.error("❌ End date must be after start date!")
            elif budget_amount <= 0:
                st.error("❌ Budget must be greater than 0")
            else:
                st.success("✅ Generating your personalized itinerary...")
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
                st.session_state.messages.append({
                    "role": "user",
                    "content": f"Plan a trip from {origin} to {destination} from {from_date} to {to_date} for a {traveler_type.lower()} of {group_size} people. Budget: {currency_type} {budget_amount}. Stay: {stay}. Interests: {', '.join(custom_activities)}. Language: {language_pref}. Sustainability: {sustainability}."
                })
                st.session_state.pending_form_response = True
                st.session_state.form_submitted = True
                st.rerun()

# --------- CHAT MODULE ---------
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("💬 Ask Trivanza anything travel-related:")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    assistant_response = get_chat_response()
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.rerun()

# --------- PROCESS FORM RESPONSE ---------
if st.session_state.pending_form_response:
    assistant_response = get_chat_response()
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.session_state.pending_form_response = False
    st.rerun()

# --------- DISPLAY CHAT ---------
for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
