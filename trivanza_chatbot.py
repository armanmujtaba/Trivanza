# ----------------- IMPORTS -----------------
import streamlit as st
from openai import OpenAI
from datetime import date, timedelta
import re

# ----------------- CONFIG -----------------
st.set_page_config(page_title="TRIVANZA", page_icon="✈️", layout="centered")

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

# ----------------- HELPER FUNCTION -----------------
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

def calculate_budget(budget_amount, currency, duration, trip_data):
    """Calculate realistic budget allocation"""
    try:
        base = int(budget_amount)
    except:
        base = 50000  # Fallback
    
    breakdown = {
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
    
    if trip_data.get("budget_type") == "Budget":
        breakdown = {k: int(v * 0.7) for k, v in breakdown.items()}
    elif trip_data.get("budget_type") == "Luxury":
        breakdown = {k: int(v * 1.5) for k, v in breakdown.items()}
    
    return breakdown

# ----------------- CHAT INPUT HANDLER -----------------
user_input = st.chat_input("Say Hi to Trivanza or ask your travel-related question...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    if user_input.strip().lower() in ["hi", "hello", "hey"] and not st.session_state.form_submitted:
        st.session_state.show_form = True
        st.session_state.form_submitted = False
        st.session_state.messages.append({
            "role": "assistant",
            "content": "👋 **Hello Traveller! Welcome to Trivanza – Your Smart Travel Buddy**\nTo help you better, please fill out your travel details below."
        })
    elif "trip_context" in st.session_state and user_input.strip().lower() not in ["hi", "hello", "hey"]:
        # Handle travel questions directly
        context = st.session_state.trip_context
        prompt = f"""You are TRIVANZA – a travel-specialized AI assistant.\nCONTEXT:\n- Origin: {context.get('origin', 'Delhi')}\n- Destination: {context.get('destination', 'Paris')}\n- Dates: {context.get('from_date', date.today()).strftime('%B %d')} - {context.get('to_date', date.today()).strftime('%B %d, %Y')}\n- Budget: {context.get('currency', '₹')}{context.get('budget_amount', '50000')} ({context.get('budget_type', 'Mid-Budget')})\n- Traveler Type: {context.get('traveler_type', 'Couple')}\n- Group Size: {context.get('group_size', '2 people')}\n- Interests: {', '.join(context.get('custom_activities', ['None']))}\n- Dietary: {', '.join(context.get('dietary_pref', ['Standard']) or ['None'])}\n- Sustainability: {context.get('sustainability', 'None')}\n\nAnswer the following question: {user_input}"""
        
        with st.spinner("✈️ Planning your response..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": prompt}],
                    temperature=0.3,
                    max_tokens=1000
                )
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response.choices[0].message.content
                })
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"⚠️ Error: {str(e)}"
                })
    else:
        st.session_state.show_form = True

# ----------------- DISPLAY CHAT HISTORY -----------------
for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png"  if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ----------------- TRAVEL FORM -----------------
if st.session_state.show_form and not st.session_state.form_submitted:
    with st.form("travel_form", clear_on_submit=False):
        st.markdown("### 🧳 Let's plan your perfect trip!")
        
        # Basic Info
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
        group_size = st.number_input("👥 Group Size", min_value=1, value=2, key="group_size")
        
        # Preferences
        st.markdown("#### 🎯 Travel Preferences")
        col5, col6 = st.columns(2)
        with col5:
            dietary_pref = st.multiselect("🥗 Dietary Preferences", ["Vegetarian", "Vegan", "Gluten-Free", "Halal", "Kosher", "Nut Allergy"], key="dietary_pref")
            sustainability = st.selectbox("🌱 Sustainability", ["None", "Eco-Friendly Stays", "Carbon Offset Flights", "Zero-Waste Activities"], key="sustainability")
        with col6:
            language_pref = st.selectbox("🌐 Language", ["English", "Hindi", "French", "Spanish", "Mandarin", "Local Phrases"], key="language_pref")
            cultural_pref = st.selectbox("👗 Cultural Sensitivity", ["Standard", "Conservative Dress", "Religious Holidays", "Gender Norms"], key="cultural_pref")
        
        # Budget & Stay
        st.markdown("#### 💰 Budget & Currency")
        col7, col8 = st.columns(2)
        with col7:
            budget_amount = st.number_input("💰 Budget Amount", min_value=1000, step=1000, key="budget_amount")
        with col8:
            currency_type = st.selectbox("💱 Currency", ["₹ INR", "$ USD", "€ EUR", "£ GBP", "¥ JPY"], key="currency_type")
        budget_type = st.selectbox("Select Budget Type", ["Luxury", "Mid-Budget", "Budget"], key="budget_type")
        
        # Advanced Options
        st.markdown("#### 🧳 Advanced Preferences")
        col9, col10 = st.columns(2)
        with col9:
            accessibility = st.checkbox("♿ Accessibility Required", key="accessibility")
            transport_pref = st.multiselect("🚇 Local Transport", ["Public Transit", "Taxi", "Uber", "Car Rental", "Walking"], default=["Public Transit"], key="transport_pref")
        with col10:
            payment_methods = st.multiselect("💳 Payment Methods", ["Credit Card", "Debit Card", "Cash", "Mobile Payment", "Local Bank Transfer"], default=["Credit Card"], key="payment_methods")
            packing_style = st.selectbox("🧳 Packing Style", ["Light Pack", "Full Suitcase", "Backpacking", "Luxury Travel"], key="packing_style")
        
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
                
                # Save trip context
                trip_data = {
                    "origin": origin.strip(),
                    "destination": destination.strip(),
                    "from_date": from_date,
                    "to_date": to_date,
                    "group_size": str(group_size),
                    "budget_amount": str(budget_amount),
                    "currency_type": currency_type,
                    "currency": currency_type.split()[0],
                    "budget_type": budget_type,
                    "dietary_pref": dietary_pref,
                    "language_pref": language_pref,
                    "cultural_pref": cultural_pref,
                    "sustainability": sustainability,
                    "transport_pref": transport_pref,
                    "payment_methods": payment_methods,
                    "packing_style": packing_style,
                    "accessibility": accessibility
                }
                
                st.session_state.trip_context = trip_data
                st.rerun()

# ----------------- ITINERARY GENERATOR -----------------
if st.session_state.generating_itinerary:
    with st.spinner("🎯 Generating your realistic itinerary..."):
        trip_data = st.session_state.trip_context
        start_date = trip_data["from_date"]
        end_date = trip_data["to_date"]
        duration = (end_date - start_date).days + 1
        all_dates = [start_date + timedelta(days=i) for i in range(duration)]
        
        # Calculate realistic budget breakdown
        breakdown = calculate_budget(
            int(trip_data["budget_amount"]), 
            trip_data["currency"], 
            duration, 
            trip_data
        )
        
        # Build enhanced prompt
        prompt = f"""You are TRIVANZA, a professional travel concierge AI.
MANDATORY REQUIREMENTS:
1. STRICT FORMAT:
   - Use markdown links: [Text](URL)
   - Include all dates from {start_date.strftime('%B %d')} to {end_date.strftime('%B %d, %Y')}
   - Show realistic prices in {trip_data['currency']} that match the user's budget
   - Adjust activities for jet lag on Day 1 and airport logistics on Departure Day

2. BUDGET REALISM:
   - Total: {trip_data['currency']}{breakdown['flights'] + breakdown['hotels'] + breakdown['food'] + breakdown['activities'] + breakdown['transport'] + breakdown['emergency']}
   - Flights: {trip_data['currency']}{breakdown['flights']} (30%)
   - Hotels: {trip_data['currency']}{breakdown['hotels']} (25%)
   - Food: {trip_data['currency']}{breakdown['food']} (20%)
   - Activities: {trip_data['currency']}{breakdown['activities']} (15%)

3. LINK REQUIREMENTS:
   - Flights: [MakeMyTrip](https://makemytrip.com),  [Skyscanner](https://skyscanner.com) 
   - Hotels: [Booking.com](https://booking.com),  [Airbnb](https://airbnb.com) 
   - Restaurants: [Zomato](https://zomato.com),  [Google Maps](https://maps.google.com) 
   - Activities: [Klook](https://klook.com),  [GetYourGuide](https://getyourguide.com) 

TRIP DETAILS:
- Origin: {trip_data['origin']}
- Destination: {trip_data['destination']}
- Duration: {duration} days
- Dates: {', '.join(date.strftime('%A, %B %d') for date in all_dates)}
- Budget: {trip_data['currency']}{trip_data['budget_amount']} ({trip_data['budget_type']})
- Group Size: {trip_data['group_size']} {f'(with {", ".join(trip_data["dietary_pref"])})' if trip_data["dietary_pref"] else ''}
- Interests: {', '.join(trip_data.get('custom_activities', ['None'])}
- Cultural Sensitivity: {trip_data['cultural_pref']}
- Accessibility: {"Yes" if trip_data['accessibility'] else "No"}
- Local Transport: {', '.join(trip_data['transport_pref'])}
- Payment Methods: {', '.join(trip_data['payment_methods'])}

CRITICAL:
- Never skip days
- Adjust activity timing for jet lag
- Show total cost per day
- Include realistic activity times
- Always use markdown links

# 🌍 {duration}-Day {trip_data['destination']} Adventure – {trip_data['budget_type']}
**Travel Period:** {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}
**Time Zone Difference:** {"-4.5 hours" if "europe" in trip_data['destination'].lower() else "-10 hours"}
**Currency:** {trip_data['currency']}{trip_data['budget_amount']}

## ✈️ FLIGHT DETAILS
**Outbound Journey**
- Departure: 9:00 PM from {trip_data['origin']}
- Flight Duration: {trip_data['origin']}-{trip_data['destination']}: 8h45m
- Arrival: Next day 6:00 AM local time
- Airport Transfer: 1.5-hour taxi to hotel ({trip_data['currency']}3,000)
- Hotel Check-in: 12:00 PM (store luggage if early)

## 🏨 ACCOMMODATION
### {trip_data['budget_type']} Option
- [{trip_data['stay']} in {trip_data['destination']}]({get_search_url('booking', trip_data['destination'], trip_data['stay'])})  
  - Price: {trip_data['currency']}{breakdown['daily_hotel']}/night  
  - Amenities: ✓ Rooftop view ✓ Free WiFi ✓ Breakfast

## 🗓️ DAY-BY-DAY ITINERARY

## Day 1 - {all_dates[0].strftime('%A, %B %d')} (Arrival Day)
**Flight Logistics**
- 6:00 PM: Depart for airport
- 9:00 PM: International flight to {trip_data['destination']}
- Arrival: Next day 6:00 AM local time
- Airport Transfer: 1.5-hour taxi to hotel

**Afternoon (Post-transfer):**
- [{trip_data['stay']} in {trip_data['destination']}]({get_search_url('booking', trip_data['destination'], trip_data['stay'])}) check-in
- [Local Cuisine Dinner]({get_search_url('zomato', trip_data['destination'], 'local cuisine')}) – {trip_data['currency']}{breakdown['daily_food']}
- [Nearby Attraction]({get_search_url('getyourguide', trip_data['destination'], 'light activity')}) – {trip_data['currency']}{breakdown['daily_activities']}

## Day 2 - {all_dates[1].strftime('%A, %B %d')}
**Morning (8:00 AM - 12:00 PM):**
- [Major Attraction]({get_search_url('klook', trip_data['destination'], 'major attraction')}) – {trip_data['currency']}{breakdown['daily_activities']}
- [Museum]({get_search_url('getyourguide', trip_data['destination'], 'museum')}) – {trip_data['currency']}{breakdown['daily_activities']}

**Afternoon (12:00 PM - 6:00 PM):**  
- [Iconic Restaurant]({get_search_url('zomato', trip_data['destination'], 'iconic restaurant')}) – {trip_data['currency']}{breakdown['daily_food']}
- [Cultural Activity]({get_search_url('getyourguide', trip_data['destination'], 'cultural activity')}) – {trip_data['currency']}{breakdown['daily_activities']}

## Day 3 - {all_dates[2].strftime('%A, %B %d')}
**Morning (8:00 AM - 12:00 PM):**
- [Historical Site]({get_search_url('klook', trip_data['destination'], 'historical site')}) – {trip_data['currency']}{breakdown['daily_activities']}
- [Local Market]({get_search_url('getyourguide', trip_data['destination'], 'local market')}) – {trip_data['currency']}{breakdown['daily_activities']}

**Afternoon (12:00 PM - 6:00 PM):**  
- [Local Restaurant]({get_search_url('zomato', trip_data['destination'], 'local restaurant')}) – {trip_data['currency']}{breakdown['daily_food']}
- [City Tour]({get_search_url('getyourguide', trip_data['destination'], 'city tour')}) – {trip_data['currency']}{breakdown['daily_activities']}

## Day {duration} - {all_dates[-1].strftime('%A, %B %d')} (Departure Day)
**Morning (8:00 AM - 12:00 PM):**
- 8:00 AM: Hotel checkout and luggage storage
- [Nearby Attraction]({get_search_url('getyourguide', trip_data['destination'], 'airport nearby activity')}) – {trip_data['currency']}{breakdown['daily_activities']}
- [Airport Breakfast]({get_search_url('zomato', trip_data['destination'], 'airport breakfast')}) – {trip_data['currency']}{breakdown['daily_food']}

**Afternoon:**
- 2:00 PM: Depart for {trip_data['destination']} Airport  
- 3:00 PM: Arrive at airport for international departure
- 6:00 PM: Flight departure to {trip_data['origin']} ({trip_data['currency']}{breakdown['flights']//2} per person)
- Arrival: Next day 6:00 AM IST in {trip_data['origin']}

## 💵 BUDGET BREAKDOWN
- ✈️ Flights: {trip_data['currency']}{breakdown['flights']} (30% of total)
- 🏨 Hotels: {trip_data['currency']}{breakdown['hotels']} (25% of total)
- 🍽️ Food: {trip_data['currency']}{breakdown['food']} (20% of total)
- 🎡 Activities: {trip_data['currency']}{breakdown['activities']} (15% of total)
- 🚖 Local Transport: {trip_data['currency']}{breakdown['transport']} (10% of total)
- 🧳 Emergency Fund: {trip_data['currency']}{breakdown['emergency']} (5% of total)
- 💰 **Total:** {trip_data['currency']}{sum(breakdown.values())}

## 🔗 BOOKING PLATFORMS
- ✈️ Flights: [MakeMyTrip](https://makemytrip.com),  [Skyscanner](https://skyscanner.com) 
- 🏨 Hotels: [Booking.com](https://booking.com),  [Airbnb](https://airbnb.com) 
- 🎡 Activities: [Klook](https://klook.com),  [GetYourGuide](https://getyourguide.com) 
- 🍽️ Restaurants: [Zomato](https://zomato.com),  [Google Maps](https://maps.google.com) 
- 🗺️ Navigation: [Citymapper](https://citymapper.com) 

Would you like to refine any aspect of this itinerary?"""

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are TRIVANZA, a travel planning AI. Always return clickable links in [Text](URL) format. Use the user's budget type to suggest realistic prices. Never skip days. Adjust activity timing for jet lag. Prioritize user interests in activity suggestions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                presence_penalty=0.2,
                frequency_penalty=0.2
            )
            itinerary = response.choices[0].message.content
            
            # Add to chat history
            st.session_state.messages.append({"role": "assistant", "content": itinerary})
            st.session_state.generating_itinerary = False
            st.rerun()
        except Exception as e:
            st.session_state.messages.append({
                "role": "assistant", 
                "content": f"❌ Error: {str(e)}"
            })
            st.session_state.generating_itinerary = False
            st.rerun()
