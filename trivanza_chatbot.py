import streamlit as st
from openai import OpenAI
from datetime import date, datetime, timedelta
import pandas as pd

# Page configuration for the Streamlit app
st.set_page_config(page_title="✈️ Trivanza - Your AI Travel Assistant", layout="centered")

# Initialize the OpenAI client
# Make sure to have your OPENAI_API_KEY set as an environment variable
client = OpenAI()

# --- Restored Original Features & Data ---

# Currency rate table for INR conversion (Restored from original script)
CURRENCY_RATES = pd.DataFrame([
    {"Currency": "US Dollar", "Code": "USD", "INR_Value": 86.28},
    {"Currency": "Euro", "Code": "EUR", "INR_Value": 99.75},
    {"Currency": "British Pound", "Code": "GBP", "INR_Value": 116.94},
    {"Currency": "Japanese Yen", "Code": "JPY", "INR_Value": 0.60},
    {"Currency": "Australian Dollar", "Code": "AUD", "INR_Value": 56.35},
    {"Currency": "Canadian Dollar", "Code": "CAD", "INR_Value": 63.55},
    {"Currency": "Swiss Franc", "Code": "CHF", "INR_Value": 106.01},
    {"Currency": "Chinese Yuan", "Code": "CNY", "INR_Value": 12.02},
    {"Currency": "UAE Dirham", "Code": "AED", "INR_Value": 23.51},
    {"Currency": "Singapore Dollar", "Code": "SGD", "INR_Value": 67.36},
    {"Currency": "New Zealand Dollar", "Code": "NZD", "INR_Value": 52.38},
    {"Currency": "Russian Ruble", "Code": "RUB", "INR_Value": 1.10},
    {"Currency": "South African Rand", "Code": "ZAR", "INR_Value": 4.83},
    {"Currency": "Brazilian Real", "Code": "BRL", "INR_Value": 15.77},
    {"Currency": "Saudi Riyal", "Code": "SAR", "INR_Value": 22.99},
    {"Currency": "Qatari Riyal", "Code": "QAR", "INR_Value": 23.66},
    {"Currency": "Kuwaiti Dinar", "Code": "KWD", "INR_Value": 281.80},
    {"Currency": "Bahraini Dinar", "Code": "BHD", "INR_Value": 228.77},
    {"Currency": "Omani Rial", "Code": "OMR", "INR_Value": 224.42},
])

# --- Core Application Logic and Prompts ---

# This is the full, combined system prompt. It includes all of your original
# detailed instructions plus the new "Google for Travelers" enhancements.
ENHANCED_SYSTEM_PROMPT_TEMPLATE = """
IMPORTANT: You are Trivanza, an expert, all-in-one AI travel assistant. You are a "Google for Travelers." YOUR #1 PRIORITY IS TO ASSIST WITH ON-THE-GO, REAL-TIME TRAVELER NEEDS. This includes emergencies, navigation, and finding local services. This is just as important as trip planning.

Your capabilities include:
- **On-the-Go & Emergency Assistance (TOP PRIORITY):** Finding nearby places (ATMs, hospitals, pharmacies, petrol pumps, EV charging), checking live flight status, navigating local transport, and providing guidance for emergencies like a lost passport.
- **Trip Planning:** Creating detailed itineraries, suggesting bookings, packing lists, and budgets.
- **Practical Information:** Answering questions on visa requirements, currency exchange, local SIM cards, and Wi-Fi.

You MUST use the current real-world date and location as context.
- Today is {today_str}.
- The user's current location is: **{current_location}**. You MUST use this for all on-the-go requests like "nearest hospital". Do NOT ask for their location.

NEVER say "I don't have access to real-time data." You MUST simulate **plausible, realistic information** based on typical data.
- For a nearby place: "The nearest hospital to your location in Gurugram is Medanta - The Medicity. It's about a 15-minute drive. Should I provide directions?"
- For flight status: "IndiGo flight 6E-204 from Delhi to Mumbai appears to be on time for its 16:30 departure today."

--- CRITICAL RULE: WHEN TO ANSWER ---
You MUST answer any query related to a traveler's needs. This includes ANY question about their location, safety, health, money, or logistics while traveling.
NEVER refuse a query about weather, local directions, finding a place, or emergencies. A request for a "hospital" or "pharmacy" is a high-priority travel request.

Refuse ONLY if a query is COMPLETELY UNRELATED to travel (e.g., "write a python script"). If you must refuse, politely say: "My expertise is in travel. I can help with planning your trip or with on-the-go needs like finding places, but I can't answer questions outside of that scope."

--- TRAVEL KEYWORDS (Your area of expertise) ---
(This is a non-exhaustive list. Use your judgment for any travel-related topic.)
🔧 **On-the-Go & Emergency:** **Nearest ATM, Hospital near me, Pharmacy, Petrol pump, EV charging, Mechanic, Free Wi-Fi, Local SIM card, Lost passport, Embassy contact, Emergency numbers, Police, Currency exchange.**
✈️ **Transportation & Logistics:** Flight deals, Flight status, Gate change, Car rentals, Self Drive Car, Train, Bus, Airport transfers, Visa requirements, Passport rules, Travel insurance, Packing checklist.
🏨 **Accommodation & Lodging:** Hotels, Resorts, Hostels, Guesthouses, Homestays, Airbnb, Boutique hotels, Budget accommodations, Luxury stays.
🍽️ **Food & Drink:** Local cuisine, Street food, Food tours, Best restaurants, Fine dining, Vegetarian-friendly, Halal food, Vegan travel.
And all other travel planning keywords (Destinations, Activities, etc.)

--- ITINERARY OUTPUT FORMAT (Original Detailed Instructions Preserved) ---
IMPORTANT: For every itinerary, you MUST follow all these instructions STRICTLY:
1.  **Greeting:** Always begin with a warm, Personalized Travel Greeting Lines (with Place & Duration) (e.g., "Hello Traveler! Let's plan your amazing 7-day getaway to Bali!").
2.  **Formatting:**
    - Use Markdown, but never use heading levels higher than `###`.
    - Each day should be started with a heading: `### Day N: <activity/city> (<YYYY-MM-DD>)`.
    - Every single itinerary item (flight, hotel, meal, activity, transportation, etc.) MUST be in a separate paragraph (two line breaks).
    - Suggest REALISTIC named options (e.g., "Air India AI-123", "Ibis Paris Montmartre") with plausible, working booking/info links: `[Book](https://www.booking.com/...)`.
    - Show the cost for each item and sum exact costs for each day: `🎯 Daily Total: ₹<amount>`.
3.  **Cost Calculation:**
    - All costs MUST be for the **total number of travelers** and the **entire trip duration**.
    - For international trips, show prices in **both local currency and INR**, clearly stating the exchange rate used.
    - Always include realistic local transportation costs for the group within each day's plan.
4.  **Final Sections (In this exact order and format):**
    - `🧾 Cost Breakdown:` (Flights, Accommodation, Meals, Transportation, Activities, Travel Extras)
    - `💰 Grand Total: ₹<sum>`
    - `🎒 Packing Checklist:` (Must be personalized for the destination, weather, and activities).
    - `💼 Budget Analysis:` (Analyze cost vs. budget and provide actionable, expert advice. State exactly how much is left or over).
    - `📌 Destination Pro Tip:` (A fun, useful tip about the location).
    - `⚠️ *Disclaimer: All estimated costs are for guidance only...*`
5.  **Closing:** Always ask: "Would you like any modifications or changes to your itinerary? If yes, please specify and I'll update it accordingly."
"""

# --- App State and Helper Functions ---
# Simulate fetching the user's current location. In a real app, this would
# come from a GPS API or a location service.
CURRENT_LOCATION = "Gurugram, Haryana, India"

def build_system_prompt():
    """Builds the system prompt with current date and location information."""
    today_str = date.today().strftime("%A, %B %d, %Y")
    return ENHANCED_SYSTEM_PROMPT_TEMPLATE.format(
        today_str=today_str,
        current_location=CURRENT_LOCATION
    )

# Build the final system prompt to be used in the API call
FINAL_SYSTEM_PROMPT = build_system_prompt()

# Initial greeting message for the chat
greeting_message = f"""
Hello Traveler! Welcome to Trivanza - I'm Your Smart Travel Companion.

I see you're currently in **{CURRENT_LOCATION}**. I'll use this for any on-the-go requests.

- **Submit the "Plan My Trip" form** for a customised itinerary.
- **Use this chat** for any other travel questions, like "Where is the nearest hospital?" or "Is my flight on time?"
"""

def format_trip_summary(ctx):
    """Formats the user's trip details for display (Restored from original)."""
    date_fmt = f"{ctx['from_date']} to {ctx['to_date']}"
    travelers = f"{ctx['group_size']} {'person' if ctx['group_size']==1 else 'people'} ({ctx['traveler_type']})"
    budget = f"{ctx['currency_type']} {ctx['budget_amount']}"
    food = ', '.join(ctx['food_preferences']) if ctx.get('food_preferences') else 'None'
    comm_conn = ', '.join(ctx['comm_connectivity']) if ctx.get('comm_connectivity') else 'None'
    sustainability = ctx['sustainability']
    cultural = ctx['cultural_pref']
    activities_interests = ', '.join(ctx['activities_interests']) if ctx.get('activities_interests') else 'None'
    accommodation = ', '.join(ctx['accommodation_pref']) if ctx.get('accommodation_pref') else 'None'
    mode = ctx.get("mode_of_transport", "Any")
    purpose = ctx.get("purpose_of_travel", "None")
    return (
        f"**Trip Summary:**\n"
        f"- **From:** {ctx['origin']}\n"
        f"- **To:** {ctx['destination']}\n"
        f"- **Dates:** {date_fmt}\n"
        f"- **Travelers:** {travelers}\n"
        f"- **Purpose of Travel:** {purpose}\n"
        f"- **Budget:** {budget}\n"
        f"- **Accommodation Preferences:** {accommodation}\n"
        f"- **Preferred Transport:** {mode}\n"
        f"- **Food Preferences:** {food}\n"
        f"- **Communication & Connectivity:** {comm_conn}\n"
        f"- **Sustainability:** {sustainability}\n"
        f"- **Cultural Sensitivity:** {cultural}\n"
        f"- **Activities & Interests:** {activities_interests}\n"
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
    .logo-container { display: flex; justify-content: center; align-items: center; margin-bottom: 10px; }
    .logo { width: 300px; }
    .stChatInputContainer { position: fixed; bottom: 0; width: 100%; background: white; z-index: 1001; padding-bottom: 1rem; }
    .appview-container .main .block-container { padding-bottom: 5rem; }
</style>
<div class="logo-container">
    <img class="logo" src="https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/Trivanza.png?raw=true" alt="Trivanza Logo">
</div>
""", unsafe_allow_html=True)

# "Plan My Trip" form inside an expander, using all original fields
with st.expander("📋 Plan My Trip", expanded=st.session_state.trip_form_expanded):
    with st.form("travel_form", clear_on_submit=True):
        st.markdown("### 🧳 Let's plan your perfect trip!")
        # All form fields are kept as per your original code
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
        with col3: from_date = st.date_input("📅 From Date", min_value=date.today(), key="from_date")
        with col4: to_date = st.date_input("📅 To Date", min_value=from_date, key="to_date")
        st.markdown("#### 💰 Budget & Accommodation")
        col5, col6 = st.columns(2)
        with col5: budget_amount = st.number_input("💰 Budget", min_value=1000, step=1000, key="budget_amount")
        with col6: currency_type = st.selectbox("💱 Currency", ["₹ INR", "$ USD", "€ EUR", "£ GBP", "¥ JPY"], key="currency_type")
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
            st.session_state.trip_context = {
                "origin": origin, "destination": destination, "from_date": from_date, "to_date": to_date,
                "traveler_type": traveler_type, "group_size": group_size, "purpose_of_travel": purpose_of_travel,
                "food_preferences": food_preferences, "comm_connectivity": comm_connectivity,
                "sustainability": sustainability, "cultural_pref": cultural_pref,
                "activities_interests": activities_interests, "budget_amount": budget_amount,
                "currency_type": currency_type, "accommodation_pref": accommodation_pref,
                "mode_of_transport": mode_of_transport
            }
            prompt_for_llm = (f"Plan a trip from {origin} to {destination} from {from_date} to {to_date} for a {traveler_type.lower()} of {group_size} people. Details: {st.session_state.trip_context}")
            st.session_state.pending_llm_prompt = prompt_for_llm
            st.session_state.messages = []
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
    with st.spinner("Thinking..."):
        try:
            messages_payload = [{"role": "system", "content": FINAL_SYSTEM_PROMPT}] + st.session_state.messages
            response = client.chat.completions.create(
                model="gpt-4o",
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
    st.session_state.pending_form_response = False
    with st.spinner("🚀 Your personalized itinerary is being crafted..."):
        try:
            messages_payload = [{"role": "system", "content": FINAL_SYSTEM_PROMPT}] + st.session_state.messages
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages_payload,
                temperature=0.7,
                max_tokens=3500
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
