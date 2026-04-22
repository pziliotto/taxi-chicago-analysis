import requests
from dotenv import load_dotenv
import os

load_dotenv()

url = "https://data.cityofchicago.org/resource/ajtu-isnz.json"
headers = {"X-App-Token": os.getenv("SOCRATA_APP_TOKEN", "")}
params = {
    "$where": "trip_start_timestamp >= '2022-01-01T00:00:00' AND trip_start_timestamp < '2022-02-01T00:00:00'",
    "$limit": 5,
    "$order": "trip_start_timestamp ASC"
}
r = requests.get(url, params=params, headers=headers)
print("Status:", r.status_code)
print("Resposta:", r.text[:500])