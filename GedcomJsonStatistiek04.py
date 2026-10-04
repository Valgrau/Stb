import json

# Vul hier de juiste bestandsnaam/pad in
JSON_BESTAND = "stamboom.json"

with open(JSON_BESTAND, "r", encoding="utf-8") as f:
    data = json.load(f)

aantal_personen = 0
aantal_mannen = 0
aantal_vrouwen = 0
met_geboortedatum = 0
zonder_geboortedatum = 0
aantal_gezinnen = 0

# Zet data om naar (key, value) paren, ongeacht of de JSON een dict of een list is
records = []
if isinstance(data, dict):
    records = list(data.items())
elif isinstance(data, list):
    for item in data:
        if isinstance(item, dict):
            for k, v in item.items():
                records.append((k, v))

for key, val in records:
    key_str = str(key)
    
    # Personen (@I...)
    if key_str.startswith("@I"):
        aantal_personen += 1

        # Geslacht bepalen
        sex = ""
        if isinstance(val, dict):
            sex_data = val.get("SEX") or val.get("sex")
            if isinstance(sex_data, dict):
                sex = sex_data.get("value") or sex_data.get("val") or ""
            elif isinstance(sex_data, str):
                sex = sex_data
            elif isinstance(sex_data, list) and sex_data:
                sex = str(sex_data[0])

        sex_str = str(sex).strip().upper()
        if sex_str.startswith("M"):
            aantal_mannen += 1
        elif sex_str.startswith("F") or sex_str.startswith("V"):
            aantal_vrouwen += 1

        # Geboortedatum controleren
        heeft_geboortedatum = False
        if isinstance(val, dict):
            birt = val.get("BIRT") or val.get("birth")
            if birt:
                if isinstance(birt, dict):
                    heeft_geboortedatum = bool(birt.get("DATE") or birt.get("date"))
                else:
                    heeft_geboortedatum = True

        if heeft_geboortedatum:
            met_geboortedatum += 1
        else:
            zonder_geboortedatum += 1

    # Gezinnen (@F...)
    elif key_str.startswith("@F"):
        aantal_gezinnen += 1

print(f"Totaal aantal personen      : {aantal_personen}")
print(f" - Aantal mannen            : {aantal_mannen}")
print(f" - Aantal vrouwen           : {aantal_vrouwen}")
print(f" - Onbekend geslacht        : {aantal_personen - aantal_mannen - aantal_vrouwen}")
print(f"Aantal met geboortedatum    : {met_geboortedatum}")
print(f"Aantal zonder geboortedatum : {zonder_geboortedatum}")
print(f"Totaal aantal gezinnen      : {aantal_gezinnen}")