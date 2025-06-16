# ----------------- IMPORTS -----------------
import streamlit as st
from openai import OpenAI
from datetime import date, timedelta

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
def generate_itinerary(trip_data):
    """Generate itinerary using OpenAI API with full flight logic and advanced preferences"""
    # Calculate all dates in the trip
    start_date = trip_data["from_date"]
    end_date = trip_data["to_date"]
    duration = (end_date - start_date).days + 1
    
    # Create list of all dates
    all_dates = []
    current_date = start_date
    for i in range(duration):
        all_dates.append(current_date.strftime("%B %d, %Y"))
        current_date += timedelta(days=1)
    
    # Calculate realistic flight times and time zones
    time_zone_diff = "-4.5 hours" if "europe" in trip_data["destination"].lower() else "-10 hours"
    arrival_time = "6:00 AM" if "europe" in trip_data["destination"].lower() else "11:00 AM"
    return_arrival_time = "6:00 AM IST"

    prompt = f"""You are TRIVANZA, the world's most advanced AI travel concierge. Create a COMPLETE {duration}-day itinerary that considers:

MANDATORY REQUIREMENTS:
1. ✈️ FLIGHT LOGISTICS (MUST INCLUDE):
   - Realistic departure/arrival times with time zone adjustments
   - Airport transfer calculations (1.5-2 hours minimum)
   - Jet lag considerations in activity planning
   - Luggage handling logistics

2. 🏨 ACCOMMODATION:
   - 3 hotel options (luxury/budget/mid-range) with booking links (e.g., [Hotel Name](https://booking.com/hotel-name)) 
   - Hotel-specific amenities (pool, gym, breakfast)
   - Strategic location recommendations near attractions
   - Safety considerations for neighborhoods

3. 🍽️ GASTRONOMY:
   - 3 meals/day with price ranges (local currency)
   - Must-try local dishes with cultural context
   - Dietary options (vegetarian, halal, vegan) with restaurant links (e.g., [Le Jules Verne](https://zomato.com/lejulesverne)) 
   - Restaurant booking links (Zomato/Google Maps)

4. 🗓️ ACTIVITIES:
   - Time-optimized routes with map links (e.g., [Eiffel Tower](https://google.com/maps/place/eiffel-tower)) 
   - Activity booking platforms (e.g., [Eiffel Tower Ticket](https://klook.com/eiffel-tower-ticket)) 
   - Weather-dependent activity alternatives
   - Cultural etiquette tips for each activity

TRIP DETAILS:
- Origin: {trip_data['origin']}
- Destination: {trip_data['destination']}
- Dates: {', '.join(all_dates)}
- Budget: {trip_data['budget']}
- Travelers: {trip_data.get('traveler_type', '2 adults')}
- Group Size: {trip_data.get('group_size', '2 people')}
- Dietary Preferences: {', '.join(trip_data.get('dietary_pref', ['No specific preferences']))}
- Language Preferences: {trip_data.get('language_pref', 'English')}
- Accessibility Required: {trip_data.get('accessibility', False)}
- Payment Methods: {', '.join(trip_data.get('payment_methods', ['Credit Card']))}
- Flight Preferences: Class={trip_data.get('flight_class', 'Economy')}, Layover={trip_data.get('layover_pref', 'None')}
- Cultural Sensitivity: {trip_data.get('cultural_pref', 'Standard')}
- Health & Safety: Risk Tolerance={trip_data.get('risk_tolerance', 'Medium')}, Vaccination Status={trip_data.get('vaccination_status', 'Up-to-Date')}
- Packing Style: {trip_data.get('packing_style', 'Light Pack')}
- Local Transport: {', '.join(trip_data.get('transport_pref', ['Public Transit']))}
- Sustainability: {trip_data.get('sustainability', 'None')}
- Custom Activities: {', '.join(trip_data.get('custom_activities', ['None']))}

CRITICAL:
- All booking links must be in the format: [Text](https://example.com) 
- Link text should match the activity or place name
- Use realistic placeholder URLs (e.g., klook.com, zomato.com, google.com/maps)
- DO NOT use [link], use full markdown syntax

EXACT OUTPUT FORMAT REQUIRED:
# 🌍 {duration}-Day {trip_data['destination']} Ultimate Adventure
**Travel Period:** {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}
**Time Zone Difference:** {time_zone_diff}
**Currency:** INR

## ✈️ FLIGHT DETAILS
**Outbound Journey**
- Departure: 9:00 PM from Delhi
- Flight Duration: e.g., Delhi-{trip_data['destination']}: 8h45m
- Arrival: Next day {arrival_time} local time
- Airport Transfer: 1.5-hour taxi/Uber to hotel (₹X,XXX)

**Return Journey**
- Departure: 3:00 PM from {trip_data['destination']} Airport
- Arrival: 6:00 AM IST in Delhi next day

## 🏨 ACCOMMODATION
### Luxury Option
- [Hotel Name](https://booking.com/hotel-name)   
  - Price: ₹X,XXX/night
  - Amenities: ✓ Rooftop view ✓ 24/7 concierge ✓ Pool

### Mid-Range Option
- [Hotel Name](https://airbnb.com/hotel-name)   
  - Price: ₹X,XXX/night
  - Amenities: ✓ Breakfast included ✓ Free WiFi

### Budget Option
- [Hostel Name](https://hostelworld.com/hostel-name)   
  - Price: ₹X,XXX/night
  - Amenities: ✓ Free walking tours ✓ Kitchen access

## 🗓️ DAY-BY-DAY ITINERARY

## Day 1 - {all_dates[0]} (Arrival Day)
**Flight Logistics**
- 6:00 PM: Depart for Delhi Airport
- 9:00 PM: Flight departure to {trip_data['destination']}
- Arrival: Next day 6:00 AM local time
- Airport Transfer: 1.5-hour taxi to hotel

**Afternoon (Post-transfer):**
- [Hotel Name](https://booking.com/hotel-name)  check-in and rest
- [Le Comptoir du Relais](https://zomato.com/lecomptoir)  – Local cuisine dinner (₹800-1200/pax)
- [Eiffel Tower](https://klook.com/eiffel-tower-ticket)  – Light evening activity

**Evening**
- [Les Ombres](https://zomato.com/lesombres)  – Light meal recommendation
- Packing tips for next day

## Day 2 - {all_dates[1]}
**Morning (8:00 AM - 12:00 PM):**
- [Louvre Museum](https://klook.com/louvre-museum-ticket)  – ₹1500
- [Tuileries Garden](https://google.com/maps/place/Tuileries+Garden)  – Free

**Afternoon (12:00 PM - 6:00 PM):**
- [Le Jules Verne](https://zomato.com/lejulesverne)  – Lunch recommendation (₹7000)
- [Eiffel Tower](https://klook.com/eiffel-tower-ticket)  – ₹2500
- [Seine River Cruise](https://getyourguide.com/seine-cruise)  – ₹2000

**Evening (6:00 PM - 10:00 PM):**
- [Les Ombres](https://zomato.com/lesombres)  – Dinner recommendation (₹5000)
- [Night Tour of Paris](https://klook.com/night-paris-tour)  – ₹3000

[Continue this pattern for all days...]

## 💵 BUDGET BREAKDOWN
- ✈️ Flights: 30% of budget (Delhi-{trip_data['destination']})
- 🏨 Hotels: 25% of budget ({duration-1} nights)
- 🍽️ Food: 20% of budget ({duration} days)
- 🎡 Activities: 15% of budget
- 🚖 Local Transport: 10% of budget
- 🧳 Emergency Fund: 5%

## 🔗 BOOKING PLATFORMS
- ✈️ Flights: [MakeMyTrip](https://makemytrip.com),  [Cleartrip](https://cleartrip.com),  [Skyscanner](https://skyscanner.com) 
- 🏨 Hotels: [Booking.com](https://booking.com),  [Airbnb](https://airbnb.com),  [Hostelworld](https://hostelworld.com) 
- 🎡 Activities: [Klook](https://klook.com),  [GetYourGuide](https://getyourguide.com) 
- 🍽️ Restaurants: [Zomato](https://zomato.com),  [TripAdvisor](https://tripadvisor.com) 
- 🗺️ Navigation: [Google Maps](https://maps.google.com),  [Citymapper](https://citymapper.com) 

Would you like to refine any aspect of this itinerary?"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"You are TRIVANZA, a detailed travel planner. You must create comprehensive itineraries that include realistic flight schedules, airport transfers, and travel logistics for {trip_data['transport']} travel from {trip_data['origin']} to {trip_data['destination']}. Always account for flight times, jet lag, and departure logistics."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=3500   # Increased for flight details
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
        # Handle regular chat queries
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
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png"   if msg["role"] == "assistant" else None
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
            traveler_type = st.selectbox("🧍 Traveler Type", 
                                      ["Solo", "Couple", "Family", "Group"], key="traveler_type")
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
        
        budget = st.text_input("💰 Budget (e.g., ₹50000 INR or $800 USD)", key="budget_input")
        activities = st.text_area("🎯 Activities", placeholder="e.g., beaches, hiking, shopping", key="activities_input")
        
        # Submit Button
        submit = st.form_submit_button("🚀 Generate My Itinerary", use_container_width=True)
        
        if submit:
            # Validation
            if not origin.strip():
                st.error("❌ Please enter your origin city!")
            elif not destination.strip():
                st.error("❌ Please enter your destination!")
            elif to_date < from_date:
                st.error("❌ End date must be after start date!")
            else:
                # Show immediate feedback
                st.success("✅ Creating your personalized itinerary...")
                # Mark form as submitted to prevent re-rendering
                st.session_state.form_submitted = True
                st.session_state.show_form = False
                st.session_state.generating_itinerary = True
                
                # Save trip context with all preferences
                trip_data = {
                    "origin": origin.strip(),
                    "destination": destination.strip(),
                    "from_date": from_date,
                    "to_date": to_date,
                    "transport": transport,
                    "stay": stay,
                    "budget": budget.strip(),
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
                    "custom_activities": custom_activities
                }
                
                st.session_state.trip_context = trip_data
                
                # Generate itinerary
                with st.spinner("🎯 Crafting your detailed multi-day itinerary... This may take a moment."):
                    itinerary = generate_itinerary(trip_data)
                    st.session_state.messages.append({"role": "assistant", "content": itinerary})
                    st.session_state.generating_itinerary = False
                
                # Force refresh to show the new message
                st.rerun()

# Handle ongoing itinerary generation
if st.session_state.generating_itinerary:
    with st.spinner("🎯 Still working on your itinerary..."):
        pass
