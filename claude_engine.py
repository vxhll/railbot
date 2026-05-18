"""
claude_engine.py
Handles all Claude AI interactions:
  1. Intent extraction from user messages → structured JSON
  2. Final conversational response using real API data as context
"""

import os
import json
import re
from datetime import datetime
from typing import Optional
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

# ── System prompts ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are RailBot, a friendly and knowledgeable Indian Railways assistant.

You help users with:
- Seat availability (General and Tatkal quota)
- PNR status lookup
- Train schedules and trains between stations
- Tatkal booking windows and surcharges

CRITICAL RULES:
1. NEVER answer availability or PNR questions from your own knowledge. Always rely on the API data provided to you.
2. When API data is provided in <api_data> tags, base your answer ONLY on that data.
3. If asked about seat availability, ALWAYS mention: available seats, fare, and Tatkal surcharge if applicable.
4. For Tatkal queries, always mention the booking window timing: AC classes open 1 day prior at 10:00 AM IST, Non-AC at 11:00 AM IST.
5. Be concise but complete. Use bullet points for structured data like passenger lists.
6. If the API returned an error, explain it politely and suggest what the user can try.
7. Always quote the train number and name, source→destination, date, and class in your answer.
8. Format fares in Indian Rupees (₹).
9. If operating in DEMO MODE (mock data), clearly mention this to the user.

Station codes for common cities (help users if they use city names):
- New Delhi: NDLS | Mumbai Central: BCT | Mumbai CSMT: CSTM
- Howrah: HWH | Chennai Central: MAS | Bangalore: SBC | SMVB
- Pune: PUNE | Ahmedabad: ADI | Hyderabad: HYB | Secunderabad: SC
- Jaipur: JP | Lucknow: LKO | Patna: PNBE | Varanasi: BSB

Quota codes: GN=General, TQ=Tatkal, LD=Ladies, HP=Handicapped, SS=Senior Citizen

Always be warm, helpful, and use 🚆 emoji sparingly for personality."""


INTENT_EXTRACTION_PROMPT_TEMPLATE = """You are a JSON intent extractor for an Indian Railways chatbot. 
Extract structured intent from the user message.

Return ONLY valid JSON, no markdown fences, no explanation.

JSON schema:
{{
  "intent": one of ["check_availability", "pnr_status", "trains_between_stations", "train_schedule", "tatkal_info", "general_question", "unknown"],
  "train_number": string or null,
  "source_station": string (station code like NDLS) or null,
  "destination_station": string (station code like BCT) or null,
  "travel_date": "YYYYMMDD" or null (default to tomorrow if not specified and intent needs a date),
  "coach_class": one of ["1A","2A","3A","SL","CC","EC","2S","FC"] or null,
  "quota": one of ["GN","TQ","LD","HP","SS"] or null (default "GN" if not specified),
  "pnr_number": string (10 digits) or null,
  "confidence": "high" or "low"
}}

Rules:
- Convert city names to station codes: Delhi→NDLS, Mumbai→BCT or CSTM, Kolkata→HWH, Chennai→MAS, Bangalore→SBC, Hyderabad→SC
- If user says "Tatkal", set quota to "TQ"
- If user says "sleeper", set coach_class to "SL"; "AC 3 tier" or "3A" → "3A"; "AC 2 tier" → "2A"; "first class" or "1A" → "1A"
- For dates: "tomorrow" = tomorrow's date, "day after tomorrow" = 2 days from now
- Today's date is: {today}
- If no date given for availability checks, use tomorrow's date
- Extract 10-digit PNR numbers carefully"""


# ── Public functions ───────────────────────────────────────────────────────────

def extract_intent(user_message: str, conversation_history: list) -> dict:
    """
    Use Claude to parse the user's message into structured intent JSON.
    Returns a dict with the extracted fields.
    """
    # Build context from recent history for better intent extraction
    context = ""
    if conversation_history:
        recent = conversation_history[-4:]  # last 2 turns
        for msg in recent:
            role = msg["role"].upper()
            content = msg["content"] if isinstance(msg["content"], str) else "[data]"
            context += f"{role}: {content[:200]}\n"

    full_prompt = f"Conversation context:\n{context}\n\nCurrent user message: {user_message}"

    # Build prompt with today's current date (evaluated per call, not at import)
    intent_prompt = INTENT_EXTRACTION_PROMPT_TEMPLATE.format(
        today=datetime.now().strftime("%Y-%m-%d")
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=intent_prompt,
            messages=[{"role": "user", "content": full_prompt}],
        )
        raw = response.content[0].text.strip()
        # Strip any accidental markdown fences
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"```$", "", raw).strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"intent": "unknown", "confidence": "low"}
    except anthropic.APIError as e:
        return {"intent": "unknown", "error": str(e), "confidence": "low"}


def generate_response(
    user_message: str,
    api_data: Optional[dict],
    api_type: str,
    conversation_history: list,
    intent: dict,
    tatkal_window: Optional[dict] = None,
) -> str:
    """
    Generate a conversational response using Claude, grounded in real API data.
    
    api_data: raw data returned from the railways API
    api_type: label like "seat_availability", "pnr_status", etc.
    tatkal_window: result of is_tatkal_open() if relevant
    """
    # Build the context block for Claude
    context_parts = []

    if api_data:
        is_mock = api_data.get("_mock", False)
        demo_note = "\n⚠️ NOTE: This is DEMO/MOCK data. Real data requires a valid RapidAPI key." if is_mock else ""
        context_parts.append(
            f"<api_data type='{api_type}'>{demo_note}\n{json.dumps(api_data, indent=2)}\n</api_data>"
        )

    if tatkal_window:
        context_parts.append(
            f"<tatkal_window>{json.dumps(tatkal_window, indent=2)}</tatkal_window>"
        )

    if intent:
        context_parts.append(
            f"<extracted_intent>{json.dumps(intent, indent=2)}</extracted_intent>"
        )

    context_block = "\n\n".join(context_parts)

    # Build message history for multi-turn memory
    messages = list(conversation_history)  # full history
    messages.append({
        "role": "user",
        "content": f"{user_message}\n\n{context_block}" if context_block else user_message,
    })

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        return response.content[0].text
    except anthropic.APIError as e:
        return f"❌ I encountered an error connecting to AI: {str(e)}\n\nPlease check your Anthropic API key and try again."


def get_general_response(user_message: str, conversation_history: list) -> str:
    """For general questions that don't need an API call."""
    messages = list(conversation_history)
    messages.append({"role": "user", "content": user_message})
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        return response.content[0].text
    except anthropic.APIError as e:
        return f"❌ Error: {str(e)}"
