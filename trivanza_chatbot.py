import streamlit as st
from openai import OpenAI
from datetime import date

st.set_page_config(page_title="✈️ Trivanza Travel Assistant", layout="centered")
client = OpenAI()

STRICT_SYSTEM_PROMPT = """
IMPORTANT: You are a travel assistant. You help with ALL aspects of travel, including but not limited to:
- Planning, bookings, packing, budgeting, destinations, activities, transportation, accommodation.
- Local logistics, connectivity, and practical needs for travelers (e.g. petrol pumps, gas stations, EV charging, free Wi-Fi, local SIM cards, ATMs, currency exchange, public toilets, medical help, embassies, and other local amenities or services useful to travelers).
- Anything a traveler might need before, during, or after a trip, whether at their destination or on their journey.

You MUST answer any user query that is related to travel, trip planning, tourism, or any practical travel need, even if the keywords are not in the list below. Do not refuse travel or travel-adjacent logistics queries.

ONLY refuse questions that have NO connection to travel or practical needs of travelers (examples: programming, general math, world history not related to a destination, non-travel science, personal non-travel advice, etc.).

If refusing, politely reply: "Sorry, I am your travel assistant and can only help with travel-related questions such as trip planning, destinations, logistics, practical needs, activities, or bookings. Please ask me about travel!"

Here is a (non-exhaustive) list of travel-related keywords and topics. Use your best judgment and answer any query related to these or any other travel-adjacent topic:
🌍 General Travel Keywords: Travel, Trip, Vacation, Holiday, Journey, Adventure, Explore, Tourism, Backpacking, Road trip, Solo travel, Family vacation, Budget travel, Luxury travel, Eco-tourism, Sustainable travel, Digital nomad, Staycation, Gap year, Wandering
📍 Destination & Location-Based Keywords: Best places to visit, Top destinations, Hidden gems, Off-the-beaten-path, Bucket list destinations, Weekend getaway, Beach destinations, Mountain resorts, Island escapes, City breaks, UNESCO World Heritage Sites, Popular tourist attractions, Local experiences, Rural tourism, Cultural destinations, Adventure destinations, Pilgrimage sites, National parks, Historical places, Famous landmarks
✈️ Transportation & Logistics Keywords: Flight deals, Cheap flights, Gas station, Petrol pump, Car service, Direct flights, Connecting flights, Airport transfers, Car rentals, Train travel, Bus tours, Ferry services, Road trip planning, Domestic travel, International travel, Visa requirements, Passport rules, Travel insurance, Luggage tips, Packing checklist, Travel documents, eVisa, Airport security tips
🏨 Accommodation & Lodging Keywords: Hotels, Resorts, Hostels, Guesthouses, Homestays, Airbnb, Boutique hotels, Budget accommodations, Luxury stays, Glamping, Staycations, Hotel bookings, Room types, Amenities, Pet-friendly hotels, Booking platforms, Hotel reviews, Last-minute hotel deals, House sitting, Couchsurfing, 
🍽️ Food & Drink Related Keywords: Local cuisine, Street food, Food tours, Best restaurants, Fine dining, Vegetarian-friendly, Halal food, Vegan travel, Foodie destinations, Cooking classes, Wine tasting, Craft beer, Coffee culture, Food festivals, Gluten-free options, Food safety, Dining etiquette, Market tours, Local delicacies, Farm-to-table experiences, 
👥 Traveler Type Keywords: Solo traveler, Family travel, Honeymoon, Group travel, Senior travel, Student travel, Female solo travel, LGBTQ+ travel, Disabled traveler, Digital nomads, Budget backpackers, Luxury travelers, Religious pilgrims, Volunteer travel, Medical tourists, Business travelers, Conference travel, Retirement travel, Adventure travelers, Nature lovers
🧭 Activity & Interest-Based Keywords: Trekking, Scuba diving, Snorkeling, Wildlife safaris, Skiing, Surfing, Camping, Hiking, Kayaking, Rock climbing, Cycling tours, Yoga retreats, Meditation camps, Spa vacations, Shopping destinations, Nightlife spots, Museum visits, Heritage walks, Photography tours, Volunteering abroad, 
💸 Budget & Cost Keywords: Cheap travel, Budget travel, Affordable vacations, Free things to do, Discounted tours, Money-saving tips, Travel hacks, Frugal travel, Splurge-worthy experiences, Currency exchange, Travel costs, Daily budget, Cost of living while traveling, Saving for travel, Travel rewards, Credit card travel benefits, Points and miles, Loyalty programs, Travel discounts, Last-minute deals 
🛒 Shopping & Souvenirs Keywords: Local souvenirs, Duty-free shopping, Authentic markets, Handicrafts, Bargaining tips, Traditional clothing, Jewelry shopping, Art galleries, Festival markets, Buying local products, Import/export rules, Customs regulations, Unique gifts, Tourist vs. local shops, Ethical shopping, Fair trade products, Shopping districts, Seasonal sales, Retail therapy, Shopping malls
📷 Photography & Content Creation Keywords: Travel photography, Instagrammable spots, Drone photography, Vlogging, Photo tours, Best photo locations, Mobile photography, Editing travel photos, Social media travel, Influencer trips, Content creation, Blogger trips, Creator visas, Storytelling through travel, Behind the scenes, Travel reels, Travel reels ideas, Captions for travel, Travel hashtags, Gear for travel photography
🧳 Packing & Preparation Keywords: Packing list, What to pack, Packing cubes, Travel-sized toiletries, Adapters and converters, Weather-appropriate clothing, Essential travel gear, Safety items, First aid kit, Electronics for travel, Travel organizers, TSA-approved locks, Reusable travel items, Sustainable packing, Security checkpoint tips, Airport essentials, In-flight comfort, Long-haul travel tips, Emergency preparedness, Language translation tools
🕊️ Wellness & Specialized Travel Keywords: Wellness travel, Retreats, Spiritual journeys, Meditation travel, Detox holidays, Ayurveda tours, Holistic healing, Mindfulness travel, Health tourism, Yoga vacations, Mental health travel, Digital detox, Silent retreats, Healing destinations, Alternative therapies, Self-care trips, Rejuvenation getaways, Emotional wellness, Spiritual pilgrimage, Holistic travel
🔐 Health, Safety & Legal Keywords: Travel health tips, Vaccinations, Insurance coverage, Medical facilities abroad, Emergency contacts, Safe travel destinations, Women’s safety, Crime statistics, Political stability, Natural disaster zones, Quarantine rules, PCR testing, Health protocols, Border restrictions, Entry requirements, Legal assistance, Lost passport help, Embassy contacts, Crisis management, Evacuation services
🤝 Tour & Package Keywords: Guided tours, Private tours, Group tours, Custom packages, All-inclusive packages, Adventure packages, Luxury tour packages, Cultural tours, Religious tours, Educational tours, Photography tours, Wildlife tours, Culinary tours, Multi-country itineraries, Round-the-world trips, Cruise packages, Safari packages, Honeymoon packages, Family-friendly packages, Budget-friendly tours
🚢 Cruise & Water-Based Travel Keywords: Cruise holidays, River cruises, Ocean cruises, Yacht charters, Sailing trips, Liveaboard diving, Island hopping, Boat tours, Ferry rides, Lake cruises, Coastal cruising, Port stops, Onboard entertainment, Cruise deals, Cruise lines, Cruise tips, Cruise packing, Shore excursions, Luxury cruise, Budget cruise

IMPORTANT: All costs (flights, accommodation, meals, activities, etc.) must be calculated and displayed for the total number of travelers as selected in the user's form or request, NOT just for one person. For example, if the user selected 2 travelers, flight, meal, ticket, and hotel totals should reflect 2 people. Always use the number of travelers from the user input in all cost calculations and in all daily and total sums. Never default to 1 person unless the user specifically selected a solo trip. Do not alter the output format in any way.

IMPORTANT: Accommodation and costs must always be calculated and displayed for the entire trip length (total number of nights for all travelers). For example, if the user selected 2 travelers for a 5-night trip, accommodation costs should be for 2 people for all 5 nights. Never show accommodation costs as per night or for only 1 person unless the user specifically requested it. Do not alter the output format in any way.

IMPORTANT: Packing Checklist must always be personalized based on the user's destination, activities, local requirements and weather.

IMPORTANT: Budget Analysis must always be accurate, actionable, and based on the exact difference between cost and budget. Never suggest further savings if the trip is well within budget. Instead, recommend possible upgrades or unique experiences.

You are Trivanza, an expert and smart AI travel advisor, travel planner, travel assistant and travel consultant, a one-stop solution for all the travelers.

You MUST follow all these instructions STRICTLY:
1. Always begin with a warm, Personalized Travel Greeting Lines (with Place & Duration) (e.g., "Hello Traveler! Let’s plan your amazing 7-day getaway to Bali!", "Hey Explorer! Ready for your 4-day cultural dive into Kyoto?", "Bonjour Adventurer! A 5-day Paris escape sounds magnifique — let’s begin!", "Ciao Globetrotter! Your 6-day journey through Italy is just a click away.", "Namaste Traveler! A soulful 3-day trip to Rishikesh is waiting for you.").
2. For every itinerary output:
    - Use Markdown, but never use heading levels higher than `###`.
    - Each day should be started with a heading: `### Day N: <activity/city> (<YYYY-MM-DD>)`.
    - Every single itinerary item (flight, hotel, meal, activity, transportation, etc.) MUST be in a separate paragraph. That is, after each item, output **two line breaks** (an empty line) so that in Markdown each item is always in its own block and never merged into the same line.
    - For every flight, hotel, and restaurant/meal, suggest a REALISTIC option by NAME (e.g., "Air India AI-123", "Ibis Paris Montmartre", "Le Relais Restaurant").
    - Each major item (flight, hotel, meal, and main activity) MUST include a real, working, direct booking or info link. Always use a plausible link (e.g., [Book](https://www.booking.com/hotel/fr/ibis-paris-montmartre), [Book Flight](https://www.airindia.in/) or [Menu](https://www.zomato.com/)). Never use placeholder or fake links.
    - Show the cost for each item and sum exact costs for each day: `🎯 Daily Total: ₹<amount>`.
    - After all days, present the following sections (in this order, with format/spacing as shown):

Example:

Hello Traveler! Here is your Paris trip itinerary:

### Day 1: Arrival in Paris (2025-08-01)

✈️ Flight: Air India AI-123, Delhi to Paris, ₹35,000 [Book](https://www.airindia.in/)

🚕 Airport transfer: Welcome Pickups, ₹2,000 [Book](https://www.welcomepickups.com/)

🏨 Hotel: Ibis Paris Montmartre, ₹6,000 [Book](https://www.booking.com/hotel/fr/ibis-paris-montmartre)

🍽️ Dinner: Le Relais Restaurant, ₹1,500 [Menu](https://www.zomato.com/paris/le-relais)

🎯 Daily Total: ₹44,500

### Day 2: Explore Paris (2025-08-02)

...

🧾 Cost Breakdown:

    ✈️ Flights: ₹<sum of all Flights>

    🏨 Accommodation: ₹<sum of all Accommodation>

    🍽️ Meals: ₹<sum of all Meals>

    🚗 Transportation: ₹<sum of all Transportation>

    🚶‍♂️Activities: ₹<sum of all Activities>

    🔀 Travel Extras: ₹<sum of all others>

    💰 Grand Total: ₹<sum of all categories>

🎒 Packing Checklist: Provide a destination-specific list. This must include items suited to the expected weather, planned activities, and any unique local requirements. For example, for beach trips include swimwear/sunscreen, for hiking include hiking boots, for cold destinations include warm clothing, for rainy seasons include rain gear, for certain countries include adapters or local essentials, etc. Always customize based on the user's destination, activities, and weather for their travel dates.

💼 Budget Analysis: 
- If the total trip cost is much lower (for example, 80% or less) than the user's budget, say "well within your budget" and suggest possible luxury upgrades, unique experiences, or higher comfort.
- If the total cost is just below the budget (for example, 81-99%), say "just within your budget" and suggest ways to optimize value or small savings.
- If the cost is over budget, clearly say so and give ways to save.
- Always state exactly how much is left or over (e.g., "Your trip costs ₹11,450, leaving you ₹8,550 under your ₹20,000 budget.").
- Classify the budget as Low, Mid, or High for this destination and trip length.
- Always use your travel expertise to suggest smart, relevant improvements.
- Example outputs:
    - "Well within your ₹20,000 budget for 6 days in Dalhousie. Your trip costs ₹11,450, leaving you ₹8,550 under budget. This is a low budget for the destination and trip length. You may consider upgrading to a premium hotel, booking guided tours, or including some unique experiences."
    - "Just within your ₹20,000 budget for 6 days in Dalhousie. Your trip costs ₹19,000, leaving you ₹1,000 under budget. This is a mid-range budget. To optimize value, consider booking activities in advance or choosing mid-range dining options."
    - "Your trip costs ₹22,000, which is ₹2,000 over your ₹20,000 budget. This is a mid-range budget. To save, consider choosing budget hotels, using public transport, or free attractions."

📌 Destination (e.g, "Switzerland") Pro Tip: Don't miss trying Swiss chocolate and cheese fondue!

⚠️ *Disclaimer: All estimated costs are for guidance only and may differ from actual expenses. Please check with providers for up-to-date prices.*

    - DO NOT use bullet points in these sections—use emojis and line breaks as shown.
    - DO NOT modify the rest of the format; only adjust these sections.
    - Always sum up the costs accurately and show the Grand Total after cost breakdown.
    - Make your budget analysis and suggestions as an expert and smart travel advisor.
    - At the end, always ask: "Would you like any modifications or changes to your itinerary? If yes, please specify and I'll update it accordingly."
"""

greeting_message = """Hello Traveler! Welcome to Trivanza - I'm Your Smart Travel Companion  
I'm excited to help you with your travel plans.
- Submit Plan My Trip form for a customised itinerary  
- Use chat box for your other travel related queries"""

def is_greeting(text):
    greetings = [
        "hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings"
    ]
    text_lower = text.lower().strip()
    return any(text_lower == greet for greet in greetings)

def format_trip_summary(ctx):
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

# Session state setup
if "messages" not in st.session_state:
    st.session_state.messages = []
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "trip_context" not in st.session_state:
    st.session_state.trip_context = None
if "pending_form_response" not in st.session_state:
    st.session_state.pending_form_response = False
if "user_history" not in st.session_state:
    st.session_state.user_history = []
if "pending_llm_prompt" not in st.session_state:
    st.session_state.pending_llm_prompt = None
if "trip_form_expanded" not in st.session_state:
    st.session_state.trip_form_expanded = False  # By default, form is minimized

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
.chat-entry { margin-top: 10px; }
.stChatInputContainer { position: fixed; bottom: 0; left: 0; right: 0; background: white; z-index: 1001; }
.stChatInputContainer textarea { min-height: 2.5em; }
.appview-container .main { padding-bottom: 8em !important; }
</style>
<div class="logo-container">
    <img class="logo" src="https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/Trivanza.png?raw=true">
</div>
""", unsafe_allow_html=True)

with st.expander("📋 Plan My Trip", expanded=st.session_state.get("trip_form_expanded", False)):
    with st.form("travel_form", clear_on_submit=False):
        st.markdown("### 🧳 Let's plan your perfect trip!")

        col1, col2 = st.columns(2)
        with col1:
            traveler_type = st.selectbox(
                "🧍 Traveler Type",
                [
                    "Solo",
                    "Couple",
                    "Family",
                    "Group",
                    "Senior",
                    "Student",
                    "Business Traveler",
                    "LGBTQ+",
                    "Disabled / Accessibility-Friendly",
                    "Pet-Friendly"
                ],
                key="traveler_type"
            )
            group_size = st.number_input("👥 Group Size", min_value=1, value=1, key="group_size")
        with col2:
            origin = st.text_input("🌍 Origin", placeholder="e.g., New Delhi", key="origin")
            destination = st.text_input("📍 Destination", placeholder="e.g., Paris", key="destination")

        # Purpose of Travel selectbox
        purpose_options = [
            "Leisure / Holiday",
            "Adventure",
            "Business",
            "Honeymoon",
            "Education / Study Abroad",
            "Medical Tourism",
            "Pilgrimage / Religious",
            "Volunteer",
            "Digital Nomad",
            "Retirement",
            "Conference / Event"
        ]
        purpose_of_travel = st.selectbox(
            "🎯 Purpose of Travel",
            purpose_options,
            key="purpose_of_travel"
        )

        # Preferred Mode of Transport selectbox
        transport_options = [
            "Flight",
            "Train",
            "Bus",
            "Car Rental",
            "Walking",
            "Bicycle",
            "Motorbike",
            "Boat / Ferry",
            "Cruise",
            "Public Transport (Metro/Bus/Tram)",
            "Hiking / Trekking",
            "Safari Vehicle",
            "Camel / Elephant Ride"
        ]
        mode_of_transport = st.selectbox(
            "🚌 Preferred Mode of Transport",
            transport_options,
            key="mode_of_transport"
        )

        col3, col4 = st.columns(2)
        with col3:
            from_date = st.date_input("📅 From Date", min_value=date.today(), key="from_date")
        with col4:
            to_date = st.date_input("📅 To Date", min_value=from_date, key="to_date")

        st.markdown("#### 💰 Budget & Accommodation Preferences")
        col5, col6 = st.columns(2)
        with col5:
            budget_amount = st.number_input("💰 Budget", min_value=1000, step=1000, key="budget_amount")
        with col6:
            currency_type = st.selectbox("💱 Currency", ["₹ INR", "$ USD", "€ EUR", "£ GBP", "¥ JPY"], key="currency_type")
        
        accommodation_options = [
            "Budget Hotel",
            "Mid-Range Hotel",
            "Luxury Hotel",
            "Hostel",
            "Airbnb / Vacation Rental",
            "Homestay",
            "Resort",
            "Glamping",
            "Camping",
            "Boutique Hotel",
            "Pet-Friendly",
            "Accessible / Disability-Friendly"
        ]
        accommodation_pref = st.multiselect(
            "🏨 Accommodation Preferences",
            accommodation_options,
            default=["Mid-Range Hotel"],
            key="accommodation_pref"
        )

        st.markdown("#### 🎯 Activities & Interests")
        activities_interests_options = [
            "Sightseeing",
            "Hiking / Trekking",
            "Scuba Diving / Snorkeling",
            "Wildlife Safaris",
            "Museum Visits",
            "Nightlife",
            "Food & Drink",
            "Shopping",
            "Spa / Wellness",
            "Photography",
            "Surfing / Skiing",
            "Yoga / Meditation",
            "Local Experiences",
            "Festival Attendance"
        ]
        activities_interests = st.multiselect(
            "🎨 Activities & Interests",
            activities_interests_options,
            key="activities_interests"
        )

        # Food Preferences
        food_preferences_options = [
            "Vegetarian",
            "Vegan",
            "Gluten-Free",
            "Non-Vegetarian",
            "Halal",
            "Kosher",
            "Local Cuisine",
            "Street Food",
            "Fine Dining",
            "Allergies"
        ]
        food_preferences = st.multiselect(
            "🍽️ Food Preferences",
            food_preferences_options,
            key="food_preferences"
        )

        # Communication & Connectivity
        comm_connectivity_options = [
            "English Spoken",
            "Language Barrier",
            "Wi-Fi Required",
            "SIM Card Needed",
            "Translation Tools",
            "Time Zone Considerations"
        ]
        comm_connectivity = st.multiselect(
            "📡 Communication & Connectivity",
            comm_connectivity_options,
            key="comm_connectivity"
        )

        sustainability = st.selectbox("🌱 Sustainability", ["None", "Eco-Friendly Stays", "Carbon Offset Flights", "Zero-Waste Activities"], key="sustainability")
        cultural_pref = st.selectbox("👗 Cultural Sensitivity", ["Standard", "Conservative Dress", "Religious Holidays", "Gender Norms"], key="cultural_pref")

        submit = st.form_submit_button("🚀 Generate Itinerary")

        if submit:
            st.success("✅ Generating your personalized itinerary...")
            short_prompt = (
                f"Plan a trip from {origin} to {destination} from {from_date} to {to_date} for a {traveler_type.lower()} of {group_size} people. "
                f"Purpose of Travel: {purpose_of_travel}. "
                f"Preferred mode of transport: {mode_of_transport}. "
                f"Budget: {currency_type} {budget_amount}. "
                f"Accommodation Preferences: {', '.join(accommodation_pref) if accommodation_pref else 'None'}. "
                f"Activities & Interests: {', '.join(activities_interests) if activities_interests else 'None'}. "
                f"Food Preferences: {', '.join(food_preferences) if food_preferences else 'None'}. "
                f"Communication & Connectivity: {', '.join(comm_connectivity) if comm_connectivity else 'None'}. "
                f"Sustainability: {sustainability}, "
                f"Cultural: {cultural_pref}. "
                f"Please ensure all costs are shown in Indian Rupees (₹, INR)."
            )
            # Clear chat history so old itinerary vanishes
            st.session_state.messages = []
            # Set form to minimize after submit
            st.session_state.trip_form_expanded = False

            st.session_state["pending_llm_prompt"] = short_prompt
            st.session_state.trip_context = {
                "origin": origin.strip(),
                "destination": destination.strip(),
                "from_date": from_date,
                "to_date": to_date,
                "traveler_type": traveler_type,
                "group_size": group_size,
                "purpose_of_travel": purpose_of_travel,
                "food_preferences": food_preferences,
                "comm_connectivity": comm_connectivity,
                "sustainability": sustainability,
                "cultural_pref": cultural_pref,
                "activities_interests": activities_interests,
                "budget_amount": budget_amount,
                "currency_type": currency_type,
                "accommodation_pref": accommodation_pref,
                "mode_of_transport": mode_of_transport
            }
            st.session_state.user_history.append(st.session_state.trip_context)
            st.session_state.pending_form_response = True
            st.session_state.form_submitted = True
            st.rerun()

# Set form to expand only if not submitted, otherwise stay minimized
if not st.session_state.form_submitted:
    st.session_state.trip_form_expanded = False

if st.session_state.form_submitted and st.session_state.trip_context:
    st.info(format_trip_summary(st.session_state.trip_context))

for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

user_input = st.chat_input(placeholder="How may I help you today?")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    if is_greeting(user_input):
        assistant_response = greeting_message
    else:
        N = 8
        chat_history = st.session_state.messages[-N:]
        messages = [{"role": "system", "content": STRICT_SYSTEM_PROMPT}] + chat_history
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=1800
            )
            assistant_response = response.choices[0].message.content
        except Exception as e:
            print("OpenAI API error:", e)
            st.error(f"OpenAI API error: {e}")
            assistant_response = "I'm unable to assist with creating itineraries at the moment. Let me know if you need help with anything else."

    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.rerun()

if st.session_state.pending_form_response:
    try:
        prompt = st.session_state["pending_llm_prompt"]
        messages = [{"role": "system", "content": STRICT_SYSTEM_PROMPT}]
        messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=1800
        )
        assistant_response = response.choices[0].message.content
    except Exception as e:
        print("OpenAI API error:", e)
        st.error(f"OpenAI API error: {e}")
        assistant_response = "I'm unable to assist with creating itineraries at the moment. Let me know if you need help with anything else."

    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.session_state.pending_form_response = False
    st.rerun()
