import json
import re

# Vul hier de bestandsnamen in
GEDCOM_BESTAND = "Gedcom.ged"
JSON_BESTAND = "Gedcom.json"

def get_birth_years(node):
    """
    Zoekt naar jaartallen (4 cijfers) in de BIRT -> DATE structuur van een INDI-node.
    """
    years = []
    if not isinstance(node, dict):
        return years

    birt = node.get("BIRT")
    if not birt:
        return years

    birt_list = birt if isinstance(birt, list) else [birt]
    for b in birt_list:
        if isinstance(b, dict):
            date_elem = b.get("DATE")
            if date_elem:
                date_list = date_elem if isinstance(date_elem, list) else [date_elem]
                for d in date_list:
                    if isinstance(d, dict) and "value" in d:
                        # Zoek naar 4 opeenvolgende cijfers (jaartal)
                        found = re.findall(r'\b\d{4}\b', str(d["value"]))
                        years.extend([int(y) for y in found])
    return years

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

    # 1. Identificeer en verwijder INDI's geboren na 1930
    for xref, node in list(root.items()):
        if isinstance(node, dict) and node.get("TAG") == "INDI":
            years = get_birth_years(node)
            # Als er een geboortejaar is gevonden en het vroegst bekende jaar is na 1930
            if years and min(years) > 1930:
                deleted_xrefs.add(xref)
                del root[xref]

    # 2. Verwijder alle referenties naar deze personen uit de overgebleven structuur (zoals FAM-records)
    remove_references(root, deleted_xrefs)

    print(f"Aantal verwijderde personen (geboren na 1930): {len(deleted_xrefs)}")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(root, f, ensure_ascii=False, indent=2)

    print(f"Conversie succesvol! '{gedcom_path}' is omgezet naar '{json_path}'.")

if __name__ == "__main__":
    convert_gedcom_to_json(GEDCOM_BESTAND, JSON_BESTAND)