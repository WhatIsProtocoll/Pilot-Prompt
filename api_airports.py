import requests
import json

API_KEY = "86b034ac4c62ff44f903c11a35486923"
icao_code = "EDFE"  # example input

BASE_URL = "https://api.core.openaip.net/api/airports"

headers = {
    "x-openaip-api-key": API_KEY,
    "Accept": "application/json"
}

params = {
    "filter[icaoCode]": icao_code,
    "filter[country]": "DE"
}

response = requests.get(BASE_URL, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2))
    airports = data.get("airports", [])
    if airports:
        airport = airports[0]
        print(f"Name: {airport['name']}")
        print(f"ICAO: {airport['icaoCode']}")
        print(f"Airport ID: {airport['_id']}")
    else:
        print("No airport found for ICAO code:", icao_code)
else:
    print("Error:", response.status_code, response.text)