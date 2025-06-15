import streamlit as st
from openai import OpenAI
from datetime import date

# ----------------- CONFIG -----------------
st.set_page_config(page_title="TRIVANZA – Your Smart Travel Buddy", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ----------------- LOGO & HEADER -----------------
st.markdown("""
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
    <img src="https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" width="45px">
    <h2 style="margin: 0;">TRIVANZA – Your Smart Travel Buddy</h2>
</div>
""", unsafe_allow_html=True)

# ----------------- SESSION INIT -----------------
for key in ["messages", "show_form", "submitted", "trip_context"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else False if key != "trip_context" else {}

# ----------------- OPENAI RESPONSE FUNCTION -----------------
def get_response(messages):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# ----------------- SYSTEM PROMPT -----------------
base_system_prompt = """
You are TRIVANZA, an expert travel planner AI assistant. Your goal is to help users plan perfect travel experiences.
When the user provides origin, destination, travel dates, budget, stay, transport and activities, generate:
- A detailed day-by-day itinerary with real hotel/flight/activity suggestions
- Each day includes: travel, stay, meals, local transport, activities
- Mention platforms like Booking.com, Viator, Zomato, Grab, etc. with realistic links
- End with a daily budget breakdown and full total
Always respond in a friendly tone.
"""

# ----------------- CHAT FLOW -----------------
user_input = st.chat_input("Ask anything about your trip or say Hi to start...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Detect greeting to show form
    if user_input.strip().lower() in ["hi", "hello", "hey"]:
        st.session_state.show_form = True
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hi there! 👋 I’m Trivanza. Let's plan your trip! Just fill out the travel form below and I’ll create a custom itinerary for you."
        })

    else:
        try:
            messages = [
                {"role": "system", "content": base_system_prompt},
                *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-10:]]
            ]
            with st.spinner("Planning your response..."):
                reply = get_response(messages)
                st.session_state.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"❌ Error: {e}"})

# ----------------- DISPLAY HISTORY -----------------
for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ----------------- FORM LOGIC -----------------
if st.session_state.show_form and not st.session_state.submitted:
    with st.form("trip_form"):
        st.markdown("### ✈️ Plan Your Trip")

        col1, col2 = st.columns(2)
        with col1:
            origin = st.text_input("Origin", placeholder="e.g. Delhi")
        with col2:
            destination = st.text_input("Destination", placeholder="e.g. Vietnam")

        col3, col4 = st.columns(2)
        with col3:
            from_date = st.date_input("From", min_value=date.today())
        with col4:
            to_date = st.date_input("To", min_value=from_date)

        transport = st.selectbox("Transport Mode", ["Flight", "Train", "Car", "Bus"])
        stay = st.selectbox("Accommodation", ["Hotel", "Hostel", "Resort", "Airbnb"])
        budget = st.text_input("Budget", placeholder="e.g. ₹50000 INR or $800 USD")
        activities = st.text_area("Activities", placeholder="e.g. beaches, hikes, temples")

        submitted = st.form_submit_button("Generate Itinerary")

        if submitted:
            st.session_state.submitted = True
            st.session_state.show_form = False

            prompt = f"""
User itinerary request:
- Origin: {origin}
- Destination: {destination}
- Dates: {from_date} to {to_date}
- Transport: {transport}
- Stay: {stay}
- Budget: {budget}
- Activities: {activities}

Generate a detailed 6-day itinerary in the format:
"6-Day {destination} Adventure – Budget Level"
Include daily travel, hotels, food, booking links, and daily totals. End with full budget summary.
"""

            try:
                with st.spinner("Generating itinerary..."):
                    plan = get_response([
                        {"role": "system", "content": base_system_prompt},
                        {"role": "user", "content": prompt}
                    ])
                    st.session_state.messages.append({"role": "assistant", "content": plan})
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"❌ Error generating itinerary: {e}"})
            finally:
                st.session_state.submitted = False
