import streamlit as st
from openai import OpenAI
import re
from datetime import date, timedelta
from nltk.stem import PorterStemmer

ps = PorterStemmer()

st.set_page_config(page_title="Trivanza Travel Assistant", layout="centered")
client = OpenAI()

def analyze_sentiment(text):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a sentiment analysis tool. Classify this review as Positive, Neutral, or Negative and explain why."},
                {"role": "user", "content": text}
            ],
            temperature=0.0,
            max_tokens=100
        )
        return response.choices[0].message.content
    except Exception:
        return "Sentiment analysis unavailable."

def detect_and_translate(text, target_language="English"):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Detect the language of the user's input. If it is not English, translate it to English. Reply as: Detected: <Language>. Translation: <English translation>."},
                {"role": "user", "content": text}
            ],
            temperature=0.0,
            max_tokens=120
        )
        return response.choices[0].message.content
    except Exception:
        return "Language detection unavailable."

def recognize_destination(image_url):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-vision-preview",
            messages=[
                {"role": "system", "content": "Given a travel photo, try to identify the destination or suggest similar travel destinations. Respond as: 'This looks like <destination> or similar to <alternatives>'."},
                {"role": "user", "content": f"<image>{image_url}</image>"}
            ],
            temperature=0.0,
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception:
        return "Image recognition unavailable."

def recommend_destinations(user_history, preferences):
    try:
        prompt = (
            "Given the user's travel history and preferences, recommend 3 destinations with reasons. "
            "User history: " + str(user_history) +
            "\nPreferences: " + str(preferences)
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a travel recommendation engine. Suggest 3 destinations and explain why."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception:
        return "Recommendations unavailable."

def post_process_itinerary(text):
    # Convert [Book: ...] or [Info: ...] to Markdown links [Book](...)
    text = re.sub(r'\[(Book|Info|Menu|Tickets|Website|Booking)\s*:\s*(https?://[^\]\s]+)\]', r'[\1](\2)', text)
    # Ensure each bullet, emoji, or heading starts on a new line
    text = re.sub(
        r'(?<!\n)([✈️🏨🍽️🍜🍹🚌🚕🚶‍♀️🛍️🎯🎉🎭🕌🍴🍣🏖️🚗🚖🚶‍♂️🚴‍♂️🌆•\-])',
        r'\n\1', text
    )
    # Ensure Markdown headings start on their own line (## Day N: ...)
    text = re.sub(r'(?<!\n)(## Day)', r'\n\1', text)
    # Ensure each itinerary item is on its own line (extra safety: split on . or ; if multiple items in one line)
    fixed_lines = []
    for line in text.split('\n'):
        # If line contains multiple emojis, split further
        splits = re.split(r'(?=(✈️|🏨|🍽️|🍜|🍹|🚌|🚕|🚶‍♀️|🛍️|🎯|🎉|🎭|🕌|🍴|🍣|🏖️|🚗|🚖|🚶‍♂️|🚴‍♂️|🌆))', line)
        splits = [s for s in splits if s]  # remove empty
        if len(splits) > 1:
            for s in splits:
                if s.strip():
                    fixed_lines.append(s.strip())
        else:
            fixed_lines.append(line.strip())
    text = '\n'.join(fixed_lines)
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', r'\n\n', text)
    return text.strip()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "trip_context" not in st.session_state:
    st.session_state.trip_context = None
if "pending_form_response" not in st.session_state:
    st.session_state.pending_form_response = False
if "user_history" not in st.session_state:
    st.session_state.user_history = []
if "pending_llm_prompt" not in st.session_state:
    st.session_state.pending_llm_prompt = None

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
.chat-entry { margin-top: 10px; }
.stChatInputContainer { position: fixed; bottom: 0; left: 0; right: 0; background: white; z-index: 1001; }
.stChatInputContainer textarea { min-height: 2.5em; }
.appview-container .main { padding-bottom: 8em !important; }
</style>
<div class="logo-container">
    <img class="logo" src="https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/Trivanza.png?raw=true">
</div>
""", unsafe_allow_html=True)

greeting_message = """Hello Traveler! Welcome to Trivanza - I'm Your Smart Travel Companion  
I'm excited to help you with your travel plans.
- Submit Plan My Trip form for customised itinerary  
- Use chat box for your other travel related queries"""

fallback_message = "This chat is strictly about Travel and TRIVANZA’s features. Please ask Travel-related questions."

def is_greeting_or_planning(text):
    greetings = [
        "hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings",
        "plan", "itinerary", "plan my trip", "journey", "my journey", "trip planning",
        "plan itinerary", "plan my itinerary"
    ]
    text_lower = text.lower()
    return any(greet in text_lower for greet in greetings)

SYSTEM_PROMPT = """You are Trivanza, a smart travel assistant.
Only answer questions that are related to travel, trip planning, destinations, activities, flights, visas, tourism, cultures, food, transport, or anything a traveler may want to know.
If a user asks something unrelated to travel, reply: "This chat is strictly about Travel and TRIVANZA’s features. Please ask Travel-related questions."
"""

with st.expander("📋 Plan My Trip", expanded=False):  # Default minimized
    with st.form("travel_form", clear_on_submit=False):
        st.markdown("### 🧳 Let's plan your perfect trip!")

        col1, col2 = st.columns(2)
        with col1:
            traveler_type = st.selectbox("🧍 Traveler Type", ["Solo", "Couple", "Family", "Group"], key="traveler_type")
            group_size = st.number_input("👥 Group Size", min_value=1, value=2, key="group_size")
        with col2:
            origin = st.text_input("🌍 Origin", placeholder="e.g., Delhi", key="origin")
            destination = st.text_input("📍 Destination", placeholder="e.g., Paris", key="destination")
        col3, col4 = st.columns(2)
        with col3:
            from_date = st.date_input("📅 From Date", min_value=date.today(), key="from_date")
        with col4:
            to_date = st.date_input("📅 To Date", min_value=from_date, key="to_date")

        st.markdown("#### 💰 Budget & Stay")
        col5, col6 = st.columns(2)
        with col5:
            budget_amount = st.number_input("💰 Budget", min_value=1000, step=1000, key="budget_amount")
        with col6:
            currency_type = st.selectbox("💱 Currency", ["₹ INR", "$ USD", "€ EUR", "£ GBP", "¥ JPY"], key="currency_type")
        stay = st.selectbox("🏨 Stay Type", ["Hotel", "Hostel", "Airbnb", "Resort"], key="stay")

        st.markdown("#### 🎯 Preferences & Interests")
        dietary_pref = st.multiselect("🥗 Dietary", ["Vegetarian", "Vegan", "Gluten-Free", "Halal", "Kosher"], key="dietary_pref")
        sustainability = st.selectbox("🌱 Sustainability", ["None", "Eco-Friendly Stays", "Carbon Offset Flights", "Zero-Waste Activities"], key="sustainability")
        language_pref = st.selectbox("🌐 Language", ["English", "Hindi", "French", "Spanish", "Mandarin", "Local Phrases"], key="language_pref")
        cultural_pref = st.selectbox("👗 Cultural Sensitivity", ["Standard", "Conservative Dress", "Religious Holidays", "Gender Norms"], key="cultural_pref")
        custom_activities = st.multiselect("🎨 Interests", [
            "Beaches", "Hiking", "Shopping", "Nightlife",
            "Cultural Immersion", "Foodie Tour", "Adventure Sports"
        ], key="custom_activities")

        submit = st.form_submit_button("🚀 Generate Itinerary")

        if submit:
            st.success("✅ Generating your personalized itinerary...")

            days = (to_date - from_date).days + 1
            dates = [(from_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
            month = from_date.strftime("%B")

            user_instructions = (
                "IMPORTANT:\n"
                "For each day, use a Markdown heading: ## Day N: <activity/city> (<YYYY-MM-DD>) with the actual date for that day. "
                "Use the correct day number and real date for each day. "
                "EVERY itinerary item (flight, return flight, transfer, hotel, meal, activity, transportation, local transport, etc.) must be on its own SEPARATE line, and must include:\n"
                "<emoji> <label>: <details>, ₹<cost> per person [Book](https://...)\n"
                "- For every flight, state the airline name, route, price, and a real booking link (e.g. [Book](https://www.vietnamairlines.com/)).\n"
                "- For every hotel, state the hotel name, price, and a real booking link (e.g. [Book](https://www.booking.com/)).\n"
                "- For every restaurant, state the restaurant name, meal type, price, and a real info or reservation link (e.g. [Zomato](https://www.zomato.com/)).\n"
                "- Every major item MUST have a real, working, direct booking/info link.\n"
                "- Every day MUST include at least one local transportation item with booking/info link and cost, and be included in daily and total costs.\n"
                "- The return flight MUST appear on the last day, with booking link and cost, and be included in the day and total costs.\n"
                "- For accommodation, food, and activities, choose and explicitly mention the best options within the user’s budget. If budget is tight, suggest a lower-cost alternative and explain.\n"
                "Daily total must be the sum of ALL items for that day, including all flights, hotels, food, transport, and activities. "
                "End every day with: 🎯 Daily Total: ₹<per person>/<total for all> on its own line. "
                "After all days, show cost breakdown as bullet points. "
                f"Add a Packing Checklist for {destination} in {month}, Budget Analysis, and a {destination} Pro Tip. "
                "Output must be in Markdown, with each heading, bullet, and cost on its own line. NEVER combine multiple itinerary items on one line."
            )

            short_prompt = (
                f"Plan a trip from {origin} to {destination} from {from_date} to {to_date} for a {traveler_type.lower()} of {group_size} people. "
                f"Budget: {currency_type} {budget_amount}. "
                f"Dietary: {', '.join(dietary_pref) if dietary_pref else 'None'}, Language: {language_pref}, Sustainability: {sustainability}, "
                f"Cultural: {cultural_pref}, Interests: {', '.join(custom_activities) if custom_activities else 'None'}. Stay: {stay}. "
                f"Please ensure all costs are shown in Indian Rupees (₹, INR)."
            )

            full_prompt = (
                short_prompt +
                "\nFormat your answer in Markdown.\n\n" +
                user_instructions
            )

            st.session_state.messages.append({
                "role": "user",
                "content": short_prompt
            })
            st.session_state["pending_llm_prompt"] = full_prompt

            trip_context = {
                "origin": origin.strip(),
                "destination": destination.strip(),
                "from_date": from_date,
                "to_date": to_date,
                "traveler_type": traveler_type,
                "group_size": group_size,
                "dietary_pref": dietary_pref,
                "language_pref": language_pref,
                "sustainability": sustainability,
                "cultural_pref": cultural_pref,
                "custom_activities": custom_activities,
                "budget_amount": budget_amount,
                "currency_type": currency_type,
                "stay": stay
            }
            st.session_state.trip_context = trip_context
            st.session_state.user_history.append(trip_context)
            st.session_state.pending_form_response = True
            st.session_state.form_submitted = True
            st.rerun()

# Render chat history above input
for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Chat input at the bottom
user_input = st.chat_input(placeholder="How may I help you today?")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if is_greeting_or_planning(user_input):
        assistant_response = greeting_message
    else:
        # Let the LLM judge travel-relatedness
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in st.session_state.messages:
            messages.append(msg)
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=1800
            )
            assistant_response = response.choices[0].message.content
            assistant_response = post_process_itinerary(assistant_response)
        except Exception:
            assistant_response = "Sorry, I'm unable to respond at the moment. Try again later."

    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.rerun()

if st.session_state.pending_form_response:
    try:
        ctx = st.session_state.trip_context or {}
        destination = ctx.get("destination", "Destination")
        from_date = ctx.get("from_date", date.today())
        month = from_date.strftime('%B')
        currency_type = ctx.get("currency_type", "₹ INR")
        currency_instruction = (
            "Please ensure all costs are shown in Indian Rupees (₹, INR)."
            if currency_type.startswith("₹")
            else f"Please show all costs in {currency_type}."
        )
        user_instructions = (
            "IMPORTANT:\n"
            "For each day, use a Markdown heading: ## Day N: <activity/city> (<YYYY-MM-DD>) with the actual date for that day. "
            "Use the correct day number and real date for each day. "
            "EVERY itinerary item (flight, return flight, transfer, hotel, meal, activity, transportation, local transport, etc.) must be on its own SEPARATE line, and must include:\n"
            "<emoji> <label>: <details>, ₹<cost> per person [Book](https://...)\n"
            "- For every flight, state the airline name, route, price, and a real booking link (e.g. [Book](https://www.vietnamairlines.com/)).\n"
            "- For every hotel, state the hotel name, price, and a real booking link (e.g. [Book](https://www.booking.com/)).\n"
            "- For every restaurant, state the restaurant name, meal type, price, and a real info or reservation link (e.g. [Zomato](https://www.zomato.com/)).\n"
            "- Every major item MUST have a real, working, direct booking/info link.\n"
            "- Every day MUST include at least one local transportation item with booking/info link and cost, and be included in daily and total costs.\n"
            "- The return flight MUST appear on the last day, with booking link and cost, and be included in the day and total costs.\n"
            "- For accommodation, food, and activities, choose and explicitly mention the best options within the user’s budget. If budget is tight, suggest a lower-cost alternative and explain.\n"
            "Daily total must be the sum of ALL items for that day, including all flights, hotels, food, transport, and activities. "
            "End every day with: 🎯 Daily Total: ₹<per person>/<total for all> on its own line. "
            "After all days, show cost breakdown as bullet points. "
            f"Add a Packing Checklist for {destination} in {month}, Budget Analysis, and a {destination} Pro Tip. "
            "Output must be in Markdown, with each heading, bullet, and cost on its own line. NEVER combine multiple itinerary items on one line.\n"
            f"{currency_instruction}\nFormat your answer in Markdown."
        )
        messages = st.session_state.messages.copy()
        messages.insert(0, {"role": "system", "content": user_instructions})
        messages.append({
            "role": "user",
            "content": st.session_state["pending_llm_prompt"]
        })
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=1800
        )
        assistant_response = response.choices[0].message.content
        assistant_response = post_process_itinerary(assistant_response)
    except Exception:
        assistant_response = "Sorry, I'm unable to generate your itinerary right now."

    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.session_state.pending_form_response = False
    st.rerun()
