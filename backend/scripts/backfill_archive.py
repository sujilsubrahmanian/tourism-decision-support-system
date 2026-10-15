import requests
from datetime import date, timedelta
from dotenv import load_dotenv
from supabase import create_client
from pathlib import Path
import os
import time

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def get_archive(lat, lon, start_date, end_date):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,wind_speed_10m_max",
        "timezone": "Asia/Kolkata",
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()["daily"]

def main():
    locations = supabase.table("locations").select("*").execute().data

    start_date = "2016-01-01"
    end_date = str(date.today() - timedelta(days=7))

    for loc in locations:
        try:
            daily = get_archive(loc["latitude"], loc["longitude"], start_date, end_date)

            rows = []
            for i in range(len(daily["time"])):
                rows.append({
                    "location_id": loc["id"],
                    "date": daily["time"][i],
                    "temp_max": daily["temperature_2m_max"][i],
                    "temp_min": daily["temperature_2m_min"][i],
                    "temp_mean": daily["temperature_2m_mean"][i],
                    "rainfall_mm": daily["precipitation_sum"][i],
                    "wind_max": daily["wind_speed_10m_max"][i],
                })

            for start in range(0, len(rows), 1000):
                chunk = rows[start:start + 1000]
                supabase.table("weather_archive").upsert(
                    chunk, on_conflict="location_id,date"
                ).execute()

            print(f"  Saved {len(rows)} days for {loc['name']}")

        except Exception as e:
            print(f"  Failed for {loc['name']}: {e}")
            
        time.sleep(15)

    print("Done.")


if __name__ == "__main__":
    main()