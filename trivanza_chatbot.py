import streamlit as st
from openai import OpenAI
from datetime import date

# ------------ CONFIG ------------
st.set_page_config(page_title="TRIVANZA - Your Smart Travel Buddy", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ------------ HEADER ------------
st.markdown("""
<div style="display: flex; align-items: center; gap: 12px;">
    <img src="trivanza_logo.png" width="45px">
    <h2 style="margin: 0;">Trivanza – Smart Travel Planner</h2>
</div>
""", unsafe_allow_html=True)

# ------------ SESSION INIT ------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "system", "content": """
You are TRIVANZA – a travel-specialized AI assistant.

🌟 PURPOSE:
Provide intelligent, personalized, and budget-conscious travel planning. Respond ONLY to travel-related queries.
Provide booking links, costs, realistic suggestions, and Markdown formatting.

Respond only in the context of travel. If asked anything else, say:
"This chat is strictly about Travel and TRIVANZA’s features. Please ask Travel-related questions."
"""}
    ]

if "show_form" not in st.session_state:
    st.session_state.show_form = False

if "submitted" not in st.session_state:
    st.session_state.submitted = False

# ------------ CHAT INPUT ------------
user_input = st.chat_input("Say hi to Trivanza or ask your travel question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Greeting check
    if user_input.lower().strip() in ["hi", "hello", "hey"]:
        st.session_state.show_form = True
        st.session_state.submitted = False
        greeting = """
👋 **Welcome to Trivanza: Your Smart Travel Companion**  
I'm excited to help you with your travel plans. To get started, please share:

- What is your origin (starting location)?  
- What is your destination?  
- What are your travel dates (from and to)?  
- Mode of transport (flight, train, car)?  
- Accommodation preference (hotel, hostel, etc.)?  
- Budget and currency?  
- Any activities or experiences you're interested in?
"""
        st.session_state.messages.append({"role": "assistant", "content": greeting})
        st.session_state.chat_history.append({"role": "assistant", "content": greeting})

    else:
        try:
            with st.spinner("✈️ Working on your travel query..."):
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=st.session_state.chat_history,
                    temperature=0.7,
                    max_tokens=1500
                )
                answer = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
        except Exception as e:
            error_msg = f"🚨 Error: {e}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

# ------------ DISPLAY CHAT ------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------ TRAVEL FORM ------------
if st.session_state.show_form and not st.session_state.submitted:
    with st.form("travel_form"):
        st.markdown("### 📝 Let's Plan Your Trip")

        col1, col2 = st.columns(2)
        with col1:
            origin = st.text_input("🌍 Origin", placeholder="e.g., New Delhi")
        with col2:
            destination = st.text_input("📍 Destination", placeholder="e.g., Paris")

        col3, col4 = st.columns(2)
        with col3:
            from_date = st.date_input("🗓️ From", min_value=date.today())
        with col4:
            to_date = st.date_input("🗓️ To", min_value=date.today())

        transport = st.selectbox("🛫 Mode of Transport", ["Flight", "Train", "Car", "Bus"])
        stay = st.selectbox("🏨 Accommodation", ["Hotel", "Hostel", "Airbnb", "Resort"])
        budget = st.text_input("💰 Budget (e.g., ₹50000 INR or $800 USD)")
        activities = st.text_area("🎯 Desired Activities", placeholder="e.g., museums, beaches, nightlife")

        submit = st.form_submit_button("🌏 Generate Itinerary")

        if submit:
            st.session_state.submitted = True
            user_prompt = f"""
User Inputs:
- Origin: {origin}
- Destination: {destination}
- Dates: {from_date} to {to_date}
- Transport: {transport}
- Stay: {stay}
- Budget: {budget}
- Activities: {activities}

Please generate a detailed, personalized travel itinerary including:
- Day-wise breakdown
- Estimated cost breakdown
- Booking links
- Final cost summary
"""
            st.session_state.chat_history.append({"role": "user", "content": user_prompt})

            try:
                with st.spinner("🛬 Crafting your itinerary..."):
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=st.session_state.chat_history,
                        temperature=0.8,
                        max_tokens=1800
                    )
                    itinerary = response.choices[0].message.content
                    st.session_state.messages.append({"role": "assistant", "content": itinerary})
                    st.session_state.chat_history.append({"role": "assistant", "content": itinerary})
            except Exception as e:
                error_msg = f"❌ Unable to generate itinerary. Error: {e}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
