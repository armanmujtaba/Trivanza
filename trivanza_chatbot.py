import streamlit as st
import openai
import re
from datetime import date

# Set your OpenAI API key (from secrets)
openai.api_key = st.secrets.get("OPENAI_API_KEY")

st.set_page_config(page_title="Trivanza", layout="centered")
st.title("Trivanza Travel Assistant")

# Initialize session state
for key in ["messages", "trip_context", "form_submitted", "show_form", "pending_form_response"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else (True if key == "show_form" else False)

# System Prompt
system_content = (
    "You are TRIVANZA Travel Assistant. Only answer travel-related questions within the following topics: "
    "travel problem-solving, personalized itineraries, real-time alerts, smart packing, culture & language, health & insurance, sustainable travel, budget & currency planning. "
    "Always provide personalized, intelligent, budget-aware assistance with real cost estimates. "
    "Break itineraries by day and time (Morning/Afternoon/Evening) and include costs, tips, and links if possible."
)

# ----------------- CUSTOM HEADER -----------------
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

# ----------------- TRAVEL FORM -----------------
if st.session_state.show_form and not st.session_state.form_submitted:
    with st.form("travel_form", clear_on_submit=False):
        st.markdown("### 🧳 Let's plan your perfect trip!")

        col1, col2 = st.columns(2)
        with col1:
            traveler_type = st.selectbox("🧟 Traveler Type", ["Solo", "Couple", "Family", "Group"], key="traveler_type")
        with col2:
            group_size = st.number_input("👥 Group Size", min_value=1, value=2, key="group_size")

        col3, col4 = st.columns(2)
        with col3:
            origin = st.text_input("🌍 Origin", placeholder="e.g., Delhi", key="origin_input")
        with col4:
            destination = st.text_input("📍 Destination", placeholder="e.g., Paris", key="dest_input")
        col5, col6 = st.columns(2)
        with col5:
            from_date = st.date_input("🗕️ From Date", min_value=date.today(), key="from_date_input")
        with col6:
            to_date = st.date_input("🗕️ To Date", min_value=from_date, key="to_date_input")

        col7, col8 = st.columns(2)
        with col7:
            dietary_pref = st.multiselect("🥗 Dietary Preferences", ["Vegetarian", "Vegan", "Gluten-Free", "Halal", "Kosher"], key="dietary_pref")
            sustainability = st.selectbox("🌱 Sustainability", ["None", "Eco-Friendly Stays", "Carbon Offset Flights", "Zero-Waste Activities"], key="sustainability")
        with col8:
            language_pref = st.selectbox("🌐 Language", ["English", "Hindi", "French", "Spanish", "Mandarin", "Local Phrases"], key="language_pref")
            cultural_pref = st.selectbox("👗 Cultural Sensitivity", ["Standard", "Conservative Dress", "Religious Holidays", "Gender Norms"], key="cultural_pref")

        col9, col10 = st.columns(2)
        with col9:
            budget_amount = st.number_input("💰 Budget Amount", min_value=1000, step=1000, key="budget_amount")
        with col10:
            currency_type = st.selectbox("💱 Currency", ["₹ INR", "$ USD", "€ EUR", "£ GBP", "¥ JPY"], key="currency_type")
        stay = st.selectbox("🏨 Accommodation", ["Hotel", "Hostel", "Airbnb", "Resort"], key="stay_input")

        custom_activities = st.multiselect("🎨 Interests", ["Beaches", "Hiking", "Shopping", "Nightlife", "Cultural Immersion", "Foodie Tour", "Adventure Sports"], key="custom_activities")

        submit = st.form_submit_button("🚀 Generate My Itinerary", use_container_width=True)

        if submit:
            if not origin.strip():
                st.error("❌ Please enter your origin city!")
            elif not destination.strip():
                st.error("❌ Please enter your destination!")
            elif to_date < from_date:
                st.error("❌ End date must be after start date!")
            elif budget_amount <= 0:
                st.error("❌ Budget must be greater than 0")
            else:
                trip_data = {
                    "origin": origin.strip(),
                    "destination": destination.strip(),
                    "from_date": from_date,
                    "to_date": to_date,
                    "traveler_type": traveler_type,
                    "group_size": str(group_size),
                    "dietary_pref": dietary_pref,
                    "language_pref": language_pref,
                    "sustainability": sustainability,
                    "cultural_pref": cultural_pref,
                    "custom_activities": custom_activities,
                    "budget_amount": str(budget_amount),
                    "currency_type": currency_type,
                    "currency": currency_type.split()[0],
                    "stay": stay
                }
                st.session_state.trip_context = trip_data
                st.session_state.form_submitted = True
                st.session_state.show_form = False
                st.session_state.pending_form_response = True
                st.rerun()

# ----------------- HANDLE FORM-BASED CHAT -----------------
if st.session_state.pending_form_response:
    ctx = st.session_state.trip_context
    user_query = (
        f"Plan a personalized itinerary from {ctx['origin']} to {ctx['destination']} between {ctx['from_date']} and {ctx['to_date']} "
        f"for a {ctx['traveler_type'].lower()} group of {ctx['group_size']} people. "
        f"Budget: {ctx['currency_type']} {ctx['budget_amount']}. Stay preference: {ctx['stay']}. "
        f"Interests: {', '.join(ctx['custom_activities']) if ctx['custom_activities'] else 'general sightseeing'}. "
        f"Language preference: {ctx['language_pref']}. Sustainability: {ctx['sustainability']}. "
        f"Cultural preferences: {ctx['cultural_pref']}. Dietary: {', '.join(ctx['dietary_pref']) if ctx['dietary_pref'] else 'None'}."
    )

    all_messages = [{"role": "system", "content": system_content}] + st.session_state.messages + [
        {"role": "user", "content": user_query}
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=all_messages,
            temperature=0.7,
            max_tokens=1200
        )
        assistant_response = response.choices[0].message['content']
    except Exception as e:
        assistant_response = f"❌ Error: Unable to generate your itinerary.\n\n```\n{str(e)}\n```"

    st.session_state.messages.append({"role": "user", "content": user_query})
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.session_state.pending_form_response = False
    st.rerun()

# ----------------- CHAT DISPLAY -----------------
for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
