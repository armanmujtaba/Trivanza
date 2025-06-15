import streamlit as st
from openai import OpenAI
from datetime import date

# ------------- CONFIG -------------
st.set_page_config(page_title="TRIVANZA - Your Smart Travel Buddy", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ------------- APP HEADER -------------
col1, col2 = st.columns([0.1, 0.9])
with col1:
    st.image("trivanza_logo.png", width=60)
with col2:
    st.markdown("## TRIVANZA - Your Smart Travel Buddy")

# ------------- SESSION STATE -------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_form" not in st.session_state:
    st.session_state.show_form = False

if "submitted" not in st.session_state:
    st.session_state.submitted = False

# ------------- CHAT INPUT -------------
user_input = st.chat_input("Say hi to Trivanza or ask your travel question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if user_input.lower().strip() in ["hi", "hello", "hey"]:
        st.session_state.show_form = True
        st.session_state.submitted = False

        st.session_state.messages.append({
            "role": "assistant",
            "content": """👋 **Welcome to Trivanza: Your Smart Travel Companion**"""
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
Provide intelligent, budget-aware travel planning. Always give real-world cost estimates, day-by-day itineraries, and booking links. Avoid non-travel content.

✅ Topics:
• Personalized itineraries
• Budget/currency planning
• Booking links (flights, stays, food, activities)
• Travel safety, insurance, health
• Cultural tips
• Sustainable travel

❌ If unrelated to travel: "This chat is strictly about Travel and TRIVANZA’s features. Please ask Travel-related questions."

📌 Format replies in **Markdown**
"""},
                        {"role": "user", "content": user_input}
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


# ------------- TRAVEL FORM -------------
if st.session_state.show_form and not st.session_state.submitted:
    with st.form("travel_form"):
        st.markdown("""
### 📝 Welcome to Trivanza: Your Smart Travel Companion

I'm excited to help you with your travel plans. Please fill out the form below:
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
            st.session_state.show_form = False  # Hide form after submission

            prompt = f"""
You are TRIVANZA – a travel-specialized AI assistant.

🎯 Generate a complete personalized itinerary based on this info:

- Origin: {origin}
- Destination: {destination}
- Dates: {from_date} to {to_date}
- Transport: {transport}
- Stay: {stay}
- Budget: {budget}
- Activities: {activities}

📋 Format:
- Title: e.g. “6-Day Vietnam Escape – Mid Budget”
- Daily breakdown (Day 1, Day 2…)
- Include prices & links for: transport, hotel, food, activities
- Estimate total daily and trip cost
- Compare to budget. Suggest cheaper/better options if needed
- Always end with: "Would you like to make any changes or adjustments?"

🧾 Trusted sources:
Flights: Skyscanner, Google Flights  
Stays: Booking.com, Agoda, Airbnb  
Food: Zomato, Swiggy, TripAdvisor  
Transport: Uber, Redbus, Zoomcar  
Activities: Viator, GetYourGuide, Klook

Format response in **Markdown**
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
                    st.session_state.messages.append({"role": "assistant", "content": itinerary})
                    st.chat_message("assistant").markdown(itinerary)
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"❌ Error: {e}"})
