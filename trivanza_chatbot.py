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
if "trip_context" not in st.session_state:
    st.session_state.trip_context = {}

# ----------------- CUSTOM FUNCTION -----------------
def get_response(messages):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    return response.choices[0].message.content

# ----------------- PROMPT TEMPLATE -----------------
base_system_prompt = """
You are TRIVANZA – a travel-specialized AI assistant.
Always return full detailed multi-day itineraries when user gives travel dates. Show each day breakdown clearly and never skip days.
"""

# ----------------- FORM -----------------
st.markdown("### 🧳 Plan Your Trip")
with st.form("trip_form"):
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
    days = (to_date - from_date).days + 1
    prompt = f"""
Please generate a complete {days}-day itinerary for a traveler from {origin} to {destination}.

Details:
- Dates: {from_date} to {to_date}
- Mode of transport: {transport}
- Accommodation: {stay}
- Budget: {budget}
- Interests/Activities: {activities}

Include:
- Day-wise plan (Day 1, Day 2, etc.)
- Costs per activity, hotel, food, transport
- Daily and total cost
- Booking links from popular trusted sources

Use friendly tone. Optimize for budget given by user. Use INR or relevant currency.
"""

    with st.spinner("🎯 Generating your itinerary..."):
        reply = get_response([
            {"role": "system", "content": base_system_prompt},
            {"role": "user", "content": prompt}
        ])
        st.session_state.messages.append({"role": "assistant", "content": reply})

# ----------------- DISPLAY RESPONSE -----------------
for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
