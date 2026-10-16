import os
import time
from dotenv import load_dotenv
from supabase import create_client
from pathlib import Path
from pytrends.request import TrendReq

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
pytrends = TrendReq(hl="en-US", tz=330)

SEARCH_TERMS = {
    "Munnar": "Munnar",
    "Taj Mahal": "Taj Mahal",
    "Jaisalmer": "Jaisalmer",
    "Cherrapunji": "Cherrapunji",
    "India Gate": "India Gate Delhi",
    "Athirappilly Falls": "Athirappilly Falls",
    "Alleppey": "Alleppey",
    "Mysore Palace": "Mysore Palace",
}

def get_interest(term):
    for attempt in range(4):
        try:
            pytrends.build_payload([term], timeframe="today 5-y", geo="IN")
            df = pytrends.interest_over_time()
            if df.empty:
                return None
            df = df[df["isPartial"] == False]
            return df[term]
        except Exception as e:
            wait = 60 * (attempt + 1)
            print(f"    Attempt {attempt + 1} failed ({e}); waiting {wait}s...")
            time.sleep(wait)
    return None

def main():
    locations = supabase.table("locations").select("*").execute().data

    for loc in locations:
        existing = (
            supabase.table("crowd_weekly")
            .select("id")
            .eq("location_id", loc["id"])
            .limit(1)
            .execute()
            .data
        )
        if existing:
            print(f"  Skipping {loc['name']} (already loaded)")
            continue

        term = SEARCH_TERMS.get(loc["name"], loc["name"])
        series = get_interest(term)

        if series is None:
            print(f"  No data for {loc['name']} - rerun later")
            continue

        rows = [
            {
                "location_id": loc["id"],
                "week_start": str(week.date()),
                "interest": int(value),
            }
            for week, value in series.items()
        ]
        supabase.table("crowd_weekly").upsert(
            rows, on_conflict="location_id,week_start"
        ).execute()
        print(f"  Saved {len(rows)} weeks for {loc['name']}")

        time.sleep(30)

    print("Done.")


if __name__ == "__main__":
    main()