import json
import re

def parse_gedcom_line(line):
    # Match GEDCOM lijnformaat: LEVEL TAG [VALUE]
    match = re.match(r'^(\d+)\s+(@[^@]+@|\w+)(?:\s+(.*))?$', line.strip())
    if match:
        level, tag_or_id, value = match.groups()
        return int(level), tag_or_id, value or ""
    return None

def gedcom_to_json_basic(input_file, output_file):
    stack = []
    root_nodes = []

    with open(input_file, 'r', encoding='utf-8-sig', errors='ignore') as f:
        for line in f:
            parsed = parse_gedcom_line(line)
            if not parsed:
                continue

            level, tag, value = parsed
            node = {"tag": tag, "value": value, "children": []}

            if level == 0:
                root_nodes.append(node)
                stack = [node]
            else:
                # Zorg dat de stack op het juiste niveau staat
                while len(stack) > level:
                    stack.pop()
                
                if stack:
                    stack[-1]["children"].append(node)
                    stack.append(node)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(root_nodes, f, ensure_ascii=False, indent=4)

    print(f"Conversie voltooid! JSON is opgeslagen als '{output_file}'.")

if __name__ == "__main__":
    gedcom_to_json_basic("Gedcom.ged", "Gedcom.json")