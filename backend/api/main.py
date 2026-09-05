from fastapi import FastAPI
from dotenv import load_dotenv
from supabase import create_client
from pathlib import Path
import os

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Tourism Decision Support System API is running"}


@app.get("/locations")
def get_locations():
    response = supabase.table("locations").select("*").execute()
    return response.data