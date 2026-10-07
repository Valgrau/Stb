import json
import re

# Vul hier de bestandsnamen in
GEDCOM_BESTAND = "Gedcom.ged"
JSON_BESTAND = "Gedcom.json"

def extract_years_from_text(text):
    """
    Haalt alle 4-cijferige jaartallen (1000-2099) uit een tekststreng.
    """
    if not text:
        return []
    return [int(y) for y in re.findall(r'\b(1\d{3}|20\d{2})\b', str(text))]

def get_birth_year(node):
    """
    Bepaalt het geboortejaar van een INDI-node.
    Kijkt primair naar BIRT -> DATE. Als die ontbreekt, kijkt de functie naar CHR (doop) -> DATE.
    """
    if not isinstance(node, dict):
        return None

    # 1. Probeer BIRT (Geboorte)
    birt = node.get("BIRT")
    if birt:
        birt_list = birt if isinstance(birt, list) else [birt]
        for b in birt_list:
            if isinstance(b, dict):
                date_elem = b.get("DATE")
                if isinstance(date_elem, dict) and "value" in date_elem:
                    years = extract_years_from_text(date_elem["value"])
                    if years:
                        return min(years)

    # 2. Alternatief: Probeer CHR (Doop) als BIRT geen datum bevat
    chr_elem = node.get("CHR")
    if chr_elem:
        chr_list = chr_elem if isinstance(chr_elem, list) else [chr_elem]
        for c in chr_list:
            if isinstance(c, dict):
                date_elem = c.get("DATE")
                if isinstance(date_elem, dict) and "value" in date_elem:
                    years = extract_years_from_text(date_elem["value"])
                    if years:
                        return min(years)

    return None

def anonymize_name_text(name_str):
    """
    Zet een GEDCOM-naam om naar initialen.
    Voorbeeld: "Elza /Diepenrijkx/" -> "E. /D./"
    Voorbeeld: "Petrus Julius /Bangels/" -> "P. /B./"
    """
    if not name_str or not isinstance(name_str, str):
        return name_str

    name_str = name_str.strip()
    if not name_str:
        return name_str

    # GEDCOM-namen gebruiken slashes voor de familienaam: "Voornaam /Familienaam/"
    if '/' in name_str:
        parts = name_str.split('/')
        given = parts[0].strip()
        surname = parts[1].strip() if len(parts) > 1 else ""

        given_initial = f"{given[0].upper()}." if given else ""
        surname_initial = f"{surname[0].upper()}." if surname else ""

        if surname_initial:
            return f"{given_initial} /{surname_initial}/".strip()
        else:
            return given_initial
    else:
        # Geen schuine strepen aanwezig
        words = name_str.split()
        if len(words) == 1:
            return f"{words[0][0].upper()}."
        elif len(words) > 1:
            given_initial = f"{words[0][0].upper()}."
            surname_initial = f"{words[-1][0].upper()}."
            return f"{given_initial} /{surname_initial}/"

    return name_str

def anonymize_person_name(name_node):
    """
    Past de naam van een persoon aan naar initialen in de GEDCOM JSON-structuur.
    Past ook eventuele sub-tags zoals GIVEN en SURN aan.
    """
    if isinstance(name_node, dict):
        if "value" in name_node:
            name_node["value"] = anonymize_name_text(name_node["value"])
        
        # Pas eventuele GEDCOM sub-tags GIVEN (voornaam) en SURN (familienaam) aan
        if "GIVEN" in name_node and isinstance(name_node["GIVEN"], dict) and "value" in name_node["GIVEN"]:
            val = name_node["GIVEN"]["value"].strip()
            if val:
                name_node["GIVEN"]["value"] = f"{val[0].upper()}."
        
        if "SURN" in name_node and isinstance(name_node["SURN"], dict) and "value" in name_node["SURN"]:
            val = name_node["SURN"]["value"].strip()
            if val:
                name_node["SURN"]["value"] = f"{val[0].upper()}."

    elif isinstance(name_node, list):
        for item in name_node:
            anonymize_person_name(item)

def convert_gedcom_to_json(gedcom_path, json_path):
    root = {}
    stack = []

    # Regex voor GEDCOM-regels: niveau [XREF] tag [waarde]
    gedcom_line_pattern = re.compile(r'^\s*(\d+)\s+(?:(@[^@]+@)\s+)?(\w+)(?:\s+(.*))?$')

    try:
        with open(gedcom_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Fout: Het bestand '{gedcom_path}' is niet gevonden.")
        return

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = gedcom_line_pattern.match(line)
        if not match:
            continue

        level = int(match.group(1))
        xref = match.group(2)
        tag = match.group(3)
        val = match.group(4).strip() if match.group(4) else ""

        # Maak nieuw node object aan
        node = {}
        if val:
            node["value"] = val

        if level == 0:
            if xref:
                node_key = xref
                root[node_key] = node
                node["TAG"] = tag
                stack = [(0, node)]
            else:
                root[tag] = node
                stack = [(0, node)]
        else:
            # Zoek de bovenliggende parent in de stack
            while stack and stack[-1][0] >= level:
                stack.pop()

            if stack:
                parent_node = stack[-1][1]

                # Als de tag al bestaat bij de parent, maak er een lijst van
                if tag in parent_node:
                    if not isinstance(parent_node[tag], list):
                        parent_node[tag] = [parent_node[tag]]
                    parent_node[tag].append(node)
                else:
                    parent_node[tag] = node

                stack.append((level, node))

    # --- NAAMWIJZIGING: Personen geboren na 1930 initialiseren ---
    modified_count = 0

    print("--- Geanonimiseerde personen (geboren na 1930) ---")
    for xref, node in root.items():
        if isinstance(node, dict) and node.get("TAG") == "INDI":
            birth_year = get_birth_year(node)
            
            # Controleer of het geboortejaar bekend is en na 1930 valt
            if birth_year is not None and birth_year > 1930:
                if "NAME" in node:
                    # Oude naam ophalen voor weergave
                    old_name = "Onbekend"
                    name_node = node["NAME"]
                    if isinstance(name_node, dict):
                        old_name = name_node.get("value", "Onbekend")
                    elif isinstance(name_node, list) and name_node:
                        old_name = name_node[0].get("value", "Onbekend")

                    # Pas de naam aan
                    anonymize_person_name(node["NAME"])

                    # Nieuwe naam ophalen voor weergave
                    new_name = "Onbekend"
                    if isinstance(name_node, dict):
                        new_name = name_node.get("value", "Onbekend")
                    elif isinstance(name_node, list) and name_node:
                        new_name = name_node[0].get("value", "Onbekend")

                    print(f"Gewijzigd: {xref} | Geboortejaar: {birth_year} | {old_name} -> {new_name}")
                    modified_count += 1

    print(f"\nTotaal aantal geanonimiseerde personen: {modified_count}")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(root, f, ensure_ascii=False, indent=2)

    print(f"Conversie succesvol! '{gedcom_path}' is omgezet naar '{json_path}'.")

if __name__ == "__main__":
    convert_gedcom_to_json(GEDCOM_BESTAND, JSON_BESTAND)