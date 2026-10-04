import json

def analyze_gedcom_json(json_file_path):
    """Leest het Gedcom.json bestand in en berekent de statistieken."""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_persons = 0
    total_men = 0
    total_women = 0
    with_birth_date = 0
    without_birth_date = 0
    total_families = 0

    # Controleer of de data een lijst is of onder een attribuut staat
    items = data if isinstance(data, list) else data.get('records', [])

    for item in items:
        tag = item.get('tag')
        
        # 1. Personen analyseren (INDI)
        if tag == 'INDI':
            total_persons += 1
            children = item.get('children', [])
            
            # Geslacht bepalen
            sex_node = next((c for c in children if c.get('tag') == 'SEX'), None)
            if sex_node:
                sex_val = (sex_node.get('value') or '').strip().upper()
                if sex_val == 'M':
                    total_men += 1
                elif sex_val == 'F':
                    total_women += 1

            # Geboortedatum bepalen (BIRT -> DATE)
            has_birth = False
            birt_node = next((c for c in children if c.get('tag') == 'BIRT'), None)
            if birt_node:
                if birt_node.get('value') and birt_node.get('value').strip():
                    has_birth = True
                else:
                    birt_children = birt_node.get('children', [])
                    date_node = next((c for c in birt_children if c.get('tag') == 'DATE'), None)
                    if date_node and date_node.get('value') and date_node.get('value').strip():
                        has_birth = True
            
            if has_birth:
                with_birth_date += 1
            else:
                without_birth_date += 1

        # 2. Gezinnen analyseren (FAM)
        elif tag == 'FAM':
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
    """Genereert het HTML-bestand met de berekende statistieken."""
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
        .icon {{
            font-size: 2rem;
            margin-bottom: 8px;
        }}
        .number {{
            font-size: 2.2rem;
            font-weight: bold;
            color: #3498db;
            margin: 8px 0;
        }}
        .label {{
            font-size: 0.95rem;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
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

    print(f"Statistieken succesvol gegenereerd in '{output_html_path}'!")

if __name__ == "__main__":
    input_file = "Gedcom.json"
    try:
        stats = analyze_gedcom_json(input_file)
        generate_html_report(stats)
    except FileNotFoundError:
        print(f"Fout: Kan '{input_file}' niet vinden in de huidige map.")
    except Exception as e:
        print(f"Er is een fout opgetreden: {e}")