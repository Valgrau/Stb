import json

def get_val(obj, *keys):
    """Zoekt een sleutel op, ongeacht hoofd- of kleine letters."""
    if not isinstance(obj, dict):
        return None
    for k in keys:
        for actual_k in obj.keys():
            if actual_k.lower() == k.lower():
                return obj[actual_k]
    return None

def extract_items(data):
    """Zet de JSON-data altijd om naar een platte lijst van records."""
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if 'records' in data and isinstance(data['records'], list):
            return data['records']
        elif 'individuals' in data or 'persons' in data:
            persons = data.get('individuals') or data.get('persons') or []
            families = data.get('families') or []
            return persons + families
        else:
            # Dict geindexeerd op ID: {"@I1@": {...}, "@I2@": {...}}
            return list(data.values())
    return []

def analyze_gedcom_json(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = extract_items(data)

    total_persons = 0
    total_men = 0
    total_women = 0
    with_birth_date = 0
    without_birth_date = 0
    total_families = 0

    for item in items:
        if not isinstance(item, dict):
            continue
            
        # Bepaal tag (tag, type, record_type, etc.)
        tag = str(get_val(item, 'tag', 'type', 'record_type', 'name') or '').strip().upper()
        
        # Bepaal sub-elementen
        children = get_val(item, 'children', 'sub_records', 'nodes', 'items', 'sub_rec_items', 'content') or []
        if isinstance(children, dict):
            children = list(children.values())

        # 1. Personen (INDI / PERSON / INDIVIDUAL)
        if tag in ['INDI', 'PERSON', 'INDIVIDUAL']:
            total_persons += 1
            
            # Geslacht bepalen
            sex_val = ''
            sex_node = next((c for c in children if isinstance(c, dict) and str(get_val(c, 'tag', 'type') or '').strip().upper() in ['SEX', 'GENDER']), None)
            if sex_node:
                sex_val = str(get_val(sex_node, 'value', 'val', 'text') or '').strip().upper()
            else:
                direct_sex = str(get_val(item, 'sex', 'gender') or '').strip().upper()
                if direct_sex in ['M', 'MALE', 'MAN']: sex_val = 'M'
                elif direct_sex in ['F', 'FEMALE', 'VROUW']: sex_val = 'F'

            if sex_val in ['M', 'MALE']:
                total_men += 1
            elif sex_val in ['F', 'FEMALE']:
                total_women += 1

            # Geboortedatum bepalen
            has_birth = False
            birt_node = next((c for c in children if isinstance(c, dict) and str(get_val(c, 'tag', 'type') or '').strip().upper() in ['BIRT', 'BIRTH']), None)
            
            if birt_node:
                birt_val = get_val(birt_node, 'value', 'val', 'date')
                if birt_val and str(birt_val).strip():
                    has_birth = True
                else:
                    birt_children = get_val(birt_node, 'children', 'sub_records', 'nodes', 'items') or []
                    if isinstance(birt_children, dict): 
                        birt_children = list(birt_children.values())
                    
                    date_node = next((dc for dc in birt_children if isinstance(dc, dict) and str(get_val(dc, 'tag', 'type') or '').strip().upper() == 'DATE'), None)
                    if date_node and get_val(date_node, 'value', 'val', 'text'):
                        has_birth = True
            elif get_val(item, 'birth_date', 'birthdate', 'birth'):
                has_birth = True

            if has_birth:
                with_birth_date += 1
            else:
                without_birth_date += 1

        # 2. Gezinnen (FAM / FAMILY)
        elif tag in ['FAM', 'FAMILY']:
            total_families += 1

    return {
        'total_persons': total_persons,
        'total_men': total_men,
        'total_women': total_women,
        'with_birth_date': with_birth_date,
        'without_birth_date': without_birth_date,
        'total_families': total_families
    }

def generate_html_report(stats, output_html_path="Gedcom_statistieken.html"):
    html_content = f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GEDCOM Statistieken</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f7f6;
            color: #333;
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        }}
        h1 {{
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }}
        .card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.05);
        }}
        .icon {{ font-size: 2rem; margin-bottom: 8px; }}
        .number {{ font-size: 2.2rem; font-weight: bold; color: #3498db; margin: 8px 0; }}
        .label {{ font-size: 0.95rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 GEDCOM Statistieken</h1>
        <div class="grid">
            <div class="card">
                <div class="icon">👥</div>
                <div class="number">{stats['total_persons']}</div>
                <div class="label">Aantal personen</div>
            </div>
            <div class="card">
                <div class="icon">👨</div>
                <div class="number">{stats['total_men']}</div>
                <div class="label">Aantal mannen</div>
            </div>
            <div class="card">
                <div class="icon">👩</div>
                <div class="number">{stats['total_women']}</div>
                <div class="label">Aantal vrouwen</div>
            </div>
            <div class="card">
                <div class="icon">📅</div>
                <div class="number">{stats['with_birth_date']}</div>
                <div class="label">Met geboortedatum</div>
            </div>
            <div class="card">
                <div class="icon">❓</div>
                <div class="number">{stats['without_birth_date']}</div>
                <div class="label">Zonder geboortedatum</div>
            </div>
            <div class="card">
                <div class="icon">🏠</div>
                <div class="number">{stats['total_families']}</div>
                <div class="label">Aantal gezinnen</div>
            </div>
        </div>
    </div>
</body>
</html>
"""

    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Statistieken gegenereerd in '{output_html_path}'.")

if __name__ == "__main__":
    input_file = "Gedcom.json"
    try:
        stats = analyze_gedcom_json(input_file)
        generate_html_report(stats)
    except FileNotFoundError:
        print(f"Fout: Kan '{input_file}' niet vinden in de huidige map.")
    except Exception as e:
        print(f"Er is een fout opgetreden: {e}")