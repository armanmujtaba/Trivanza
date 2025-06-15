import streamlit as st
from openai import OpenAI

# ----------------- CONFIG -----------------
st.set_page_config(page_title="Trivanza – AI Travel Planner", page_icon="🧳")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ----------------- STATE INIT -----------------
if "itinerary_ready" not in st.session_state:
    st.session_state.itinerary_ready = False

# ----------------- CHAT GREETING -----------------
user_input = st.chat_input("Say hi to Trivanza!")

if user_input and not st.session_state.itinerary_ready:
    if "hi" in user_input.lower() or "hello" in user_input.lower():
        with st.chat_message("assistant"):
            st.markdown("""
                ### 👋 Hey there, I'm Trivanza – your personal AI travel planner!  
                Let's build your perfect trip together. Fill out a few quick details below:
            """)

        # ----------------- USER TRAVEL FORM -----------------
        with st.form("travel_form"):
            col1, col2 = st.columns(2)
            with col1:
                origin = st.text_input("🌍 Where are you starting from?")
            with col2:
                destination = st.text_input("📍 Where are you going?")

            travel_dates = st.text_input("📅 Travel Dates (e.g. 1-7 July)")
            transport = st.selectbox("🚗 Preferred Mode of Transport", ["Flight", "Train", "Bus", "Car"])
            stay = st.selectbox("🏨 Preferred Stay Type", ["Hotel", "Hostel", "Airbnb", "Resort"])
            budget = st.text_input("💰 Budget (e.g. ₹50,000 or $800)")
            activities = st.text_area("🎯 What kind of experiences are you looking for?", placeholder="Adventure, food, culture, beaches, mountains...")

            submitted = st.form_submit_button("📍 Generate My Itinerary")

            # ----------------- ON SUBMIT -----------------
            if submitted:
                st.session_state.itinerary_ready = True
                with st.spinner("🧭 Crafting your personalized travel plan..."):

                    prompt = f"""
You are an expert travel planner AI.

Plan a detailed day-wise itinerary for a trip from {origin} to {destination} during {travel_dates}.
Preferences:
- Transport: {transport}
- Stay: {stay}
- Budget: {budget}
- Interests: {activities}

Must Include:
- Each day as a new section with emoji title
- Transport & accommodation suggestions with prices and booking links
- Food and activities with names and links (e.g., Zomato, Booking.com, Viator)
- Daily budget total
- Final total cost
- End with: "Would you like to make any changes or adjustments?"

Use clean, readable Markdown formatting.
                    """

                    try:
                        response = client.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": "You are an expert AI travel planner."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7,
                            max_tokens=2000
                        )

                        final_plan = response.choices[0].message.content
                        st.chat_message("assistant").markdown(final_plan)

                    except Exception as e:
                        st.error(f"⚠️ Failed to generate itinerary: {e}")
