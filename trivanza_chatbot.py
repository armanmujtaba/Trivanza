import streamlit as st
import re

# Page setup
st.set_page_config(page_title="Trivanza Travel Bot", page_icon="✈️")
st.title("🧳 Trivanza: Your Smart Travel Companion")

# Initialize state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "form_filled" not in st.session_state:
    st.session_state.form_filled = False
if "travel_response_generated" not in st.session_state:
    st.session_state.travel_response_generated = False
if "travel_form_data" not in st.session_state:
    st.session_state.travel_form_data = {}

# Greeting detector
def is_greeting(text):
    return bool(re.search(r"\b(hi|hello|hey|namaste|salaam|yo|hola|greetings)\b", text, re.I))

# Sample Itinerary Generator
def generate_itinerary(data):
    return f"""**6-Day {data['destination']} Adventure – Mid-Budget**

Based on your travel dates ({data['from_date']} to {data['to_date']}) and destination ({data['destination']}), I've created a personalized itinerary for you. Since you're traveling from {data['origin']}, I've included travel details.

**Day 1: Arrival in {data['destination']}**
✈️ Travel from {data['origin']} to {data['destination']}
🏨 Stay at a {data['accommodation']} – Budget: {data['budget']}
🎯 Activities: Arrival, check-in, explore nearby markets

**Day 2 to Day 5:** Sightseeing, cultural tours, and specific activities like:
🎡 {data['activities'] or "City tour, local cuisine, shopping"}

**Day 6: Return to {data['origin']}**
✈️ Return flight or transport

💰 Approx. Budget: {data['budget']}
Let me know if you'd like to adjust anything!
"""

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input handler
user_input = st.chat_input("Ask me anything about your trip...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if is_greeting(user_input) and not st.session_state.form_filled:
        greeting_response = (
            "Welcome to Trivanza: Your Smart Travel Companion\n"
            "I'm excited to help you with your travel plans. "
            "To provide you with the best possible assistance, could you please share some details with me?"
        )
        st.session_state.messages.append({"role": "assistant", "content": greeting_response})
        st.rerun()

# Show form if not already filled
if not st.session_state.form_filled:
    with st.form("travel_form"):
        st.subheader("📝 Travel Preferences Form")
        origin = st.text_input("What is your origin (starting location)?")
        destination = st.text_input("What is your destination (where are you headed)?")
        from_date = st.date_input("Travel start date")
        to_date = st.date_input("Travel end date")
        transport = st.selectbox("Preferred mode of transport", ["Flight", "Train", "Car", "Bus"])
        accommodation = st.selectbox("Accommodation preference", ["Hotel", "Hostel", "Guest House", "Airbnb"])
        budget = st.text_input("Budget & Currency (e.g., ₹50000 INR)")
        activities = st.text_area("Any specific activities/experiences?")

        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state.travel_form_data = {
                "origin": origin,
                "destination": destination,
                "from_date": from_date,
                "to_date": to_date,
                "transport": transport,
                "accommodation": accommodation,
                "budget": budget,
                "activities": activities
            }
            st.session_state.form_filled = True
            st.rerun()

# Generate itinerary once after form submission
if st.session_state.form_filled and not st.session_state.travel_response_generated:
    itinerary = generate_itinerary(st.session_state.travel_form_data)
    st.session_state.messages.append({"role": "assistant", "content": itinerary})
    st.session_state.travel_response_generated = True
    st.rerun()
