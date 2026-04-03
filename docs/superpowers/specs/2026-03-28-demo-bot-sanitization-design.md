# Demo Bot Sanitization Design

**Goal:** Refactor the demo bot to be completely self-contained with synthetic data only, removing all production database footprints while maintaining structural authenticity (same data shapes, fake values).

---

## Scope

This refactoring affects:
- `demo_bot.py` - Main bot application
- `demo_backend.py` - Synthetic data generators
- `intelligence/app.py` - Dashboard API
- `query_bot.sql` - SQL queries file
- `README.md` - Documentation
- `.env.example` - Environment template

---

## Principles

1. **No production references** - Delete all MySQL code, queries, credentials, and comments about production
2. **Structural authenticity** - Synthetic data must match production data shapes exactly
3. **Commit and forget** - Self-contained, works out of the box after clone
4. **Single code path** - No `if DEMO_MODE:` conditionals, only synthetic data path remains

---

## Changes by File

### 1. demo_bot.py

#### 1.1 Delete MySQL Infrastructure

Remove entirely:
- `import mysql.connector` and related imports
- `import aiomysql` and related imports
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT` environment variables
- `get_db_connection()` function (lines ~467-490)
- `get_db_connection_async()` function (lines ~492-516)
- `USE_ASYNC_DB` flag

#### 1.2 Remove DEMO_MODE Conditional Pattern

Replace every instance of:
```python
if DEMO_MODE:
    return demo_backend.some_function()
else:
    # production database code
    conn = mysql.connector.connect(...)
    ...
```

With:
```python
return demo_backend.some_function()
```

#### 1.3 Functions Requiring DEMO_MODE Check Removal

Based on codebase analysis, these locations need refactoring (approximate line numbers):

| Location | Function | Action |
|----------|----------|--------|
| ~297-310 | Database connection setup | Delete entirely |
| ~398+ | Various handlers | Remove DEMO_MODE check, keep demo branch |
| ~4664 | `fetch_payment_data_batched()` | Route to demo_backend |
| ~12390 | `get_distinct_woks_for_branches()` | Route to demo_backend |
| ~14000 | `get_churn_data_by_location()` | Route to demo_backend |
| ~14057 | `get_churn_data_by_location_lowmid()` | Route to demo_backend |
| ~14068 | `get_odp_data_by_location()` | Route to demo_backend |
| ~15091 | Visit history query | Route to demo_backend |
| ~16645 | `get_latest_csi_table()` | Route to demo_backend |
| ~21100 | PDD calculator query | Route to demo_backend |

#### 1.4 Functions With Missing DEMO_MODE Guards

These functions bypass DEMO_MODE entirely and query production directly. They need synthetic implementations:

| Location | Function | Action |
|----------|----------|--------|
| ~669 | Domain user lookup | Already uses demo_backend |
| ~3775 | Dynamic table query by bb_id | Add demo_backend function |
| ~4435+ | ODP map queries | Add demo_backend function |
| ~10029+ | Nested pagination queries | Add demo_backend function |
| ~12186+ | Ten segment queries | Add demo_backend function |

#### 1.5 Remove DEMO_MODE Variable Declaration

Delete:
```python
DEMO_MODE = demo_backend.is_demo_mode()
```

Delete `is_demo_mode()` function from demo_backend.py.

---

### 2. demo_backend.py

#### 2.1 Delete Obsolete Functions

Remove:
- `is_demo_mode()` - No longer needed

#### 2.2 Add Missing Synthetic Data Functions

Add these new functions:

```python
def fetch_payment_data_batched(bb_ids: List[str]) -> List[Dict]:
    """Synthetic payment data for demo."""
    # Returns same structure as production

def get_distinct_woks_for_branches(branches: List[str]) -> List[str]:
    """Synthetic WOK list for demo."""

def get_churn_data_by_location(lat: float, lon: float, radius: int) -> List[Dict]:
    """Synthetic churn risk data around coordinates."""

def get_churn_data_by_location_lowmid(lat: float, lon: float, radius: int) -> List[Dict]:
    """Synthetic low-mid segment churn data."""

def get_odp_data_by_location(lat: float, lon: float, radius: int) -> List[Dict]:
    """Synthetic ODP points around coordinates."""

def get_visit_history(bb_id: str) -> List[Dict]:
    """Synthetic visit history for customer."""

def get_latest_csi_table() -> str:
    """Return mock CSI table name."""

def get_ten_segment_summary(sto: str, months: int = 3) -> List[Dict]:
    """Synthetic Ten Segment data for STO."""

def fetch_odp_map_summary(branch: str) -> List[Dict]:
    """Synthetic ODP map summary for branch."""

def fetch_order_by_bb_id(bb_id: str) -> Dict:
    """Synthetic order lookup by BB ID."""

def fetch_dynamic_table_data(table_name: str, bb_id: str) -> List[Dict]:
    """Synthetic data for dynamic table queries."""
```

#### 2.3 Data Authenticity Requirements

All synthetic data must match production data shapes:

| Data Type | Required Fields |
|-----------|-----------------|
| User | `user_id`, `username`, `nik_tsel`, `user_level`, `region_level`, `is_authorized`, `employer`, `sf_code`, `user_name`, `agency_name` |
| Order | `order_id`, `c_wonum`, `region`, `branch`, `status`, `created_at`, ... |
| ODP | `odp_name`, `latitude`, `longitude`, `status`, `capacity`, `branch`, `sto` |
| Churn | `msisdn`, `default_probability_score`, `segment`, `location` |
| Payment | `bb_id`, `amount`, `date`, `status`, `channel` |

---

### 3. intelligence/app.py

#### 3.1 Delete MySQL Infrastructure

Remove:
- `import mysql.connector`
- `DB_CONFIG` dictionary
- `mysql.connector.connect()` call

#### 3.2 Replace with Demo Backend

Replace database query with:
```python
import sys
sys.path.append('..')
from demo_backend import fetch_dashboard_data

@app.route('/api/dashboard')
def dashboard():
    return fetch_dashboard_data()
```

---

### 4. query_bot.sql

**Delete entire file.** All queries are production-only and not needed for demo.

---

### 5. README.md

#### 5.1 Remove DEMO_MODE References

Delete sections:
- "How Demo Mode Works" diagram showing toggle
- Environment variables for `DEMO_MODE=0` (production)
- Any mentions of "production mode" or "corporate database"

#### 5.2 Simplify Architecture Section

Replace:
```markdown
## How Demo Mode Works
[diagram showing DEMO_MODE toggle]
```

With:
```markdown
## Architecture

This demo bot runs entirely on synthetic data stored in `.demo_runtime/`. No database connection required.

All data functions in `demo_backend.py` return realistic fake data matching production structures.
```

#### 5.3 Remove Production Prerequisites

Delete:
- Production database credentials
- Proxy configuration for corporate network
- LDAP/Domain services

---

### 6. .env.example

Simplify to demo-only:

```bash
# Demo Bot Configuration
# All settings are optional - defaults work for local demo

BOT_TOKEN=your_telegram_token_here
BOT_BASE_DIR=/optional/path/to/data
```

Remove:
- `DEMO_MODE` variable
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT`
- Proxy settings
- Any production-only variables

---

## Implementation Order

1. **README.md** - Update documentation first (defines intent)
2. **.env.example** - Simplify environment
3. **demo_backend.py** - Add missing synthetic functions
4. **demo_bot.py** - Remove MySQL, remove DEMO_MODE checks, route to demo_backend
5. **intelligence/app.py** - Remove MySQL, route to demo_backend
6. **query_bot.sql** - Delete file
7. **Testing** - Run demo_harness.py to verify

---

## Files Modified

| File | Action |
|------|--------|
| `README.md` | Update, remove DEMO_MODE references |
| `.env.example` | Simplify |
| `demo_backend.py` | Expand with missing functions, remove `is_demo_mode()` |
| `demo_bot.py` | Major refactor - remove MySQL, remove conditionals |
| `intelligence/app.py` | Remove MySQL, route to demo_backend |
| `query_bot.sql` | Delete |

---

## Verification

After refactoring:
- `grep -i "mysql"` returns no matches in `.py` files
- `grep -i "DB_HOST\|DB_USER\|DB_PASSWORD"` returns no matches
- `grep -i "DEMO_MODE"` returns no matches
- `python demo_harness.py` passes all tests
- Bot starts without errors when run locally

---

## Out of Scope

- Adding new features
- Changing bot behavior
- Modifying test data values (unless structure is wrong)
- GTM commands (intentionally disabled in README)