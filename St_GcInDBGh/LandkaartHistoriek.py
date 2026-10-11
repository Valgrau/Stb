import re
import time
import json
import csv
from geopy.geocoders import Nominatim

# ==============================================================================
# CONFIGURATIE PARAMETERS
# ==============================================================================
gedcom_file = "Gedcom.ged"
LIMIT = None  # Zet op None zodat werkelijk ALLE personen (26.816+) worden meegenomen

individuals = {}
current_type = None
current_id = None
current_obj = None
in_birt = False
in_deat = False

def clean_id(raw_id):
    if not raw_id:
        return ""
    return re.sub(r'[^0-9]', '', str(raw_id))

def normalize_location(loc_str):
    if not loc_str:
        return None
    lower_loc = loc_str.lower()
    if lower_loc.startswith("binderveld") or "binderveld" in lower_loc:
        return "Binderveld, België"
    if "sint-truiden" in lower_loc:
        return "Sint-Truiden, België"
    if "hasselt" in lower_loc:
        return "Hasselt, België"
    
    clean = re.split(r'[,(]', loc_str)[0].strip()
    clean = re.sub(r'\b\d+\b', '', clean).strip()
    if clean and 'belgi' not in clean.lower():
        clean = f"{clean}, België"
    return clean

print("1. GEDCOM parseren...")

with open(gedcom_file, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split(" ", 2)
        level = parts[0]
        tag = parts[1] if len(parts) > 1 else ""
        value = parts[2] if len(parts) > 2 else ""

        if level == "0":
            if current_type == "INDI" and current_id:
                individuals[current_id] = current_obj

            if "INDI" in value or tag == "INDI":
                current_type = "INDI"
                raw = tag if tag != "INDI" else parts[2] if len(parts) > 2 else ""
                current_id = clean_id(raw)
                current_obj = {
                    "id": current_id,
                    "name": "Onbekend",
                    "birth_year": None,
                    "birth_place": None,
                    "death_year": None,
                    "death_place": None
                }
            else:
                current_type = None
                current_id = None
                current_obj = None

            in_birt = False
            in_deat = False

        elif current_obj and current_type == "INDI":
            if level == "1":
                in_birt = (tag == "BIRT")
                in_deat = (tag == "DEAT")
                if tag == "NAME":
                    name_clean = value.replace("/", " ").replace("  ", " ").strip()
                    if name_clean:
                        current_obj["name"] = name_clean
            elif level == "2":
                if tag == "SURN" and current_obj["name"] != "Onbekend":
                    surn = value.replace("/", "").strip()
                    if surn and surn not in current_obj["name"]:
                        current_obj["name"] += f" {surn}"
                
                if in_birt:
                    if tag == "DATE":
                        match = re.search(r'\b(1\d{3}|20\d{2})\b', value)
                        if match:
                            current_obj["birth_year"] = int(match.group(1))
                    elif tag == "PLAC":
                        current_obj["birth_place"] = normalize_location(value)
                elif in_deat:
                    if tag == "DATE":
                        match = re.search(r'\b(1\d{3}|20\d{2})\b', value)
                        if match:
                            current_obj["death_year"] = int(match.group(1))
                    elif tag == "PLAC":
                        current_obj["death_place"] = normalize_location(value)

if current_type == "INDI" and current_id:
    individuals[current_id] = current_obj

all_persons = list(individuals.values())
total_parsed = len(all_persons)

if LIMIT and isinstance(LIMIT, int) and LIMIT > 0:
    all_persons = all_persons[:LIMIT]

print(f"✓ Totaal ingelezen personen: {total_parsed}")

# Unieke locaties verzamelen
location_counts = {}
for p in all_persons:
    place = p["birth_place"] or p["death_place"]
    if place:
        location_counts[place] = location_counts.get(place, 0) + 1

location_list = sorted(list(location_counts.keys()))
total_locations = len(location_list)

geolocator = Nominatim(user_agent="StamboomApp_v2026")
geo_coords = {}

print(f"\n2. Geocoden van {total_locations} unieke locaties (even geduld)...")
for index, loc_name in enumerate(location_list, start=1):
    try:
        time.sleep(1)
        loc = geolocator.geocode(loc_name, timeout=10)
        if loc:
            geo_coords[loc_name] = [loc.latitude, loc.longitude]
    except Exception as e:
        pass

for loc_name in location_list:
    if loc_name not in geo_coords:
        geo_coords[loc_name] = [50.8503, 4.3517]

all_years = [p["birth_year"] for p in all_persons if p["birth_year"] is not None]
min_year = min(all_years) if all_years else 1600
max_year = 2026

map_center = [50.8503, 4.3517]
if geo_coords:
    map_center = list(geo_coords.values())[0]

compact_persons = []
for p in all_persons:
    place = p["birth_place"] or p["death_place"]
    if place:
        compact_persons.append({
            "n": p["name"],
            "by": p["birth_year"],
            "dy": p["death_year"],
            "p": place
        })

# ==============================================================================
# 3. EXCEL / CSV OVERZICHT GENEREREN
# ==============================================================================
print("\n3. Excel/CSV overzicht aanmaken...")
excel_data = []

for p in all_persons:
    place = p["birth_place"] or p["death_place"]
    if place:
        b_year = p["birth_year"]
        d_year = p["death_year"]
        van_jaar = b_year if b_year else "Onbekend"
        
        if d_year:
            tot_jaar = d_year
            status = "Bekend"
        elif b_year:
            tot_jaar = b_year + 80
            status = "Geschat (+80 jr)"
        else:
            tot_jaar = "Onbekend"
            status = "Onbekend"

        excel_data.append({
            "ID": p["id"],
            "Naam": p["name"],
            "Locatie": place,
            "Geboortejaar (Van)": van_jaar,
            "Overlijdensjaar (Tot)": tot_jaar,
            "Status Overlijden": status
        })

csv_bestandsnaam = "stamboom_personen_overzicht.csv"
with open(csv_bestandsnaam, mode="w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["ID", "Naam", "Locatie", "Geboortejaar (Van)", "Overlijdensjaar (Tot)", "Status Overlijden"], delimiter=";")
    writer.writeheader()
    writer.writerows(excel_data)

print(f"✓ Overzicht opgeslagen als '{csv_bestandsnaam}' ({len(excel_data)} personen).")

# ==============================================================================
# 4. HTML BESTAND GENEREREN (Let op de dubbele $$ voor JS template literals)
# ==============================================================================
print("\n4. HTML-bestand genereren...")
json_persons = json.dumps(compact_persons, ensure_ascii=False)
json_coords = json.dumps(geo_coords, ensure_ascii=False)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Stamboom Tijdmachine</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        html, body {{ height: 100%; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
        #map {{ height: 100vh; width: 100vw; position: absolute; top: 0; bottom: 0; left: 0; right: 0; }}
        
        .time-panel {{
            position: absolute;
            bottom: 25px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            background: rgba(255, 255, 255, 0.95);
            padding: 12px 20px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            text-align: center;
            width: 80%;
            max-width: 450px;
        }}
        .slider {{ width: 100%; margin-top: 8px; }}
        .year-display {{ font-size: 22px; font-weight: bold; color: #2c3e50; }}
        .stats {{ font-size: 12px; color: #7f8c8d; margin-top: 4px; }}

        .custom-count-icon {{
            background-color: #2b78e4;
            color: white;
            border: 2px solid white;
            border-radius: 50%;
            font-weight: bold;
            font-size: 13px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 6px rgba(0,0,0,0.4);
        }}

        .leaflet-popup-content-wrapper {{ border-radius: 10px; padding: 0; }}
        .leaflet-popup-content {{ margin: 12px 14px !important; width: 280px !important; }}
        .popup-container h4 {{ margin: 0 0 4px 0; color: #2c3e50; font-size: 15px; }}
        .popup-list {{
            padding-left: 18px;
            margin: 8px 0 0 0;
            font-size: 12px;
            max-height: 200px;
            overflow-y: auto;
            -webkit-overflow-scrolling: touch;
            touch-action: pan-y;
        }}
        .popup-list li {{ margin-bottom: 4px; }}
    </style>
</head>
<body>

<div id="map"></div>

<div class="time-panel">
    <div class="year-display">Jaar: <span id="selected-year">{max_year}</span></div>
    <input type="range" min="{min_year}" max="{max_year}" value="{max_year}" class="slider" id="year-slider">
    <div class="stats"><span id="active-count">0</span> personen zichtbaar</div>
</div>

<script>
    const persons = {json_persons};
    const coords = {json_coords};

    const map = L.map('map', {{ preferCanvas: true }}).setView([{map_center[0]}, {map_center[1]}], 8);
    
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
        maxZoom: 19,
        attribution: 'Tiles &copy; Esri'
    }}).addTo(map);

    let markersGroup = L.layerGroup().addTo(map);
    let renderTimer = null;

    function updateMap(selectedYear) {{
        markersGroup.clearLayers();
        
        let locationMap = {{}};
        let activePersonsCount = 0;

        for (let i = 0; i < persons.length; i++) {{
            let p = persons[i];
            let bYear = p.by;
            let dYear = p.dy || (bYear ? bYear + 80 : null);

            let isAlive = false;
            if (bYear && bYear <= selectedYear && dYear >= selectedYear) {{
                isAlive = true;
            }} else if (!bYear && p.dy && p.dy >= selectedYear) {{
                isAlive = true;
            }}

            if (isAlive) {{
                activePersonsCount++;
                if (!locationMap[p.p]) locationMap[p.p] = [];
                locationMap[p.p].push(p);
            }}
        }}

        for (let place in locationMap) {{
            let latLng = coords[place];
            if (latLng) {{
                let peopleArray = locationMap[place];
                
                peopleArray.sort((a, b) => (a.by || 9999) - (b.by || 9999));

                let peopleList = peopleArray.map(item => {{
                    let yearStr = item.by ? item.by : 'Onbekend';
                    return `<li><b>$${{item.n}}</b> (Geboren: $${{yearStr}})</li>`;
                }}).join('');
                
                let popupContent = `
                    <div class="popup-container">
                        <h4>$${{place}}</h4>
                        <b>Aantal: $${{peopleArray.length}}</b>
                        <ul class="popup-list">$${{peopleList}}</ul>
                    </div>
                `;

                let countIcon = L.divIcon({{
                    className: 'custom-count-icon',
                    html: peopleArray.length,
                    iconSize: [32, 32],
                    iconAnchor: [16, 16]
                }});

                let marker = L.marker(latLng, {{ icon: countIcon }})
                    .bindPopup(popupContent)
                    .addTo(markersGroup);

                marker.on('popupopen', function(e) {{
                    let popupNode = e.popup.getElement().querySelector('.popup-list');
                    if (popupNode) {{
                        L.DomEvent.disableScrollPropagation(popupNode);
                        L.DomEvent.disableClickPropagation(popupNode);
                    }}
                }});
            }}
        }}

        document.getElementById('active-count').innerText = activePersonsCount;
    }}

    const slider = document.getElementById('year-slider');
    const yearDisplay = document.getElementById('selected-year');

    slider.addEventListener('input', function() {{
        yearDisplay.innerText = this.value;
        if (renderTimer) clearTimeout(renderTimer);
        renderTimer = setTimeout(() => {{
            updateMap(parseInt(this.value));
        }}, 60);
    }});

    updateMap({max_year});
</script>

</body>
</html>
"""

with open("stamboom_subset.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("✓ HTML-bestand succesvol gegenereerd als 'stamboom_subset.html' met alle personen!")