import streamlit as st
from openai import OpenAI

# Set the page title
st.set_page_config(page_title="Trivanza: Your Travel Companion")
st.title("Trivanza: Your Travel Companion")

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": (
            "You are Trivanza, a travel assistant chatbot. Always greet users with: "
            "'Welcome to Trivanza: Your Travel Companion. I'm excited to help you with your travel plans.'"
            "Always create structured, cost-estimated day-by-day itineraries with real links. "
            "When users directly ask travel-related questions, do not ask for origin, transport or accommodation preferences unless required."
            "Focus on solving travel-related queries from packing, scams, bookings, safety, or budget planning."
            "Only respond to travel-related content. If a question is off-topic, respond with: "
            "'This chat is strictly about Travel. Please ask Travel-related questions.'"
        )}
    ]

# Display previous chat messages
for message in st.session_state.messages[1:]:  # skip system prompt
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input for user
if prompt := st.chat_input("Ask me anything about your trip..."):
    # Display user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Define response function
    def get_response(messages):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content

    # Get assistant reply
    assistant_reply = get_response(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

    # Display assistant reply
    with st.chat_message("assistant"):
        st.markdown(assistant_reply)
