import streamlit as st
from openai import OpenAI
from datetime import date

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

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "trip_context" not in st.session_state:
    st.session_state.trip_context = {}

# ----------------- CHAT INPUT HANDLER -----------------
user_input = st.chat_input("Say Hi to Trivanza or ask your travel-related question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if user_input.strip().lower() in ["hi", "hello", "hey"]:
        st.session_state.show_form = True
        st.session_state.submitted = False
        st.session_state.messages.append({
            "role": "assistant",
            "content": "👋 **Hello Traveller! Welcome to Trivanza – Your Smart Travel Buddy**\nTo help you better, please fill out your travel details below."
        })
    else:
        try:
            # Convert dates to strings for better context formatting
            from_date_str = st.session_state.trip_context.get("from_date", "")
            to_date_str = st.session_state.trip_context.get("to_date", "")
            
            # Format dates properly if they exist
            if from_date_str and hasattr(from_date_str, 'strftime'):
                from_date_str = from_date_str.strftime("%Y-%m-%d")
            if to_date_str and hasattr(to_date_str, 'strftime'):
                to_date_str = to_date_str.strftime("%Y-%m-%d")
            
            messages = [
                {"role": "system", "content": f"""
You are TRIVANZA – a travel-specialized AI assistant.

🎯 PURPOSE:
Provide personalized, real-world, budget-aware travel guidance and itineraries. Use the user's last submitted travel details unless updated.

📌 CONTEXT:
Origin: {st.session_state.trip_context.get("origin", "Not provided")}
Destination: {st.session_state.trip_context.get("destination", "Not provided")}
Travel Duration: {from_date_str} to {to_date_str}
Transport: {st.session_state.trip_context.get("transport", "")}
Stay: {st.session_state.trip_context.get("stay", "")}
Budget: {st.session_state.trip_context.get("budget", "")}
Activities: {st.session_state.trip_context.get("activities", "")}

✅ Answer ONLY travel-related questions.
✅ Suggest costed, bookable activities.
✅ Use Markdown format. Do not repeat old answers unless modifications requested.
✅ Always consider the full travel duration from start date to end date when making recommendations.
                """}
            ]
            messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]

            with st.spinner("✈️ Planning your travel response..."):
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
if st.session_state.show_form and not st.session_state.submitted:
    with st.form("travel_form"):
        st.markdown("### 🧳 Let's plan your perfect trip!")

        col1, col2 = st.columns(2)
        with col1:
            origin = st.text_input("🌍 Origin", placeholder="e.g., Delhi")
        with col2:
            destination = st.text_input("📍 Destination", placeholder="e.g., Paris")

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
            # Validate dates
            if to_date < from_date:
                st.error("❌ End date must be after start date!")
            else:
                st.session_state.submitted = True
                st.session_state.show_form = False

                # Calculate trip duration
                trip_duration = (to_date - from_date).days + 1  # +1 to include both start and end days
                
                # Save to memory with proper date formatting
                st.session_state.trip_context = {
                    "origin": origin,
                    "destination": destination,
                    "from_date": from_date,
                    "to_date": to_date,
                    "trip_duration": trip_duration,
                    "transport": transport,
                    "stay": stay,
                    "budget": budget,
                    "activities": activities
                }

                # Format dates for the prompt
                from_date_formatted = from_date.strftime("%B %d, %Y")
                to_date_formatted = to_date.strftime("%B %d, %Y")

                itinerary_prompt = f"""
You are TRIVANZA – a travel-specialized AI assistant.

User wants a full travel plan with these inputs:
- Origin: {origin}
- Destination: {destination}
- Travel Dates: {from_date_formatted} to {to_date_formatted} ({trip_duration} days)
- Transport: {transport}
- Stay: {stay}
- Budget: {budget}
- Activities: {activities}

📌 IMPORTANT: Create a {trip_duration}-day itinerary covering the ENTIRE duration from {from_date_formatted} to {to_date_formatted}.

📌 FORMAT:
- Title (e.g., "{trip_duration}-Day {destination} Getaway – Mid-Budget")
- Day-by-day breakdown for ALL {trip_duration} days with food, hotel, transport, activities
- Estimated Prices and Booking links for each day
- Total estimated budget summary
- End with: "Would you like to make any changes or adjustments?"

Platforms: Trusted Platforms in user area
Flights: Skyscanner, MakeMyTrip etc.
Hotels: Booking.com, Airbnb etc.
Food: Zomato, TripAdvisor etc.
Transport: Uber, RedBus, Zoomcar etc.
Activities: Klook, Viator, GetYourGuide etc.

Make sure to cover every single day from day 1 to day {trip_duration}.
"""

                try:
                    with st.spinner("🎯 Crafting your itinerary..."):
                        response = client.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": "You are TRIVANZA – a travel-specialized AI assistant."},
                                {"role": "user", "content": itinerary_prompt}
                            ],
                            temperature=0.8,
                            max_tokens=1800
                        )
                        itinerary = response.choices[0].message.content
                        st.session_state.messages.append({"role": "assistant", "content": itinerary})
                except Exception as e:
                    st.session_state.messages.append({"role": "assistant", "content": f"❌ Error generating itinerary: {e}"})
