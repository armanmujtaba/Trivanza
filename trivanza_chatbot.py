import streamlit as st
from openai import OpenAI
from datetime import date

# ----------------- CONFIG -----------------
st.set_page_config(page_title="TRIVANZA – Your Smart Travel Buddy", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ----------------- HEADER -----------------
st.markdown("""
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
    <img src="https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" width="45px">
    <h2 style="margin: 0;">TRIVANZA – Your Smart Travel Buddy</h2>
</div>
""", unsafe_allow_html=True)

# ----------------- STATE INIT -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_form" not in st.session_state:
    st.session_state.show_form = False

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "trip_context" not in st.session_state:
    st.session_state.trip_context = {}

# ----------------- OPENAI CHAT -----------------
def get_response(messages):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content

# ----------------- CHAT INPUT -----------------
user_input = st.chat_input("Say Hi to Trivanza or ask your travel-related question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if user_input.strip().lower() in ["hi", "hello", "hey"]:
        st.session_state.show_form = True
        st.session_state.submitted = False
        st.session_state.messages.append({
            "role": "assistant",
            "content": "👋 **Hello Traveller! Welcome to Trivanza – Your Smart Travel Buddy**\nPlease fill out the form below to get your itinerary."
        })
    else:
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"""
You are TRIVANZA – a travel-specialized AI assistant.

🎯 PURPOSE:
Generate strict, structured travel itineraries and answer travel-related queries using context below.

📌 CONTEXT:
Origin: {st.session_state.trip_context.get("origin", "Not provided")}
Destination: {st.session_state.trip_context.get("destination", "Not provided")}
Dates: {st.session_state.trip_context.get("from_date", "")} to {st.session_state.trip_context.get("to_date", "")}
Transport: {st.session_state.trip_context.get("transport", "")}
Stay: {st.session_state.trip_context.get("stay", "")}
Budget: {st.session_state.trip_context.get("budget", "")}
Activities: {st.session_state.trip_context.get("activities", "")}

✅ Format answers in Markdown
✅ All suggestions should be real, bookable, with estimated pricing
✅ Avoid repeated or generic replies. No filler
"""
                }
            ] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]

            with st.spinner("✈️ Planning your response..."):
                bot_reply = get_response(messages)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ Error: {e}"})

# ----------------- CHAT HISTORY -----------------
for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ----------------- FORM DISPLAY -----------------
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

            prompt = f"""
You are TRIVANZA – a travel-specialized AI assistant.

Please generate a structured, mid-budget travel itinerary for:
- Origin: {origin}
- Destination: {destination}
- Dates: {from_date} to {to_date}
- Transport: {transport}
- Stay: {stay}
- Budget: {budget}
- Activities: {activities}

🎯 Follow this FORMAT:

**6-Day [Destination] Itinerary – Mid-Budget**

Day 1: Title  
✈️ Flight: Details + INR/₹  
🏨 Hotel: Name + Price + Booking.com Link  
🍽️ Meals: Restaurant Suggestion + Cost + Zomato Link  
🚕 Transport: Local Ride + Cost  
🎟️ Activities: Entry ticket + Link  
🎯 Daily Total: ₹____

Repeat for each day.

📌 At the end:
**Budget Summary**  
- Flights: ₹___  
- Hotels: ₹___  
- Food: ₹___  
- Activities: ₹___  
- Total: ₹___

Finish with:  
**Would you like to make any changes or adjustments?**
"""

            try:
                with st.spinner("🎯 Crafting your itinerary..."):
                    itinerary = get_response([
                        {"role": "system", "content": "You are TRIVANZA – a travel-specialized AI assistant."},
                        {"role": "user", "content": prompt}
                    ])
                    st.session_state.messages.append({"role": "assistant", "content": itinerary})
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"❌ Error generating itinerary: {e}"})
