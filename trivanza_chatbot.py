import streamlit as st
from openai import OpenAI
from datetime import date

# ------------- CONFIG -------------
st.set_page_config(page_title="TRIVANZA - Your Smart Travel Buddy", layout="centered")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ------------- APP HEADER -------------
st.markdown(
    """
    <div style="display: flex; align-items: center; gap: 12px;">
        <img src="trivanza_logo.png" width="45px">
        <h2 style="margin: 0;">Trivanza – Smart Travel Planner</h2>
    </div>
    """,
    unsafe_allow_html=True
)

# ------------- SESSION STATE -------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_form" not in st.session_state:
    st.session_state.show_form = False

if "submitted" not in st.session_state:
    st.session_state.submitted = False

# ------------- CONTEXTUAL PROMPT GENERATOR -------------
def generate_contextual_prompt(user_query):
    if "travel_data" in st.session_state:
        data = st.session_state.travel_data
        context = f"""
You are TRIVANZA – a travel-specialized AI assistant. The user has already provided the following travel plan:

- Origin: {data['origin']}
- Destination: {data['destination']}
- Dates: {data['from_date']} to {data['to_date']}
- Transport: {data['transport']}
- Stay: {data['stay']}
- Budget: {data['budget']}
- Interests: {data['activities']}

Now they asked: \"{user_query}\"
Respond accordingly, remembering their earlier inputs.
"""
        return context
    else:
        return user_query

# ------------- CHAT INPUT -------------
user_input = st.chat_input("Say hi to Trivanza or ask your travel question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Check greeting to show form
    if user_input.lower().strip() in ["hi", "hello", "hey"]:
        st.session_state.show_form = True
        st.session_state.submitted = False
        st.session_state.messages.append({
            "role": "assistant",
            "content": """
👋 **Welcome to Trivanza: Your Smart Travel Companion**  
I'm excited to help you with your travel plans. To provide you with the best possible assistance, could you please share some details with me?

- What is your origin (starting location)?  
- What is your destination (where are you headed)?  
- What are your travel dates (from and to)?  
- What is your preferred mode of transport (flight, train, car, etc.)?  
- What are your accommodation preferences (hotel, hostel, etc.)?  
- What are your budget and currency type (INR, Dollar, Pound, etc.)?  
- Are there any specific activities or experiences you're looking to have during your trip?
"""
        })
    else:
        try:
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
                        {"role": "user", "content": generate_contextual_prompt(user_input)}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                answer = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"🚨 Error: {e}"})

# ------------- DISPLAY CHAT HISTORY -------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------- TRAVEL FORM (Only on greeting) -------------
if st.session_state.show_form and not st.session_state.submitted:
    with st.form("travel_form"):
        st.markdown("""
### 📝 Let's plan your trip!
I'm excited to help you with your travel plans. To provide you with the best possible assistance, could you please share some details with me?
""")

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

            st.session_state.travel_data = {
                "origin": origin,
                "destination": destination,
                "from_date": from_date,
                "to_date": to_date,
                "transport": transport,
                "stay": stay,
                "budget": budget,
                "activities": activities
            }

            prompt = f"""
You are TRIVANZA – a travel-specialized AI assistant.

🎯 PURPOSE:
Provide personalized, real-world travel itineraries based on user input.
Respond ONLY with travel-related content.
Provide booking links, costs, realistic suggestions, and budget comparison.

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
- Include daily breakdown (Day 1, Day 2…)
- Show: transport, hotel, food, activity with links & prices
- Estimate cost per item and daily total
- Show full trip cost at the end
- If budget is too low, show estimated cost vs. budget and suggest trade-offs
- Always end with: "Would you like to make any changes or adjustments?"

💡 Use trusted platforms:
Flights: Skyscanner, Google Flights, MakeMyTrip or best at destination
Hotels: Booking.com, Agoda, Airbnb  or best at destination
Food: Zomato, Swiggy, TripAdvisor  or best at destination
Transport: Uber, Redbus, Zoomcar or best at destination
Activities: Viator, Klook, GetYourGuide or best at destination

📌 Format everything in Markdown.
            """

            try:
                with st.spinner("🧳 Making your perfect Trip itinerary..."):
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
                st.session_state.messages.append({"role": "assistant", "content": f"❌ Unable to generate itinerary. Error: {e}"})
