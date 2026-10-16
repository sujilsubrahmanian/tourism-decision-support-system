import os
import time
import requests
import pandas as pd
from datetime import date, timedelta
from dotenv import load_dotenv
from supabase import create_client
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def get_aq_range(lat, lon, start, end):
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "hourly": "pm2_5,pm10,us_aqi",
        "timezone": "Asia/Kolkata",
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    h = response.json()["hourly"]

    df = pd.DataFrame({
        "time": pd.to_datetime(h["time"]),
        "pm25": h["pm2_5"],
        "pm10": h["pm10"],
        "aqi": h["us_aqi"],
    })
    df["date"] = df["time"].dt.date.astype(str)

    daily = df.groupby("date").agg(
        pm25_mean=("pm25", "mean"),
        pm10_mean=("pm10", "mean"),
        aqi_mean=("aqi", "mean"),
        aqi_max=("aqi", "max"),
    ).reset_index()
    return daily

def year_chunks(start, end):
    chunks = []
    current = start
    while current <= end:
        chunk_end = min(date(current.year, 12, 31), end)
        chunks.append((str(current), str(chunk_end)))
        current = chunk_end + timedelta(days=1)
    return chunks


def main():
    locations = supabase.table("locations").select("*").execute().data

    start = date(2022, 8, 1)
    end = date.today() - timedelta(days=2)
    chunks = year_chunks(start, end)

    for loc in locations:
        total = 0
        try:
            for c_start, c_end in chunks:
                daily = get_aq_range(loc["latitude"], loc["longitude"], c_start, c_end)
                daily = daily.astype(object).where(daily.notna(), None)

                rows = daily.to_dict("records")
                for r in rows:
                    r["location_id"] = loc["id"]

                for i in range(0, len(rows), 1000):
                    supabase.table("air_quality_archive").upsert(
                        rows[i:i + 1000], on_conflict="location_id,date"
                    ).execute()

                total += len(rows)
                time.sleep(5)

            print(f"  Saved {total} days for {loc['name']}")

        except Exception as e:
            print(f"  Failed for {loc['name']}: {e}")

        time.sleep(10)

    print("Done.")


if __name__ == "__main__":
    main()