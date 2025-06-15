import streamlit as st
from openai import OpenAI
import re

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Set Streamlit page config and title
st.set_page_config(page_title="Trivanza: Your Smart Travel Companion")
st.title("✈️ Trivanza Travel Chatbot")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "system",
        "content": """
You are TRIVANZA, a smart travel assistant. Only respond to travel-related questions.
Reject any unrelated query politely with:
"This chat is strictly about travel. Please ask travel-related questions only."

Your responsibilities include:
1. Travel problem solving (flights, luggage, scams, emergencies)
2. Personalized itineraries with bookings and costs
3. Travel alerts (weather, delays)
4. Packing assistant
5. Local language & etiquette support
6. Health & insurance
7. Sustainable travel tips
8. Multi-language translator
9. Budget planner & currency
10. Expense breakdown by category
"""
    }]

# Greeting detector
def is_greeting(msg):
    return re.match(r"^(hi|hello|hey|namaste|salaam|greetings|good\s(morning|evening|afternoon))\b", msg.strip().lower()) is not None

# Get response from OpenAI
def get_response(messages):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content

# Display chat history
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Trigger form display
show_form = False

# Chat input box
user_input = st.chat_input("Ask me about your travel...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    if is_greeting(user_input):
        with st.chat_message("assistant"):
            st.markdown("**Welcome to Trivanza: Your Smart Travel Companion**\nI'm excited to help you with your travel plans. Please fill out the form below.")
        show_form = True
    else:
        assistant_reply = get_response(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
        with st.chat_message("assistant"):
            st.markdown(assistant_reply)

# Display form only after greeting
if show_form or st.session_state.get("form_filled", False):
    with st.form("travel_form"):
        origin = st.text_input("What is your origin (starting location)?")
        destination = st.text_input("What is your destination (where are you headed)?")
        dates = st.text_input("What are your travel dates (from and to)?")
        transport = st.text_input("Preferred transport (flight, train, car, etc.)?")
        accommodation = st.text_input("Accommodation preferences (hotel, hostel, etc.)?")
        budget = st.text_input("Budget and currency type (INR, Dollar, Pound, etc.)?")
        activities = st.text_area("Any specific activities or experiences you're looking for?")
        submitted = st.form_submit_button("Submit")

        if submitted:
            st.session_state["form_filled"] = True
            form_message = f"""
I want to plan a trip with the following details:

- Origin: {origin}
- Destination: {destination}
- Dates: {dates}
- Transport: {transport}
- Accommodation: {accommodation}
- Budget: {budget}
- Activities: {activities}
            """.strip()

            with st.chat_message("user"):
                st.markdown(form_message)
            st.session_state.messages.append({"role": "user", "content": form_message})

            assistant_reply = get_response(st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
            with st.chat_message("assistant"):
                st.markdown(assistant_reply)
