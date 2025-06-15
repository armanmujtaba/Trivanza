import streamlit as st
from openai import OpenAI
from datetime import date

# ----------------- CONFIG -----------------
st.set_page_config(page_title="TRIVANZA – Your Smart Travel Buddy", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ----------------- SESSION STATE INIT -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "trip_context" not in st.session_state:
    st.session_state.trip_context = {}

# ----------------- BASE SYSTEM PROMPT -----------------
base_system_prompt = """
You are TRIVANZA – a travel-specialized AI assistant.
Only generate personalized itineraries with cost breakdowns, booking links, daily schedules.
NEVER reply to off-topic prompts.
"""

# ----------------- FUNCTION TO CALL OPENAI -----------------
def get_response(messages):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content

# ----------------- CUSTOM HEADER -----------------
st.markdown("""
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
    <img src="https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" width="45px">
    <h2 style="margin: 0;">TRIVANZA – Your Smart Travel Buddy</h2>
</div>
""", unsafe_allow_html=True)

# ----------------- CHAT HANDLER -----------------
user_input = st.chat_input("Say Hi to Trivanza or ask your travel-related question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if user_input.strip().lower() in ["hi", "hello", "hey"]:
        st.session_state.show_form = True
        st.session_state.submitted = False
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Welcome to Trivanza: Your Smart Travel Companion\n\nPlease provide these trip details:\n- Origin\n- Destination\n- Dates (from/to)\n- Transport Mode\n- Stay Type\n- Budget & Currency\n- Activities"
        })
    else:
        try:
            messages = [
                {"role": "system", "content": base_system_prompt},
                *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]
            ]
            with st.spinner("✈️ Planning your travel response..."):
                reply = get_response(messages)
                st.session_state.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})

# ----------------- DISPLAY MESSAGES -----------------
for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ----------------- TRAVEL FORM -----------------
if st.session_state.show_form and not st.session_state.submitted:
    with st.form("travel_form"):
        st.markdown("### 🧳️ Let’s plan your perfect trip!")

        col1, col2 = st.columns(2)
        with col1:
            origin = st.text_input("🌍 Origin", placeholder="e.g., Delhi")
        with col2:
            destination = st.text_input("📍 Destination", placeholder="e.g., Paris")

        col3, col4 = st.columns(2)
        with col3:
            from_date = st.date_input("📅 From Date", min_value=date.today())
        with col4:
            to_date = st.date_input("📅 To Date", min_value=from_date)

        transport = st.selectbox("🛫 Transport Mode", ["Flight", "Train", "Car", "Bus"])
        stay = st.selectbox("🏨 Accommodation", ["Hotel", "Hostel", "Airbnb", "Resort"])
        budget = st.text_input("💰 Budget (e.g., ₹50000 INR or $800 USD)")
        activities = st.text_area("🎯 Activities", placeholder="e.g., museums, cafes, sightseeing")

        submit = st.form_submit_button("Generate Itinerary")

        if submit:
            st.session_state.submitted = True
            st.session_state.show_form = False

            trip_days = (to_date - from_date).days + 1

            user_prompt = f"""
Create a detailed {trip_days}-day itinerary for a trip:
- Origin: {origin}
- Destination: {destination}
- Dates: {from_date.strftime('%d %B %Y')} to {to_date.strftime('%d %B %Y')}
- Transport: {transport}
- Accommodation: {stay}
- Budget: {budget}
- Activities: {activities}

Include:
- Day-wise plan (Day 1 to Day {trip_days}) with morning/afternoon/evening
- Cost estimates for flights, hotel, food, local transport, and activities
- Daily total + grand total
- Booking links (Skyscanner, Booking.com, Viator, etc.)
"""

            try:
                with st.spinner("🌏 Crafting your itinerary..."):
                    itinerary = get_response([
                        {"role": "system", "content": base_system_prompt},
                        {"role": "user", "content": user_prompt}
                    ])
                    st.session_state.messages.append({"role": "assistant", "content": itinerary})
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"Error generating itinerary: {e}"})
            finally:
                st.session_state.submitted = False
