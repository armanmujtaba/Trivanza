import streamlit as st
import requests
from openai import OpenAI
from datetime import date, timedelta

# ----------------- CONFIG -----------------
st.set_page_config(page_title="TRIVANZA – Your Smart Travel Buddy", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ----------------- UTILITY FUNCTIONS -----------------
def get_response(messages):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content

def get_weather_forecast(destination):
    try:
        key = st.secrets["weatherapi_key"]
        response = requests.get(f"http://api.weatherapi.com/v1/forecast.json?key={key}&q={destination}&days=3")
        forecast = response.json()
        weather_msg = "".join([
            f"**{day['date']}**: {day['day']['condition']['text']}, Avg Temp: {day['day']['avgtemp_c']}°C\n"
            for day in forecast["forecast"]["forecastday"]
        ])
        return f"### ⛅ Weather Forecast for {destination}\n" + weather_msg
    except:
        return ""

def get_destination_image(destination):
    try:
        access_key = st.secrets["unsplash"]["access_key"]
        url = f"https://api.unsplash.com/photos/random?query={destination}+travel&client_id={access_key}&orientation=landscape"
        res = requests.get(url).json()
        return res["urls"]["regular"]
    except:
        return None

# ----------------- SESSION STATE INIT -----------------
for key in ["messages", "show_form", "submitted", "trip_context"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else False if key != "trip_context" else {}

# ----------------- CUSTOM HEADER -----------------
st.markdown("""
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
    <img src="https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" width="45px">
    <h2 style="margin: 0;">TRIVANZA – Your Smart Travel Buddy</h2>
</div>
""", unsafe_allow_html=True)

# ----------------- BASE SYSTEM PROMPT -----------------
base_system_prompt = """
You are TRIVANZA – a travel-specialized AI assistant.

🎯 PURPOSE: Personalized and budget-conscious travel planning with real costs and booking links.
✅ ALLOWED TOPICS: Travel only – itineraries, alerts, packing, budget, weather, etc.
❌ Restrict non-travel queries.
💸 Include cost breakdown, daily plan, booking links.
🧾 FORMAT: Trip title, Day-wise sections, cost per item, daily + total cost.
"""

# ----------------- CHAT INPUT HANDLER -----------------
user_input = st.chat_input("Say Hi to Trivanza or ask your travel-related question...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    if user_input.strip().lower() in ["hi", "hello", "hey"]:
        st.session_state.show_form = True
        st.session_state.submitted = False
        st.session_state.messages.append({"role": "assistant", "content": "Welcome to Trivanza: Your Smart Travel Companion\nPlease share: origin, destination, dates, transport, stay, budget, and activities."})
    else:
        messages = [{"role": "system", "content": base_system_prompt}] + [
            {"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]
        ]
        with st.spinner("✈️ Planning your travel response..."):
            try:
                reply = get_response(messages)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"⚠️ Error: {e}"})

# ----------------- DISPLAY CHAT HISTORY -----------------
for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ----------------- TRAVEL FORM -----------------
if st.session_state.show_form and not st.session_state.submitted:
    with st.form("travel_form"):
        st.markdown("### 🧳 Let’s plan your perfect trip!")
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
            st.session_state.submitted = True
            st.session_state.show_form = False

            trip_days = (to_date - from_date).days + 1
            st.session_state.trip_context = {
                "origin": origin,
                "destination": destination,
                "from_date": from_date,
                "to_date": to_date,
                "trip_days": trip_days,
                "transport": transport,
                "stay": stay,
                "budget": budget,
                "activities": activities
            }

            user_prompt = f"""
User wants a full travel plan:
- Origin: {origin}
- Destination: {destination}
- Dates: {from_date} to {to_date} ({trip_days} days)
- Transport: {transport}
- Stay: {stay}
- Budget: {budget}
- Activities: {activities}
"""

            image_url = get_destination_image(destination)
            weather_report = get_weather_forecast(destination)

            with st.spinner("🎯 Crafting your itinerary..."):
                try:
                    itinerary = get_response([
                        {"role": "system", "content": base_system_prompt},
                        {"role": "user", "content": user_prompt}
                    ])

                    st.session_state.messages.append({"role": "assistant", "content": weather_report})
                    if image_url:
                        st.markdown(f"""
                            <div style='margin-top:10px;margin-bottom:16px;border-radius: 16px; overflow: hidden;'>
                            <img src="{image_url}" style='width:100%;border-radius:12px;'>
                            </div>
                        """, unsafe_allow_html=True)

                    st.session_state.messages.append({"role": "assistant", "content": itinerary})
                except Exception as e:
                    st.session_state.messages.append({"role": "assistant", "content": f"❌ Error generating itinerary: {e}"})
