import streamlit as st
from openai import OpenAI
from datetime import date

# -------------- CONFIG ----------------
st.set_page_config(page_title="TRIVANZA – Your Smart Travel Buddy", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -------------- SESSION INIT ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_form" not in st.session_state:
    st.session_state.show_form = False

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "trip_context" not in st.session_state:
    st.session_state.trip_context = {}

if "pending_itinerary_prompt" not in st.session_state:
    st.session_state.pending_itinerary_prompt = None

# -------------- OPENAI CHAT FUNCTION ----------------
def get_response(messages):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content.strip()

# -------------- HEADER ----------------
st.markdown("""
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
    <img src="https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" width="45px">
    <h2 style="margin: 0;">TRIVANZA – Your Smart Travel Buddy</h2>
</div>
""", unsafe_allow_html=True)

# -------------- CHAT HANDLER ----------------
user_input = st.chat_input("Say Hi to Trivanza or ask your travel-related question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if user_input.strip().lower() in ["hi", "hello", "hey"]:
        st.session_state.show_form = True
        st.session_state.submitted = False
        st.session_state.messages.append({
            "role": "assistant",
            "content": "👋 **Hello Traveller!** Please fill out the form to create your itinerary."
        })
    else:
        messages = [
            {"role": "system", "content": f"""
You are TRIVANZA – a smart travel planner.

Use the user's travel context to answer travel questions only.

TRAVEL CONTEXT:
- Origin: {st.session_state.trip_context.get("origin", "Not provided")}
- Destination: {st.session_state.trip_context.get("destination", "Not provided")}
- Dates: {st.session_state.trip_context.get("from_date", "")} to {st.session_state.trip_context.get("to_date", "")}
- Transport: {st.session_state.trip_context.get("transport", "")}
- Stay: {st.session_state.trip_context.get("stay", "")}
- Budget: {st.session_state.trip_context.get("budget", "")}
- Activities: {st.session_state.trip_context.get("activities", "")}

Only respond to travel-related questions using real, bookable services, pricing, and Markdown formatting.
            """}
        ] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]

        with st.spinner("✈️ Planning your response..."):
            reply = get_response(messages)
            st.session_state.messages.append({"role": "assistant", "content": reply})

# -------------- CHAT DISPLAY ----------------
for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# -------------- FORM ----------------
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
                "from_date": str(from_date),
                "to_date": str(to_date),
                "transport": transport,
                "stay": stay,
                "budget": budget,
                "activities": activities
            }

            # Build prompt and store for next rerun
            prompt = f"""
Create a strict Markdown-formatted travel itinerary.

🧾 DETAILS:
- From: {origin}
- To: {destination}
- Dates: {from_date} to {to_date}
- Budget: {budget}
- Transport: {transport}
- Stay: {stay}
- Interests: {activities}

📌 FORMAT STRICTLY AS:

**[Trip Title – Budget Level]**

### Day 1: [Title]
✈️ Flight: Airline, Time, Cost  
🏨 Hotel: Name + Price (Booking.com)  
🍽️ Breakfast/Lunch/Dinner: Name, ₹, Zomato/Tripadvisor  
🎟️ Activities: Name + Link + Cost  
🚕 Local Transport: Uber/Metro – ₹  
💰 Total: ₹____

Repeat for all days.

### Budget Summary
- Flight: ₹___
- Stay: ₹___
- Food: ₹___
- Activities/Transport: ₹___  
**Total: ₹___**

🎯 End with:
“Would you like to adjust anything?”

Only output in Markdown and use Indian platforms for costs/links where applicable.
"""
            st.session_state.pending_itinerary_prompt = prompt

# -------------- POST-FORM GENERATION ----------------
if st.session_state.pending_itinerary_prompt:
    with st.spinner("🎯 Generating your itinerary..."):
        itinerary = get_response([
            {"role": "system", "content": "You are TRIVANZA – a travel-specialized AI assistant."},
            {"role": "user", "content": st.session_state.pending_itinerary_prompt}
        ])
        st.session_state.messages.append({"role": "assistant", "content": itinerary})
        st.session_state.pending_itinerary_prompt = None  # Clear so doesn't run again
