import requests
from dotenv import load_dotenv
import os
load_dotenv()

url = "https://data.cityofchicago.org/resource/ajtu-isnz.json"
headers = {"X-App-Token": os.getenv("SOCRATA_APP_TOKEN", "")}

# Pega o registro mais antigo disponível
params_oldest = {
    "$limit": 1,
    "$order": "trip_start_timestamp ASC"
}
r = requests.get(url, params=params_oldest, headers=headers)
oldest = r.json()
print("Registro mais ANTIGO:", oldest[0].get("trip_start_timestamp") if oldest else "nenhum")

# Pega o registro mais recente disponível
params_newest = {
    "$limit": 1,
    "$order": "trip_start_timestamp DESC"
}
r = requests.get(url, params=params_newest, headers=headers)
newest = r.json()
print("Registro mais RECENTE:", newest[0].get("trip_start_timestamp") if newest else "nenhum")