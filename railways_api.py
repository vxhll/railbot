"""
railways_api.py
Indian Railways API client using RapidAPI.
Handles seat availability, Tatkal quota, PNR status.
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")

# RapidAPI base URLs — using "Indian Railway Irctc" API (free tier)
BASE_URL = "https://indian-railway-irctc.p.rapidapi.com"
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "indian-railway-irctc.p.rapidapi.com",
}

# Dedicated PNR status API — more reliable for live PNR lookups
PNR_HOST = "irctc-indian-railway-pnr-status.p.rapidapi.com"
PNR_HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": PNR_HOST,
    "x-rapidapi-key": RAPIDAPI_KEY,
}

# ── Tatkal window logic ────────────────────────────────────────────────────────
TATKAL_WINDOWS = {
    # AC classes open 1 day prior at 10:00 AM IST
    "AC": {"days_prior": 1, "open_hour": 10, "open_minute": 0},
    # Non-AC classes open 1 day prior at 11:00 AM IST
    "NON_AC": {"days_prior": 1, "open_hour": 11, "open_minute": 0},
}
AC_CLASSES = {"1A", "2A", "3A", "CC", "EC"}
NON_AC_CLASSES = {"SL", "2S", "FC"}


def is_tatkal_open(travel_date_str: str, coach_class: str) -> dict:
    """
    Check if Tatkal booking window is currently open.
    travel_date_str: 'YYYYMMDD' or 'YYYY-MM-DD'
    Returns dict with open status and explanation.
    """
    try:
        travel_date_str = travel_date_str.replace("-", "")
        travel_date = datetime.strptime(travel_date_str, "%Y%m%d")
        now = datetime.now()
        coach_upper = coach_class.upper()

        if coach_upper in AC_CLASSES:
            window = TATKAL_WINDOWS["AC"]
            class_type = "AC"
        else:
            window = TATKAL_WINDOWS["NON_AC"]
            class_type = "Non-AC"

        booking_opens = travel_date - timedelta(days=window["days_prior"])
        booking_opens = booking_opens.replace(
            hour=window["open_hour"], minute=window["open_minute"], second=0
        )
        booking_closes = travel_date.replace(hour=23, minute=59)

        is_open = booking_opens <= now <= booking_closes

        return {
            "is_open": is_open,
            "class_type": class_type,
            "booking_opens": booking_opens.strftime("%d %b %Y at %I:%M %p IST"),
            "booking_closes": booking_closes.strftime("%d %b %Y at %I:%M %p IST"),
            "current_time": now.strftime("%d %b %Y %I:%M %p"),
            "message": (
                f"Tatkal booking for {class_type} class ({coach_class}) is currently OPEN."
                if is_open
                else f"Tatkal booking for {class_type} class ({coach_class}) opens on {booking_opens.strftime('%d %b %Y at %I:%M %p IST')}."
            ),
        }
    except Exception as e:
        return {"error": str(e), "is_open": False}


# ── API Calls ─────────────────────────────────────────────────────────────────

def get_seat_availability(
    train_number: str,
    source_station: str,
    destination_station: str,
    travel_date: str,
    coach_class: str,
    quota: str = "GN",
) -> dict:
    """
    Fetch seat availability for a specific train, route, date, class, quota.
    travel_date: YYYYMMDD format
    quota: GN (General), TQ (Tatkal), LD (Ladies), etc.
    """
    if not RAPIDAPI_KEY:
        return _mock_availability(train_number, source_station, destination_station, travel_date, coach_class, quota)

    travel_date = travel_date.replace("-", "")

    url = f"{BASE_URL}/api/v3/checkSeatAvailability"
    params = {
        "trainNo": train_number,
        "fromStationCode": source_station.upper(),
        "toStationCode": destination_station.upper(),
        "dateOfJourney": travel_date,
        "classType": coach_class.upper(),
        "quota": quota.upper(),
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        data["_api_called"] = True
        data["_params"] = params
        return data
    except requests.exceptions.HTTPError as e:
        return {"error": f"API Error {e.response.status_code}: {e.response.text}", "_api_called": False}
    except requests.exceptions.Timeout:
        return {"error": "API request timed out. Please try again.", "_api_called": False}
    except Exception as e:
        return {"error": str(e), "_api_called": False}


def get_pnr_status(pnr_number: str) -> dict:
    """
    Fetch PNR status using the dedicated IRCTC PNR Status API.
    Falls back to mock data if no API key is configured.
    """
    if not RAPIDAPI_KEY:
        return _mock_pnr(pnr_number)

    pnr = pnr_number.strip()
    url = f"https://{PNR_HOST}/getPNRStatus/{pnr}"

    try:
        response = requests.get(url, headers=PNR_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        data["_api_called"] = True
        return data
    except requests.exceptions.HTTPError as e:
        return {"error": f"API Error {e.response.status_code}: {e.response.text}", "_api_called": False}
    except requests.exceptions.Timeout:
        return {"error": "API request timed out. Please try again.", "_api_called": False}
    except Exception as e:
        return {"error": str(e), "_api_called": False}


def get_trains_between_stations(
    source: str, destination: str, travel_date: str
) -> dict:
    """Fetch list of trains between two stations on a given date."""
    if not RAPIDAPI_KEY:
        return _mock_trains(source, destination, travel_date)

    travel_date = travel_date.replace("-", "")
    url = f"{BASE_URL}/api/v3/trainBetweenStation"
    params = {
        "fromStationCode": source.upper(),
        "toStationCode": destination.upper(),
        "dateOfJourney": travel_date,
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        data["_api_called"] = True
        return data
    except requests.exceptions.HTTPError as e:
        return {"error": f"API Error {e.response.status_code}: {e.response.text}", "_api_called": False}
    except requests.exceptions.Timeout:
        return {"error": "API request timed out. Please try again.", "_api_called": False}
    except Exception as e:
        return {"error": str(e), "_api_called": False}


def get_train_schedule(train_number: str) -> dict:
    """Fetch the full schedule/route for a train."""
    if not RAPIDAPI_KEY:
        return _mock_schedule(train_number)

    url = f"{BASE_URL}/api/v1/getTrainSchedule"
    params = {"trainNo": train_number}

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        data["_api_called"] = True
        return data
    except requests.exceptions.HTTPError as e:
        return {"error": f"API Error {e.response.status_code}: {e.response.text}", "_api_called": False}
    except requests.exceptions.Timeout:
        return {"error": "API request timed out. Please try again.", "_api_called": False}
    except Exception as e:
        return {"error": str(e), "_api_called": False}


# ── Mock / Demo data (used when no API key is configured) ─────────────────────

def _mock_availability(train_no, src, dst, date, cls, quota):
    return {
        "_api_called": False,
        "_mock": True,
        "status": True,
        "data": {
            "trainNumber": train_no,
            "trainName": "RAJDHANI EXPRESS",
            "fromStation": src.upper(),
            "toStation": dst.upper(),
            "journeyDate": date,
            "classType": cls.upper(),
            "quota": quota.upper(),
            "availability": [
                {"date": date, "available": "AVAILABLE-42", "fare": 1850},
                {"date": date, "available": "AVAILABLE-28", "fare": 1850},
            ],
            "tatkalFare": 2405 if cls.upper() in AC_CLASSES else 1250,
        },
        "message": "DEMO MODE — add RapidAPI key for live data",
    }


def _mock_pnr(pnr):
    return {
        "_api_called": False,
        "_mock": True,
        "status": True,
        "data": {
            "pnrNumber": pnr,
            "trainNumber": "12951",
            "trainName": "MUMBAI RAJDHANI",
            "journeyDate": "25-Mar-2026",
            "fromStation": "NDLS",
            "toStation": "BCT",
            "classType": "3A",
            "chartStatus": "CHART PREPARED",
            "passengers": [
                {
                    "no": 1,
                    "bookingStatus": "S5,42,LOWER",
                    "currentStatus": "S5,42,LOWER",
                    "coachPosition": 5,
                }
            ],
            "fare": 1850,
        },
        "message": "DEMO MODE — add RapidAPI key for live data",
    }


def _mock_trains(src, dst, date):
    return {
        "_api_called": False,
        "_mock": True,
        "status": True,
        "data": [
            {
                "trainNumber": "12951",
                "trainName": "MUMBAI RAJDHANI",
                "fromStationCode": src.upper(),
                "toStationCode": dst.upper(),
                "departureTime": "16:25",
                "arrivalTime": "08:15",
                "duration": "15h 50m",
                "runningDays": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
                "classes": ["1A", "2A", "3A"],
            },
            {
                "trainNumber": "12953",
                "trainName": "GUJARAT QUEEN",
                "fromStationCode": src.upper(),
                "toStationCode": dst.upper(),
                "departureTime": "22:05",
                "arrivalTime": "14:30",
                "duration": "16h 25m",
                "runningDays": ["MON", "WED", "FRI"],
                "classes": ["2A", "3A", "SL"],
            },
        ],
        "message": "DEMO MODE — add RapidAPI key for live data",
    }


def _mock_schedule(train_no):
    return {
        "_api_called": False,
        "_mock": True,
        "status": True,
        "data": {
            "trainNumber": train_no,
            "trainName": "RAJDHANI EXPRESS",
            "schedule": [
                {"stationCode": "NDLS", "stationName": "NEW DELHI", "arrivalTime": "--", "departureTime": "16:25", "haltTime": "--", "distance": 0},
                {"stationCode": "MTJ", "stationName": "MATHURA JN", "arrivalTime": "18:18", "departureTime": "18:20", "haltTime": "2m", "distance": 141},
                {"stationCode": "BCT", "stationName": "MUMBAI CENTRAL", "arrivalTime": "08:15", "departureTime": "--", "haltTime": "--", "distance": 1384},
            ],
        },
        "message": "DEMO MODE — add RapidAPI key for live data",
    }
