import streamlit as st
from openai import OpenAI
import re
from datetime import date
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
</style>
<div class="logo-container">
    <img class="logo" src="https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/Trivanza.png?raw=true">
</div>
""", unsafe_allow_html=True)

system_content = (
    "You are TRIVANZA Travel Assistant. For every trip, follow these rules:\n"
    "1. Begin with a friendly, personalized intro summarizing destination, dates, and user’s main interests.\n"
    "2. For each day, use a heading (e.g., 'Day 1: Arrival in Bangkok').\n"
    "   - For each event/expense, use a new line with an emoji, label, price in ₹, and booking/info link in brackets.\n"
    "   - Use only real or plausible options that match user dietary, sustainability, and other preferences (e.g., vegetarian food, eco hotels, activities matching interests).\n"
    "   - Separate each item on its own new line for maximum readability.\n"
    "   - End each day with a 🎯 Daily Total on a new line.\n"
    "3. After daily plans, show total trip cost as 'Total Trip Cost: ₹xx,xxx' on its own line.\n"
    "4. Create a packing checklist based on the destination’s weather/season and user activities. Use June/July Bangkok weather for packing if applicable.\n"
    "5. Add a short, clear budget analysis: is the user’s budget low/medium/high for their preferences? Suggest adjustments if needed.\n"
    "6. End with a friendly ‘Pro Tip’ for the destination (e.g., money-saving, cultural, or local tip).\n"
    "7. Output must be in Markdown, with each heading, bullet, and total on its own line, never run-together. Do not summarize days—always list every day.\n"
    "8. All costs must be shown in Indian Rupees (₹, INR).\n"
)

greeting_message = """Welcome to Trivanza: Your Smart Travel Companion  
I'm excited to help you with your travel plans. Could you please share some details like:  
- Where you're starting and going  
- Travel dates  
- Transport and accommodation preferences  
- Budget and currency  
- Any activities you're excited about?"""

fallback_message = "This chat is strictly about Travel and TRIVANZA’s features. Please ask Travel-related questions."

with st.expander("📋 Plan My Trip", expanded=not st.session_state.form_submitted):
    with st.form("travel_form", clear_on_submit=False):
        st.markdown("### 🧳 Let's plan your perfect trip!")

        col1, col2 = st.columns(2)
        with col1:
            traveler_type = st.selectbox("🧍 Traveler Type", ["Solo", "Couple", "Family", "Group"])
            group_size = st.number_input("👥 Group Size", min_value=1, value=2)
        with col2:
            origin = st.text_input("🌍 Origin", placeholder="e.g., Delhi")
            destination = st.text_input("📍 Destination", placeholder="e.g., Paris")
        col3, col4 = st.columns(2)
        with col3:
            from_date = st.date_input("📅 From Date", min_value=date.today())
        with col4:
            to_date = st.date_input("📅 To Date", min_value=from_date)

        st.markdown("#### 💰 Budget & Stay")
        col5, col6 = st.columns(2)
        with col5:
            budget_amount = st.number_input("💰 Budget", min_value=1000, step=1000)
        with col6:
            currency_type = st.selectbox("💱 Currency", ["₹ INR", "$ USD", "€ EUR", "£ GBP", "¥ JPY"])
        stay = st.selectbox("🏨 Stay Type", ["Hotel", "Hostel", "Airbnb", "Resort"])

        st.markdown("#### 🎯 Preferences & Interests")
        dietary_pref = st.multiselect("🥗 Dietary", ["Vegetarian", "Vegan", "Gluten-Free", "Halal", "Kosher"])
        sustainability = st.selectbox("🌱 Sustainability", ["None", "Eco-Friendly Stays", "Carbon Offset Flights", "Zero-Waste Activities"])
        language_pref = st.selectbox("🌐 Language", ["English", "Hindi", "French", "Spanish", "Mandarin", "Local Phrases"])
        cultural_pref = st.selectbox("👗 Cultural Sensitivity", ["Standard", "Conservative Dress", "Religious Holidays", "Gender Norms"])
        custom_activities = st.multiselect("🎨 Interests", [
            "Beaches", "Hiking", "Shopping", "Nightlife",
            "Cultural Immersion", "Foodie Tour", "Adventure Sports"
        ])

        submit = st.form_submit_button("🚀 Generate Itinerary")

        if submit:
            if not origin.strip():
                st.error("❌ Enter your origin city!")
            elif not destination.strip():
                st.error("❌ Enter your destination!")
            elif to_date < from_date:
                st.error("❌ End date must be after start date!")
            elif budget_amount <= 0:
                st.error("❌ Budget must be greater than 0")
            else:
                st.success("✅ Generating your personalized itinerary...")
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
                st.session_state.just_generated_form_prompt = True
                user_instructions = (
                    "IMPORTANT: Format each day as:\n"
                    "Day X: <Title>\n"
                    "✈️ Flight: ... ₹... [Book: ...]\n"
                    "🏨 Stay: ... ₹... [Book: ...]\n"
                    "🍽️ Meal: ... ₹... [Book: ...]\n"
                    "🎯 Daily Total: ₹...\n"
                    "Each item must be on its own new line. Do not combine items. Use only options matching my preferences (dietary, eco-friendly, interests).\n"
                    "After the last day, add:\n"
                    "- Total Trip Cost: ₹<total>\n"
                    "- Packing Checklist for " + destination + f" in {from_date.strftime('%B')} (based on weather & activities)\n"
                    "- Budget analysis: Is my budget low/medium/high? Suggest what to change if needed.\n"
                    "- End with a friendly {destination} pro tip."
                )
                prompt = (
                    f"Plan a trip from {origin} to {destination} from {from_date} to {to_date} for a {traveler_type.lower()} of {group_size} people. Budget: {currency_type} {budget_amount}. "
                    f"Dietary: {', '.join(dietary_pref) if dietary_pref else 'None'}, Language: {language_pref}, Sustainability: {sustainability}, "
                    f"Cultural: {cultural_pref}, Interests: {', '.join(custom_activities) if custom_activities else 'None'}. Stay: {stay}.\n"
                    "Please ensure all costs are shown in Indian Rupees (₹, INR). Format your answer in Markdown with clear headings, bullets, and cost tables.\n\n"
                    f"{user_instructions}"
                )
                st.session_state.messages.append({
                    "role": "user",
                    "content": prompt
                })
                st.session_state.pending_form_response = True
                st.session_state.form_submitted = True
                st.rerun()

travel_keywords = [
    "travel", "travelling", "trip", "vacation", "explore", "journey", "tour", "destination", "destinations",
    "summer", "india", "holiday", "beach", "mountain", "adventure", "hotel", "flight", "sightseeing", "tourist",
    "places", "itinerary", "plan", "attraction", "resort", "city", "backpacking", "road", "solo", "family", "budget",
    "luxury", "eco", "sustainable", "nomad", "staycation", "getaway", "island", "unesco", "local", "cultural",
    "trekking", "safari", "group", "hostel", "accommodation", "booking", "transport", "bus", "train", "car", "visa",
    "passport", "insurance", "luggage", "packing", "currency", "cost", "expenses", "food", "cuisine", "restaurant",
    "restaurants", "street", "dining", "festival", "nightlife", "shopping", "souvenir", "photography", "wellness",
    "retreat", "spa", "guide", "cruise", "winter", "spring", "autumn", "monsoon", "hiking", "trek", "camping",
    "surfing", "snorkeling", "scuba", "skiing", "kayaking", "cycling", "yoga", "meditation", "spiritual", "pilgrimage",
    "heritage", "museum", "landmark", "nature", "wildlife", "park", "sports", "volunteer", "medical", "conference",
    "business", "honeymoon", "offbeat", "hidden", "gem"
]
stemmed_keywords = set(ps.stem(k) for k in travel_keywords)

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("💬 Ask Trivanza anything travel-related:")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    text_lower = user_input.lower()
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    words = re.findall(r'\w+', text_lower)
    is_travel_related = any(ps.stem(word) in stemmed_keywords for word in words)

    # PATCH: Also treat as travel-related if the message looks like a trip plan
    form_keywords = ["plan a trip", "itinerary", "hotel", "flight", "travel to", "budget"]
    if any(kw in user_input.lower() for kw in form_keywords):
        is_travel_related = True

    currency_type = "₹ INR"
    if "trip_context" in st.session_state and st.session_state.trip_context:
        currency_type = st.session_state.trip_context.get("currency_type", "₹ INR")
    currency_instruction = (
        "Please ensure all costs are shown in Indian Rupees (₹, INR)."
        if currency_type.startswith("₹")
        else f"Please show all costs in {currency_type}."
    )

    if user_input.lower().startswith("analyze review:"):
        review = user_input.split(":", 1)[1]
        sentiment = analyze_sentiment(review)
        assistant_response = f"Sentiment Analysis: {sentiment}"
    elif user_input.lower().startswith("recommend destinations"):
        preferences = user_input.split(":", 1)[1] if ":" in user_input else ""
        recommendations = recommend_destinations(st.session_state.user_history, preferences)
        assistant_response = f"Recommended Destinations:\n{recommendations}"
    elif user_input.lower().startswith("detect language:"):
        phrase = user_input.split(":", 1)[1]
        assistant_response = detect_and_translate(phrase)
    elif user_input.lower().startswith("analyze image:"):
        image_url = user_input.split(":", 1)[1].strip()
        assistant_response = recognize_destination(image_url)
    elif any(greet in text_lower for greet in greetings) and not is_travel_related:
        assistant_response = greeting_message
    elif not is_travel_related and not st.session_state.get("pending_form_response", False):
        assistant_response = fallback_message
    else:
        try:
            user_instructions = (
                "IMPORTANT: Format each day as:\n"
                "Day X: <Title>\n"
                "✈️ Flight: ... ₹... [Book: ...]\n"
                "🏨 Stay: ... ₹... [Book: ...]\n"
                "🍽️ Meal: ... ₹... [Book: ...]\n"
                "🎯 Daily Total: ₹...\n"
                "Each item must be on its own new line. Do not combine items. Use only options matching my preferences (dietary, eco-friendly, interests).\n"
                "After the last day, add:\n"
                "- Total Trip Cost: ₹<total>\n"
                "- Packing Checklist for the destination in the travel month (based on weather & activities)\n"
                "- Budget analysis: Is my budget low/medium/high? Suggest what to change if needed.\n"
                "- End with a friendly pro tip."
            )
            messages = [{"role": "system", "content": system_content}] + st.session_state.messages
            messages.append({
                "role": "user",
                "content": f"{currency_instruction} Format your answer in Markdown with clear headings, bullets, and cost tables.\n\n{user_instructions}"
            })
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=1800
            )
            assistant_response = response.choices[0].message.content
            # Post-processing: ensure each bullet/emoji appears on a new line
            assistant_response = re.sub(r'(?<!\n)([✈️🏨🍽️🍜🍹🚌🚕🚶‍♀️🛍️🎯🎉🎭🕌🍴🍣])', r'\n\1', assistant_response)
        except Exception:
            assistant_response = "Sorry, I'm unable to respond at the moment. Try again later."

    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.rerun()

if st.session_state.pending_form_response:
    try:
        currency_type = st.session_state.trip_context.get("currency_type", "₹ INR") if st.session_state.trip_context else "₹ INR"
        currency_instruction = (
            "Please ensure all costs are shown in Indian Rupees (₹, INR)."
            if currency_type.startswith("₹")
            else f"Please show all costs in {currency_type}."
        )
        destination = st.session_state.trip_context["destination"]
        from_date = st.session_state.trip_context["from_date"]
        user_instructions = (
            "IMPORTANT: Format each day as:\n"
            "Day X: <Title>\n"
            "✈️ Flight: ... ₹... [Book: ...]\n"
            "🏨 Stay: ... ₹... [Book: ...]\n"
            "🍽️ Meal: ... ₹... [Book: ...]\n"
            "🎯 Daily Total: ₹...\n"
            "Each item must be on its own new line. Do not combine items. Use only options matching my preferences (dietary, eco-friendly, interests).\n"
            f"After the last day, add:\n"
            f"- Total Trip Cost: ₹<total>\n"
            f"- Packing Checklist for {destination} in {from_date.strftime('%B')} (based on weather & activities)\n"
            "- Budget analysis: Is my budget low/medium/high? Suggest what to change if needed.\n"
            f"- End with a friendly {destination} pro tip."
        )
        messages = [{"role": "system", "content": system_content}] + st.session_state.messages
        messages.append({
            "role": "user",
            "content": f"{currency_instruction} Format your answer in Markdown with clear headings, bullets, and cost tables.\n\n{user_instructions}"
        })
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=1800
        )
        assistant_response = response.choices[0].message.content
        # Post-processing: ensure each bullet/emoji appears on a new line
        assistant_response = re.sub(r'(?<!\n)([✈️🏨🍽️🍜🍹🚌🚕🚶‍♀️🛍️🎯🎉🎭🕌🍴🍣])', r'\n\1', assistant_response)
    except Exception:
        assistant_response = "Sorry, I'm unable to generate your itinerary right now."

    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.session_state.pending_form_response = False
    st.rerun()

for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
