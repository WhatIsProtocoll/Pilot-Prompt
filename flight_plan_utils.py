from collections import defaultdict
import inspect
from icao_rules_de import ICAO_RULES_DE, PHASE_MAPPING, PHASE_ORDER
from collections import OrderedDict
from shapely.geometry import Point
import geopandas as gpd
import json
from frequency_retrieval import (get_airport_by_icao, get_frequencies, get_lat_lon, generate_route_points,plot_route_over_fis, get_ordered_frequencies, create_nested_frequency_map, extract_frequency_roles)

# Load geojson for airport and airspace data
with open("openaip_data/de_apt.geojson", "r") as file:
    airport_data = json.load(file)

airspaces = gpd.read_file("openaip_data/de_asp.geojson")
airspaces = airspaces[airspaces.geometry.type == "Polygon"].set_geometry("geometry").to_crs(epsg=4326)

def build_checklist_from_rules(user_data):
    checklist = defaultdict(list)

    for key, rule in ICAO_RULES_DE.items():
        phase = PHASE_MAPPING.get(key)
        if not phase:
            continue  # skip if not assigned to a phase

        try:
            sig = inspect.signature(rule["response"])
            kwargs = {k: v for k, v in user_data.items() if k in sig.parameters}
            call = rule["response"](**kwargs)
            checklist[phase].append(call)
        except Exception as e:
            print(f"Could not format {key}: {e}")

    return checklist

def inject_frequency_transitions(checklist, nested_freqs):
    enhanced = {}
    last_freq_name = None
    phase_sequence = ["Pre-Start / Taxi", "Departure / Takeoff", "Enroute / Cruise", "Arrival / Traffic Circuit"]

    for phase in phase_sequence:
        items = checklist.get(phase, []).copy()

        # Find matching frequency for this phase
        for freq_key, info in nested_freqs.items():
            if info["phase"] == phase:
                if freq_key != last_freq_name:
                    name, value = freq_key  # unpack the tuple
                    transition_text = f"👉 Change to {name}: {value}"
                    items.insert(0, transition_text)
                    last_freq_name = freq_key
                break

        enhanced[phase] = items

    return enhanced

def generate_checklist_from_form(cs, airplane_type, num_pax, dep_icao, arr_icao, position):
    # Get airport features
    dep_airport = get_airport_by_icao(dep_icao, airport_data)
    arr_airport = get_airport_by_icao(arr_icao, airport_data)

    if not dep_airport or not arr_airport:
        return "Error: Could not retrieve one or both airport features."

    # Extract frequencies
    dep_freqs = get_frequencies(dep_airport)
    arr_freqs = get_frequencies(arr_airport)

    # Generate route and enroute frequencies
    start = Point(*get_lat_lon(dep_airport))
    print(f"Departure Frequencies: {dep_freqs}")
    end = Point(*get_lat_lon(arr_airport))
    print(f"Arrival Frequencies: {arr_freqs}")
    route_points = generate_route_points(start, end)
    enroute_freqs = get_ordered_frequencies(route_points, airspaces)
    print("Nested Frequency List:")
    for (name, value), info in enroute_freqs.items():
        print(f"{name} ({value} MHz): used during {info['phase']}")

    route_points = generate_route_points(start, end)
    plot_route_over_fis(route_points, airspaces, dep_icao, arr_icao)

    # Use new nested structure
    nested_freqs = create_nested_frequency_map(dep_freqs, arr_freqs, enroute_freqs)
    print(f"Nested Frequencies: {nested_freqs}")

    # Retrieve frequency names for radio roles
    roles = extract_frequency_roles(dep_freqs, arr_freqs, enroute_freqs)
    print(f"Roles: {roles}")

    # Prepare user data
    user_data = {
        "cs": cs,
        "airplane_type": airplane_type,
        "num_pax": int(num_pax),
        "dep": dep_icao,
        "arr": arr_icao,
        "position": position,
        "vorfeld": roles.get("vorfeld", ""),
        "info": roles.get("info", ""),
        "fis": roles.get("fis", ""),
        "fis2": roles.get("fis2", ""),  # optional fallback for enroute switch
        "arr_info": roles.get("arr_info", "")
    }

    # Build and enhance checklist
    base = build_checklist_from_rules(user_data)
    with_transitions = inject_frequency_transitions(base, nested_freqs)

    # Format for display
    output = ""
    for phase, calls in with_transitions.items():
        output += f"### {phase}\n"
        output += "\n".join(f"- {call}" for call in calls) + "\n\n"

    return with_transitions


'''
def generate_checklist(dep, arr):
    freq_map = get_phase_frequency_map(dep, arr)
    if freq_map is None:
        return f"Error: Could not find data for {dep} or {arr}"

    checklist = build_checklist_from_rules()  # Still based on dummy_data for now
    final = inject_frequency_transitions(checklist, freq_map)

    output_lines = []
    for phase in PHASE_ORDER:
        output_lines.append(f"📌 {phase}")
        for item in final.get(phase, []):
            output_lines.append(f"• {item}")
        output_lines.append("")  # newline

    return "\n".join(output_lines)
'''