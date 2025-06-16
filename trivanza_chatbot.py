import streamlit as st
import openai
import re
import requests
from datetime import date

# --------- CONFIG ---------
st.set_page_config(page_title="Trivanza Travel Assistant", layout="centered")
openai.api_key = st.secrets.get("OPENAI_API_KEY")

# --------- SESSION INIT ---------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "trip_context" not in st.session_state:
    st.session_state.trip_context = None
if "pending_form_response" not in st.session_state:
    st.session_state.pending_form_response = False

# --------- CUSTOM HEADER ---------
st.markdown("""
<style>
.logo-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 10px;
}
.logo {
    width: 300px;
}
@media (min-width: 601px) {
    .logo {
        width: 350px;
    }
}
</style>
<div class="logo-container">
    <img class="logo" src="https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/Trivanza.png?raw=true">
</div>
""", unsafe_allow_html=True)

# --------- SYSTEM PROMPT ---------
system_content = (
    "You are TRIVANZA Travel Assistant. Only answer travel-related questions within the following topics: "
    "travel problem-solving (cancellations, theft, health issues), personalized itineraries (day-by-day, by budget, by interests, events), "
    "real-time alerts (weather, political unrest, flight delays), smart packing (checklists by weather & activity), "
    "culture & language (local etiquette, translations), health & insurance (local medical help, insurance), "
    "sustainable travel (eco-friendly stays, eco-transport), live translation (signs, speech, receipts), "
    "budget & currency planning, and expense categories (flight, hotel, food, transport). "
    "If the user asks anything outside these topics, reply with: \"This chat is strictly about Travel and TRIVANZA’s features. Please ask Travel-related questions.\"\n"
    "Always provide intelligent, personalized, budget-aware travel planning assistance. "
    "Give real cost estimates for every element (flight, hotel, food, transport), daily plans, and booking links for key components. "
    "When providing itineraries, break them down by day (Day 1, Day 2, etc.) with Morning/Afternoon/Evening blocks. "
    "Include the cost per day and total cost. "
    "If the user's budget is too low, calculate the true cost of the trip and suggest trade-offs or alternatives."
)

greeting_message = """Welcome to Trivanza: Your Smart Travel Companion  
I'm excited to help you with your travel plans. Could you please share some details like:  
- Where you're starting and going  
- Travel dates  
- Transport and accommodation preferences  
- Budget and currency  
- Any activities you're excited about?"""

fallback_message = "This chat is strictly about Travel and TRIVANZA’s features. Please ask Travel-related questions."

# --------- WEATHER FUNCTION ---------
def get_weather(city_name, api_key="c7410425e996d5fa16ed7f3c2835a73c"):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("cod") != 200:
            return f"❌ Could not find weather info for {city_name}."
        weather = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        return (
            f"🌦️ **Weather in {city_name.title()}**:\n"
            f"- Condition: {weather}\n"
            f"- Temperature: {temp}°C (Feels like {feels_like}°C)\n"
            f"- Humidity: {humidity}%\n"
            f"- Wind Speed: {wind_speed} m/s"
        )
    except Exception as e:
        return f"⚠️ Error getting weather: {e}"

# --------- CHAT MODULE ---------
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("💬 Ask Trivanza anything travel-related:")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    text_lower = user_input.lower()
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    travel_keywords = ["trip", "flight", "itinerary", "weather", "hotel", "visa", "insurance", "food", "culture", "currency", "booking", "transport", "tour", "packing", "theft", "delay", "sightseeing"]

    if any(greet in text_lower for greet in greetings) and not any(k in text_lower for k in travel_keywords):
        assistant_response = greeting_message
    elif "weather" in text_lower:
        match = re.search(r"weather in ([a-zA-Z\s]+)", text_lower)
        city = match.group(1).strip() if match else text_lower.replace("weather", "").strip()
        assistant_response = get_weather(city)
    elif not any(k in text_lower for k in travel_keywords):
        assistant_response = fallback_message
    else:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": system_content}] + st.session_state.messages,
                temperature=0.7,
                max_tokens=1200
            )
            assistant_response = response.choices[0].message['content']
        except Exception:
            assistant_response = "Sorry, I'm unable to respond at the moment. Try again later."

    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.rerun()

# --------- DISPLAY CHAT ---------
for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
