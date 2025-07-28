import streamlit as st
from openai import OpenAI
from datetime import date, datetime, timedelta
import pandas as pd

# Page configuration for the Streamlit app
st.set_page_config(page_title="✈️ Trivanza - Your AI Travel Assistant", layout="centered")

# Initialize the OpenAI client
# Make sure to have your OPENAI_API_KEY set as an environment variable
client = OpenAI()

# --- Core Application Logic and Prompts ---

# This is the new, enhanced system prompt based on the PDF's vision.
# It instructs the AI to be an all-in-one assistant, handling everything from planning
# to on-the-go needs like finding nearby places, emergency assistance, and visa info.
# It now also includes the detailed formatting and logic from your original prompt.
ENHANCED_SYSTEM_PROMPT_TEMPLATE = """
IMPORTANT: You are Trivanza, an expert, all-in-one AI travel assistant. You are a "Google for Travelers," designed to help with ALL aspects of travel, both for planning *before* a trip and for real-time assistance *during* a trip.

Your capabilities include, but are not limited to:
- **Trip Planning:** Itineraries, bookings, packing, budgeting, destinations, activities, transport, accommodation.
- **On-the-Go Assistance:** Finding nearby places (ATMs, petrol pumps, EV charging, hospitals, pharmacies, restaurants), checking live flight status, and navigating local transport.
- **Emergency Support:** Providing guidance for medical emergencies, lost passports, and connecting with local authorities or embassies.
- **Practical Information:** Answering questions about visa requirements, currency exchange, local SIM cards, Wi-Fi hotspots, and weather forecasts.

You MUST use the current real-world date as context. Today is {today_str}.
- "today" is {today_date}.
- "tomorrow" is {tomorrow_str}.
- "yesterday" is {yesterday_str}.
- "this weekend" starts Saturday, {weekend_str}.

NEVER say "I don't have access to real-time data." Instead, you MUST simulate **plausible, realistic information** based on seasonal norms, location, and typical patterns.
- For weather: "Today ({today_date}), the weather in Delhi is 41°C and sunny — typical for late May."
- For flights: "IndiGo flight 6E-204 from Delhi to Mumbai appears to be on time for its 16:30 departure today."
- For nearby places: "The nearest ATM to the Eiffel Tower is a BNP Paribas, located at 5 Avenue Anatole France. It should be a 2-minute walk."

You MUST answer any user query related to the keywords below or any other travel-adjacent topic. NEVER refuse a query about weather, local directions, or emergencies.

If a query is completely unrelated to travel (e.g., programming, complex math), politely refuse: "Sorry, I am your travel assistant and can only help with travel-related questions. Please ask me about trip planning, destinations, or on-the-go travel needs!"

--- TRAVEL KEYWORDS (Your area of expertise) ---
🌍 **General Travel:** Trip, Vacation, Holiday, Journey, Adventure, Explore, Tourism, Backpacking, Road trip, Solo travel, Family vacation, Budget travel, Luxury travel, weather.
📍 **Destinations:** Best places, Hidden gems, Weekend getaway, Beach, Mountains, City breaks, UNESCO sites, Tourist attractions, Local experiences.
✈️ **Transportation & Logistics:** Flight deals, **Flight status, Gate change,** Car rentals, **Self Drive Car,** Train, Bus, Airport transfers, **Visa requirements, Passport rules,** Travel insurance, Packing list.
🏨 **Accommodation:** Hotels, Resorts, Hostels, Homestays, Airbnb, Boutique hotels, Budget stays, Luxury stays.
🍽️ **Food & Drink:** Local cuisine, Street food, Best restaurants, Fine dining, Vegetarian, Vegan, Halal.
🔧 **On-the-Go & Emergency Assistance:** **Nearest ATM, Hospital near me, Pharmacy, Petrol pump, EV charging, Mechanic, Free Wi-Fi, Local SIM card, eSIM, Lost passport, Embassy contact, Emergency numbers, Police, Currency exchange.**
🧭 **Activities & Interests:** Trekking, Scuba diving, Safaris, Skiing, Surfing, Camping, Hiking, Museums, Nightlife, Shopping, Spa, Yoga retreats.
--- END OF KEYWORDS ---

--- SPECIAL INSTRUCTIONS FOR ON-THE-GO QUERIES ---
IMPORTANT: When the user asks for on-the-go assistance, follow these rules:
1.  **Nearby Places (ATM, Hospital, etc.):** If a user asks for a nearby service, provide a plausible, specific name and location. Simulate giving clear directions (e.g., "Walk 200m towards the main square, it's on your left next to the pharmacy.").
2.  **Lost Passport:** If a user reports a lost passport, provide a clear, step-by-step action plan: 1. Report to local police. 2. Get a police report. 3. Contact your country's nearest embassy or consulate. Provide a simulated address and contact number for the embassy.
3.  **Visa Requirements:** For visa queries, state the general requirements for the given nationality and destination. Provide a plausible link to the official embassy or government website for detailed information.
4.  **Currency Conversion:** Act as a real-time currency converter. When asked to convert an amount, perform the calculation and show the result clearly.
5.  **Flight Status:** When asked for a flight status, provide a simulated real-time update (e.g., "On Time," "Delayed by 30 minutes," "Gate Change to B24").

--- ITINERARY OUTPUT FORMAT ---
IMPORTANT: For every itinerary, you MUST follow all these instructions STRICTLY:
1.  **Greeting:** Always begin with a warm, personalized greeting (e.g., "Hello Traveler! Let's plan your amazing 7-day getaway to Bali!").
2.  **Formatting:**
    - Use Markdown, but never use heading levels higher than `###`.
    - Each day starts with `### Day N: <Activity/City> (<YYYY-MM-DD>)`.
    - Every single item (flight, hotel, meal, activity, local transport) MUST be in its own paragraph (use two line breaks).
    - Suggest REALISTIC named options (e.g., "Air India AI-123," "Ibis Paris Montmartre") with plausible booking/info links: `[Book](https://www.booking.com/...)`.
    - Show costs for each item and a daily total: `🎯 Daily Total: ₹<amount>`.
3.  **Cost Calculation:**
    - All costs MUST be for the **total number of travelers** and the **entire trip duration**.
    - For international trips, show prices in **both local currency and INR**, clearly stating the exchange rate used (e.g., "$100 USD (approx. ₹8300 INR)").
    - Always include realistic local transportation costs for the group within each day's plan.
4.  **Final Sections (After all days, in this exact order and format):**
    - `🧾 Cost Breakdown:` (Flights, Accommodation, Meals, Transportation, Activities, Travel Extras)
    - `💰 Grand Total: ₹<sum>`
    - `🎒 Packing Checklist:` (Must be personalized for the destination, weather, and activities).
    - `💼 Budget Analysis:` (Analyze cost vs. budget and provide actionable, expert advice. State how much is left or over).
    - `📌 Destination Pro Tip:` (A fun, useful tip about the location).
    - `⚠️ *Disclaimer: All estimated costs are for guidance only...*`
    - Finally, always ask: "Would you like any modifications or changes to your itinerary? If yes, please specify and I'll update it accordingly."
"""

# Real-world date setup for the prompt
CURRENT_DATETIME = datetime.now()
CURRENT_DATE = CURRENT_DATETIME.date()

def build_system_prompt():
    """Builds the system prompt with current date information."""
    today_str = CURRENT_DATE.strftime("%A, %B %d, %Y")
    tomorrow_str = (CURRENT_DATE + timedelta(days=1)).strftime("%B %d, %Y")
    yesterday_str = (CURRENT_DATE - timedelta(days=1)).strftime("%B %d, %Y")
    # Find the next upcoming Saturday
    upcoming_weekend = CURRENT_DATE + timedelta(days=(5 - CURRENT_DATE.weekday() + 7) % 7)
    if upcoming_weekend <= CURRENT_DATE:
        upcoming_weekend += timedelta(days=7)
    weekend_str = upcoming_weekend.strftime("%B %d")

    return ENHANCED_SYSTEM_PROMPT_TEMPLATE.format(
        today_str=today_str,
        today_date=CURRENT_DATE,
        tomorrow_str=tomorrow_str,
        yesterday_str=yesterday_str,
        weekend_str=weekend_str
    )

# Build the final system prompt to be used in the API call
FINAL_SYSTEM_PROMPT = build_system_prompt()

# Initial greeting message for the chat
greeting_message = """
Hello Traveler! Welcome to Trivanza - I'm Your Smart Travel Companion.

I can help you with all your travel needs, from detailed planning to on-the-go assistance.

- **Fill out the "Plan My Trip" form** for a customized itinerary.
- **Use this chat** for any other travel questions, like finding nearby places, checking flight status, or getting visa information.
"""

def is_greeting(text):
    """Checks if the user input is a simple greeting."""
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    return text.lower().strip() in greetings

def is_weather_query(text):
    """Checks if the user is asking about the weather."""
    weather_keywords = [
        "weather", "temperature", "rain", "sunny", "cloudy", "forecast",
        "hot", "cold", "climate", "humidity", "wind"
    ]
    return any(keyword in text.lower() for keyword in weather_keywords)


def format_trip_summary(ctx):
    """Formats the user's trip details for display."""
    date_fmt = f"{ctx['from_date']} to {ctx['to_date']}"
    travelers = f"{ctx['group_size']} {'person' if ctx['group_size']==1 else 'people'} ({ctx['traveler_type']})"
    budget = f"{ctx['currency_type']} {ctx['budget_amount']}"
    accommodation = ', '.join(ctx['accommodation_pref'])
    mode = ctx.get("mode_of_transport", "Any")
    purpose = ctx.get("purpose_of_travel", "None")
    activities = ', '.join(ctx['activities_interests']) if ctx.get('activities_interests') else 'None'
    food = ', '.join(ctx['food_preferences']) if ctx.get('food_preferences') else 'None'

    return (
        f"**Trip Summary:**\n"
        f"- **From:** {ctx['origin']} -> **To:** {ctx['destination']}\n"
        f"- **Dates:** {date_fmt}\n"
        f"- **Travelers:** {travelers}\n"
        f"- **Purpose:** {purpose}\n"
        f"- **Budget:** {budget}\n"
        f"- **Transport:** {mode}\n"
        f"- **Accommodation:** {accommodation}\n"
        f"- **Interests:** {activities}\n"
        f"- **Food Prefs:** {food}\n"
    )

# --- Streamlit UI and Session State Management ---

# Initialize session state variables
if "trip_form_expanded" not in st.session_state:
    st.session_state.trip_form_expanded = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "trip_context" not in st.session_state:
    st.session_state.trip_context = None
if "pending_form_response" not in st.session_state:
    st.session_state.pending_form_response = False

# Custom CSS for UI enhancements
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
    /* Make chat input sticky at the bottom */
    .stChatInputContainer {
        position: fixed;
        bottom: 0;
        width: 100%;
        background: white;
        z-index: 1001;
        padding-bottom: 1rem;
    }
    /* Add padding to the bottom of the main content to avoid overlap with chat input */
    .appview-container .main .block-container {
        padding-bottom: 5rem;
    }
</style>
<div class="logo-container">
    <img class="logo" src="https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/Trivanza.png?raw=true" alt="Trivanza Logo">
</div>
""", unsafe_allow_html=True)

# "Plan My Trip" form inside an expander, restoring all original fields
with st.expander("📋 Plan My Trip", expanded=st.session_state.trip_form_expanded):
    with st.form("travel_form", clear_on_submit=True):
        st.markdown("### 🧳 Let's plan your perfect trip!")

        col1, col2 = st.columns(2)
        with col1:
            origin = st.text_input("🌍 Origin", placeholder="e.g., New Delhi", key="origin")
            traveler_type = st.selectbox("🧍 Traveler Type", ["Solo", "Couple", "Family", "Group", "Senior", "Student", "Business Traveler", "LGBTQ+", "Disabled / Accessibility-Friendly", "Pet-Friendly"], key="traveler_type")
        with col2:
            destination = st.text_input("📍 Destination", placeholder="e.g., Paris", key="destination")
            group_size = st.number_input("👥 Group Size", min_value=1, value=1, key="group_size")

        purpose_of_travel = st.selectbox("🎯 Purpose of Travel", ["Leisure / Holiday", "Adventure", "Business", "Honeymoon", "Education / Study Abroad", "Medical Tourism", "Pilgrimage / Religious", "Volunteer", "Digital Nomad", "Retirement", "Conference / Event"], key="purpose_of_travel")
        mode_of_transport = st.selectbox("🚌 Preferred Transport", ["Flight", "Train", "Bus", "Car Rental", "Self Drive Car", "Walking", "Bicycle", "Motorbike", "Boat / Ferry", "Cruise", "Public Transport (Metro/Bus/Tram)"], key="mode_of_transport")

        col3, col4 = st.columns(2)
        with col3:
            from_date = st.date_input("📅 From Date", min_value=date.today(), key="from_date")
        with col4:
            to_date = st.date_input("📅 To Date", min_value=from_date, key="to_date")

        st.markdown("#### 💰 Budget & Accommodation")
        col5, col6 = st.columns(2)
        with col5:
            budget_amount = st.number_input("💰 Budget", min_value=1000, step=1000, key="budget_amount")
        with col6:
            currency_type = st.selectbox("💱 Currency", ["₹ INR", "$ USD", "€ EUR", "£ GBP", "¥ JPY"], key="currency_type")
        
        accommodation_pref = st.multiselect("🏨 Accommodation", ["Budget Hotel", "Mid-Range Hotel", "Luxury Hotel", "Hostel", "Airbnb / Vacation Rental", "Homestay", "Resort", "Glamping", "Boutique Hotel"], default=["Mid-Range Hotel"], key="accommodation_pref")
        
        st.markdown("#### 🎯 Preferences & Interests")
        activities_interests = st.multiselect("🎨 Activities & Interests", ["Sightseeing", "Hiking / Trekking", "Scuba Diving / Snorkeling", "Wildlife Safaris", "Museum Visits", "Nightlife", "Food & Drink", "Shopping", "Spa / Wellness", "Photography"], key="activities_interests")
        food_preferences = st.multiselect("🍽️ Food Preferences", ["Vegetarian", "Vegan", "Gluten-Free", "Non-Vegetarian", "Halal", "Kosher", "Local Cuisine", "Street Food", "Fine Dining"], key="food_preferences")
        comm_connectivity = st.multiselect("📡 Communication & Connectivity", ["English Spoken", "Language Barrier", "Wi-Fi Required", "SIM Card Needed", "Translation Tools"], key="comm_connectivity")
        sustainability = st.selectbox("🌱 Sustainability", ["None", "Eco-Friendly Stays", "Carbon Offset Flights", "Zero-Waste Activities"], key="sustainability")
        cultural_pref = st.selectbox("👗 Cultural Sensitivity", ["Standard", "Conservative Dress", "Religious Holidays", "Gender Norms"], key="cultural_pref")

        submit_button = st.form_submit_button("🚀 Generate Itinerary")

        if submit_button:
            st.session_state.trip_form_expanded = False
            st.session_state.form_submitted = True
            st.session_state.pending_form_response = True
            
            # Store all form data in session state
            st.session_state.trip_context = {
                "origin": origin, "destination": destination, "from_date": from_date, "to_date": to_date,
                "traveler_type": traveler_type, "group_size": group_size, "purpose_of_travel": purpose_of_travel,
                "food_preferences": food_preferences, "comm_connectivity": comm_connectivity,
                "sustainability": sustainability, "cultural_pref": cultural_pref,
                "activities_interests": activities_interests, "budget_amount": budget_amount,
                "currency_type": currency_type, "accommodation_pref": accommodation_pref,
                "mode_of_transport": mode_of_transport
            }
            
            # Create a detailed prompt for the LLM based on the complete form input
            prompt_for_llm = (
                f"Plan a trip from {origin} to {destination} from {from_date} to {to_date} for a {traveler_type.lower()} of {group_size} people. "
                f"Purpose: {purpose_of_travel}. Budget: {currency_type} {budget_amount}. "
                f"Transport: {mode_of_transport}. Accommodation: {', '.join(accommodation_pref)}. "
                f"Interests: {', '.join(activities_interests)}. Food: {', '.join(food_preferences)}. "
                f"Connectivity: {', '.join(comm_connectivity)}. Sustainability: {sustainability}. Cultural: {cultural_pref}. "
                f"Ensure you follow all formatting and content rules from your system instructions precisely."
            )
            st.session_state.pending_llm_prompt = prompt_for_llm
            st.session_state.messages = [] # Clear previous messages for a new itinerary
            st.rerun()

# Display trip summary if a form was submitted
if st.session_state.form_submitted and st.session_state.trip_context:
    st.info(format_trip_summary(st.session_state.trip_context))

# Display chat history
for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Handle new user input from chat box
if user_input := st.chat_input("Ask me anything about your travel..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Handle simple greetings or weather queries directly for a faster response
    if is_greeting(user_input):
        assistant_response = "Hello! How can I help you with your travels today?"
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        st.rerun()
    else:
        with st.spinner("Thinking..."):
            try:
                # Construct the messages payload for the API
                messages_payload = [{"role": "system", "content": FINAL_SYSTEM_PROMPT}] + st.session_state.messages
                
                response = client.chat.completions.create(
                    model="gpt-4o", # Using a more advanced model
                    messages=messages_payload,
                    temperature=0.7,
                    max_tokens=2048
                )
                assistant_response = response.choices[0].message.content
            except Exception as e:
                st.error(f"An error occurred: {e}")
                assistant_response = "I'm having trouble connecting right now. Please try again in a moment."
                
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        st.rerun()

# Handle the response generation after form submission
if st.session_state.pending_form_response:
    prompt = st.session_state.pending_llm_prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.pending_form_response = False # Prevent re-triggering

    with st.spinner("🚀 Your personalized itinerary is being crafted..."):
        try:
            messages_payload = [{"role": "system", "content": FINAL_SYSTEM_PROMPT}] + st.session_state.messages
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages_payload,
                temperature=0.7,
                max_tokens=3500 # Increased tokens for detailed itineraries
            )
            assistant_response = response.choices[0].message.content
        except Exception as e:
            st.error(f"An error occurred while generating the itinerary: {e}")
            assistant_response = "I'm unable to create the itinerary at this moment. Please try again later."
            
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.rerun()

# Show initial greeting if there are no messages
if not st.session_state.messages:
    st.session_state.messages.append({"role": "assistant", "content": greeting_message})
    st.rerun()
