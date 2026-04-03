# Demo Bot Sanitization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all production database footprints from the demo bot, keeping only synthetic data paths with structural authenticity.

**Architecture:** Delete all MySQL code and DEMO_MODE conditionals. Route all data functions through demo_backend.py. The result is a self-contained demo bot with zero production references.

**Tech Stack:** Python, aiogram, pandas, asyncio

---

## Files to Modify

| File | Action |
|------|--------|
| `README.md` | Update - remove DEMO_MODE references |
| `.env.example` | Simplify - demo-only settings |
| `demo_backend.py` | Expand - add missing synthetic functions, remove `is_demo_mode()` |
| `demo_bot.py` | Major refactor - delete MySQL, remove conditionals |
| `intelligence/app.py` | Simplify - remove MySQL |
| `query_bot.sql` | Delete |

---

## Task 1: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Remove "How Demo Mode Works" section**

Find and delete the section showing DEMO_MODE toggle (lines ~215-240):

```markdown
## How Demo Mode Works

### Data Flow

```
User Command
     │
     ▼
demo_bot.py
     │
     ├── DEMO_MODE=True? ──► demo_backend.py (synthetic data)
     │                            │
     │                            └── Returns fake but realistic data
     │
     └── DEMO_MODE=False? ──► Database (production)
                                  │
                                  └── Real queries (disabled in demo)
```
```

Replace with:

```markdown
## Architecture

This demo bot runs entirely on synthetic data. No database connection required.

All data functions in `demo_backend.py` return realistic fake data matching production structures.
```

- [ ] **Step 2: Update Quick Start section**

Remove the "Demo Mode Features" section title and merge into main description. Find:

```markdown
## Demo Mode Features

This demo bot runs entirely on **synthetic data** - no connection to:
```

Replace with:

```markdown
## Features

This bot runs entirely on **synthetic data** - no connection to:
```

- [ ] **Step 3: Remove disabled commands disclaimer**

Find and delete the "Disabled in Demo Mode" section (lines ~112-118).

- [ ] **Step 4: Commit README changes**

```bash
git add README.md
git commit -m "docs: remove DEMO_MODE references, clarify synthetic-only architecture"
```

---

## Task 2: Simplify .env.example

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Replace entire file with demo-only config**

```bash
# ==============================================
# Demo Bot Environment Configuration
# ==============================================
# Copy this file to .env and fill in your values
# IMPORTANT: Never commit .env to version control

# ==============================================
# Telegram Bot Configuration
# ==============================================
# Get your bot token from @BotFather on Telegram
BOT_TOKEN=your_telegram_bot_token_here

# ==============================================
# AI API Keys (Optional - for /lapor image analysis)
# ==============================================
# Google Gemini API key for image-to-text extraction
# Get yours at: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# OpenAI API key (if using OpenAI features)
OPENAI_API_KEY=your_openai_api_key_here

# Google Maps API key (optional - for reverse geocoding)
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# ==============================================
# Data Directory (Optional)
# ==============================================
# Base directory for demo data (defaults to .demo_runtime/)
# BOT_BASE_DIR=/path/to/your/data
```

- [ ] **Step 2: Commit .env.example changes**

```bash
git add .env.example
git commit -m "chore: simplify env config to demo-only settings"
```

---

## Task 3: Expand demo_backend.py

**Files:**
- Modify: `demo_backend.py`

- [ ] **Step 1: Remove is_demo_mode function**

Find and delete:

```python
def is_demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "1").strip().lower() not in {"0", "false", "no", "off"}
```

- [ ] **Step 2: Add synthetic data functions for missing features**

Add these functions after the existing data functions (before the ORDER_MAIN dictionary):

```python
# ==============================================================================
# SYNTHETIC DATA GENERATORS - ALL DATA IS FAKE
# ==============================================================================

def get_distinct_woks_for_branches(branches: List[str]) -> List[str]:
    """Return synthetic WOK names for given branches."""
    branch_woks = {
        "SURABAYA": ["SBY-RAJ", "SBY-KEN", "SBY-JEM"],
        "SIDOARJO": ["SDA-DMO", "SDA-PRN", "SDA-GEM"],
        "MALANG": ["MLG-KOT", "MLG-KDR", "MLG-LMG"],
        "SEMARANG": ["SMG-PON", "SMG-TEM", "SMG-UND"],
        "DENPASAR": ["DPS-REN", "DPS-UBD", "DPS-KUT"],
    }
    result = []
    for branch in branches:
        if branch.upper() in branch_woks:
            result.extend(branch_woks[branch.upper()])
    return result if result else ["DEMO-WOK-001", "DEMO-WOK-002"]


def get_churn_data_by_location(lat: float, lon: float, radius: int = 500) -> List[Dict]:
    """Return synthetic churn risk data around coordinates."""
    import random
    base_lat = lat if lat else -7.2575
    base_lon = lon if lon else 112.7521

    results = []
    for i in range(random.randint(5, 15)):
        results.append({
            "msisdn": f"628{random.randint(1000000000, 9999999999)}",
            "default_probability_score": round(random.uniform(0.1, 0.95), 3),
            "segment": random.choice(["HIGH", "MID", "LOW"]),
            "latitude": round(base_lat + random.uniform(-0.005, 0.005), 6),
            "longitude": round(base_lon + random.uniform(-0.005, 0.005), 6),
            "sto": random.choice(["RKT", "SBY", "SBYUT"]),
            "branch": random.choice(["SURABAYA", "SIDOARJO", "MALANG"]),
        })
    return results


def get_churn_data_by_location_lowmid(lat: float, lon: float, radius: int = 500) -> List[Dict]:
    """Return synthetic low-mid segment churn data around coordinates."""
    data = get_churn_data_by_location(lat, lon, radius)
    return [d for d in data if d["segment"] in ["MID", "LOW"]]


def get_odp_data_by_location(lat: float, lon: float, radius: int = 500) -> List[Dict]:
    """Return synthetic ODP points around coordinates."""
    import random
    base_lat = lat if lat else -7.2575
    base_lon = lon if lon else 112.7521

    odp_names = ["ODP-SBY-RAJ/001", "ODP-SBY-KEN/002", "ODP-SDA-DMO/010",
                 "ODP-MLG-KOT/020", "ODP-SMG-PON/030", "ODP-DPS-REN/040"]

    results = []
    for i, odp in enumerate(odp_names[:random.randint(3, 6)]):
        results.append({
            "odp_name": odp,
            "latitude": round(base_lat + random.uniform(-0.003, 0.003), 6),
            "longitude": round(base_lon + random.uniform(-0.003, 0.003), 6),
            "status": random.choice(["GREEN", "YELLOW", "ORANGE", "RED"]),
            "capacity": random.randint(8, 16),
            "used": random.randint(0, 16),
            "branch": random.choice(["SURABAYA", "SIDOARJO", "MALANG", "SEMARANG", "DENPASAR"]),
            "sto": random.choice(["RKT", "SBY", "SDA", "MLG", "SMG", "DPS"]),
        })
    return results


def get_visit_history(bb_id: str) -> List[Dict]:
    """Return synthetic visit history for customer."""
    from datetime import datetime, timedelta
    import random

    results = []
    base_date = datetime.now()
    for i in range(random.randint(2, 5)):
        visit_date = base_date - timedelta(days=random.randint(1, 90))
        results.append({
            "bb_id": bb_id,
            "visit_date": visit_date.strftime("%Y-%m-%d %H:%M:%S"),
            "visit_type": random.choice(["INSTALLATION", "MAINTENANCE", "SURVEY", "REPAIR"]),
            "technician": random.choice(["T001-ANDI", "T002-BUDI", "T003-CITRA"]),
            "notes": random.choice(["Completed successfully", "Customer not home", "Rescheduled", "Parts needed"]),
            "sto": random.choice(["RKT", "SBY", "SDA", "MLG"]),
        })
    return results


def get_latest_csi_table() -> str:
    """Return mock CSI table name."""
    return "bot_csi_summary_202603"


def get_ten_segment_summary(sto: str, months: int = 3) -> List[Dict]:
    """Return synthetic Ten Segment data for STO."""
    import random
    from datetime import datetime, timedelta

    results = []
    segments = ["PLATINUM", "GOLD", "SILVER", "BRONZE", "NEW", "CHURN_RISK"]

    for segment in segments:
        for i in range(months):
            month_date = datetime.now() - timedelta(days=30 * i)
            results.append({
                "sto": sto.upper(),
                "segment": segment,
                "month": month_date.strftime("%Y%m"),
                "total_customers": random.randint(100, 500),
                "arpu": round(random.uniform(50000, 200000), 0),
                "churn_rate": round(random.uniform(0.01, 0.15), 3),
                "growth_rate": round(random.uniform(-0.05, 0.10), 3),
            })
    return results


def fetch_odp_map_summary(branch: str) -> List[Dict]:
    """Return synthetic ODP map summary for branch."""
    import random

    branch_odp_counts = {
        "SURABAYA": 245,
        "SIDOARJO": 189,
        "MALANG": 156,
        "SEMARANG": 134,
        "DENPASAR": 98,
    }

    count = branch_odp_counts.get(branch.upper(), 50)

    return [{
        "branch": branch.upper(),
        "total_odp": count,
        "green": int(count * 0.6),
        "yellow": int(count * 0.2),
        "orange": int(count * 0.15),
        "red": int(count * 0.05),
        "total_capacity": count * 16,
        "total_used": int(count * 16 * random.uniform(0.5, 0.8)),
    }]


def fetch_order_by_bb_id(bb_id: str) -> Dict:
    """Return synthetic order lookup by BB ID."""
    import random

    return {
        "bb_id": bb_id,
        "order_id": f"AO{random.randint(16660000, 16669999)}",
        "status": random.choice(["COMPLETED", "IN_PROGRESS", "PENDING"]),
        "region": random.choice(["JATIM", "JATENG-DIY", "BALI-NUSRA"]),
        "branch": random.choice(["SURABAYA", "SIDOARJO", "MALANG", "SEMARANG", "DENPASAR"]),
        "created_at": "2026-03-15 10:30:00",
        "updated_at": "2026-03-20 14:45:00",
        "package": random.choice(["INDIEHOME 2P", "INDIEHOME 3P", "ORBIT"]),
        "speed": random.choice(["10", "20", "50", "100"]),
    }


def fetch_dynamic_table_data(table_name: str, bb_id: str) -> List[Dict]:
    """Return synthetic data for dynamic table queries."""
    import random

    # Handle various table types
    if "payment" in table_name.lower():
        return [{
            "bb_id": bb_id,
            "amount": random.randint(100000, 500000),
            "payment_date": "2026-03-15",
            "channel": random.choice(["ECHANNEL", "MYTELKOMSEL", "GERAI"]),
            "status": "SUCCESS",
        }]
    elif "history" in table_name.lower():
        return get_visit_history(bb_id)
    else:
        return [{
            "bb_id": bb_id,
            "data": "No data available for this table",
            "status": "DEMO",
        }]


def fetch_payment_data_batched(bb_ids: List[str]) -> List[Dict]:
    """Return synthetic payment data for multiple BB IDs."""
    import random

    results = []
    for bb_id in bb_ids:
        results.append({
            "bb_id": bb_id,
            "total_payments": random.randint(1, 12),
            "last_payment_date": "2026-03-01",
            "last_payment_amount": random.randint(100000, 500000),
            "avg_payment": random.randint(150000, 350000),
            "payment_channel": random.choice(["ECHANNEL", "MYTELKOMSEL", "GERAI"]),
        })
    return results
```

- [ ] **Step 3: Commit demo_backend.py changes**

```bash
git add demo_backend.py
git commit -m "feat: add synthetic data generators, remove is_demo_mode"
```

---

## Task 4: Refactor demo_bot.py - Remove MySQL Infrastructure

**Files:**
- Modify: `demo_bot.py`

- [ ] **Step 1: Remove MySQL imports**

Find and delete these import lines:
```python
import mysql.connector
import aiomysql
```

- [ ] **Step 2: Remove database credential variables**

Find and delete (lines ~288-292):
```python
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = 3307
db_pool = None
```

- [ ] **Step 3: Remove DEMO_MODE variable and related setup**

Find and delete:
```python
DEMO_MODE = demo_backend.is_demo_mode()
```

And delete:
```python
if not DEMO_MODE:
    if os.getenv("HTTP_PROXY"):
        os.environ["http_proxy"] = os.getenv("HTTP_PROXY")
        os.environ["HTTP_PROXY"] = os.getenv("HTTP_PROXY")
    if os.getenv("HTTPS_PROXY"):
        os.environ["https_proxy"] = os.getenv("HTTPS_PROXY")
        os.environ["HTTPS_PROXY"] = os.getenv("HTTPS_PROXY")
    if os.getenv("NO_PROXY"):
        os.environ["no_proxy"] = os.getenv("NO_PROXY")
```

And delete:
```python
USE_ASYNC_DB = not DEMO_MODE
```

- [ ] **Step 4: Simplify BOT_TOKEN assignment**

Find:
```python
BOT_TOKEN = demo_backend.bot_token() if DEMO_MODE else os.getenv("BOT_TOKEN")
```

Replace with:
```python
BOT_TOKEN = demo_backend.bot_token()
```

- [ ] **Step 5: Remove database connection functions**

Delete these entire functions (lines ~467-516):
```python
def get_db_connection():
    """Establishes and returns a new database connection."""
    try:
        # ... entire function body
        return mysql.connector.connect(**connection_args)
    except mysql.connector.Error as err:
        logger.error(f"Database connection failed: {err}")
        return None

async def get_db_connection_async():
    """Establishes and returns an asynchronous database connection POOL."""
    try:
        # ... entire function body
        return await aiomysql.create_pool(**connection_args, loop=asyncio.get_event_loop())
    except Exception as err:
        logging.error(f"Database connection pool creation failed: {err}", exc_info=True)
        return None
```

- [ ] **Step 6: Commit demo_bot.py infrastructure changes**

```bash
git add demo_bot.py
git commit -m "refactor: remove MySQL imports, credentials, and connection functions"
```

---

## Task 5: Refactor demo_bot.py - Remove DEMO_MODE Conditionals

**Files:**
- Modify: `demo_bot.py`

This task requires finding and replacing all `if DEMO_MODE:` blocks. Each one follows a pattern.

- [ ] **Step 1: Find all DEMO_MODE conditionals**

Run grep to identify all locations:
```bash
grep -n "if DEMO_MODE" demo_bot.py
```

- [ ] **Step 2: Replace each conditional block**

For each `if DEMO_MODE:` block:

Pattern to find:
```python
if DEMO_MODE:
    return demo_backend.some_function(args)
else:
    # production database code
    conn = get_db_connection()
    ...
```

Replace with:
```python
return demo_backend.some_function(args)
```

Pattern to find:
```python
if DEMO_MODE:
    # demo code
    data = demo_backend.some_function()
    # ... process demo data
else:
    # production code
    # ... process production data
```

Replace with just the demo branch code (remove the if/else structure).

- [ ] **Step 3: Handle special cases**

For functions that bypass DEMO_MODE and query production directly, add calls to the new demo_backend functions:

Example - fetch_payment_data_batched:
Find the function and replace the entire body with:
```python
def fetch_payment_data_batched(bb_ids: List[str]) -> List[Dict]:
    return demo_backend.fetch_payment_data_batched(bb_ids)
```

- [ ] **Step 4: Commit conditional removal**

```bash
git add demo_bot.py
git commit -m "refactor: remove all DEMO_MODE conditionals, use demo_backend directly"
```

---

## Task 6: Refactor intelligence/app.py

**Files:**
- Modify: `intelligence/app.py`

- [ ] **Step 1: Remove MySQL import and config**

Find and delete:
```python
import mysql.connector
```

And delete:
```python
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT', 3306))
}
```

And delete:
```python
SQL_QUERY = """
select b.*, a.provider, a.speed, a.price
from `dashboard_provider_matpro` a
right join (select regional,branch_new,wok_vol_2,kab_tsel from `ref_wok_sto_v3_2025` group by 1,2,3,4) b
on a.`found` = b.kab_tsel
"""
```

- [ ] **Step 2: Simplify get_data function**

Find:
```python
def get_data():
    if demo_backend.is_demo_mode():
        return pd.read_csv(demo_backend.matrix_dataframe_csv())
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        df = pd.read_sql(SQL_QUERY, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"DB Error: {e}. Using sample data.")
        return pd.read_csv(io.StringIO(SAMPLE_CSV))
```

Replace with:
```python
def get_data():
    return pd.read_csv(demo_backend.matrix_dataframe_csv())
```

- [ ] **Step 3: Remove SAMPLE_CSV fallback**

Delete:
```python
SAMPLE_CSV = """regional,branch_new,wok_vol_2,kab_tsel,provider,speed,price
JATIM,JEMBER,JEMBER,JEMBER,ID.NET,10,150000
"""
```

- [ ] **Step 4: Commit intelligence/app.py changes**

```bash
git add intelligence/app.py
git commit -m "refactor: remove MySQL from intelligence app, use demo_backend only"
```

---

## Task 7: Delete query_bot.sql

**Files:**
- Delete: `query_bot.sql`

- [ ] **Step 1: Delete the file**

```bash
rm query_bot.sql
git add query_bot.sql
git commit -m "chore: remove production SQL queries file"
```

---

## Task 8: Verification

**Files:**
- None (verification task)

- [ ] **Step 1: Verify no MySQL references remain**

```bash
grep -r "mysql" --include="*.py" . 2>/dev/null || echo "No MySQL references found"
grep -r "DB_HOST\|DB_USER\|DB_PASSWORD\|DB_NAME" --include="*.py" . 2>/dev/null || echo "No DB credentials found"
grep -r "DEMO_MODE" --include="*.py" . 2>/dev/null || echo "No DEMO_MODE references found"
```

Expected output: No matches found (except in comments/docs if any remain).

- [ ] **Step 2: Run test harness**

```bash
python demo_harness.py
```

Expected: All tests pass.

- [ ] **Step 3: Start bot and verify basic commands**

```bash
python demo_bot.py
```

Verify:
- Bot starts without errors
- No database connection attempts in logs
- `/start` command works

---

## Task 9: Final Commit

- [ ] **Step 1: Create summary commit**

```bash
git add -A
git commit -m "refactor: complete demo bot sanitization

- Remove all MySQL imports, connections, and queries
- Remove DEMO_MODE conditionals throughout codebase
- Expand demo_backend.py with all required synthetic data functions
- Simplify .env.example to demo-only settings
- Update README.md to reflect synthetic-only architecture
- Delete query_bot.sql (production queries not needed)

This bot now runs entirely on synthetic data with zero production references."
```

---

## Summary of Changes

| File | Lines Changed | Purpose |
|------|---------------|---------|
| README.md | ~30 | Remove DEMO_MODE docs |
| .env.example | ~60 | Simplify to demo-only |
| demo_backend.py | +200 | Add synthetic data generators |
| demo_bot.py | -300 | Remove MySQL, DEMO_MODE |
| intelligence/app.py | -30 | Remove MySQL |
| query_bot.sql | deleted | Production queries |

---

## Notes

- All synthetic data functions return data structures matching production exactly
- No production queries preserved even as comments
- Bot behavior remains identical from user perspective
- Self-contained for GitHub "commit and forget"