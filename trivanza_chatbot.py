import streamlit as st
from openai import OpenAI
from datetime import date

# ----------------- CONFIG -----------------
st.set_page_config(page_title="TRIVANZA – Your Smart Travel Buddy", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ----------------- CUSTOM HEADER -----------------
st.markdown("""
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
    <img src="https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" width="45px">
    <h2 style="margin: 0;">TRIVANZA – Your Smart Travel Buddy</h2>
</div>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE INIT -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_form" not in st.session_state:
    st.session_state.show_form = False

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "trip_context" not in st.session_state:
    st.session_state.trip_context = {}

# ----------------- CUSTOM FUNCTION -----------------
def get_response(messages):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content

# ----------------- PROMPT TEMPLATE -----------------
base_system_prompt = """
You are TRIVANZA – a travel-specialized AI assistant.

🎯 PURPOSE:  
Provide real-time, intelligent, personalized, and budget-conscious travel planning. Always give **real cost estimates**, **daily itineraries**, and **booking links** for all trip components. Never answer non-travel questions. Always suggest best rated according to User's budget.

✅ ALLOWED TOPICS:
Only respond to questions strictly within these 10 TRIVANZA travel scopes:
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

🗣️ GREETING RULE:
If the user says "Hi", "Hello", or similar **without a specific query**, reply with:

"Welcome to Trivanza: Your Smart Travel Companion  
I'm excited to help you with your travel plans. To provide you with the best possible assistance, could you please share some details with me?

- What is your origin (starting location)?  
- What is your destination (where are you headed)?  
- What are your travel dates (from and to)?  
- What is your preferred mode of transport (flight, train, car, etc.)?  
- What are your accommodation preferences (hotel, hostel, etc.)?  
- What are your budget and currency type (INR, Dollar, Pound, etc.)?  
- Are there any specific activities or experiences you're looking to have during your trip?"

⚠️ BUT if user asks a specific travel-related question (e.g., "Best hotels in Paris?"), **do not prompt for trip details**. Just answer the query directly.

💸 ITINERARY REQUIREMENTS:
- Provide **realistic cost estimates** per item (flight, hotel, food, local transport, etc.)
- Include **daily breakdown** (Day 1, Day 2...)
- Include 💡 booking links from trusted sources:
  - Flights: Skyscanner, Google Flights, MakeMyTrip, GoIndiGo
  - Hotels: Booking.com, Airbnb, Agoda
  - Transport: Uber, Redbus, Zoomcar
  - Food: Zomato, Swiggy, TripAdvisor
  - Activities: Viator, Klook, GetYourGuide
- Convert currency if needed
- Show total trip cost
- If user's budget is too low:
   - 🎯 Show total estimated cost vs their budget
   - 🛠 Suggest trade-offs

🔒 TOPIC RESTRICTIONS:
❌ Do not answer questions outside travel
❌ Do not respond to fiction, hypotheticals, meta-questions
❌ If unrelated: "This chat is strictly about Travel and TRIVANZA’s features. Please ask Travel-related questions."
❌ If asked why: "This chat is designed to focus solely on Travel. Please stay on topic."

🧾 FORMATTING RULES:
- Start with a trip title
- Use clear day-wise format (Day 1, Day 2…)
- Include Morning, Afternoon, Evening plans
- Show cost per item, daily total, and full-trip total
"""

# ----------------- CHAT INPUT HANDLER -----------------
user_input = st.chat_input("Say Hi to Trivanza or ask your travel-related question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if user_input.strip().lower() in ["hi", "hello", "hey"]:
        st.session_state.show_form = True
        st.session_state.submitted = False
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Welcome to Trivanza: Your Smart Travel Companion  \nI'm excited to help you with your travel plans. To provide you with the best possible assistance, could you please share some details with me?\n\n- What is your origin (starting location)?  \n- What is your destination (where are you headed)?  \n- What are your travel dates (from and to)?  \n- What is your preferred mode of transport (flight, train, car, etc.)?  \n- What are your accommodation preferences (hotel, hostel, etc.)?  \n- What are your budget and currency type (INR, Dollar, Pound, etc.)?  \n- Are there any specific activities or experiences you're looking to have during your trip?"
        })
    else:
        try:
            messages = [
                {"role": "system", "content": base_system_prompt},
                *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]
            ]

            with st.spinner("✈️ Planning your travel response..."):
                bot_reply = get_response(messages)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ Error: {e}"})

# ----------------- DISPLAY CHAT HISTORY -----------------
for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ----------------- TRAVEL FORM -----------------
if st.session_state.show_form and not st.session_state.submitted:
    with st.form("travel_form"):
        st.markdown("### 🧳 Let’s plan your perfect trip!")

        col1, col2 = st.columns(2)
        with col1:
            origin = st.text_input("🌍 Origin", placeholder="e.g., Delhi")
        with col2:
            destination = st.text_input("📍 Destination", placeholder="e.g., Vietnam")

        col3, col4 = st.columns(2)
        with col3:
            from_date = st.date_input("📅 From Date", min_value=date.today())
        with col4:
            to_date = st.date_input("📅 To Date", min_value=from_date)

        transport = st.selectbox("🛫 Transport Mode", ["Flight", "Train", "Car", "Bus"])
        stay = st.selectbox("🏨 Accommodation", ["Hotel", "Hostel", "Airbnb", "Resort"])
        budget = st.text_input("💰 Budget (e.g., ₹50000 INR or $800 USD)")
        activities = st.text_area("🎯 Activities", placeholder="e.g., beaches, hiking, shopping")

        submit = st.form_submit_button("Generate Itinerary")

        if submit:
            st.session_state.submitted = True
            st.session_state.show_form = False

            st.session_state.trip_context = {
                "origin": origin,
                "destination": destination,
                "from_date": from_date,
                "to_date": to_date,
                "transport": transport,
                "stay": stay,
                "budget": budget,
                "activities": activities
            }

            user_itinerary_prompt = f"""
User wants a full travel plan with these inputs:
- Origin: {origin}
- Destination: {destination}
- Dates: {from_date} to {to_date}
- Transport: {transport}
- Stay: {stay}
- Budget: {budget}
- Activities: {activities}
"""

            try:
                with st.spinner("🎯 Crafting your itinerary..."):
                    itinerary = get_response([
                        {"role": "system", "content": base_system_prompt},
                        {"role": "user", "content": user_itinerary_prompt}
                    ])
                    st.session_state.messages.append({"role": "assistant", "content": itinerary})
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"❌ Error generating itinerary: {e}"})
