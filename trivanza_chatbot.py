
import streamlit as st
import openai

# Title of the app
st.title("TRIVANZA - Your Travel Companion")

# Initialize OpenAI client using new SDK (v1.0+)
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are TRIVANZA – a travel-specialized AI assistant.\n"
                "You only respond to travel-related queries and do not entertain any off-topic questions.\n"
                "Always include real estimated costs, day-by-day itineraries, and booking links when relevant.\n"
                "Do not ask for user travel details if the question is already specific.\n"
                "If the question is general (like 'help me plan a trip'), then ask:\n"
                "- What is your origin?\n"
                "- What is your destination?\n"
                "- What are your travel dates?\n"
                "- Preferred mode of transport?\n"
                "- Accommodation preferences?\n"
                "- Budget and currency?\n"
                "- Specific activities or experiences?\n"
                "Only respond to travel-related content and ignore or redirect unrelated topics."
            )
        }
    ]

# Display chat history
for msg in st.session_state.messages[1:]:  # Skip the system message
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Function to get assistant response
def get_response(messages):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content

# User input box
user_input = st.chat_input("Ask me anything about your travel...")

if user_input:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get assistant response
    assistant_reply = get_response(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    with st.chat_message("assistant"):
        st.markdown(assistant_reply)
