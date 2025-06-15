import streamlit as st
from openai import OpenAI
import re

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Set app title
st.set_page_config(page_title="Trivanza: Your Smart Travel Companion")
st.title("Trivanza Chatbot")

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to detect if the message is a greeting
def is_greeting(message):
    return bool(re.match(r"^(hi|hello|hey|good morning|good evening|namaste|salaam)\b", message.lower()))

# Function to get response from OpenAI
def get_response(messages):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input box
if prompt := st.chat_input("Ask me about your travel plans..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Greeting detected
    if is_greeting(prompt):
        with st.chat_message("assistant"):
            st.markdown("**Welcome to Trivanza: Your Smart Travel Companion**\nI'm excited to help you with your travel plans. To provide you with the best possible assistance, could you please share some details with me?")

        with st.form("travel_form", clear_on_submit=True):
            origin = st.text_input("What is your origin (starting location)?")
            destination = st.text_input("What is your destination (where are you headed)?")
            dates = st.text_input("What are your travel dates (from and to)?")
            transport = st.text_input("What is your preferred mode of transport (flight, train, car, etc.)?")
            accommodation = st.text_input("What are your accommodation preferences (hotel, hostel, etc.)?")
            budget = st.text_input("What is your budget and currency type (INR, Dollar, Pound, etc.)?")
            experiences = st.text_area("Are there any specific activities or experiences you're looking to have during your trip?")
            submitted = st.form_submit_button("Submit")

            if submitted:
                form_summary = f"""Here are the travel details:
- Origin: {origin}
- Destination: {destination}
- Dates: {dates}
- Transport: {transport}
- Accommodation: {accommodation}
- Budget: {budget}
- Experiences: {experiences}"""
                st.session_state.messages.append({"role": "user", "content": form_summary})
                with st.chat_message("user"):
                    st.markdown(form_summary)

                assistant_reply = get_response(st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
                with st.chat_message("assistant"):
                    st.markdown(assistant_reply)

    else:
        # Standard travel query
        with st.chat_message("user"):
            st.markdown(prompt)

        assistant_reply = get_response(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

        with st.chat_message("assistant"):
            st.markdown(assistant_reply)
