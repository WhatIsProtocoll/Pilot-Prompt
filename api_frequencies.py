import requests
import json

# Replace with your actual API token from openaip.net
API_KEY = "86b034ac4c62ff44f903c11a35486923"
# icao_code = "62614a361eacded7b7bbdd12"  # Frankfurt Egelsbach
BASE_URL = f"https://api.core.openaip.net/api/airports"

""" headers = {
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
 """

def get_airport_info(icao: str):
    resp = requests.get(
        BASE_URL,
        params={
            "search": icao.upper(),
            "limit": 1,
            "page": 1
            },
        headers={"x-openaip-api-key": API_KEY, "Accept": "application/json"},
    )
    #print("DEBUG resp status:", resp.status_code)
    #print("DEBUG resp json:", resp.json())
    resp.raise_for_status()
    items = resp.json().get("items", [])
    #print(f"DEBUG {icao} response items:", json.dumps(items.get("items", []), indent=2))
    return items[0] if items else None

def get_freqs_from_api(icao: str) -> dict[str, str]:
    # Return {frequency_name: 'value MHz'} or {}.
    info = get_airport_info(icao)
    if not info:
        return {}
    freqs = {}
    for f in info.get("frequencies", []):
        val = f.get("value")
        name = f.get("name", "").strip()
        if name and val:
            freqs[name] = f"{val} MHz"
    return freqs