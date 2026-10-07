import json
with open("Gedcom.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Toon het type en de eerste paar sleutels/elementen
print("Type:", type(data))
print("Voorbeeld:", str(data)[:300])