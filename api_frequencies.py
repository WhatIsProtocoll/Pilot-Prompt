import requests
import json

# Replace with your actual API token from openaip.net
API_KEY = "86b034ac4c62ff44f903c11a35486923"
icao_code = "62614a361eacded7b7bbdd12"  # Frankfurt Egelsbach

BASE_URL = f"https://api.core.openaip.net/api/airports/{icao_code}"

headers = {
    "x-openaip-api-key": API_KEY,
    "Accept": "application/json"
}

response = requests.get(BASE_URL, headers=headers)

if response.status_code == 200:
    data = response.json()

    print(f"Frequencies for {data.get('name')} ({data.get('icaoCode')}):")
    for freq in data.get("frequencies", []):
        freq_type = freq.get("name", "Unknown")
        value = freq.get("value", "N/A")
        primary = "(Primary)" if freq.get("primary", False) else ""
        print(f"• {freq_type}: {value} MHz {primary}")
else:
    print("Error:", response.status_code, response.text)