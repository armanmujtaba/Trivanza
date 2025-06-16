import streamlit as st
import openai
import re

# Set your OpenAI API key (ensure this is set in Streamlit secrets or environment variables)
openai.api_key = st.secrets.get("OPENAI_API_KEY")

st.title("Trivanza Travel Assistant")

# Initialize session state for conversation
if "messages" not in st.session_state:
    st.session_state.messages = []

# System prompt enforcing allowed topics and itinerary format
system_content = (
    "You are TRIVANZA Travel Assistant. Only answer travel-related questions within the following topics: "
    "travel problem-solving (cancellations, theft, health issues), personalized itineraries (day-by-day, by budget, by interests, events), "
    "real-time alerts (weather, political unrest, flight delays), smart packing (checklists by weather & activity), "
    "culture & language (local etiquette, translations), health & insurance (local medical help, insurance), "
    "sustainable travel (eco-friendly stays, eco-transport), live translation (signs, speech, receipts), "
    "budget & currency planning, and expense categories (flight, hotel, food, transport). "
    "If the user asks anything outside these topics, reply with: \"This chat is strictly about Travel and TRIVANZA\u2019s features. Please ask Travel-related questions.\"\n"
    "Always provide intelligent, personalized, budget-aware travel planning assistance. "
    "Give real cost estimates for every element (flight, hotel, food, transport), daily plans, and booking links for key components. "
    "When providing itineraries, break them down by day (Day 1, Day 2, etc.) with Morning/Afternoon/Evening blocks. "
    "Include the cost per day and total cost. "
    "If the user's budget is too low, calculate the true cost of the trip and suggest trade-offs or alternatives."
)

# Greeting and fallback messages
greeting_message = """Welcome to Trivanza: Your Smart Travel Companion
I'm excited to help you with your travel plans. To provide you with the best possible assistance, could you please share some details with me?
  - What is your origin (starting location)?
  - What is your destination (where are you headed)?
  - What are your travel dates (from and to)?
  - What is your preferred mode of transport (flight, train, car, etc.)?
  - What are your accommodation preferences (hotel, hostel, etc.)?
  - What are your budget and currency type (INR, Dollar, Pound, etc.)?
  - Are there any specific activities or experiences you're looking to have during your trip?"""
fallback_message = "This chat is strictly about Travel and TRIVANZA\u2019s features. Please ask Travel-related questions."

# UI: input form for chat
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("You:")
    submit_button = st.form_submit_button("Send")

if submit_button and user_input:
    # Append user message to session state
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Detect greeting without travel specifics
    text_lower = user_input.strip().lower()
    words = re.sub(r"[^\w\s]", "", text_lower).split()
    first_word = words[0] if len(words) >= 1 else ""
    first_two = " ".join(words[:2]) if len(words) >= 2 else ""
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    greet_flag = False
    if (first_word in greetings) or (first_two in greetings):
        travel_keywords = [
            "travel", "trip", "flight", "train", "bus", "hotel", "itinerary",
            "pack", "packing", "weather", "delay", "alert", "culture",
            "language", "translate", "etiquette", "insurance", "health",
            "sustain", "eco", "budget", "currency", "expense", "cost",
            "booking", "destination", "visa", "passport", "tour", "guide",
            "tourism", "sightseeing", "restaurant", "food", "transport",
            "car", "taxi", "uber", "station", "airport", "theft",
            "lost", "cancellation"
        ]
        # If no travel keyword present, consider it a simple greeting
        if not any(keyword in text_lower for keyword in travel_keywords):
            greet_flag = True

    assistant_response = ""
    if greet_flag:
        # User greeted without specifics: provide welcome message
        assistant_response = greeting_message
    else:
        # Check if the user's query is within travel scope
        travel_keywords = [
            "travel", "trip", "flight", "train", "bus", "hotel", "itinerary",
            "pack", "packing", "weather", "delay", "alert", "culture",
            "language", "translate", "etiquette", "insurance", "health",
            "sustain", "eco", "budget", "currency", "expense", "cost",
            "booking", "destination", "visa", "passport", "tour", "guide",
            "tourism", "sightseeing", "restaurant", "food", "transport",
            "car", "taxi", "uber", "station", "airport", "theft",
            "lost", "cancellation", "health"
        ]
        if not any(keyword in text_lower for keyword in travel_keywords):
            # Off-topic query: provide fallback message
            assistant_response = fallback_message
        else:
            # Valid travel-related query: call OpenAI with system prompt
            messages = [{"role": "system", "content": system_content}]
            for msg in st.session_state.messages:
                messages.append(msg)
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                assistant_response = response.choices[0].message['content']
            except Exception:
                assistant_response = "I'm sorry, I couldn't process your request at the moment."

    # Append assistant's response to conversation
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})

# Display the conversation history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**Trivanza:** {msg['content']}")
