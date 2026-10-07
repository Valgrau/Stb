import json

with open("Gedcom.json", "r", encoding="utf-8") as f:
    data = json.load(f)

if isinstance(data, list):
    # 1. Welke unieke tags bestaan er allemaal op het hoogste niveau?
    alle_tags = set(item.get('tag') for item in data if isinstance(item, dict) and 'tag' in item)
    print("Gevonden tags op hoogste niveau:", alle_tags)
    
    # 2. Zoek een voorbeeld van een INDI record
    indi = next((item for item in data if isinstance(item, dict) and 'INDI' in str(item.get('tag')).upper()), None)
    print("\n--- VOORBEELD PERSOON (INDI) ---")
    print(json.dumps(indi, indent=2)[:600] if indi else "Geen INDI tag gevonden op dit niveau.")

    # 3. Zoek een voorbeeld van een FAM record
    fam = next((item for item in data if isinstance(item, dict) and 'FAM' in str(item.get('tag')).upper()), None)
    print("\n--- VOORBEELD GEZIN (FAM) ---")
    print(json.dumps(fam, indent=2)[:600] if fam else "Geen FAM tag gevonden op dit niveau.")
else:
    print("Het bestand is geen lijst, maar een:", type(data))