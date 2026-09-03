import os
import requests
from datetime import datetime, date
from dotenv import load_dotenv
from supabase import create_client
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

AQICN_TOKEN = os.getenv("AQICN_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_aqi(lat, lon):
    url = f"https://api.waqi.info/feed/geo:{lat};{lon}/"
    params = {
        "token": AQICN_TOKEN,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if data["status"] != "ok":
        raise Exception(f"AQICN returned status: {data['status']}")

    iaqi = data["data"].get("iaqi", {})

    return {
        "aqi_value": data["data"]["aqi"],
        "pm25": iaqi.get("pm25", {}).get("v"),
        "pm10": iaqi.get("pm10", {}).get("v"),
    }
    
def main():
    locations = supabase.table("locations").select("*").execute().data

    if not locations:
        print("No locations found in the 'locations' table. Add some first.")
        return

    print(f"Fetching AQI for {len(locations)} locations...")

    for loc in locations:
        try:
            aqi = get_aqi(loc["latitude"], loc["longitude"])

            row = {
                "location_id": loc["id"],
                "date": str(date.today()),
                "collected_at": datetime.now().isoformat(),
                **aqi,
            }

            supabase.table("air_quality_daily").insert(row).execute()
            print(f"  Saved AQI for {loc['name']}")

        except Exception as e:
            print(f"  Failed for {loc['name']}: {e}")

    print("Done.")


if __name__ == "__main__":
    main()