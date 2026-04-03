import os
import pandas as pd
from jinja2 import Template
from dotenv import load_dotenv
import io
import math
import demo_backend

# Load Environment Variables
load_dotenv()

# Define Buckets (Label is Display, Min/Max is Logic)
BUCKETS = [
    {'id': 'b1', 'label': '1-10 Mbps',   'min': 0,   'max': 10},
    {'id': 'b2', 'label': '11-20 Mbps',  'min': 10,  'max': 20},
    {'id': 'b3', 'label': '21-40 Mbps',  'min': 20,  'max': 40},
    {'id': 'b4', 'label': '41-50 Mbps',  'min': 40,  'max': 50},
    {'id': 'b5', 'label': '51-75 Mbps',  'min': 50,  'max': 75},
    {'id': 'b6', 'label': '76-100 Mbps', 'min': 75,  'max': 100},
    {'id': 'b7', 'label': '101-150 Mbps','min': 100, 'max': 150},
    {'id': 'b8', 'label': '151-500 Mbps','min': 150, 'max': 500},
    {'id': 'b9', 'label': '> 500 Mbps',  'min': 500, 'max': 99999}
]

def get_data():
    return pd.read_csv(demo_backend.matrix_dataframe_csv())

def format_currency(value):
    if pd.isna(value): return ""
    return f"{int(value):,}".replace(",", ".")

def get_bucket_id(speed):
    for b in BUCKETS:
        if b['min'] < speed <= b['max']:
            return b['id']
    return None

def process_data(df):
    # 1. CONVERT NUMERICS (Do not drop rows yet!)
    # errors='coerce' turns non-numbers into NaN (Not a Number)
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['speed'] = pd.to_numeric(df['speed'], errors='coerce')
    
    # 2. CLEAN TEXT DATA
    # Ensure location columns are strings and handle NULLs gracefully
    # This prevents grouping errors if the reference table has empty cells
    text_cols = ['regional', 'branch_new', 'wok_vol_2', 'kab_tsel', 'provider']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).replace({r'\\N': '-', 'nan': '-', 'None': '-', '<NA>': '-'}, regex=True)

    # 3. GROUP BY LOCATION
    # Because we didn't drop NAs, this includes territories with no competitor data
    grouped = df.groupby(['regional', 'branch_new', 'wok_vol_2', 'kab_tsel'])
    matrix_rows = []
    
    bucket_ids = [b['id'] for b in BUCKETS]

    for (reg, branch, wok, kab), group in grouped:
        # Create the search string
        search_meta = f"{reg} {branch} {wok} {kab}".lower()
        
        row = {
            'regional': reg,
            'branch': branch,
            'wok': wok,
            'kab': kab,
            'bucket_data': {bid: [] for bid in bucket_ids},
            'search_meta': search_meta,
            'has_data': False # Flag to track if this row is empty
        }
        
        for _, item in group.iterrows():
            # 4. CHECK VALIDITY PER ITEM
            # Only add to bucket if we actually have valid speed AND price
            s = item['speed']
            p = item['price']
            
            if pd.notna(s) and pd.notna(p):
                s = int(s)
                bid = get_bucket_id(s)
                
                if bid:
                    row['has_data'] = True # Mark that this row isn't empty
                    p_fmt = format_currency(p)
                    display_text = f"{s}M: {p_fmt}"
                    
                    row['bucket_data'][bid].append({
                        'provider': item['provider'],
                        'display_text': display_text, 
                        'price_val': p 
                    })
                    
                    # Add provider details to search
                    row['search_meta'] += f" {item['provider']} {p_fmt} {p} {s}mb".lower()
        
        # Sort items inside each bucket by price
        for bid in bucket_ids:
            row['bucket_data'][bid].sort(key=lambda x: x['price_val'])

        matrix_rows.append(row)
        
    return matrix_rows

def generate_html(buckets, matrix_rows):
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Competitor Matrix</title>
        <style>
            :root {
                --border-color: #cbd5e1;
                --header-bg: #b91c1c; 
                --header-text: #ffffff;
                --header-border: #7f1d1d;
                --hover-bg: #fffbeb;
                --text-main: #0f172a;
                --chip-bg: #eff6ff;
                --chip-border: #bfdbfe;
                --chip-text: #1e40af;
                --highlight-match: #fbbf24;
                --highlight-match-text: #000;
            }
            * { box-sizing: border-box; }
            body {
                font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background: #ffffff;
                color: var(--text-main);
                margin: 0;
                padding: 15px;
                font-size: 10px;
            }
            .controls { display: flex; flex-direction: column; gap: 5px; margin-bottom: 15px; position: sticky; left: 0; }
            .controls-row { display: flex; gap: 10px; }
            .search-box { flex: 1; max-width: 500px; padding: 8px 12px; border: 2px solid #b91c1c; border-radius: 4px; font-size: 12px; }
            .hint { font-size: 11px; color: #64748b; font-style: italic; }
            .btn { padding: 6px 15px; background: #059669; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 11px; }
            .btn:hover { background: #047857; }
            .table-wrapper { max-height: 85vh; overflow: auto; border: 1px solid var(--border-color); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
            table { border-collapse: separate; border-spacing: 0; width: 100%; min-width: 1000px; table-layout: fixed; }
            
            thead th {
                position: sticky; top: 0; background: var(--header-bg); color: var(--header-text);
                font-weight: 700; text-align: left; padding: 8px;
                border-bottom: 2px solid var(--header-border); border-right: 1px solid var(--header-border);
                z-index: 20; font-size: 11px; white-space: nowrap;
            }
            th.fix-col, td.fix-col { position: sticky; z-index: 10; border-right: 1px solid #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            th.fix-col { z-index: 30; background: var(--header-bg); color: var(--header-text); border-right: 1px solid var(--header-border); }
            td.fix-col { background: #fff; }

            .col-1 { left: 0; width: 60px; }
            .col-2 { left: 60px; width: 80px; }
            .col-3 { left: 140px; width: 80px; }
            .col-4 { left: 220px; width: 120px; border-right: 2px solid #64748b !important; }

            td.col-1 { color: #991b1b; font-weight: 700; background: #fffdfd; }
            td.col-2 { color: #5b21b6; background: #fdfbff; }
            td.col-3 { color: #374151; }
            td.col-4 { color: #000; font-weight: 700; }
            
            td { padding: 4px 6px; border-bottom: 1px solid var(--border-color); border-right: 1px solid #f1f5f9; vertical-align: top; }
            tr:hover td { background-color: var(--hover-bg) !important; }
            
            .price-stack { display: flex; flex-direction: column; gap: 2px; }
            .chip { display: block; padding: 1px 4px; background: var(--chip-bg); border: 1px solid var(--chip-border); border-radius: 3px; color: var(--chip-text); font-family: "Menlo", monospace; font-size: 9.5px; cursor: help; white-space: nowrap; position: relative; }
            .chip:hover { background: #2563eb; color: white; z-index: 50; }
            .chip:hover::after { content: attr(data-prov); position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%); background: #1e293b; color: #fff; padding: 4px 8px; border-radius: 4px; white-space: nowrap; font-size: 10px; pointer-events: none; z-index: 100; }
            .chip.highlight-hit { background-color: var(--highlight-match); color: var(--highlight-match-text); border-color: #d97706; font-weight: bold; }
            .empty { color: #e2e8f0; text-align: center; }
            .hidden { display: none; }

            tr.row-empty td {
                background-color: #fff1f2 !important; /* Very light red */
                color: #881337;
            }
            /* Ensure sticky columns inherit this color */
            tr.row-empty td.fix-col {
                background-color: #fff1f2 !important;
            }

        </style>
    </head>
    <body>

    <div class="controls">
        <div class="controls-row">
            <input type="text" id="searchInput" class="search-box" placeholder="e.g. Surabaya Biznet, Semarang MyRepublic" onkeyup="filterTable()">
            <button class="btn" onclick="exportTableToExcel('matrixTable', 'competitor_matrix_analysis')">Download Excel</button>
        </div>
        <div class="hint">Tip: <b>Space</b> = AND, <b>Comma</b> = OR. Use <b>"Quotes"</b> for exact phrases with spaces (e.g., <i>"Kota Surabaya" Biznet</i>).</div>
    </div>

    <div class="table-wrapper">
        <table id="matrixTable">
            <thead>
                <tr>
                    <th class="fix-col col-1">Reg</th>
                    <th class="fix-col col-2">Branch</th>
                    <th class="fix-col col-3">WOK</th>
                    <th class="fix-col col-4">City</th>
                    {% for b in buckets %}<th>{{ b.label }}</th>{% endfor %}
                </tr>
            </thead>
            <tbody>
                {% for row in matrix %}
                <tr data-meta="{{ row.search_meta }}" class="{{ 'row-empty' if not row.has_data else '' }}">
                    <td class="fix-col col-1" title="{{ row.regional }}">{{ row.regional }}</td>
                    <td class="fix-col col-2" title="{{ row.branch }}">{{ row.branch }}</td>
                    <td class="fix-col col-3" title="{{ row.wok }}">{{ row.wok }}</td>
                    <td class="fix-col col-4" title="{{ row.kab }}">{{ row.kab }}</td>
                    {% for b in buckets %}
                    <td>
                        {% if row.bucket_data[b.id] %}
                            <div class="price-stack">
                            {% for item in row.bucket_data[b.id] %}
                                <div class="chip" data-prov="{{ item.provider }}" data-val="{{ item.price_val }}" data-search-term="{{ item.provider }} {{ item.display_text }}">
                                    {{ item.display_text }}
                                </div>
                            {% endfor %}
                            </div>
                        {% else %}<div class="empty">&middot;</div>{% endif %}
                    </td>
                    {% endfor %}
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <script>
    function filterTable() {
        const inputRaw = document.getElementById("searchInput").value.toLowerCase();
        function parseTerms(str) {
            const regex = /"([^"]+)"|(\S+)/g;
            const terms = [];
            let match;
            while ((match = regex.exec(str)) !== null) terms.push(match[1] || match[2]);
            return terms;
        }
        const orGroups = inputRaw.split(',');
        const allKeywords = parseTerms(inputRaw);
        const rows = document.getElementById("matrixTable").getElementsByTagName("tr");

        for (let i = 1; i < rows.length; i++) {
            const row = rows[i];
            const meta = row.getAttribute('data-meta') || "";
            let showRow = false;

            if (inputRaw.trim() === "") showRow = true;
            else {
                for (let group of orGroups) {
                    const andTerms = parseTerms(group);
                    if (andTerms.length === 0) continue;
                    let matchAllAnd = true;
                    for (let term of andTerms) if (meta.indexOf(term) === -1) { matchAllAnd = false; break; }
                    if (matchAllAnd) { showRow = true; break; }
                }
            }

            if (showRow) {
                row.classList.remove("hidden");
                const chips = row.getElementsByClassName("chip");
                for (let chip of chips) {
                    const chipMeta = chip.getAttribute('data-search-term').toLowerCase();
                    let highlight = false;
                    if (allKeywords.length > 0) {
                        for (let kw of allKeywords) if (chipMeta.indexOf(kw) > -1) { highlight = true; break; }
                    }
                    if (highlight) chip.classList.add("highlight-hit"); else chip.classList.remove("highlight-hit");
                }
            } else row.classList.add("hidden");
        }
    }

    function exportTableToExcel(tableID, filename = '') {
        var downloadLink;
        var dataType = 'application/vnd.ms-excel';
        var tableSelect = document.getElementById(tableID);
        var clone = tableSelect.cloneNode(true);
        var rows = clone.getElementsByTagName('tr');
        
        for (let row of rows) {
            row.classList.remove('hidden'); 
            let cells = row.cells;
            for (let cell of cells) {
                cell.className = ''; cell.style.overflow = 'visible'; cell.style.whiteSpace = 'normal';
                let stack = cell.querySelector('.price-stack');
                if (stack) {
                    let textParts = [];
                    let chips = stack.querySelectorAll('.chip');
                    chips.forEach(c => { textParts.push(c.getAttribute('data-prov') + ': ' + c.innerText); });
                    cell.innerHTML = textParts.join('<br style="mso-data-placement:same-cell;" />');
                    cell.style.verticalAlign = 'top';
                }
                let empty = cell.querySelector('.empty');
                if (empty) cell.innerHTML = "";
            }
        }
        clone.style.border = '1px solid black';
        var tableHTML = clone.outerHTML.replace(/ /g, '%20');
        filename = filename ? filename + '.xls' : 'excel_data.xls';
        downloadLink = document.createElement("a");
        document.body.appendChild(downloadLink);
        
        if(navigator.msSaveOrOpenBlob){
            var blob = new Blob(['\ufeff', clone.outerHTML], { type: dataType });
            navigator.msSaveOrOpenBlob(blob, filename);
        } else {
            downloadLink.href = 'data:' + dataType + ', ' + tableHTML;
            downloadLink.download = filename;
            downloadLink.click();
        }
        document.body.removeChild(downloadLink);
    }
    </script>

    </body>
    </html>
    """
    template = Template(html_template)
    return template.render(buckets=BUCKETS, matrix=matrix_rows)

def get_matrix_file_object():
    """
    BOT API: Generates HTML and returns BytesIO buffer.
    """
    df = get_data()
    if df is not None and not df.empty:
        matrix = process_data(df)
        html_content = generate_html(BUCKETS, matrix)
        
        file_buffer = io.BytesIO()
        file_buffer.write(html_content.encode('utf-8'))
        file_buffer.seek(0)
        return file_buffer
    return None

if __name__ == "__main__":
    df = get_data()
    if df is not None and not df.empty:
        matrix = process_data(df)
        html = generate_html(BUCKETS, matrix)
        with open("compact_matrix_red_search.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Generated locally.")
