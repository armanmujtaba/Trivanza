import streamlit as st
from openai import OpenAI
import re

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Set app title
st.set_page_config(page_title="Trivanza: Your Smart Travel Companion")
st.title("Trivanza Chatbot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": """
You are TRIVANZA, a smart travel assistant. Only respond to travel-related questions.
Reject any unrelated query politely with:
"This chat is strictly about travel. Please ask travel-related questions only."

Your duties include:
1. Solving travel issues (cancellations, luggage, visas, health, scams).
2. Planning personalized day-by-day itineraries.
3. Sending real-time travel alerts.
4. Packing tips based on destination/weather.
5. Local etiquette, culture, translations.
6. Health and insurance advice.
7. Sustainable travel tips.
8. Multi-language translation support.
9. Budget & currency support.
10. Expense breakdown (flights, hotels, food, etc.).
""" }]

# Greeting detector
def is_greeting(msg):
    return bool(re.match(r"^(hi|hello|hey|namaste|salaam|greetings|good\s(morning|evening|afternoon))\b", msg.strip().lower()))

# Get assistant response
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

# Chat input
if prompt := st.chat_input("Ask me about your travel plans..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    if is_greeting(prompt):
        with st.chat_message("assistant"):
            st.markdown("**Welcome to Trivanza: Your Smart Travel Companion**\nI'm excited to help you with your travel plans. To provide you with the best possible assistance, could you please share some details with me?")

        with st.form("travel_form", clear_on_submit=True):
            origin = st.text_input("What is your origin (starting location)?")
            destination = st.text_input("What is your destination (where are you headed)?")
            dates = st.text_input("What are your travel dates (from and to)?")
            transport = st.text_input("Preferred transport (flight, train, car, etc.)?")
            accommodation = st.text_input("Accommodation preferences (hotel, hostel, etc.)?")
            budget = st.text_input("Budget and currency type (INR, Dollar, Pound, etc.)?")
            activities = st.text_area("Any specific activities or experiences you're looking for?")
            submit = st.form_submit_button("Submit")

            if submit:
                user_summary = f"""Plan my trip with the following details:
- Origin: {origin}
- Destination: {destination}
- Dates: {dates}
- Transport: {transport}
- Accommodation: {accommodation}
- Budget: {budget}
- Activities: {activities}
"""
                st.session_state.messages.append({"role": "user", "content": user_summary})
                with st.chat_message("user"):
                    st.markdown(user_summary)

                assistant_reply = get_response(st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
                with st.chat_message("assistant"):
                    st.markdown(assistant_reply)
    else:
        # Handle regular travel questions
        assistant_reply = get_response(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
        with st.chat_message("assistant"):
            st.markdown(assistant_reply)
