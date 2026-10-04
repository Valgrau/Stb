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
                        # Neem het vroegst vermelde jaartal bij de geboortedatum
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

def remove_references(data, deleted_xrefs):
    """
    Verwijdert recursief alle verwijzingen (XREFs) naar de verwijderde personen
    uit de JSON-structuur (bijv. HUSB, WIFE, CHIL in FAM-records).
    """
    if isinstance(data, dict):
        keys_to_delete = []
        for key, value in list(data.items()):
            if isinstance(value, dict):
                if value.get("value") in deleted_xrefs:
                    keys_to_delete.append(key)
                else:
                    remove_references(value, deleted_xrefs)
            elif isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, dict):
                        if item.get("value") in deleted_xrefs:
                            continue  # Sla verwijderde persoon over
                        remove_references(item, deleted_xrefs)
                    else:
                        new_list.append(item)
                
                if not new_list:
                    keys_to_delete.append(key)
                else:
                    data[key] = new_list

        for key in keys_to_delete:
            del data[key]

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

    # --- FILTERING: Personen geboren na 1930 filteren ---
    deleted_xrefs = set()

    print("--- Overzicht van verwijderde personen (geboren na 1930) ---")
    for xref, node in list(root.items()):
        if isinstance(node, dict) and node.get("TAG") == "INDI":
            birth_year = get_birth_year(node)
            
            # Verwijder als het geboortejaar bekend is en na 1930 valt
            if birth_year is not None and birth_year > 1930:
                name_node = node.get("NAME", {})
                name_val = "Onbekend"
                if isinstance(name_node, dict):
                    name_val = name_node.get("value", "Onbekend")
                elif isinstance(name_node, list) and name_node:
                    name_val = name_node[0].get("value", "Onbekend")
                
                print(f"Verwijderd: {xref} | Naam: {name_val} | Geboortejaar: {birth_year}")
                deleted_xrefs.add(xref)
                del root[xref]

    # Verwijder alle referenties naar de gewiste personen uit FAM records
    remove_references(root, deleted_xrefs)

    print(f"\nTotaal aantal verwijderde personen: {len(deleted_xrefs)}")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(root, f, ensure_ascii=False, indent=2)

    print(f"Conversie succesvol! '{gedcom_path}' is omgezet naar '{json_path}'.")

if __name__ == "__main__":
    convert_gedcom_to_json(GEDCOM_BESTAND, JSON_BESTAND)