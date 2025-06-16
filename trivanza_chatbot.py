import streamlit as st
import openai
import re
from datetime import date

# Set your OpenAI API key from secrets
openai.api_key = st.secrets.get("OPENAI_API_KEY")

st.set_page_config(page_title="Trivanza Travel Planner")
st.title("Trivanza Travel Assistant")

# ----------------- SESSION INITIALIZATION -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "show_form" not in st.session_state:
    st.session_state.show_form = True
if "generating_itinerary" not in st.session_state:
    st.session_state.generating_itinerary = False

# ----------------- SYSTEM PROMPT -----------------
system_content = (
    "You are TRIVANZA Travel Assistant. Only answer travel-related questions within the following topics: "
    "🧳 Travel Purpose: Leisure, Business, Adventure, Educational, Medical, Pilgrimage, Cultural, Honeymoon, Volunteer, Conferences. "
    "🌍 Destination Preferences: Domestic/International, Region, Climate, Urban/Rural, Offbeat, Safety, Visa. "
    "📅 Travel Dates & Duration: Month/Season, Weekend or Long Travel, Peak/Off-Season. "
    "💵 Budget: Range, Inclusion Types, Currency Exchange, Splurge or Save Options. "
    "🏨 Accommodation: Hotel Type, Room Type, Amenities, Proximity, Pet-Friendly. "
    "✈️ Transportation: Flight/Train/Bus/Car, Class, Airport Transfer, Local Transport, Driving License Validity. "
    "🍽️ Dietary: Restrictions, Allergies, Tolerance, Cuisine Interest, Hygiene. "
    "👥 Group Composition: Solo, Couple, Family, Friends, Senior, Disabled, Pets. "
    "🧭 Activities: Sightseeing, Adventure, Wildlife, Beach, Shopping, Culture, Nightlife, Spa, Culinary, Photography, Spiritual. "
    "🩺 Health: Vaccines, Insurance, Medications, Warnings, Safety Tips. "
    "📱 Communication: Internet, Roaming, Language Tools, Time Zones, Apps. "
    "🛒 Shopping: Local Goods, Duty-Free, Bargaining, Limits. "
    "📜 Documentation: Passport, Visa, eSIM, Permits, Copies, Embassy. "
    "🧳 Packing: Weather Clothes, Toiletries, Gadgets, Security, Reusables. "
    "💬 Culture: Language Phrases, Etiquette, Dress Code, Tipping, Sacred Sites. "
    "📸 Photography: Camera Rules, Drones, Photo Spots, Privacy. "
    "🕰️ Time Management: Schedule Flexibility, Pace, Buffer Days. "
    "🤝 Interactions: Locals, Tours, Group Engagement, Guides. "
    "If the user asks anything outside these topics, reply with: 'This chat is strictly about Travel and TRIVANZA’s features. Please ask Travel-related questions.'\n"
    "Always provide intelligent, personalized, budget-aware travel planning assistance. "
    "Give real cost estimates for every element (flight, hotel, food, transport), daily plans, and booking links for key components. "
    "When providing itineraries, break them down by day (Day 1, Day 2, etc.) with Morning/Afternoon/Evening blocks. "
    "Include the cost per day and total cost. "
    "If the user's budget is too low, calculate the true cost of the trip and suggest trade-offs or alternatives."
)

# ----------------- TRAVEL FORM -----------------
if st.session_state.show_form and not st.session_state.form_submitted:
    with st.form("travel_form", clear_on_submit=False):
        st.markdown("### 🧳 Let's plan your perfect trip!")

        col1, col2 = st.columns(2)
        with col1:
            traveler_type = st.selectbox("🧍 Traveler Type", ["Solo", "Couple", "Family", "Group"], key="traveler_type")
        with col2:
            group_size = st.number_input("👥 Group Size", min_value=1, value=2, key="group_size")

        col3, col4 = st.columns(2)
        with col3:
            origin = st.text_input("🌍 Origin", placeholder="e.g., Delhi", key="origin_input")
        with col4:
            destination = st.text_input("📍 Destination", placeholder="e.g., Paris", key="dest_input")

        col5, col6 = st.columns(2)
        with col5:
            from_date = st.date_input("📅 From Date", min_value=date.today(), key="from_date_input")
        with col6:
            to_date = st.date_input("📅 To Date", min_value=from_date, key="to_date_input")

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

        custom_activities = st.multiselect("🎯 Interests", ["Beaches", "Hiking", "Shopping", "Nightlife", "Cultural Immersion", "Foodie Tour", "Adventure Sports"], key="custom_activities")

        submit = st.form_submit_button("🚀 Generate My Itinerary")

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
                st.session_state.generating_itinerary = True
                st.rerun()

# ----------------- TRIGGER ITINERARY GENERATION -----------------
if st.session_state.generating_itinerary and "trip_context" in st.session_state:
    trip = st.session_state.trip_context
    user_query = (
        f"Plan a trip from {trip['origin']} to {trip['destination']} from {trip['from_date']} to {trip['to_date']} "
        f"for a {trip['traveler_type']} of {trip['group_size']} people. "
        f"Budget: {trip['currency']} {trip['budget_amount']}. "
        f"Stay: {trip['stay']}. "
        f"Interests: {', '.join(trip['custom_activities']) or 'General Sightseeing'}. "
        f"Language: {trip['language_pref']}. "
        f"Sustainability: {trip['sustainability']}."
    )

    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.spinner("🧠 Generating personalized itinerary..."):
        try:
            messages = [{"role": "system", "content": system_content}] + st.session_state.messages
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            assistant_reply = response.choices[0].message["content"]
        except Exception as e:
            assistant_reply = f"Sorry, I couldn't generate your itinerary right now. ({str(e)})"

        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
        st.session_state.generating_itinerary = False
        st.rerun()

# ----------------- DISPLAY CHAT HISTORY -----------------
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**Trivanza:** {msg['content']}")
