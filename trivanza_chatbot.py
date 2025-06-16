# ----------------- IMPORTS -----------------
import streamlit as st
from openai import OpenAI
from datetime import date, timedelta
import re

# ----------------- CONFIG -----------------
st.set_page_config(page_title="TRIVANZA", page_icon="✈️", layout="wide")

# ----------------- INIT CLIENT -----------------
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

# ----------------- HELPER FUNCTIONS -----------------
def get_search_url(platform, destination, query):
    """Generate working search URLs"""
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

def calculate_budget(budget_amount, currency, duration):
    """Calculate daily/total expenses"""
    try:
        base = int(budget_amount)
    except:
        base = 50000  # Fallback
    
    return {
        "flights": int(base * 0.3),
        "hotels": int(base * 0.25),
        "food": int(base * 0.2),
        "activities": int(base * 0.15),
        "transport": int(base * 0.1),
        "emergency": int(base * 0.05),
        "daily_hotel": int(base * 0.25 / duration),
        "daily_food": int(base * 0.2 / duration),
        "daily_activities": int(base * 0.15 / duration)
    }

# ----------------- CHAT INPUT HANDLER -----------------
user_input = st.chat_input("Say Hi to Trivanza or ask your travel-related question...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    if user_input.strip().lower() in ["hi", "hello", "hey"] and not st.session_state.form_submitted:
        st.session_state.show_form = True
        st.session_state.messages.append({
            "role": "assistant",
            "content": """👋 **Welcome to Trivanza: Your Smart Travel Companion**  
I'm excited to help you with your travel plans. To provide you with the best possible assistance, could you please share some details with me?

- What is your origin (starting location)?  
- What is your destination (where are you headed)?  
- What are your travel dates (from and to)?  
- What is your preferred mode of transport (flight, train, car, etc.)?  
- What are your accommodation preferences (hotel, hostel, etc.)?  
- What are your budget and currency type (INR, Dollar, Pound, etc.)?  
- Are there any specific activities or experiences you're looking to have during your trip?"""
        })
    elif "trip_context" in st.session_state and user_input.strip().lower() not in ["hi", "hello", "hey"]:
        # Handle regular travel questions
        try:
            messages = [{"role": "system", "content": f"""
You are TRIVANZA – a travel-specialized AI assistant.
CONTEXT:
Origin: {st.session_state.trip_context.get('origin', 'Not provided')}
Destination: {st.session_state.trip_context.get('destination', 'Not provided')}
Travel Duration: {st.session_state.trip_context.get('from_date', '')} to {st.session_state.trip_context.get('to_date', '')}
Transport: {st.session_state.trip_context.get('transport', '')}
Stay: {st.session_state.trip_context.get('stay', '')}
Budget: {st.session_state.trip_context.get('budget_amount', '')} {st.session_state.trip_context.get('currency_type', '')}
Answer ONLY travel-related questions using this context.
            """}]
            messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]
            
            with st.spinner("✈️ Planning your response..."):
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=1000
                )
                bot_reply = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ Error: {str(e)}"})
    else:
        # Generate itinerary
        with st.spinner("🎯 Generating your itinerary..."):
            st.session_state.show_form = False
            st.session_state.generating_itinerary = True
            st.rerun()

# ----------------- DISPLAY CHAT HISTORY -----------------
for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png"  if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ----------------- TRAVEL FORM -----------------
if st.session_state.show_form and not st.session_state.form_submitted:
    with st.form("travel_form", clear_on_submit=False):
        st.markdown("### 🧳 Let's plan your perfect trip!")
        
        # Traveler Details
        st.markdown("#### 🧑‍🤝‍🧑 Traveler Details")
        col1, col2 = st.columns(2)
        with col1:
            traveler_type = st.selectbox("🧍 Traveler Type", ["Solo", "Couple", "Family", "Group"], key="traveler_type")
        with col2:
            group_size = st.number_input("👥 Group Size", min_value=1, value=2, key="group_size")
        
        # Destination & Dates
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
        
        # Preferences
        st.markdown("#### 🎯 Travel Preferences")
        col7, col8 = st.columns(2)
        with col7:
            dietary_pref = st.multiselect("🥗 Dietary Preferences", ["Vegetarian", "Vegan", "Gluten-Free", "Halal", "Kosher"], key="dietary_pref")
            sustainability = st.selectbox("🌱 Sustainability", ["None", "Eco-Friendly Stays", "Carbon Offset Flights", "Zero-Waste Activities"], key="sustainability")
        with col8:
            language_pref = st.selectbox("🌐 Language", ["English", "Hindi", "French", "Spanish", "Mandarin", "Local Phrases"], key="language_pref")
            cultural_pref = st.selectbox("👗 Cultural Sensitivity", ["Standard", "Conservative Dress", "Religious Holidays", "Gender Norms"], key="cultural_pref")
        
        # Budget & Stay
        st.markdown("#### 💰 Budget & Stay")
        col9, col10 = st.columns(2)
        with col9:
            budget_amount = st.number_input("💰 Budget Amount", min_value=1000, step=1000, key="budget_amount")
        with col10:
            currency_type = st.selectbox("💱 Currency", ["₹ INR", "$ USD", "€ EUR", "£ GBP", "¥ JPY"], key="currency_type")
        stay = st.selectbox("🏨 Accommodation", ["Hotel", "Hostel", "Airbnb", "Resort"], key="stay_input")
        
        # Interests
        st.markdown("#### 🎨 Custom Interests")
        custom_activities = st.multiselect("🎯 Interests", [
            "Beaches", "Hiking", "Shopping", "Nightlife", 
            "Cultural Immersion", "Foodie Tour", "Adventure Sports"
        ], key="custom_activities")
        
        # Submit
        submit = st.form_submit_button("🚀 Generate My Itinerary", use_container_width=True)
        
        if submit:
            # Validation
            if not origin.strip():
                st.error("❌ Please enter your origin city!")
            elif not destination.strip():
                st.error("❌ Please enter your destination!")
            elif to_date < from_date:
                st.error("❌ End date must be after start date!")
            elif budget_amount <= 0:
                st.error("❌ Budget must be greater than 0")
            else:
                # Show immediate feedback
                st.success("✅ Creating your personalized itinerary...")
                
                # Save trip context
                trip_data = {
                    "origin": origin.strip(),
                    "destination": destination.strip(),
                    "from_date": from_date,
                    "to_date": to_date,
                    "traveler_type": traveler_type,
                    "group_size": str(group_size),
                    "dietary_pref": dietary_pref,
                    "language_pref": language_pref,
                    "sustainability": sustainability,
                    "cultural_pref": cultural_pref,
                    "custom_activities": custom_activities,
                    "budget_amount": str(budget_amount),
                    "currency_type": currency_type,
                    "currency": currency_type.split()[0],
                    "stay": stay
                }
                
                st.session_state.trip_context = trip_data
                st.session_state.form_submitted = True
                st.session_state.show_form = False
                st.session_state.generating_itinerary = True
                st.rerun()

# ----------------- ITINERARY GENERATOR -----------------
if st.session_state.generating_itinerary:
    with st.spinner("🎯 Generating your itinerary..."):
        trip_data = st.session_state.trip_context
        start_date = trip_data["from_date"]
        end_date = trip_data["to_date"]
        duration = (end_date - start_date).days + 1
        all_dates = [start_date + timedelta(days=i) for i in range(duration)]
        
        # Calculate budget
        budget_amount = int(trip_data["budget_amount"])
        currency = trip_data["currency"]
        budget_breakdown = calculate_budget(budget_amount, currency, duration)
        
        # Build itinerary prompt
        prompt = f"""You are TRIVANZA, a professional travel planning assistant. Create a COMPLETE {duration}-day itinerary with:
        
MANDATORY REQUIREMENTS:
1. STRICT FORMAT: 
   - Title: "{duration}-Day {{destination}} Adventure – {{budget_type}}"
   - Daily breakdown: Day 1 to Day {duration}, each with:
     - Morning (8:00 AM - 12:00 PM)
     - Afternoon (12:00 PM - 6:00 PM)
     - Evening (6:00 PM - 10:00 PM)
     - Costs in {currency}{budget_amount} format
     - Functional links in [Text](URL) format

2. BUDGET BREAKDOWN:
   - Flights: {budget_breakdown['flights']} {currency}
   - Hotels: {budget_breakdown['hotels']} {currency}
   - Food: {budget_breakdown['food']} {currency}
   - Activities: {budget_breakdown['activities']} {currency}
   - Transport: {budget_breakdown['transport']} {currency}
   - Emergency Fund: {budget_breakdown['emergency']} {currency}

3. FUNCTIONAL LINKS:
   - Flights: [MakeMyTrip](https://makemytrip.com),  [Skyscanner](https://skyscanner.com) 
   - Hotels: [Booking.com](https://booking.com),  [Airbnb](https://airbnb.com) 
   - Restaurants: [Zomato](https://zomato.com),  [Google Maps](https://maps.google.com) 
   - Activities: [Klook](https://klook.com),  [GetYourGuide](https://getyourguide.com) 

TRIP DETAILS:
- Origin: {trip_data['origin']}
- Destination: {trip_data['destination']}
- Dates: {', '.join(date.strftime('%B %d') for date in all_dates)}
- Budget: {currency}{budget_amount} ({trip_data['stay']})
- Interests: {', '.join(trip_data['custom_activities'])}
- Group Size: {trip_data['group_size']}
- Dietary Preferences: {', '.join(trip_data['dietary_pref'] or ['None'])}

EXACT OUTPUT FORMAT REQUIRED:
# 🌍 {duration}-Day {trip_data['destination']} Adventure – Mid-Budget
**Travel Period:** {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}
**Time Zone Difference:** {"-4.5 hours" if "europe" in trip_data['destination'].lower() else "-10 hours"}
**Currency:** {currency}{budget_amount}

## ✈️ FLIGHT DETAILS
**Outbound Journey**
- Departure: 9:00 PM from Delhi
- Flight Duration: Delhi-{trip_data['destination']}: 8h45m
- Arrival: Next day 6:00 AM local time
- Airport Transfer: 1.5-hour taxi to hotel ({currency}3,000)

**Return Journey**
- Departure: 3:00 PM from {trip_data['destination']} Airport
- Arrival: 6:00 AM IST in Delhi next day

## 🏨 ACCOMMODATION
### {trip_data['stay']} Option
- [{trip_data['stay']} in {trip_data['destination']}]({get_search_url('booking', trip_data['destination'], trip_data['stay'])})  
  - Price: {currency}{budget_breakdown['daily_hotel']}/night  
  - Amenities: ✓ Rooftop view ✓ Free WiFi ✓ Breakfast

## 🗓️ DAY-BY-DAY ITINERARY

## Day 1 - {all_dates[0].strftime('%A, %B %d')} (Arrival Day)
**Flight Logistics**
- 6:00 PM: Depart for Delhi Airport
- 9:00 PM: Flight to {trip_data['destination']}
- Arrival: Next day 6:00 AM local time

**Afternoon (Post-transfer):**
- [Hotel Name]({get_search_url('booking', trip_data['destination'], trip_data['stay'])}) check-in and rest
- [Local Cuisine Dinner]({get_search_url('zomato', trip_data['destination'], 'local cuisine')}) – {currency}{budget_breakdown['daily_food']}
- [Nearby attraction]({get_search_url('getyourguide', trip_data['destination'], 'light evening activity')}) – Light evening activity

## Day 2 - {all_dates[1].strftime('%A, %B %d')}
**Morning (8:00 AM - 12:00 PM):**
- [Major Attraction]({get_search_url('klook', trip_data['destination'], 'major attraction')}) – {currency}{budget_breakdown['daily_activities']}
- [Local Tour]({get_search_url('getyourguide', trip_data['destination'], 'local tour')}) – {currency}{budget_breakdown['daily_activities']}

**Afternoon (12:00 PM - 6:00 PM):**
- [Iconic Restaurant]({get_search_url('zomato', trip_data['destination'], 'iconic restaurant')}) – {currency}{budget_breakdown['daily_food']}
- [Cultural Experience]({get_search_url('getyourguide', trip_data['destination'], 'cultural experience')}) – {currency}{budget_breakdown['daily_activities']}

**Evening (6:00 PM - 10:00 PM):**
- [Night Activity]({get_search_url('klook', trip_data['destination'], 'night activity')}) – {currency}{budget_breakdown['daily_activities']}
- [Local Bar/Nightspot]({get_search_url('zomato', trip_data['destination'], 'bar nightspot')}) – {currency}{budget_breakdown['daily_food']}

## Day 3 - {all_dates[2].strftime('%A, %B %d')}
**Morning (8:00 AM - 12:00 PM):**
- [Historical Site]({get_search_url('klook', trip_data['destination'], 'historical site')}) – {currency}{budget_breakdown['daily_activities']}
- [Local Market]({get_search_url('getyourguide', trip_data['destination'], 'local market')}) – {currency}{budget_breakdown['daily_activities']}

**Afternoon (12:00 PM - 6:00 PM):**
- [Local Restaurant]({get_search_url('zomato', trip_data['destination'], 'local restaurant')}) – {currency}{budget_breakdown['daily_food']}
- [Cultural Activity]({get_search_url('getyourguide', trip_data['destination'], 'cultural activity')}) – {currency}{budget_breakdown['daily_activities']}

**Evening (6:00 PM - 10:00 PM):**
- [Evening Show]({get_search_url('getyourguide', trip_data['destination'], 'evening show')}) – {currency}{budget_breakdown['daily_activities']}
- [Casual Dinner]({get_search_url('zomato', trip_data['destination'], 'casual dinner')}) – {currency}{budget_breakdown['daily_food']}

## Day {duration} - {all_dates[-1].strftime('%A, %B %d')} (Departure Day)
**Morning (8:00 AM - 12:00 PM):**
- 8:00 AM: Hotel checkout and luggage storage
- [Nearby attraction]({get_search_url('getyourguide', trip_data['destination'], 'airport nearby activity')}) – Light morning activity
- [Quick bite location]({get_search_url('zomato', trip_data['destination'], 'airport breakfast')}) – Breakfast recommendation

**Afternoon:**
- 2:00 PM: Depart for {trip_data['destination']} Airport  
- 3:00 PM: Arrive at airport for international departure
- 6:00 PM: Flight departure to Delhi ({currency}{budget_breakdown['flights']//2} per person)

## 💵 BUDGET BREAKDOWN
- ✈️ Flights: {currency}{budget_breakdown['flights']} (30% of total)
- 🏨 Hotels: {currency}{budget_breakdown['hotels']} (25% of total)
- 🍽️ Food: {currency}{budget_breakdown['food']} (20% of total)
- 🎡 Activities: {currency}{budget_breakdown['activities']} (15% of total)
- 🚖 Local Transport: {currency}{budget_breakdown['transport']} (10% of total)
- 🧳 Emergency Fund: {currency}{budget_breakdown['emergency']} (5% of total)
- 💰 **Total:** {currency}{budget_amount}

## 🔗 BOOKING PLATFORMS
- ✈️ Flights: [MakeMyTrip](https://makemytrip.com),  [Skyscanner](https://skyscanner.com) 
- 🏨 Hotels: [Booking.com](https://booking.com),  [Airbnb](https://airbnb.com) 
- 🎡 Activities: [Klook](https://klook.com),  [GetYourGuide](https://getyourguide.com) 
- 🍽️ Restaurants: [Zomato](https://zomato.com),  [Google Maps](https://maps.google.com) 

Would you like to refine any aspect of this itinerary?"""

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are TRIVANZA, a detailed travel planner. Always return clickable links in [Text](URL) format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                presence_penalty=0.2,
                frequency_penalty=0.2
            )
            itinerary = response.choices[0].message.content
            
            # Save and display
            st.session_state.messages.append({"role": "assistant", "content": itinerary})
            st.session_state.generating_itinerary = False
            st.rerun()
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})
            st.session_state.generating_itinerary = False
            st.rerun()
