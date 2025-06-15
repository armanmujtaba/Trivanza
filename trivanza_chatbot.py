import streamlit as st
from openai import OpenAI
from datetime import date

# ----------------- Configuration -----------------
st.set_page_config(page_title="Trivanza Smart Travel Planner", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ----------------- Branding -----------------
col1, col2 = st.columns([1, 6])
with col1:
    st.image("trivanza_logo.png", width=60)  # Ensure this logo exists in your app directory
with col2:
    st.markdown("## ✈️ TRIVANZA – Smart Travel Planner")

st.markdown("---")

# ----------------- Session State -----------------
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# ----------------- Chat Input & Greeting -----------------
user_input = st.chat_input("Say hi to Trivanza or ask your travel question...")

if user_input and not st.session_state.submitted:
    if user_input.strip().lower() in ["hi", "hello", "hey"]:
        with st.chat_message("assistant"):
            st.markdown("""
👋 **Welcome to Trivanza: Your Smart Travel Companion**  
I'm excited to help you with your travel plans. To provide you with the best possible assistance, could you please share some details with me?

- What is your origin (starting location)?  
- What is your destination (where are you headed)?  
- What are your travel dates (from and to)?  
- What is your preferred mode of transport (flight, train, car, etc.)?  
- What are your accommodation preferences (hotel, hostel, etc.)?  
- What are your budget and currency type (INR, Dollar, Pound, etc.)?  
- Are there any specific activities or experiences you're looking to have during your trip?
            """)
    else:
        try:
            with st.chat_message("assistant"):
                with st.spinner("✈️ Fetching the best answer for your travel query..."):
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": """
You are TRIVANZA – a travel-specialized AI assistant.

🎯 PURPOSE:
Provide real-time, intelligent, personalized, and budget-conscious travel planning. Always give real cost estimates, daily itineraries, and booking links. Never answer non-travel questions. Always suggest best-rated options within the user's budget.

✅ ALLOWED TOPICS:
1. Travel problem-solving (cancellations, theft, health issues)
2. Personalized itineraries (day-by-day, by budget, interest, events)
3. Real-time alerts (weather, political unrest, flight delays)
4. Smart packing assistant (checklists by weather & activity)
5. Culture & Language (local etiquette, translations)
6. Health & Insurance (local medical help, insurance)
7. Sustainable travel tips (eco-stays, transport)
8. Live translation help (signs, speech, receipts)
9. Budget & currency planning
10. Expense categories (flight, hotel, food, transport)

❌ If asked something unrelated to travel, respond with:
"This chat is strictly about Travel and TRIVANZA’s features. Please ask Travel-related questions."

🧾 FORMAT all responses in Markdown. Include booking links when suggesting flights, stays, food or activities.
"""},
                            {"role": "user", "content": user_input}
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
                    st.markdown(response.choices[0].message.content)
        except Exception as e:
            st.error("🚨 Error responding to your query.")
            st.exception(e)

# ----------------- Travel Form & Itinerary -----------------
with st.form("travel_form"):
    st.markdown("### 📝 Let's plan your trip!")

    origin = st.text_input("🌍 Origin", placeholder="e.g., Delhi")
    destination = st.text_input("📍 Destination", placeholder="e.g., Vietnam")

    # NEW DATE PICKERS
    from_date = st.date_input("📅 Start Date", min_value=date.today())
    to_date = st.date_input("📅 End Date", min_value=from_date)

    transport = st.selectbox("🛫 Mode of Transport", ["Flight", "Train", "Car", "Bus"])
    stay = st.selectbox("🏨 Accommodation", ["Hotel", "Hostel", "Airbnb", "Resort"])
    budget = st.text_input("💰 Budget (e.g., ₹50000 INR or $800 USD)")
    activities = st.text_area("🎯 Desired Activities", placeholder="e.g., hiking, beach, food tour")

    submitted = st.form_submit_button("Generate Itinerary")

    if submitted:
        st.session_state.submitted = True
        travel_dates = f"{from_date.strftime('%d %b %Y')} to {to_date.strftime('%d %b %Y')}"

        prompt = f"""
You are TRIVANZA – a travel-specialized AI assistant.

🎯 PURPOSE:
Provide personalized, real-world travel itineraries based on user input.
Respond ONLY with travel-related content.
Provide booking links, costs, realistic suggestions, and budget comparison.

User Inputs:
- Origin: {origin}
- Destination: {destination}
- Dates: {travel_dates}
- Transport: {transport}
- Stay: {stay}
- Budget: {budget}
- Interests: {activities}

💸 ITINERARY REQUIREMENTS:
- Give a title (e.g., "6-Day Vietnam Adventure – Mid-Budget")
- Include daily breakdown (Day 1, Day 2…)
- Show: transport, hotel, food, activity with links & prices
- Estimate cost per item and daily total
- Show full trip cost at the end
- If budget is too low, show estimated cost vs. budget and suggest trade-offs
- Always end with: "Would you like to make any changes or adjustments?"

💡 Use trusted platforms:
Flights: Skyscanner, Google Flights, MakeMyTrip  
Hotels: Booking.com, Agoda, Airbnb  
Food: Zomato, Swiggy, TripAdvisor  
Transport: Uber, Redbus, Zoomcar  
Activities: Viator, Klook, GetYourGuide

📌 Format everything in Markdown.
        """

        try:
            with st.spinner("🧳 Planning your perfect trip..."):
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
                with st.chat_message("assistant"):
                    st.markdown(itinerary)
        except Exception as e:
            st.error("❌ Unable to generate itinerary. Please check your OpenAI key or try again later.")
            st.exception(e)
