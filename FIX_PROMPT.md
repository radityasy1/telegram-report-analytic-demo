# Fix Ten Segment Demo Data Issue & Complete DEMO_MODE Coverage

## Context
This is a Telegram bot demo application (`telegram_bot_demo`) that uses synthetic demo data instead of connecting to a real database. The `DEMO_MODE` flag is set to `True` by default in `.env`.

**CRITICAL REQUIREMENT**: When `DEMO_MODE=True`, the bot must NEVER attempt to connect to any MySQL database. ALL database calls must have DEMO_MODE checks that return synthetic demo data instead.

## Problem 1: Missing Demo Data for STOs

### Symptom
When testing "10 Segments Tracking" feature in Heatmap Analytics menu:
- Select Branch: SEMARANG
- Select STO: KDS

Returns error:
```
⚠️ Tidak ada data Ten Segment summary untuk STO yang dipilih dalam 3 bulan terakhir.
```

### Root Cause
The demo data arrays in `demo_backend.py` only contain entries for a subset of STOs:

**Currently covered STOs:**
- RKT, SBY, SDA, MLG, SMG (partial)

**Missing STOs that need data:**
| Branch | Missing STOs |
|--------|--------------|
| SURABAYA | SBYUT |
| SIDOARJO | GEM, PRN |
| MALANG | LMG, KDR |
| SEMARANG | SMGUT, KDS |
| DENPASAR | DPS, DPSUT |

### Files to Modify

#### `demo_backend.py` - Lines 456-503

**1. `CHURN_COORDINATES_HIGH` array (lines 456-474)**
Add entries for missing STOs with realistic coordinates:
- SBYUT (Surabaya Utara)
- GEM, PRN (Sidoarjo)
- LMG, KDR (Malang)
- SMGUT, KDS (Semarang)
- DPS, DPSUT (Denpasar)

**2. `CHURN_COORDINATES_LOWMID` array (lines 476-489)**
Add entries for all missing STOs.

**3. `CHURN_SUMMARY` array (lines 491-503)**
Add entries for all missing STOs. Each row needs:
```python
{"sto": "KDS", "customer_segment": "CT1", "user_count": 85, "paid_count": 48, "event_date": "2026-03-28"},
{"sto": "KDS", "customer_segment": "CT2", "user_count": 65, "paid_count": 38, "event_date": "2026-03-28"},
# ... for each segment CT1-CT5 for each missing STO
```

**Approximate coordinates for missing STOs:**
- SBYUT: lat -7.25, lon 112.75
- GEM: lat -7.39, lon 112.71
- PRN: lat -7.45, lon 112.73
- LMG: lat -7.90, lon 112.62
- KDR: lat -7.82, lon 112.02
- SMGUT: lat -6.94, lon 110.43
- KDS: lat -6.98, lon 110.41
- DPS: lat -8.65, lon 115.22
- DPSUT: lat -8.67, lon 115.18

---

## Problem 2: Functions Missing DEMO_MODE Checks

These functions call `execute_query_async()` or `get_db_connection()` without DEMO_MODE checks. When DEMO_MODE is True, these will attempt to connect to the corporate database and fail.

### Functions in `demo_bot.py` that need DEMO_MODE checks:

| Line | Function Name | Issue |
|------|---------------|-------|
| ~4664 | `fetch_payment_data_batched()` | No DEMO_MODE check - calls `execute_query_async` |
| ~12390 | `get_distinct_woks_for_branches()` | No DEMO_MODE check - calls `execute_query_async` |
| ~14000 | `get_churn_data_by_location()` | No DEMO_MODE check - calls `execute_query_async` |
| ~14057 | `get_churn_data_by_location_lowmid()` | No DEMO_MODE check - calls `execute_query_async` |
| ~14068 | `get_odp_data_by_location()` | No DEMO_MODE check - calls `execute_query_async` |
| ~15091 | Visit history query function | No DEMO_MODE check |
| ~15264 | Query function | No DEMO_MODE check |
| ~15299 | Query function | No DEMO_MODE check |
| ~15361 | Query function | No DEMO_MODE check |
| ~15405 | Query function | No DEMO_MODE check |
| ~15441 | Query function | No DEMO_MODE check |
| ~16645 | `get_latest_csi_table()` | No DEMO_MODE check - calls `execute_query_async` |
| ~21100 | PDD calculator query | No DEMO_MODE check |

### Required Fix Pattern
Each function must have a DEMO_MODE check at the beginning:

```python
async def function_name(...):
    if DEMO_MODE:
        return demo_backend.function_name(...)  # or return appropriate demo data
    # ... existing production code
```

### Add demo functions in `demo_backend.py` for:
- `fetch_payment_data_batched()` - Return dict of bb_id to payment dates
- `get_distinct_woks_for_branches()` - Return list of WOK names
- `get_churn_data_by_location()` - Return list of churn coordinates
- `get_churn_data_by_location_lowmid()` - Return list of low-mid churn coordinates
- `get_odp_data_by_location()` - Return list of ODP data
- `get_latest_csi_table()` - Return table name like "ih_msisdn_csi_202603"
- PDD calculator - Return CSI score for MSISDN lookup

---

## Tasks

### Task 1: Fix Demo Data for Missing STOs
1. Open `demo_backend.py`
2. Add entries to `CHURN_COORDINATES_HIGH` for: SBYUT, GEM, PRN, LMG, KDR, SMGUT, KDS, DPS, DPSUT
3. Add entries to `CHURN_COORDINATES_LOWMID` for: SBYUT, GEM, PRN, LMG, KDR, SMGUT, KDS, DPS, DPSUT
4. Add entries to `CHURN_SUMMARY` for: SBYUT, GEM, PRN, LMG, KDR, SMGUT, KDS, DPS, DPSUT
5. Each STO should have data for segments CT1-CT5

### Task 2: Add DEMO_MODE Checks to Database Functions
For each function listed above:
1. Add `if DEMO_MODE:` check at the beginning
2. Return appropriate demo data
3. Add corresponding demo function in `demo_backend.py` if needed

### Task 3: Search for Any Remaining Database Calls Without DEMO_MODE
```bash
# Find all database calls
grep -n "execute_query_async\|get_db_connection" demo_bot.py

# For each result, verify it has a preceding DEMO_MODE check
```

### Task 4: Test All Features in DEMO_MODE
1. Test `/churn` command - should work without database connection
2. Test Heatmap Analytics → 10 Segments Tracking - all STOs should show data
3. Test Heatmap Analytics → Churn Clustering - all STOs should show data
4. Test `/lapor` command - simulated AI flow should work
5. Test PDD Calculator - should work without database

---

## Verification Commands
```bash
# Check all STOs have demo data
python -c "from demo_backend import CHURN_SUMMARY; stos = set(r['sto'] for r in CHURN_SUMMARY); print(f'STOs with data: {sorted(stos)}')"

# Verify no database calls when DEMO_MODE is True
grep -c "if DEMO_MODE:" demo_bot.py  # Should be many
grep -B5 "execute_query_async" demo_bot.py | grep "if DEMO_MODE:"  # Should match most calls
```

## Expected Outcome
- All STOs (RKT, SBY, SBYUT, SDA, GEM, PRN, MLG, LMG, KDR, SMG, SMGUT, KDS, DPS, DPSUT) should have demo data
- No MySQL connection attempts when DEMO_MODE=True
- All bot features work offline with synthetic data