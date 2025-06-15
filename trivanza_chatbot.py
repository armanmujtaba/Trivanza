import streamlit as st
from openai import OpenAI

# ----------------- Configuration -----------------
st.set_page_config(page_title="Trivanza Smart Travel Planner")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ----------------- Session State -----------------
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# ----------------- Chat Input & Greeting -----------------
user_input = st.chat_input("Say hi to Trivanza!")

if user_input and not st.session_state.submitted:
    if "hi" in user_input.lower() or "hello" in user_input.lower():
        with st.chat_message("assistant"):
            st.markdown("""
                ### 👋 Welcome to Trivanza: Your Smart Travel Companion  
                I'm excited to help you with your travel plans. To provide the best experience, could you please share a few details with me?
            """)

        with st.form("travel_form"):
            origin = st.text_input("🌍 What is your origin (starting location)?")
            destination = st.text_input("📍 What is your destination (where are you headed)?")
            travel_dates = st.text_input("📅 What are your travel dates (from and to)?")
            transport = st.selectbox("🛫 Preferred mode of transport", ["Flight", "Train", "Car", "Bus"])
            stay = st.selectbox("🏨 Accommodation preference", ["Hotel", "Hostel", "Airbnb", "Resort"])
            budget = st.text_input("💰 Budget and currency (e.g., ₹50000 INR or $800 USD)")
            activities = st.text_area("🎯 Activities or experiences you're looking for?")

            submitted = st.form_submit_button("Get My Travel Plan")

            if submitted:
                st.session_state.submitted = True

                # Build Prompt for AI
                prompt = f"""
You are a travel expert. Create a detailed day wise travel itinerary for a user traveling from {origin} to {destination} during {travel_dates}.
Preferences:
- Transport: {transport}
- Stay: {stay}
- Budget: {budget}
- Activities: {activities}

Include:
- Day-wise plan with emoji
- Flight/train/transport details with prices
- Hotel/stay suggestions with prices and booking links
- Meal or activity suggestions with links
- Total daily cost and overall budget
- End with: "Would you like to make any changes or adjustments?"

Format everything cleanly using Markdown.
                """

                with st.spinner("🧭 Creating your personalized itinerary..."):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": "You are an expert AI travel planner."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7,
                            max_tokens=1800
                        )

                        itinerary = response.choices[0].message.content
                        st.chat_message("assistant").markdown(itinerary)

                    except Exception as e:
                        st.error(f"🚨 Error generating itinerary: {e}")
