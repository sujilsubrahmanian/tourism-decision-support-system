import os
from datetime import datetime, date
from dotenv import load_dotenv
from supabase import create_client
from pathlib import Path
from pytrends.request import TrendReq

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

pytrends = TrendReq(hl="en-US", tz=330)

def get_search_interest(location_name):
    pytrends.build_payload([location_name], timeframe="now 7-d", geo="IN")
    data = pytrends.interest_over_time()

    if data.empty:
        return None

    latest_score = int(data[location_name].iloc[-1])
    return latest_score

import time


def main():
    locations = supabase.table("locations").select("*").execute().data

    if not locations:
        print("No locations found in the 'locations' table. Add some first.")
        return

    print(f"Fetching crowd/search interest for {len(locations)} locations...")

    for loc in locations:
        try:
            score = get_search_interest(loc["name"])

            if score is None:
                print(f"  No trend data available for {loc['name']}")
                continue

            today = date.today()

            row = {
                "location_id": loc["id"],
                "date": str(today),
                "search_interest_score": score,
                "day_of_week": today.strftime("%A"),
                "is_holiday": False,
                "collected_at": datetime.now().isoformat(),
            }

            supabase.table("crowd_daily").insert(row).execute()
            print(f"  Saved crowd data for {loc['name']} (score: {score})")

        except Exception as e:
            print(f"  Failed for {loc['name']}: {e}")

        time.sleep(5)

    print("Done.")


if __name__ == "__main__":
    main()