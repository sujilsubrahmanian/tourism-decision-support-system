import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fixed origin point for all traffic checks — using Delhi as a starting reference
ORIGIN_LAT = 28.6139
ORIGIN_LNG = 77.2090

def get_traffic(dest_lat, dest_lng):
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{ORIGIN_LAT},{ORIGIN_LNG}",
        "destination": f"{dest_lat},{dest_lng}",
        "departure_time": "now",
        "key": GOOGLE_MAPS_API_KEY,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if data["status"] != "OK":
        raise Exception(f"Google Directions returned status: {data['status']} — {data.get('error_message', 'no additional message')}")
    
    leg = data["routes"][0]["legs"][0]

    normal_duration_min = leg["duration"]["value"] / 60
    traffic_duration_min = leg.get("duration_in_traffic", leg["duration"])["value"] / 60
    distance_km = leg["distance"]["value"] / 1000
    congestion_ratio = traffic_duration_min / normal_duration_min

    return {
        "normal_duration_min": normal_duration_min,
        "traffic_duration_min": traffic_duration_min,
        "congestion_ratio": congestion_ratio,
        "distance_km": distance_km,
    }
    
def main():
    locations = supabase.table("locations").select("*").execute().data

    if not locations:
        print("No locations found in the 'locations' table. Add some first.")
        return

    print(f"Fetching traffic for {len(locations)} locations...")

    for loc in locations:
        try:
            traffic = get_traffic(loc["latitude"], loc["longitude"])

            row = {
                "location_id": loc["id"],
                "collected_at": datetime.now().isoformat(),
                **traffic,
            }

            supabase.table("traffic_snapshots").insert(row).execute()
            print(f"  Saved traffic for {loc['name']}")

        except Exception as e:
            print(f"  Failed for {loc['name']}: {e}")

    print("Done.")


if __name__ == "__main__":
    main()