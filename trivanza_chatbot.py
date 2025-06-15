import streamlit as st
from openai import OpenAI

# Set your page configuration
st.set_page_config(page_title="Trivanza Smart Travel Planner", layout="centered")

# Setup OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Session state to track form submission
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# Chat input box
user_input = st.chat_input("Say hi to Trivanza!")

# Greet the user and ask for travel details
if user_input and not st.session_state.submitted:
    if "hi" in user_input.lower() or "hello" in user_input.lower():
        with st.chat_message("assistant"):
            st.markdown("""
                ### 👋 Welcome to Trivanza: Your Smart Travel Companion  
                I'm excited to help you with your travel plans. Fill out this quick form to get your custom itinerary.
            """)

        with st.form("travel_form"):
            origin = st.text_input("🌍 What is your origin (starting location)?", placeholder="e.g., Delhi")
            destination = st.text_input("📍 What is your destination?", placeholder="e.g., Vietnam")
            travel_dates = st.text_input("📅 What are your travel dates (from and to)?", placeholder="e.g., 1-7 June")
            transport = st.selectbox("🛫 Preferred mode of transport", ["Flight", "Train", "Car", "Bus"])
            stay = st.selectbox("🏨 Accommodation preference", ["Hotel", "Hostel", "Airbnb", "Resort"])
            budget = st.text_input("💰 Budget and currency", placeholder="e.g., ₹50,000 INR or $800 USD")
            activities = st.text_area("🎯 Activities or experiences you're looking for?", placeholder="e.g., adventure, beach, historical sites")

            submitted = st.form_submit_button("🧭 Get My Travel Plan")

            if submitted:
                st.session_state.submitted = True

                # Create the travel planning prompt
                prompt = f"""
You are a travel expert. Create a detailed day-wise travel itinerary for a user traveling from {origin} to {destination} during {travel_dates}.
Preferences:
- Transport: {transport}
- Stay: {stay}
- Budget: {budget}
- Activities: {activities}

Include:
- Day-wise plan with emoji
- Flight/train/transport options with prices
- Hotel/stay suggestions with prices and booking links
- Meal or activity suggestions with prices and links
- Total daily cost and full trip budget
- End with: "Would you like to make any changes or adjustments?"

Format everything in clean Markdown.
                """

                with st.spinner("🛫 Crafting your itinerary..."):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": "You are an expert AI travel planner."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.8,
                            max_tokens=1800
                        )

                        itinerary = response.choices[0].message.content
                        with st.chat_message("assistant"):
                            st.markdown(itinerary)

                    except Exception as e:
                        st.error("❌ Error generating itinerary. Please try again.")
                        st.exception(e)
