import json
from geopy.point import Point
from shapely.geometry import Point as ShapelyPoint
import geopandas as gpd
from collections import OrderedDict, defaultdict
import matplotlib.pyplot as plt


with open("openaip_data/de_apt.geojson", "r") as file:
    airport = json.load(file)

def get_airport_by_icao(icao_code, geojson):
    for feature in geojson["features"]:
        props = feature.get("properties", {})
        if props.get("icaoCode") == icao_code.upper():
            return feature  
    return None

def get_frequencies(feature):
    props = feature.get("properties", {})
    frequencies = props.get("frequencies", [])
    freq_dict = OrderedDict()

    for freq in frequencies:
        name = freq.get("name", "").strip()
        value = freq.get("value", "").strip()
        if name and value and name not in freq_dict:
            freq_dict[name] = f"{value} MHz"

    return freq_dict

def get_lat_lon(feature):
    coords = feature.get("geometry", {}).get("coordinates", [])
    if coords and len(coords) >= 2:
        return coords[0], coords[1]  # ✅ lon, lat
    return None, None

def generate_route_points(start, end, num_points: int = 20):
    # Assuming Shapely points: start.x = lon, start.y = lat
    lat_steps = [
        start.y + i * (end.y - start.y) / num_points
        for i in range(num_points + 1)
    ]
    lon_steps = [
        start.x + i * (end.x - start.x) / num_points
        for i in range(num_points + 1)
    ]
    route_points = [ShapelyPoint(lon, lat) for lon, lat in zip(lon_steps, lat_steps)]
    
    return route_points

def plot_route_over_fis(route_points, fis_airspaces, dep_icao="DEP", arr_icao="ARR"):
    import matplotlib.pyplot as plt
    import geopandas as gpd

    # Create a GeoDataFrame from route points
    route_gdf = gpd.GeoDataFrame(geometry=route_points, crs="EPSG:4326")

    # Plot FIS polygons
    ax = fis_airspaces.plot(edgecolor='blue', facecolor='lightblue', figsize=(8, 10), alpha=0.4)

    # Plot route points
    route_gdf.plot(ax=ax, color='red', markersize=20, label="Route Points")

    plt.title("Route over FIS Airspaces")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.legend()
    plt.grid(True)

    # Generate dynamic filename
    filename = f"route_{dep_icao.upper()}_{arr_icao.upper()}.png"
    plt.savefig(filename, dpi=300)
    print(f"Plot saved as {filename}")

# Ensure enroute frequencies are ordered and unique
def get_ordered_frequencies(route_points, fis_airspaces):
    freq_dict = OrderedDict()

    for point in route_points:
        buffered = point.buffer(0.01)
        matches = fis_airspaces[fis_airspaces.geometry.intersects(buffered)]

        for _, row in matches.iterrows():
            freqs_raw = row.get("frequencies", [])
            freqs = safe_parse_frequencies(freqs_raw)

            for freq_obj in freqs:
                name = freq_obj.get("name", "").strip()
                value = freq_obj.get("value", "").strip()

                # Skip if name or value is missing or name is UNKNOWN
                if not name or not value or name.upper() == "UNKNOWN":
                    continue

                key = (name, value)
                if key not in freq_dict:
                    freq_dict[key] = {
                        "name": name,
                        "frequency": f"{value} MHz",
                        "phase": "Enroute / Cruise"  # Default phase label
                    }
    return freq_dict

'''
def get_intersected_frequencies(route_points, fis_airspaces):
    intersected_freqs = set()

    for point in route_points:
        buffered = point.buffer(0.01)
        matches = fis_airspaces[fis_airspaces.geometry.intersects(buffered)]
        print(f"Point {point} intersects {len(matches)} FIS polygons")

        for _, row in matches.iterrows():
            print(f"Raw frequencies: {row.get('frequencies')}")
            freqs_raw = row.get("frequencies", [])
            freqs = safe_parse_frequencies(freqs_raw)

            for freq_obj in freqs:
                name = freq_obj.get("name", "UNKNOWN")
                value = freq_obj.get("value")
                if value:
                    intersected_freqs.add(f"{name}: {value} MHz")

    return intersected_freqs
'''

# Ensure frequencies are parsed safely
def safe_parse_frequencies(freq_data):
    if isinstance(freq_data, list):
        return freq_data
    elif isinstance(freq_data, str):
        try:
            parsed = json.loads(freq_data)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            return []
    return []

# This function extracts specific frequency roles based on common patterns
def extract_frequency_roles(dep_freqs, arr_freqs, enroute_freqs):
    roles = {
    "vorfeld": None,
    "info": None,
    "fis": [],
    "arr_info": None
    }
    vorfeld_fallback = None

    # Pre-start: look for vorfeld, fallback to info or radio
    for name, freq in dep_freqs.items():
        upper = name.upper()

        if "VORFELD" in upper or "GROUND" in upper:
            roles["vorfeld"] = (name, freq)
        elif "INFORMATION" in upper and "LANGEN" not in upper:
            roles["info"] = (name, freq)
        elif "RADIO" in upper and roles["info"] is None:
            roles["info"] = (name, freq)

    # Apply fallback only if no vorfeld found
    if not roles["vorfeld"] and vorfeld_fallback:
        roles["vorfeld"] = vorfeld_fallback
    """ 
    # Tower or info for departure
    for name in dep_freqs:
        upper = name.upper()
        if "INFORMATION" in upper and "LANGEN" not in upper:
            roles["info"] = name
        elif "TOWER" in upper or "RADIO" in upper:
            roles.setdefault("info", name)
    """
    # FIS / enroute frequencies    
    for (name, freq), info in enroute_freqs.items():
        upper = name.upper()
        if "LANGEN" in upper or "FIS" in upper:
            roles["fis"].append((name, info["frequency"]))

    # Arrival: look for radio/info from arrival field
    for (name, freq) in arr_freqs.items():
        upper = name.upper()
        if "RADIO" in upper or "INFO" in upper:
            roles["arr_info"] = (name, freq)
            break

    return roles

# This function creates a nested frequency map with phases
def create_nested_frequency_map(dep_freqs, arr_freqs, enroute_freqs):
    phase_map = OrderedDict()

    # Departure frequencies
    for name, value in dep_freqs.items():
        phase = classify_frequency_by_context(name, context="departure")
        key = (name, value)
        if key not in phase_map:
            phase_map[key] = {
                "name": name,
                "frequency": value,
                "phase": phase
            }

    # Enroute frequencies
    for (name, value), info in enroute_freqs.items():
        key = (name, value)
        if key not in phase_map:
            phase_map[key] = info  # Already contains name, frequency, phase

    # Arrival frequencies
    for name, value in arr_freqs.items():
        phase = classify_frequency_by_context(name, context="arrival")
        key = (name, value)
        if key not in phase_map:
            phase_map[key] = {
                "name": name,
                "frequency": value,
                "phase": phase
            }

    return phase_map

# This function maps frequencies to flight phases
def classify_frequency_by_context(name, context):
    name = name.upper()

    if "VORFELD" in name or "GROUND" in name:
        return "Pre-Start / Taxi" if context == "departure" else "Arrival / Traffic Circuit"
    elif "INFORMATION" in name and "LANGEN" not in name:
        return "Departure / Takeoff" if context == "departure" else "Arrival / Traffic Circuit"
    elif "FIS" in name or "LANGEN INFORMATION" in name:
        return "Enroute / Cruise"
    elif "RADIO" in name or "INFO" in name:
        return "Departure / Takeoff" if context == "departure" else "Arrival / Traffic Circuit"
    else:
        return "Other"
