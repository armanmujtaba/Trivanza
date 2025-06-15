import streamlit as st
from openai import OpenAI
from datetime import date, timedelta

# ----------------- CONFIG -----------------
st.set_page_config(page_title="TRIVANZA – Your Smart Travel Buddy", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ----------------- CUSTOM HEADER -----------------
st.markdown("""
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
    <img src="https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" width="45px">
    <h2 style="margin: 0;">TRIVANZA – Your Smart Travel Buddy</h2>
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
    """Generate itinerary using OpenAI API"""
    
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
    
    dates_list = "\n".join([f"Day {i+1}: {date}" for i, date in enumerate(all_dates)])
    
    prompt = f"""You are TRIVANZA, a professional travel planning assistant. 

MANDATORY REQUIREMENTS:
1. Create a COMPLETE {duration}-day itinerary INCLUDING flight schedules and travel logistics
2. Account for flight departure/arrival times and jet lag
3. Include realistic travel times between airports and hotels
4. Adjust activities based on actual arrival/departure times
5. Include specific prices in INR for all items

TRIP DETAILS:
- Origin: {trip_data['origin']}
- Destination: {trip_data['destination']}
- Transport Mode: {trip_data['transport']}
- Duration: {duration} days
- Dates: {dates_list}
- Budget: {trip_data['budget']}
- Accommodation: {trip_data['stay']}
- Interests: {trip_data['activities']}

CRITICAL FLIGHT INFORMATION TO INCLUDE:
- For international flights from India: Include realistic departure times (usually evening/night)
- Include flight duration and arrival times (accounting for time zones)
- Include airport transfer times (1-2 hours each way)
- For return flights: Include departure times and travel to airport
- Account for check-in times (3 hours for international flights)

EXACT OUTPUT FORMAT REQUIRED:

# {duration}-Day {trip_data['destination']} Adventure
**Travel Period:** {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}

## OUTBOUND FLIGHT DETAILS
**{all_dates[0]} - Departure Day**
- **6:00 PM:** Depart for Indira Gandhi International Airport, Delhi
- **9:00 PM:** Flight departure to {trip_data['destination']} (₹X,XXX per person)
- **Flight Duration:** X hours XX minutes
- **Arrival:** Next day X:XX AM local time
- **Airport Transfer:** X:XX AM - Taxi/Uber to hotel (₹X,XXX)
- **Hotel Check-in:** X:XX AM (if available) or luggage storage

---

## Day 1 - {all_dates[0]} (Arrival Day)
**Late Morning/Afternoon (11:00 AM onwards):**
- [Light activities accounting for jet lag and late arrival]
- [Include hotel check-in process]

**Evening:**
- [Easy dinner and rest activities]

---

## Day 2 - {all_dates[1] if len(all_dates) > 1 else "N/A"}
**Morning (8:00 AM - 12:00 PM):**
- [Full day activities now that settled in]

**Afternoon (12:00 PM - 6:00 PM):**  
- [Activities with prices and booking links]

**Evening (6:00 PM - 10:00 PM):**
- [Evening activities with prices]

---

[Continue this pattern for middle days...]

---

## Day {duration} - {all_dates[-1]} (Departure Day)
**Morning (8:00 AM - 12:00 PM):**
- **8:00 AM:** Hotel checkout and luggage storage/taxi
- [Light morning activities near hotel/airport area]

**Afternoon:**
- **2:00 PM:** Depart for {trip_data['destination']} Airport  
- **3:00 PM:** Arrive at airport for international departure
- **6:00 PM:** Flight departure to Delhi (₹X,XXX per person)
- **Flight Duration:** X hours XX minutes
- **Next day arrival:** X:XX AM IST in Delhi

## RETURN FLIGHT DETAILS
**{(end_date + timedelta(days=1)).strftime('%B %d, %Y')} - Arrival in Delhi**
- **Arrival:** X:XX AM at IGI Airport, Delhi
- **Airport transfer home:** ₹X,XXX

## Budget Summary
- **Round-trip Flights:** ₹X,XXX (Delhi-{trip_data['destination']}-Delhi)
- **Airport Transfers:** ₹X,XXX
- **Hotels ({duration-1} nights):** ₹X,XXX  
- **Food ({duration} days):** ₹X,XXX
- **Activities:** ₹X,XXX
- **Local Transport:** ₹X,XXX
- **TOTAL:** ₹X,XXX

## Booking Platforms
- **Flights:** MakeMyTrip, Cleartrip, Skyscanner
- **Hotels:** Booking.com, Airbnb
- **Activities:** Klook, GetYourGuide

CRITICAL: 
- Include realistic flight times for {trip_data['origin']} to {trip_data['destination']} route
- Account for time zone differences
- Adjust Day 1 activities for late arrival and jet lag
- Adjust final day activities for departure logistics
- Include all airport transfers and check-in times

Would you like to make any changes to this itinerary?"""

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
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
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

                # Save trip context
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
