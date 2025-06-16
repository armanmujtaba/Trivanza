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

def post_process_itinerary(text):
    # Ensure emoji-bullets start on new lines
    text = re.sub(r'(?<!\n)([✈️🏨🍽️🍜🍹🚌🚕🚶‍♀️🛍️🎯🎉🎭🕌🍴🍣🏖️🚗🚖🚶‍♂️🚴‍♂️🌆])', r'\n\1', text)
    # Make sure each table row starts on a new line
    text = re.sub(r'(\|\s*)', r'\n\1', text)
    # Remove triple+ newlines
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
</style>
<div class="logo-container">
    <img class="logo" src="https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/Trivanza.png?raw=true">
</div>
""", unsafe_allow_html=True)

system_content = (
    "You are TRIVANZA Travel Assistant. "
    "For every trip request, ALWAYS reply in the following structure and style:\n"
    "1. Friendly short intro, summarizing trip city, dates, and user interests.\n"
    "2. For each day, use a heading (e.g., 'Day 1: Arrival in Paris').\n"
    "3. For EVERY itinerary item (flight, transfer, hotel, meal, activity, transportation), use a SEPARATE line with:\n"
    "   <emoji> <label>: <details>, ₹<cost> per person [<Link/Info>]\n"
    "   - Always state 'per person' and multiply for total day cost if group size >1.\n"
    "   - At end of EACH day, show both per person and total cost if group size >1.\n"
    "4. End every day with 🎯 Daily Total: ₹<per person>/<total for all> on its own line.\n"
    "5. After all days, show a bold Markdown cost breakdown table:\n"
    "   | Day    | Per Person | Group |\n"
    "   |--------|------------|-------|\n"
    "   | ...    | ...        | ...   |\n"
    "   | Total  | ...        | ...   |\n"
    "6. Add a Packing Checklist for the destination in the travel month (based on weather & activities).\n"
    "7. Add Budget Analysis: Is the budget low/medium/high for this trip? Suggest how to adjust if needed.\n"
    "8. Add a friendly Pro Tip at the end.\n"
    "9. Output must be in Markdown, with each heading, bullet, and cost on its own line. Do NOT combine lines. Do NOT summarize days. Do NOT skip any section above.\n"
    "10. Never repeat the prompt or any instructions in your output."
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
            # Use local form variables for prompt construction!
            st.success("✅ Generating your personalized itinerary...")

            # --- Build user-friendly prompt for chat display ---
            short_prompt = (
                f"Plan a trip from {origin} to {destination} from {from_date} to {to_date} for a {traveler_type.lower()} of {group_size} people. "
                f"Budget: {currency_type} {budget_amount}. "
                f"Dietary: {', '.join(dietary_pref) if dietary_pref else 'None'}, Language: {language_pref}, Sustainability: {sustainability}, "
                f"Cultural: {cultural_pref}, Interests: {', '.join(custom_activities) if custom_activities else 'None'}. Stay: {stay}. "
                f"Please ensure all costs are shown in Indian Rupees (₹, INR)."
            )
            # --- Strong, uniform instructions for LLM ---
            user_instructions = (
                "IMPORTANT:\n"
                "1. Begin with a friendly, short intro (one line), summarizing trip city, dates, and user interests.\n"
                "2. For each day, use a heading (e.g., 'Day 1: Arrival in Paris').\n"
                "3. For EVERY itinerary item (flight, transfer, hotel, meal, activity, transportation), use a SEPARATE line with:\n"
                "   <emoji> <label>: <details>, ₹<cost> per person [<Link/Info>]\n"
                "   - Always state 'per person' and multiply for total day cost.\n"
                "   - If group size >1, at end of EACH day, show both per person and total costs.\n"
                "4. End every day with 🎯 Daily Total: ₹<per person>/<total for all> on its own line.\n"
                "5. After all days, show a clear, bold cost breakdown table:\n"
                "   - Table columns: Day, Per Person, Group\n"
                "   - Row: Total\n"
                f"6. Add a Packing Checklist for {destination} in {from_date.strftime('%B')} (based on weather & activities).\n"
                "7. Add Budget Analysis: Is the budget low/medium/high for this trip? Suggest how to adjust if needed.\n"
                f"8. Add a friendly {destination} Pro Tip at the end.\n"
                "9. Output must be in Markdown, with each heading, bullet, and cost on its own line. Do NOT combine lines. Do NOT summarize days. Do NOT skip any section above."
            )
            full_prompt = (
                short_prompt +
                "\nFormat your answer in Markdown.\n\n" +
                user_instructions
            )

            # Store only the short, human-friendly prompt as the user message
            st.session_state.messages.append({
                "role": "user",
                "content": short_prompt
            })
            # Store the full LLM prompt for the next LLM call
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

# ... (rest of the code unchanged, including chat logic and LLM call) ...

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
    elif not is_travel_related:
        assistant_response = fallback_message
    else:
        try:
            user_instructions = (
                "IMPORTANT:\n"
                "1. Begin with a friendly, short intro (one line), summarizing trip city, dates, and user interests.\n"
                "2. For each day, use a heading (e.g., 'Day 1: Arrival in Paris').\n"
                "3. For EVERY itinerary item (flight, transfer, hotel, meal, activity, transportation), use a SEPARATE line with:\n"
                "   <emoji> <label>: <details>, ₹<cost> per person [<Link/Info>]\n"
                "   - Always state 'per person' and multiply for total day cost.\n"
                "   - If group size >1, at end of EACH day, show both per person and total costs.\n"
                "4. End every day with 🎯 Daily Total: ₹<per person>/<total for all> on its own line.\n"
                "5. After all days, show a clear, bold cost breakdown table:\n"
                "   - Table columns: Day, Per Person, Group\n"
                "   - Row: Total\n"
                "6. Add a Packing Checklist for the destination in the travel month (based on weather & activities).\n"
                "7. Add Budget Analysis: Is the budget low/medium/high for this trip? Suggest how to adjust if needed.\n"
                "8. Add a friendly Pro Tip at the end.\n"
                "9. Output must be in Markdown, with each heading, bullet, and cost on its own line. Do NOT combine lines. Do NOT summarize days. Do NOT skip any section above."
            )
            messages = [{"role": "system", "content": system_content}] + st.session_state.messages
            messages.append({
                "role": "user",
                "content": f"{currency_instruction}\nFormat your answer in Markdown.\n\n{user_instructions}"
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
            assistant_response = "Sorry, I'm unable to respond at the moment. Try again later."

    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.rerun()

if st.session_state.pending_form_response:
    try:
        messages = [{"role": "system", "content": system_content}] + st.session_state.messages
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

for msg in st.session_state.messages:
    avatar = "https://raw.githubusercontent.com/armanmujtaba/Trivanza/main/trivanza_logo.png" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
