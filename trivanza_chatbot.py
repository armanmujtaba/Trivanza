import streamlit as st
import openai
from datetime import date, timedelta
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set API keys from .env file
openai.api_key = os.getenv("OPENAI_API_KEY")
timezonedb_api_key = os.getenv("TIMEZONEDB_API_KEY")
weather_api_key = os.getenv("WEATHER_API_KEY")
google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
exchange_rate_api_key = os.getenv("EXCHANGE_RATE_API_KEY")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "trip_context" not in st.session_state:
    st.session_state.trip_context = {}

# ----------------- CUSTOM HEADER -----------------
st.markdown("""
<style>
@media (max-width: 600px) {
    .logo {
        width: 35px;
    }
    .header-text {
        font-size: 18px;
    }
}
@media (min-width: 601px) {
    .logo {
        width: 45px;
    }
    .header-text {
        font-size: 22px;
    }
}
</style>
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
    <img class="logo" src="https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/Trivanza.png"  alt="Logo">
    <h2 class="header-text" style="margin: 0;">TRIVANZA</h2>
</div>
""", unsafe_allow_html=True)

# Remove page title
st.set_page_config(page_title="", page_icon="✈️", layout="centered")

# ----------------- HELPER FUNCTIONS -----------------
def get_time_difference(origin, destination):
    """Get time difference between origin and destination"""
    url = f"http://api.timezonedb.com/v2.1/get-time-difference?key={timezonedb_api_key}&format=json&from={origin}&to={destination}"
    try:
        response = requests.get(url)
        data = response.json()
        return data.get("toZoneShortName", "") + " (" + str(data.get("totalOffset", 0)) + " hrs)"
    except:
        return "N/A"

def get_weather_forecast(city, date):
    """Get weather forecast for destination city"""
    url = f"http://api.weatherapi.com/v1/forecast.json?key={weather_api_key}&q={city}&dt={date.strftime('%Y-%m-%d')}"
    try:
        response = requests.get(url)
        data = response.json()
        return data["forecast"]["forecastday"][0]["day"]["condition"]["text"] + ", " + str(data["forecast"]["forecastday"][0]["day"]["avgtemp_c"]) + "°C"
    except:
        return "N/A"

def get_hotels(city, budget):
    """Get hotel recommendations using Google Maps API"""
    search_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query=hotels+in+{city}&key={google_maps_api_key}"
    try:
        response = requests.get(search_url)
        data = response.json()
        results = data.get("results", [])
        return [f"[{res['name']}]({res['website']}) - ₹{budget//5}/night" for res in results[:3]]
    except:
        return ["N/A"]

def get_restaurants(city):
    """Get restaurant recommendations"""
    search_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query=restaurants+in+{city}&key={google_maps_api_key}"
    try:
        response = requests.get(search_url)
        data = response.json()
        results = data.get("results", [])
        return [f"[{res['name']}]({res['website']})" for res in results[:3]]
    except:
        return ["N/A"]

def convert_currency(amount, from_curr="INR", to_curr="USD"):
    """Convert budget to local currency"""
    url = f"https://v6.exchangerate-api.com/v4/{exchange_rate_api_key}/latest/{from_curr}"
    try:
        response = requests.get(url)
        data = response.json()
        rate = data["conversion_rates"].get(to_curr, 1)
        return round(amount * rate, 2)
    except:
        return amount

# ----------------- ITINERARY GENERATOR ----------------- 
def generate_itinerary(trip_data):
    """Generate itinerary with enhanced logic"""
    start_date = trip_data["from_date"]
    end_date = trip_data["to_date"]
    duration = (end_date - start_date).days + 1
    all_dates = [start_date + timedelta(days=i) for i in range(duration)]

    # Calculate time zone difference
    time_diff = get_time_difference("Asia/Kolkata", trip_data["destination"])

    # Get weather
    weather = get_weather_forecast(trip_data["destination"], start_date)

    # Get hotel and restaurant recommendations
    hotels = get_hotels(trip_data["destination"], int(trip_data["budget"].replace("₹", "").strip()))
    restaurants = get_restaurants(trip_data["destination"])

    # Convert budget to USD
    budget_inr = int(trip_data["budget"].replace("₹", "").strip())
    budget_usd = convert_currency(budget_inr, "INR", "USD")

    prompt = f"""You are TRIVANZA, the world's most advanced travel assistant. Create a complete itinerary including:

1. ✈️ FLIGHT LOGISTICS:
   - Realistic arrival/departure times
   - Time zone adjustments
   - Airport transfers

2. 🏨 ACCOMMODATION:
   - Top 3 hotels with links
   - Budget considerations

3. 🍽️ FOOD:
   - Top 3 restaurants
   - Local cuisine highlights

4. 🗓️ ACTIVITIES:
   - Weather-aware planning
   - Local tips and cultural etiquette

5. 💵 BUDGET:
   - INR and USD breakdown
   - Activity and transport costs

TRIP DETAILS:
- Origin: {trip_data['origin']}
- Destination: {trip_data['destination']}
- Dates: {all_dates[0].strftime('%B %d')} - {all_dates[-1].strftime('%B %d, %Y')}
- Time Zone Difference: {time_diff}
- Weather Forecast: {weather}
- Budget: {trip_data['budget']} (≈ ${budget_usd} USD)
- Travelers: 2 adults
- Interests: {trip_data['activities']}

FORMAT:
# 🌍 {duration}-Day {trip_data['destination']} Ultimate Adventure
**Travel Period:** {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}
**Weather:** {weather}

## ✈️ FLIGHT DETAILS
**Outbound Journey**
- Departure: 9:00 PM from Delhi
- Arrival: Next day 6:00 AM in {trip_data['destination']} (Time Diff: {time_diff})
- Airport Transfer: 1.5 hours

## 🏨 ACCOMMODATION
### Top Hotels:
{chr(10).join(hotels)}

## 🍽️ FOOD
### Top Restaurants:
{chr(10).join(restaurants)}

## 🗓️ DAY-BY-DAY ITINERARY

## Day 1 - {all_dates[0].strftime('%A, %B %d')}
**Arrival Day**
- 6:00 AM: Arrive at airport
- 7:30 AM: Transfer to hotel
- 11:00 AM: Light activities near hotel
- 7:00 PM: Dinner at recommended restaurant

## Day 2 - {all_dates[1].strftime('%A, %B %d')}
**Morning:**
- Visit top attractions
- Explore local markets

**Afternoon:**
- Lunch at [Restaurant]
- Cultural activity

**Evening:**
- Night tour or local nightlife

[Continue for all days...]

## 💵 BUDGET BREAKDOWN
- ✈️ Flights: ₹{budget_inr * 0.3}
- 🏨 Hotels: ₹{budget_inr * 0.25}
- 🍽️ Food: ₹{budget_inr * 0.2}
- 🎡 Activities: ₹{budget_inr * 0.15}
- 🚖 Transport: ₹{budget_inr * 0.1}
- 🧳 Emergency Fund: ₹{budget_inr * 0.05}

## 🔗 BOOKING LINKS
- ✈️ Flights: MakeMyTrip, Cleartrip, Skyscanner
- 🏨 Hotels: Booking.com, Airbnb
- 🎡 Activities: Klook, GetYourGuide
- 🍽️ Restaurants: Zomato, TripAdvisor
- 🗺️ Navigation: Google Maps, Citymapper

Would you like to refine any aspect of this itinerary?"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"You are TRIVANZA, a detailed travel planner. You must create comprehensive itineraries that include realistic flight schedules, airport transfers, and travel logistics for {trip_data['transport']} travel from {trip_data['origin']} to {trip_data['destination']}. Always account for flight times, jet lag, and departure logistics."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=3500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error generating itinerary: {str(e)}"

# ----------------- CHAT INPUT HANDLER -----------------
user_input = st.chat_input("Say Hi to Trivanza or ask your travel-related question...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    if user_input.strip().lower() in ["hi", "hello", "hey"]:
        st.session_state.show_form = True
        st.session_state.form_submitted = False
        st.session_state.messages.append({
            "role": "assistant",
            "content": "👋 **Hello Traveller! Welcome to Trivanza – Your Smart Travel Buddy**\nTo help you better, please fill out your travel details below."
        })
    else:
        try:
            from_date_str = st.session_state.trip_context.get("from_date", "")
            to_date_str = st.session_state.trip_context.get("to_date", "")
            if from_date_str and hasattr(from_date_str, 'strftime'):
                from_date_str = from_date_str.strftime("%Y-%m-%d")
            if to_date_str and hasattr(to_date_str, 'strftime'):
                to_date_str = to_date_str.strftime("%Y-%m-%d")
            messages = [
                {"role": "system", "content": f"""
You are TRIVANZA – a travel-specialized AI assistant.
CONTEXT:
Origin: {st.session_state.trip_context.get("origin", "Not provided")}
Destination: {st.session_state.trip_context.get("destination", "Not provided")}
Travel Duration: {from_date_str} to {to_date_str}
Transport: {st.session_state.trip_context.get("transport", "")}
Stay: {st.session_state.trip_context.get("stay", "")}
Budget: {st.session_state.trip_context.get("budget", "")}
Activities: {st.session_state.trip_context.get("activities", "")}
Answer ONLY travel-related questions using this context.
                """}
            ]
            messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]
            with st.spinner("✈️ Planning your response..."):
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1200
                )
                bot_reply = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ Error: {e}"})

# ----------------- DISPLAY CHAT HISTORY -----------------
for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png"  if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ----------------- TRAVEL FORM -----------------
if st.session_state.show_form and not st.session_state.form_submitted:
    with st.form("travel_form", clear_on_submit=False):
        st.markdown("### 🧳 Let's plan your perfect trip!")
        col1, col2 = st.columns(2)
        with col1:
            origin = st.text_input("🌍 Origin", placeholder="e.g., Delhi", key="origin_input")
        with col2:
            destination = st.text_input("📍 Destination", placeholder="e.g., Paris", key="dest_input")
        col3, col4 = st.columns(2)
        with col3:
            from_date = st.date_input("📅 From Date", min_value=date.today(), key="from_date_input")
        with col4:
            to_date = st.date_input("📅 To Date", min_value=from_date, key="to_date_input")
        transport = st.selectbox("🛫 Transport Mode", ["Flight", "Train", "Car", "Bus"], key="transport_input")
        stay = st.selectbox("🏨 Accommodation", ["Hotel", "Hostel", "Airbnb", "Resort"], key="stay_input")
        budget = st.text_input("💰 Budget (e.g., ₹50000 INR or $800 USD)", key="budget_input")
        activities = st.text_area("🎯 Activities", placeholder="e.g., beaches, hiking, shopping", key="activities_input")
        submit = st.form_submit_button("🚀 Generate My Itinerary", use_container_width=True)
        if submit:
            if not origin.strip():
                st.error("❌ Please enter your origin city!")
            elif not destination.strip():
                st.error("❌ Please enter your destination!")
            elif to_date < from_date:
                st.error("❌ End date must be after start date!")
            else:
                st.success("✅ Creating your personalized itinerary...")
                st.session_state.form_submitted = True
                st.session_state.show_form = False
                trip_data = {
                    "origin": origin.strip(),
                    "destination": destination.strip(),
                    "from_date": from_date,
                    "to_date": to_date,
                    "transport": transport,
                    "stay": stay,
                    "budget": budget.strip(),
                    "activities": activities.strip()
                }
                st.session_state.trip_context = trip_data
                with st.spinner("🎯 Crafting your detailed multi-day itinerary..."):
                    itinerary = generate_itinerary(trip_data)
                    st.session_state.messages.append({"role": "assistant", "content": itinerary})
                st.rerun()
