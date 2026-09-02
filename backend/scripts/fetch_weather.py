import os
import requests
from datetime import datetime, date
from dotenv import load_dotenv
from supabase import create_client

from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("URL:", SUPABASE_URL)
print("KEY:", SUPABASE_KEY)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_weather(lat, lon):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    return {
        "temp_avg": data["main"]["temp"],
        "temp_min": data["main"]["temp_min"],
        "temp_max": data["main"]["temp_max"],
        "humidity": data["main"]["humidity"],
        "rainfall_mm": data.get("rain", {}).get("1h", 0.0),
        "visibility_km": data.get("visibility", 10000) / 1000,
        "wind_speed": data["wind"]["speed"],
    }


def main():
    locations = supabase.table("locations").select("*").execute().data

    if not locations:
        print("No locations found in the 'locations' table. Add some first.")
        return

    print(f"Fetching weather for {len(locations)} locations...")

    for loc in locations:
        try:
            weather = get_weather(loc["latitude"], loc["longitude"])

            row = {
                "location_id": loc["id"],
                "date": str(date.today()),
                "collected_at": datetime.now().isoformat(),
                **weather,
            }

            supabase.table("weather_daily").insert(row).execute()
            print(f"  Saved weather for {loc['name']}")

        except Exception as e:
            print(f"  Failed for {loc['name']}: {e}")

    print("Done.")


if __name__ == "__main__":
    main()