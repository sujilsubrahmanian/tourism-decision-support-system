import os
import sys
import requests
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from supabase import create_client
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

VISUALCROSSING_API_KEY = os.getenv("VISUALCROSSING_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_historical_weather(lat, lon, start_date, end_date):
    url = (
        f"https://weather.visualcrossing.com/VisualCrossingWebServices/"
        f"rest/services/timeline/{lat},{lon}/{start_date}/{end_date}"
    )
    params = {
        "unitGroup": "metric",
        "key": VISUALCROSSING_API_KEY,
        "include": "days",
        "elements": "datetime,temp,tempmax,tempmin,humidity,precip,visibility,windspeed",
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    return data.get("days", [])

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/fetch_historical_weather.py <location_name> [days_back]")
        return

    location_name = sys.argv[1]
    days_back = int(sys.argv[2]) if len(sys.argv) > 2 else 730

    result = supabase.table("locations").select("*").eq("name", location_name).execute()
    if not result.data:
        print(f"No location found matching '{location_name}'. Check the exact name in Supabase.")
        return

    loc = result.data[0]

    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=days_back)

    print(f"Fetching {days_back} days of history for {loc['name']} ({start_date} to {end_date})...")

    days = get_historical_weather(loc["latitude"], loc["longitude"], start_date, end_date)

    if not days:
        print("No historical data returned. Check your API key and location coordinates.")
        return

    saved_count = 0
    for day in days:
        try:
            row = {
                "location_id": loc["id"],
                "date": day["datetime"],
                "temp_avg": day.get("temp"),
                "temp_min": day.get("tempmin"),
                "temp_max": day.get("tempmax"),
                "humidity": day.get("humidity"),
                "rainfall_mm": day.get("precip", 0.0),
                "visibility_km": day.get("visibility"),
                "wind_speed": day.get("windspeed"),
                "collected_at": datetime.now().isoformat(),
            }
            supabase.table("weather_historical").insert(row).execute()
            saved_count += 1
        except Exception as e:
            print(f"  Failed for {day.get('datetime')}: {e}")

    print(f"Done. Saved {saved_count} of {len(days)} days for {loc['name']}.")


if __name__ == "__main__":
    main()