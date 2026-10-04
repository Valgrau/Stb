import json
import re

# Vul hier de bestandsnamen in
GEDCOM_BESTAND = "Gedcom.ged"
JSON_BESTAND = "Gedcom.json"

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

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(root, f, ensure_ascii=False, indent=2)

    print(f"Conversie succesvol! '{gedcom_path}' is omgezet naar '{json_path}'.")

if __name__ == "__main__":
    convert_gedcom_to_json(GEDCOM_BESTAND, JSON_BESTAND)