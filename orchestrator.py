"""
orchestrator.py
Wires together: Claude intent extraction → Railways API → Claude response.
This is the main brain that decides which API to call based on intent.
"""

from datetime import datetime, timedelta
from typing import Optional
import claude_engine as claude
import railways_api as api


def get_tomorrow() -> str:
    return (datetime.now() + timedelta(days=1)).strftime("%Y%m%d")


def process_user_query(user_message: str, conversation_history: list) -> tuple[str, dict]:
    """
    Main pipeline:
    1. Extract intent from user message
    2. Call the right Railways API
    3. Generate Claude response grounded in real data
    
    Returns: (response_text, intent_dict)
    """
    # Step 1: Extract intent
    intent = claude.extract_intent(user_message, conversation_history)
    intent_type = intent.get("intent", "unknown")

    api_data = None
    api_type = ""
    tatkal_window = None

    # Step 2: Route to appropriate API call
    # Handle general questions and unrecognised intents without an API call
    if intent_type in ("general_question", "unknown"):
        response = claude.get_general_response(user_message, conversation_history)
        return response, intent

    if intent_type == "pnr_status":
        pnr = intent.get("pnr_number")
        if not pnr:
            response = claude.get_general_response(
                user_message + "\n\n[System: PNR number not found in message. Ask user for their 10-digit PNR number.]",
                conversation_history,
            )
            return response, intent
        api_data = api.get_pnr_status(pnr)
        api_type = "pnr_status"

    elif intent_type == "check_availability":
        train_no = intent.get("train_number")
        src = intent.get("source_station")
        dst = intent.get("destination_station")
        date = intent.get("travel_date") or get_tomorrow()
        cls = intent.get("coach_class") or "SL"
        quota = intent.get("quota") or "GN"

        # Check if we have enough info
        missing = []
        if not train_no:
            missing.append("train number")
        if not src:
            missing.append("source station")
        if not dst:
            missing.append("destination station")

        if missing:
            hint = f"[System: Missing fields for availability check: {', '.join(missing)}. Ask user for these.]"
            response = claude.get_general_response(
                user_message + f"\n\n{hint}", conversation_history
            )
            return response, intent

        # Check Tatkal window if quota is TQ
        if quota == "TQ":
            tatkal_window = api.is_tatkal_open(date, cls)

        api_data = api.get_seat_availability(train_no, src, dst, date, cls, quota)
        api_type = "seat_availability"

    elif intent_type == "trains_between_stations":
        src = intent.get("source_station")
        dst = intent.get("destination_station")
        date = intent.get("travel_date") or get_tomorrow()

        if not src or not dst:
            hint = "[System: Missing source or destination station. Ask user to specify both stations.]"
            response = claude.get_general_response(
                user_message + f"\n\n{hint}", conversation_history
            )
            return response, intent

        api_data = api.get_trains_between_stations(src, dst, date)
        api_type = "trains_between_stations"

    elif intent_type == "train_schedule":
        train_no = intent.get("train_number")
        if not train_no:
            hint = "[System: Train number not found. Ask user for the train number.]"
            response = claude.get_general_response(
                user_message + f"\n\n{hint}", conversation_history
            )
            return response, intent

        api_data = api.get_train_schedule(train_no)
        api_type = "train_schedule"

    elif intent_type == "tatkal_info":
        # Purely informational — check window if we have enough context
        cls = intent.get("coach_class") or "SL"
        date = intent.get("travel_date") or get_tomorrow()
        tatkal_window = api.is_tatkal_open(date, cls)
        api_type = "tatkal_info"

    # Step 3: Generate Claude response using API data as context
    response = claude.generate_response(
        user_message=user_message,
        api_data=api_data,
        api_type=api_type,
        conversation_history=conversation_history,
        intent=intent,
        tatkal_window=tatkal_window,
    )

    return response, intent
