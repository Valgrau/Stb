import re

def parse_gedcom_line(line):
    """Ontleedt een enkele GEDCOM-regel in niveau, xref, tag en waarde."""
    line = line.strip('\r\n')
    if not line:
        return None
    
    # Matching GEDCOM formaat: LEVEL [@ID@] TAG [VALUE]
    match = re.match(r'^(\d+)\s+(?:(@[^@]+@)\s+)?(\w+)(?:\s+(.*))?$', line)
    if match:
        level = int(match.group(1))
        xref = match.group(2) or ''
        tag = match.group(3).upper()
        val = match.group(4) or ''
        return level, xref, tag, val
    return None

def analyze_gedcom_file(gedcom_path):
    """Leest het GEDCOM-bestand in en berekent alle statistieken."""
    total_persons = 0
    total_men = 0
    total_women = 0
    with_birth_date = 0
    without_birth_date = 0
    total_families = 0

    current_record = None
    current_person_sex = None
    current_person_has_birth = False
    in_birt_block = False

    def finalize_person():
        nonlocal total_persons, total_men, total_women
        nonlocal with_birth_date, without_birth_date
        nonlocal current_person_sex, current_person_has_birth

        if current_record == 'INDI':
            total_persons += 1
            
            # Geslacht verwerken
            if current_person_sex == 'M':
                total_men += 1
            elif current_person_sex == 'F':
                total_women += 1

            # Geboortedatum verwerken
            if current_person_has_birth:
                with_birth_date += 1
            else:
                without_birth_date += 1

    # Inlezen van bestand met ondersteuning voor verschillende coderingen
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
    lines = None
    for enc in encodings:
        try:
            with open(gedcom_path, 'r', encoding=enc) as f:
                lines = f.readlines()
            break
        except (UnicodeDecodeError, Exception):
            continue

    if lines is None:
        raise ValueError(f"Kon het bestand '{gedcom_path}' niet inlezen.")

    for line in lines:
        parsed = parse_gedcom_line(line)
        if not parsed:
            continue

        level, xref, tag, val = parsed

        if level == 0:
            # Sla de vorige persoon op zodra we bij een nieuw hoofdrecord komen
            finalize_person()

            current_record = tag
            current_person_sex = None
            current_person_has_birth = False
            in_birt_block = False

            if tag == 'FAM':
                total_families += 1

        elif current_record == 'INDI':
            if level == 1:
                in_birt_block = False
                if tag == 'SEX':
                    current_person_sex = val.strip().upper()
                elif tag == 'BIRT':
                    in_birt_block = True
                    if val.strip():
                        current_person_has_birth = True

            elif level == 2 and in_birt_block:
                if tag == 'DATE' and val.strip():
                    current_person_has_birth = True

    # Sla de laatste persoon in het bestand op
    finalize_person()

    return {
        'total_persons': total_persons,
        'total_men': total_men,
        'total_women': total_women,
        'with_birth_date': with_birth_date,
        'without_birth_date': without_birth_date,
        'total_families': total_families
    }

def generate_html_report(stats, output_html_path="Gedcom_statistieken.html"):
    """Genereert een overzichtelijk HTML-rapport."""
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
        <h1>📊 GEDCOM Statistieken (uit Gedcom.ged)</h1>
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
    input_gedcom = "Gedcom.ged"
    try:
        stats = analyze_gedcom_file(input_gedcom)
        generate_html_report(stats)
    except FileNotFoundError:
        print(f"Fout: Kan '{input_gedcom}' niet vinden in de huidige map.")
    except Exception as e:
        print(f"Er is een fout opgetreden: {e}")