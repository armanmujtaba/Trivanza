import streamlit as st
from openai import OpenAI
from datetime import date

# ----------------- CONFIG -----------------
st.set_page_config(page_title="TRIVANZA - Your Smart Travel Buddy", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ----------------- APP HEADER -----------------
st.markdown("""
<div style="display: flex; align-items: center; gap: 12px;">
    <img src="https://i.imgur.com/fnJLrMq.png" width="45px">
    <h2 style="margin: 0;">Trivanza – Smart Travel Planner</h2>
</div>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_form" not in st.session_state:
    st.session_state.show_form = False

if "submitted" not in st.session_state:
    st.session_state.submitted = False

# ----------------- CHAT INPUT -----------------
user_input = st.chat_input("Say hi to Trivanza or ask your travel question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if user_input.strip().lower() in ["hi", "hello", "hey"]:
        st.session_state.show_form = True
        st.session_state.submitted = False
        st.session_state.messages.append({
            "role": "assistant",
            "content": """
👋 **Welcome to Trivanza: Your Smart Travel Companion**  
I'm excited to help you with your travel plans. To get started, please fill in the trip planner form below.
"""})
    else:
        try:
            with st.spinner("✈️ Fetching the best answer for your travel query..."):
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": """
You are TRIVANZA – a travel-specialized AI assistant.

🎯 PURPOSE:
Provide real-time, intelligent, personalized, and budget-conscious travel planning. Always give real cost estimates, daily itineraries, and booking links. Never answer non-travel questions.

🧾 FORMAT all responses in Markdown. Include booking links when suggesting flights, stays, food or activities.
                        """},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                reply = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"🚨 Error: {str(e)}"})

# ----------------- DISPLAY CHAT HISTORY -----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ----------------- TRAVEL FORM -----------------
if st.session_state.show_form and not st.session_state.submitted:
    with st.form("travel_form"):
        st.markdown("### 📝 Let's plan your trip")

        col1, col2 = st.columns(2)
        with col1:
            origin = st.text_input("🌍 Origin", placeholder="e.g., New Delhi")
        with col2:
            destination = st.text_input("📍 Destination", placeholder="e.g., Paris")

        col3, col4 = st.columns(2)
        with col3:
            from_date = st.date_input("📅 From Date", min_value=date.today())
        with col4:
            to_date = st.date_input("📅 To Date", min_value=from_date)

        transport = st.selectbox("🛫 Mode of Transport", ["Flight", "Train", "Car", "Bus"])
        stay = st.selectbox("🏨 Accommodation", ["Hotel", "Hostel", "Airbnb", "Resort"])
        budget = st.text_input("💰 Budget (e.g., ₹50000 INR or $800 USD)")
        activities = st.text_area("🎯 Desired Activities", placeholder="e.g., hiking, beach, food tour")

        submitted = st.form_submit_button("Plan My Trip")

        if submitted:
            st.session_state.submitted = True

            prompt = f"""
You are TRIVANZA – a travel-specialized AI assistant.

🎯 PURPOSE:
Provide personalized, real-world travel itineraries based on user input.  
Provide booking links, realistic suggestions, and compare budget vs. estimate.

User Inputs:
- Origin: {origin}
- Destination: {destination}
- Dates: {from_date} to {to_date}
- Transport: {transport}
- Stay: {stay}
- Budget: {budget}
- Interests: {activities}

💸 ITINERARY REQUIREMENTS:
- Give a title (e.g., "6-Day Vietnam Adventure – Mid-Budget")
- Daily breakdown (Day 1, Day 2…)
- Include: transport, stay, food, activities with links & prices
- Show estimated daily and total cost
- Warn if budget is too low and suggest trade-offs
- Always end with: "Would you like to make any changes or adjustments?"

💡 Use trusted platforms:
Flights: Skyscanner, Google Flights, MakeMyTrip  
Stays: Booking.com, Agoda, Airbnb  
Food: TripAdvisor, Zomato  
Transport: Uber, Zoomcar, RedBus  
Activities: Viator, Klook, GetYourGuide

📌 Respond in Markdown format.
            """

            try:
                with st.spinner("🧳 Crafting your perfect itinerary..."):
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are TRIVANZA – a travel-specialized AI assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.8,
                        max_tokens=1800
                    )
                    itinerary = response.choices[0].message.content
                    st.session_state.messages.append({"role": "assistant", "content": itinerary})
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"❌ Error generating itinerary: {str(e)}"})
