# ----------------- IMPORTS -----------------
import streamlit as st
from openai import OpenAI
from datetime import date, timedelta
import re

# ----------------- CONFIG (MUST BE FIRST STREAMLIT COMMAND) -----------------
st.set_page_config(page_title="TRIVANZA", page_icon="✈️", layout="centered")

# ----------------- INIT CLIENT AFTER CONFIG -----------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ----------------- CUSTOM HEADER -----------------
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

# ----------------- SESSION STATE INIT -----------------  
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "trip_context" not in st.session_state:
    st.session_state.trip_context = {}
if "generating_itinerary" not in st.session_state:
    st.session_state.generating_itinerary = False

# ----------------- HELPER FUNCTION -----------------
def get_search_url(platform, destination, query):
    """Generate working search URLs for platforms"""
    domains = {
        "booking": "https://booking.com",  
        "zomato": "https://zomato.com",  
        "klook": "https://klook.com",  
        "getyourguide": "https://getyourguide.com",  
        "airbnb": "https://airbnb.com",  
        "hostelworld": "https://hostelworld.com",  
        "googlemaps": "https://maps.google.com",  
        "citymapper": "https://citymapper.com" 
    }
    encoded_query = "+".join(query.split())
    return f"{domains[platform]}/search?q={destination}+{encoded_query}"

def calculate_arrival_time(trip_data):
    """Calculate local arrival time based on time zone"""
    if "europe" in trip_data["destination"].lower():
        return "6:00 AM CET"
    elif "usa" in trip_data["destination"].lower():
        return "11:00 AM EST"
    else:
        return "6:00 AM Local Time"

def generate_itinerary(trip_data):
    """Generate itinerary using OpenAI API with full flight logic and advanced preferences"""
    start_date = trip_data["from_date"]
    end_date = trip_data["to_date"]
    duration = (end_date - start_date).days + 1
    all_dates = [start_date + timedelta(days=i) for i in range(duration)]

    # Budget parsing
    try:
        budget_amount = int(trip_data["budget_amount"])
    except ValueError:
        st.warning("⚠️ Invalid budget amount. Using default ₹50,000 for planning.")
        budget_amount = 50000

    budget_type = trip_data.get("budget_type", "Mid-Budget")
    currency = trip_data.get("currency", "INR")

    # Budget allocations
    if budget_type == "Luxury":
        flight_pct, hotel_pct, food_pct = 40, 30, 15
    elif budget_type == "Budget":
        flight_pct, hotel_pct, food_pct = 20, 20, 25
    else:
        flight_pct, hotel_pct, food_pct = 30, 25, 20

    # Calculate exact values
    flights = (budget_amount * flight_pct) // 100
    hotels = (budget_amount * hotel_pct) // 100
    food = (budget_amount * food_pct) // 100
    activities = (budget_amount * 15) // 100
    transport = (budget_amount * 10) // 100
    emergency = (budget_amount * 5) // 100

    time_zone_diff = "-4.5 hours" if "europe" in trip_data["destination"].lower() else "-10 hours"

    # Interest-based recommendations
    interest = trip_data.get("custom_activities", [])
    interest_details = {
        "street food": """
- Local food markets with safety tips
- Street food tours with tasting notes
- Best street food for dietary preferences""",
        "hiking": """
- National park passes and guided tours
- Trail difficulty ratings
- Equipment rental options""",
        "shopping": """
- Local market hours and negotiation tips
- Duty-free shopping strategies
- Luxury shopping districts""",
        "nightlife": """
- Top night clubs and bars
- Late-night transportation tips
- Safety guidelines for nightlife"""
    }

    prompt = f"""You are TRIVANZA, the world's most advanced AI travel concierge. Create a COMPLETE {duration}-day itinerary that considers:

MANDATORY REQUIREMENTS:
1. FULL DAY-BY-DAY COVERAGE:
   - Include EVERY day from {all_dates[0].strftime('%B %d')} to {all_dates[-1].strftime('%B %d')}
   - Generate a detailed plan for EACH day (no skipped days)
   - Adjust activities for jet lag on Day 1

2. BUDGET CALCULATIONS:
   - Use total budget: {currency}{budget_amount} ({budget_type})
   - Calculate EXACT amounts from budget:
     - ✈️ Flights: {flight_pct}% of total (₹{flights})
     - 🏨 Hotels: {hotel_pct}% of total (₹{hotels})
     - 🍽️ Food: {food_pct}% of total (₹{food})
     - 🎡 Activities: 15% of total (₹{activities})
     - 🚖 Local Transport: 10% of total (₹{transport})
     - 🧳 Emergency Fund: 5% of total (₹{emergency})

3. FUNCTIONAL LINKS:
   - All links must be in [Text](URL) format
   - Use real platform domains with search parameters
   - Example: [Eiffel Tower]({get_search_url('klook', trip_data['destination'], 'Eiffel Tower')})

TRIP DETAILS:
- Origin: {trip_data['origin']}
- Destination: {trip_data['destination']}
- Dates: {', '.join(date.strftime('%B %d') for date in all_dates)}
- Budget: {currency}{budget_amount} ({budget_type})
- Interests: {', '.join(interest)}
- Group Size: {trip_data.get('group_size', '2 people')}
- Dietary Preferences: {', '.join(trip_data.get('dietary_pref', ['None']))}
- Traveler Type: {trip_data.get('traveler_type', '2 adults')}

CRITICAL LOGISTICS TO INCLUDE:
- Realistic flight departure times (evening from India)
- Time zone adjustments (e.g., Delhi to London: -5.5 hours)
- Airport transfer times (1.5-2 hours)
- Hotel check-in/out logistics
- Jet lag considerations on Day 1
- Return airport logistics on final day

EXACT OUTPUT FORMAT REQUIRED:
# 🌍 {duration}-Day {trip_data['destination']} {budget_type} Adventure
**Travel Period:** {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}
**Time Zone Difference:** {time_zone_diff}
**Currency:** {currency}{budget_amount} ({trip_data.get('currency_type', 'INR')})

## ✈️ FLIGHT DETAILS
**Outbound Journey**
- **6:00 PM IST:** Depart for Indira Gandhi International Airport, Delhi
- **9:00 PM IST:** Flight to {trip_data['destination']} ({trip_data.get('currency_type', 'INR')}{flights} per person)
- **Flight Duration:** Delhi-{trip_data['destination']}: 8h45m
- **Arrival:** Next day {calculate_arrival_time(trip_data)}
- **Airport Transfer:** 1.5-hour taxi to hotel ({trip_data.get('currency_type', 'INR')}{3000 if currency == '₹' else 50})

**Return Journey**
- **Day {duration}:**
  - **2:00 PM {trip_data['destination']} Time:** Depart for airport
  - **3:00 PM {trip_data['destination']} Time:** Arrive at airport
  - **6:00 PM {trip_data['destination']} Time:** Flight departure to Delhi ({trip_data.get('currency_type', 'INR')}{flights//2} per person)
- **Next Day Arrival:** 6:00 AM IST in Delhi

## 🏨 ACCOMMODATION
### {budget_type} Option
- [{trip_data['stay']} in {trip_data['destination']}]({get_search_url('booking', trip_data['destination'], trip_data['stay'])})
  - Price: {trip_data.get('currency_type', 'INR')}{hotels//duration}/night (total: {trip_data.get('currency_type', 'INR')}{hotels})
  - Amenities: ✓ Rooftop view ✓ 24/7 concierge ✓ Pool

## 🗓️ DAY-BY-DAY ITINERARY

## Day 1 - {all_dates[0].strftime('%A, %B %d')} (Arrival Day)
**Flight Logistics**
- 6:00 PM IST: Depart for Delhi Airport
- 9:00 PM IST: Flight to {trip_data['destination']}
- Arrival: Next day {calculate_arrival_time(trip_data)}
- Airport Transfer: 1.5-hour taxi to hotel

**Afternoon (Post-transfer):**
- [{trip_data['stay']} in {trip_data['destination']}]({get_search_url('booking', trip_data['destination'], trip_data['stay'])}) check-in
- [Local Cuisine Dinner]({get_search_url('zomato', trip_data['destination'], 'local cuisine')}) – {trip_data.get('currency_type', 'INR')}{food//duration} per person
- [Nearby attraction]({get_search_url('getyourguide', trip_data['destination'], 'light evening activity')}) – Light evening activity

**Evening:**
- [Restaurant name]({get_search_url('zomato', trip_data['destination'], 'light meal')}) – Light meal recommendation
- Packing tips for next day

## Day 2 - {all_dates[1].strftime('%A, %B %d')}
**Morning (8:00 AM - 12:00 PM):**
- [Major Attraction]({get_search_url('klook', trip_data['destination'], 'major attraction')}) – {trip_data.get('currency_type', 'INR')}{activities//duration}
- [Local Activity]({get_search_url('getyourguide', trip_data['destination'], 'local activity')}) – {trip_data.get('currency_type', 'INR')}{activities//duration}

**Afternoon (12:00 PM - 6:00 PM):**
- [Iconic Restaurant]({get_search_url('zomato', trip_data['destination'], 'iconic restaurant')}) – {trip_data.get('currency_type', 'INR')}{food//duration}
- [Cultural Experience]({get_search_url('getyourguide', trip_data['destination'], 'cultural experience')}) – {trip_data.get('currency_type', 'INR')}{activities//duration}

**Evening (6:00 PM - 10:00 PM):**
- [Night Activity]({get_search_url('klook', trip_data['destination'], 'night activity')}) – {trip_data.get('currency_type', 'INR')}{activities//duration}
- [Local Bar/Nightspot]({get_search_url('zomato', trip_data['destination'], 'bar nightspot')}) – {trip_data.get('currency_type', 'INR')}{food//duration}

## Day 3 - {all_dates[2].strftime('%A, %B %d')}
**Morning (8:00 AM - 12:00 PM):**
- [Historical Site]({get_search_url('klook', trip_data['destination'], 'historical site')}) – {trip_data.get('currency_type', 'INR')}{activities//duration}
- [Local Tour]({get_search_url('getyourguide', trip_data['destination'], 'local tour')}) – {trip_data.get('currency_type', 'INR')}{activities//duration}

**Afternoon (12:00 PM - 6:00 PM):**
- [Iconic Restaurant]({get_search_url('zomato', trip_data['destination'], 'iconic restaurant')}) – {trip_data.get('currency_type', 'INR')}{food//duration}
- [Cultural Activity]({get_search_url('getyourguide', trip_data['destination'], 'cultural activity')}) – {trip_data.get('currency_type', 'INR')}{activities//duration}

**Evening (6:00 PM - 10:00 PM):**
- [Evening Show]({get_search_url('getyourguide', trip_data['destination'], 'evening show')}) – {trip_data.get('currency_type', 'INR')}{activities//duration}
- [Casual Dinner]({get_search_url('zomato', trip_data['destination'], 'casual dinner')}) – {trip_data.get('currency_type', 'INR')}{food//duration}

## Day {duration} - {all_dates[-1].strftime('%A, %B %d')} (Departure Day)
**Morning (8:00 AM - 12:00 PM):**
- **8:00 AM:** Hotel checkout and luggage storage
- [Nearby attraction]({get_search_url('getyourguide', trip_data['destination'], 'airport nearby activity')}) – Light morning activity
- [Quick bite location]({get_search_url('zomato', trip_data['destination'], 'airport breakfast')}) – Breakfast recommendation

**Afternoon:**
- **2:00 PM:** Depart for {trip_data['destination']} Airport  
- **3:00 PM:** Arrive at airport for international departure
- **6:00 PM:** Flight departure to Delhi ({trip_data.get('currency_type', 'INR')}{flights//2} per person)

## RETURN FLIGHT DETAILS
**{(end_date + timedelta(days=1)).strftime('%B %d, %Y')} - Arrival in Delhi**
- **Arrival:** {calculate_arrival_time(trip_data)} at IGI Airport, Delhi
- **Airport transfer home:** {trip_data.get('currency_type', 'INR')}3,000

## 💵 BUDGET BREAKDOWN
- ✈️ Flights: {trip_data.get('currency_type', 'INR')}{flights} ({flight_pct}% of {trip_data.get('currency_type', 'INR')}{budget_amount})
- 🏨 Hotels: {trip_data.get('currency_type', 'INR')}{hotels} ({hotel_pct}% of {trip_data.get('currency_type', 'INR')}{budget_amount})
- 🍽️ Food: {trip_data.get('currency_type', 'INR')}{food} ({food_pct}% of {trip_data.get('currency_type', 'INR')}{budget_amount})
- 🎡 Activities: {trip_data.get('currency_type', 'INR')}{activities} (15% of {trip_data.get('currency_type', 'INR')}{budget_amount})
- 🚖 Local Transport: {trip_data.get('currency_type', 'INR')}{transport} (10% of {trip_data.get('currency_type', 'INR')}{budget_amount})
- 🧳 Emergency Fund: {trip_data.get('currency_type', 'INR')}{emergency} (5% of {trip_data.get('currency_type', 'INR')}{budget_amount})
- 💰 **Total:** {trip_data.get('currency_type', 'INR')}{budget_amount}

## 📌 INTEREST-BASED RECOMMENDATIONS
{"\n".join([f"- {detail}" for interest_type in interest for detail in interest_details.get(interest_type, "").split("\n")])}

## 🔗 BOOKING PLATFORMS
- ✈️ Flights: [MakeMyTrip](https://makemytrip.com),  [Skyscanner](https://skyscanner.com) 
- 🏨 Hotels: [Booking.com](https://booking.com),  [Airbnb](https://airbnb.com) 
- 🎡 Activities: [Klook](https://klook.com),  [GetYourGuide](https://getyourguide.com) 
- 🍽️ Restaurants: [Zomato](https://zomato.com),  [Google Maps](https://maps.google.com) 
- 🗺️ Navigation: [Citymapper](https://citymapper.com) 

Would you like to refine any aspect of this itinerary?"""

    try:
        response = client.chat.completions.create(
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
Budget: {st.session_state.trip_context.get("budget_amount", "")} {st.session_state.trip_context.get("currency_type", "")}
Activities: {st.session_state.trip_context.get("activities", "")}
Answer ONLY travel-related questions using this context.
                """}
            ]
            messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]
            with st.spinner("✈️ Planning your response..."):
                response = client.chat.completions.create(
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
        
        # Basic Information
        st.markdown("#### 🧑‍🤝‍🧑 Traveler Details")
        col1, col2 = st.columns(2)
        with col1:
            traveler_type = st.selectbox("🧍 Traveler Type", ["Solo", "Couple", "Family", "Group"], key="traveler_type")
        with col2:
            group_size = st.number_input("👥 Group Size", min_value=1, value=2, key="group_size")
        
        # Origin & Destination
        st.markdown("#### 📍 Destination & Dates")
        col3, col4 = st.columns(2)
        with col3:
            origin = st.text_input("🌍 Origin", placeholder="e.g., Delhi", key="origin_input")
        with col4:
            destination = st.text_input("📍 Destination", placeholder="e.g., Paris", key="dest_input")
        col5, col6 = st.columns(2)
        with col5:
            from_date = st.date_input("📅 From Date", min_value=date.today(), key="from_date_input")
        with col6:
            to_date = st.date_input("📅 To Date", min_value=from_date, key="to_date_input")
        
        # Preferences Section
        st.markdown("#### 🎯 Travel Preferences")
        col7, col8 = st.columns(2)
        with col7:
            dietary_pref = st.multiselect("🥗 Dietary Preferences", 
                                        ["Vegetarian", "Vegan", "Gluten-Free", "Halal", "Kosher", "Nut Allergy"], 
                                        key="dietary_pref")
            language_pref = st.selectbox("🌐 Preferred Language", 
                                       ["English", "Hindi", "French", "Spanish", "Mandarin", "Local Phrases"], 
                                       key="language_pref")
            accessibility = st.checkbox("♿ Accessibility Required", key="accessibility")
            payment_methods = st.multiselect("💳 Payment Methods", 
                                          ["Credit Card", "Debit Card", "Cash", "Mobile Payment", "Local Bank Transfer"],
                                          default=["Credit Card"],
                                          key="payment_methods")
        with col8:
            sustainability = st.selectbox("🌱 Sustainability Preference", 
                                       ["None", "Eco-Friendly Stays", "Carbon Offset Flights", "Zero-Waste Activities"], 
                                       key="sustainability")
            flight_class = st.selectbox("✈️ Flight Class", 
                                      ["Economy", "Premium Economy", "Business"], 
                                      key="flight_class")
            layover_pref = st.selectbox("⌛ Layover Preference", 
                                       ["None", "Short", "Long"], 
                                       key="layover_pref")
            cultural_pref = st.selectbox("👗 Cultural Sensitivity", 
                                       ["Standard", "Conservative Dress", "Religious Holidays", "Gender Norms"], 
                                       key="cultural_pref")
        
        # Advanced Preferences
        st.markdown("#### 🧳 Advanced Preferences")
        col9, col10 = st.columns(2)
        with col9:
            health_risk = st.selectbox("🛡️ Risk Tolerance", 
                                      ["Low", "Medium", "High"], 
                                      key="risk_tolerance")
            vaccination = st.selectbox("💉 Vaccination Status", 
                                     ["Up-to-Date", "Not Required", "Partially Vaccinated"], 
                                     key="vaccination_status")
        with col10:
            packing_style = st.selectbox("🧳 Packing Style", 
                                       ["Light Pack", "Full Suitcase", "Backpacking", "Luxury Travel"], 
                                       key="packing_style")
            transport_pref = st.multiselect("🚇 Local Transport", 
                                         ["Public Transit", "Taxi", "Uber", "Car Rental", "Walking"],
                                         default=["Public Transit"],
                                         key="transport_pref")
        
        # Custom Interests
        st.markdown("#### 🎨 Custom Interests")
        custom_activities = st.multiselect("🎯 Interests",
                                       ["Photography Spots", "Hidden Gems", "Adventure Sports", 
                                        "Shopping", "Nightlife", "Cultural Immersion", "Foodie Tour"],
                                       key="custom_activities")
        
        # Budget & Accommodation
        st.markdown("#### 💰 Budget & Stay")
        col11, col12 = st.columns(2)
        with col11:
            transport = st.selectbox("🛫 Transport Mode", ["Flight", "Train", "Car", "Bus"], key="transport_input")
        with col12:
            stay = st.selectbox("🏨 Accommodation", ["Hotel", "Hostel", "Airbnb", "Resort"], key="stay_input")
        col13, col14 = st.columns(2)
        with col13:
            budget_amount = st.number_input("💰 Budget Amount", min_value=1000, step=1000, key="budget_amount")
        with col14:
            currency_type = st.selectbox("💱 Currency", ["₹ INR", "$ USD", "€ EUR", "£ GBP", "¥ JPY"], key="currency_type")
        activities = st.text_area("🎯 Activities", placeholder="e.g., beaches, hiking, shopping", key="activities_input")
        
        # Submit Button
        submit = st.form_submit_button("🚀 Generate My Itinerary", use_container_width=True)
        
        if submit:
            if not origin.strip():
                st.error("❌ Please enter your origin city!")
            elif not destination.strip():
                st.error("❌ Please enter your destination!")
            elif to_date < from_date:
                st.error("❌ End date must be after start date!")
            elif budget_amount <= 0:
                st.error("❌ Budget must be greater than 0")
            else:
                st.success("✅ Creating your personalized itinerary...")
                st.session_state.form_submitted = True
                st.session_state.show_form = False
                st.session_state.generating_itinerary = True

                trip_data = {
                    "origin": origin.strip(),
                    "destination": destination.strip(),
                    "from_date": from_date,
                    "to_date": to_date,
                    "transport": transport,
                    "stay": stay,
                    "budget_amount": str(budget_amount),
                    "currency_type": currency_type,
                    "activities": activities.strip(),
                    "traveler_type": traveler_type,
                    "group_size": str(group_size),
                    "dietary_pref": dietary_pref,
                    "language_pref": language_pref,
                    "accessibility": accessibility,
                    "payment_methods": payment_methods,
                    "flight_class": flight_class,
                    "layover_pref": layover_pref,
                    "cultural_pref": cultural_pref,
                    "risk_tolerance": health_risk,
                    "vaccination_status": vaccination,
                    "packing_style": packing_style,
                    "transport_pref": transport_pref,
                    "sustainability": sustainability,
                    "custom_activities": custom_activities,
                    "budget_type": trip_data.get("budget_type", "Mid-Budget"),
                    "currency": currency_type[0]
                }

                st.session_state.trip_context = trip_data
                with st.spinner("🎯 Crafting your detailed multi-day itinerary..."):
                    itinerary = generate_itinerary(trip_data)
                    st.session_state.messages.append({"role": "assistant", "content": itinerary})
                    st.session_state.generating_itinerary = False
                st.rerun()

# Handle ongoing itinerary generation
if st.session_state.generating_itinerary:
    with st.spinner("🎯 Still working on your itinerary..."):
        pass
