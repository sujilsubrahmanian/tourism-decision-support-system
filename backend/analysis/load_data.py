import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def fetch_table(table_name, page_size=1000):
    all_rows = []
    start = 0
    while True:
        response = (
            supabase.table(table_name)
            .select("*")
            .range(start, start + page_size - 1)
            .execute()
        )
        rows = response.data
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < page_size:
            break
        start += page_size
    return pd.DataFrame(all_rows)


if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    for name in ["locations", "weather_archive", "air_quality_archive",
                 "crowd_weekly", "weather_historical", "weather_daily",
                 "air_quality_daily", "crowd_daily"]:
        df = fetch_table(name)
        df.to_csv(data_dir / f"{name}.csv", index=False)
        print(f"{name}: {len(df)} rows saved")