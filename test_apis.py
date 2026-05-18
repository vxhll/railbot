"""
test_apis.py
Quick smoke-test for all API integrations.
Run this BEFORE launching the Streamlit app to verify your setup.

Usage: python test_apis.py
"""

import json
import os
import sys
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")


def section(title: str):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print("=" * 55)


def ok(msg): print(f"  ✅  {msg}")
def fail(msg): print(f"  ❌  {msg}")
def info(msg): print(f"  ℹ️   {msg}")


# ── Test 1: Environment variables ─────────────────────────────────────────────
section("1. Environment Variables")
if ANTHROPIC_KEY and ANTHROPIC_KEY != "your_anthropic_api_key_here":
    ok(f"ANTHROPIC_API_KEY found (***{ANTHROPIC_KEY[-4:]})")
else:
    fail("ANTHROPIC_API_KEY not set — copy .env.example to .env and add your key")

if RAPIDAPI_KEY and RAPIDAPI_KEY != "your_rapidapi_key_here":
    ok(f"RAPIDAPI_KEY found (***{RAPIDAPI_KEY[-4:]})")
else:
    info("RAPIDAPI_KEY not set — will run in DEMO MODE with mock data")


# ── Test 2: Claude intent extraction ──────────────────────────────────────────
section("2. Claude Intent Extraction")
if not ANTHROPIC_KEY or ANTHROPIC_KEY == "your_anthropic_api_key_here":
    fail("Skipping — no Anthropic key")
else:
    try:
        import claude_engine as claude
        test_msg = "Check availability on train 12951 from NDLS to BCT tomorrow in 3A Tatkal"
        intent = claude.extract_intent(test_msg, [])
        ok(f"Intent extracted: {intent.get('intent')}")
        ok(f"Train: {intent.get('train_number')} | Class: {intent.get('coach_class')} | Quota: {intent.get('quota')}")
        ok(f"Source: {intent.get('source_station')} → Dest: {intent.get('destination_station')}")
        ok(f"Date: {intent.get('travel_date')} | Confidence: {intent.get('confidence')}")
    except Exception as e:
        fail(f"Claude intent extraction failed: {e}")


# ── Test 3: Tatkal window logic ────────────────────────────────────────────────
section("3. Tatkal Window Logic (no API needed)")
try:
    from railways_api import is_tatkal_open
    from datetime import datetime, timedelta

    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y%m%d")
    result_ac = is_tatkal_open(tomorrow, "3A")
    result_sl = is_tatkal_open(tomorrow, "SL")

    ok(f"3A (AC) window: {'OPEN' if result_ac['is_open'] else 'CLOSED'} — opens {result_ac.get('booking_opens')}")
    ok(f"SL (Non-AC) window: {'OPEN' if result_sl['is_open'] else 'CLOSED'} — opens {result_sl.get('booking_opens')}")
except Exception as e:
    fail(f"Tatkal logic error: {e}")


# ── Test 4: Railways API — Seat Availability ───────────────────────────────────
section("4. Railways API — Seat Availability")
from railways_api import get_seat_availability
from datetime import datetime, timedelta

tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y%m%d")
result = get_seat_availability("12951", "NDLS", "BCT", tomorrow, "3A", "GN")

if result.get("_mock"):
    info("Running in DEMO MODE (no RapidAPI key)")
    ok(f"Mock data returned for train {result['data']['trainNumber']}")
    ok(f"Status: {result['data']['availability'][0]['available']}")
    ok(f"Fare: ₹{result['data']['availability'][0]['fare']}")
elif result.get("error"):
    fail(f"API error: {result['error']}")
else:
    ok("Live API call succeeded!")
    print(f"  Raw response: {json.dumps(result, indent=4)[:300]}...")


# ── Test 5: Railways API — PNR Status ─────────────────────────────────────────
section("5. Railways API — PNR Status")
from railways_api import get_pnr_status

result = get_pnr_status("1234567890")

if result.get("_mock"):
    info("Running in DEMO MODE")
    ok(f"Mock PNR: {result['data']['pnrNumber']}")
    ok(f"Train: {result['data']['trainName']} ({result['data']['trainNumber']})")
    ok(f"Status: {result['data']['passengers'][0]['currentStatus']}")
elif result.get("error"):
    fail(f"API error: {result['error']}")
else:
    ok("Live PNR lookup succeeded!")


# ── Test 6: Railways API — Trains between stations ────────────────────────────
section("6. Railways API — Trains Between Stations")
from railways_api import get_trains_between_stations

result = get_trains_between_stations("NDLS", "BCT", tomorrow)

if result.get("_mock"):
    info("Running in DEMO MODE")
    trains = result.get("data", [])
    ok(f"Found {len(trains)} mock trains")
    for t in trains:
        ok(f"  {t['trainNumber']} — {t['trainName']} | Dep: {t['departureTime']} | Dur: {t['duration']}")
elif result.get("error"):
    fail(f"API error: {result['error']}")
else:
    ok("Live train search succeeded!")


# ── Test 7: Full pipeline test ────────────────────────────────────────────────
section("7. Full Pipeline Test (Intent → API → Claude Response)")
if not ANTHROPIC_KEY or ANTHROPIC_KEY == "your_anthropic_api_key_here":
    fail("Skipping — no Anthropic key")
else:
    try:
        from orchestrator import process_user_query
        test_query = "Check seat availability on train 12951 from New Delhi to Mumbai tomorrow in 3A class"
        info(f"Query: {test_query}")
        response, intent = process_user_query(test_query, [])
        ok(f"Intent detected: {intent.get('intent')}")
        ok("Claude response generated successfully")
        print(f"\n  --- RESPONSE PREVIEW ---")
        print(f"  {response[:300]}...")
        print(f"  --- END ---\n")
    except Exception as e:
        fail(f"Pipeline error: {e}")


# ── Summary ───────────────────────────────────────────────────────────────────
section("Summary")
print("  Run the app with:  streamlit run app.py")
if not RAPIDAPI_KEY or RAPIDAPI_KEY == "your_rapidapi_key_here":
    info("Add RAPIDAPI_KEY to .env for live Indian Railways data")
print()
