import csv
import io
import os
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


DEMO_TOKEN = os.getenv("DEMO_BOT_TOKEN", "")  # Load from environment - do NOT hardcode tokens
DEMO_NOW = datetime(2026, 3, 28, 9, 0, 0)


DEMO_USERS = [
    {"user_id": "700000001", "username": "@demo_tsel", "nik_tsel": "94211", "user_level": "user", "region_level": "jatim", "is_authorized": "yes", "employer": "tsel", "sf_code": "", "user_name": "Dimas Telkomsel", "agency_name": "", "registered_at": DEMO_NOW.isoformat()},
    {"user_id": "700000002", "username": "@demo_admin", "nik_tsel": "ADM001", "user_level": "admin", "region_level": "jatim", "is_authorized": "yes", "employer": "admin", "sf_code": "", "user_name": "Nadia Admin", "agency_name": "Rajawali Demo Ops", "registered_at": (DEMO_NOW - timedelta(days=3)).isoformat()},
    {"user_id": "700000003", "username": "@demo_sf", "nik_tsel": "UID_SF_001", "user_level": "user", "region_level": "", "is_authorized": "yes", "employer": "sf", "sf_code": "SPXM999", "user_name": "Fajar Sales", "agency_name": "Rajawali Demo Agency", "registered_at": (DEMO_NOW - timedelta(days=5)).isoformat()},
    {"user_id": "700000004", "username": "@demo_pending", "nik_tsel": "95555", "user_level": "user", "region_level": "jateng-diy", "is_authorized": "no", "employer": "tsel", "sf_code": "", "user_name": "Ayu Pending", "agency_name": "", "registered_at": (DEMO_NOW - timedelta(hours=10)).isoformat()},
]

DEMO_DOMAIN_USERS = {
    "94211": {"nik": "94211", "name": "Dimas Telkomsel", "title": "Territory Performance Lead"},
    "95555": {"nik": "95555", "name": "Ayu Pending", "title": "Regional Analyst"},
}

DEMO_AGENCIES = ["Rajawali Demo Agency", "Rajawali Demo Ops", "Mitra Fiber Nusantara"]

DEMO_COMPETITOR_ROWS = [
    {"timestamp": "20260301100000", "provider": "Biznet", "package_name": "Biznet Home 100B", "speed": "100 Mbps", "price": "375000", "gimmicks": "Free router + OTT 3 bulan", "found": "SURABAYA"},
    {"timestamp": "20260303100000", "provider": "MyRepublic", "package_name": "Nova 50", "speed": "50 Mbps", "price": "299000", "gimmicks": "Instalasi promo area Darmo", "found": "SURABAYA"},
    {"timestamp": "20260305110000", "provider": "First Media", "package_name": "Jet 75", "speed": "75 Mbps", "price": "345000", "gimmicks": "Bundling TV basic", "found": "SIDOARJO"},
    {"timestamp": "20260307130000", "provider": "CBN", "package_name": "Fiber 50", "speed": "50 Mbps", "price": "319000", "gimmicks": "Free install", "found": "SEMARANG"},
]

# Simulated competitor packages for /lapor demo extraction
DEMO_COMPETITOR_PACKAGES = [
    {"Provider_Name": "Biznet", "Package_Name": "Biznet Home 100B", "Speed": "100", "Price": "375000", "Gimmick": "Gratis router WiFi + 3 bulan Netflix"},
    {"Provider_Name": "MyRepublic", "Package_Name": "Nova 50", "Speed": "50", "Price": "299000", "Gimmick": "Biaya instalasi Rp 99.000"},
    {"Provider_Name": "First Media", "Package_Name": "Jet 75", "Speed": "75", "Price": "345000", "Gimmick": "Gratis 50 channel TV kabel"},
    {"Provider_Name": "CBN", "Package_Name": "Fiber 50", "Speed": "50", "Price": "319000", "Gimmick": "Gratis instalasi + router"},
    {"Provider_Name": "IconNet", "Package_Name": "IconNet Pro 100", "Speed": "100", "Price": "420000", "Gimmick": "Unlimited tanpa FUP"},
    {"Provider_Name": "IndiHome", "Package_Name": "IndiHome 1P", "Speed": "100", "Price": "385000", "Gimmick": "Gratis 6 bulan Disney+ Hotstar"},
]

DEMO_MATRIX_CSV = """regional,branch_new,wok_vol_2,kab_tsel,provider,speed,price
JATIM,SURABAYA,SURABAYA,SURABAYA,Biznet,100,375000
JATIM,SURABAYA,SURABAYA,SURABAYA,MyRepublic,50,299000
JATIM,SIDOARJO,SIDOARJO,SIDOARJO,First Media,75,345000
JATENG-DIY,SEMARANG,SEMARANG,SEMARANG,CBN,50,319000
"""

import random


def simulate_brochure_extraction() -> List[Dict[str, str]]:
    """
    Simulate AI extraction of competitor package info from a brochure image.
    Returns realistic-looking extracted data for demo purposes.

    Mimics production behavior:
    - Randomly selects 1-3 packages from the demo pool
    - Varies the extraction slightly (sometimes finds 1, sometimes multiple)
    - Returns data in the same format as the real AI extraction
    - Converts Speed and Price to integers (as real AI extraction would)
    """
    # Randomly select 1-3 packages
    num_packages = random.randint(1, 3)
    selected = random.sample(DEMO_COMPETITOR_PACKAGES, min(num_packages, len(DEMO_COMPETITOR_PACKAGES)))

    # Convert to proper format with integer values
    result = []
    for pkg in selected:
        pkg_copy = pkg.copy()
        # Convert Speed to integer (real AI extraction returns integers)
        pkg_copy["Speed"] = int(pkg_copy["Speed"])
        # Convert Price to integer (real AI extraction returns integers)
        pkg_copy["Price"] = int(pkg_copy["Price"])
        # Occasionally add a note to gimmick for variety
        if random.random() < 0.2:
            if pkg_copy.get("Gimmick"):
                pkg_copy["Gimmick"] = pkg_copy["Gimmick"] + " (promo terbatas)"
        result.append(pkg_copy)

    return result


def bot_token() -> str:
    """Get bot token from environment. DEMO_BOT_TOKEN is preferred for demo instances."""
    token = os.getenv("DEMO_BOT_TOKEN") or os.getenv("BOT_TOKEN") or DEMO_TOKEN
    if not token:
        raise ValueError(
            "No bot token found. Set DEMO_BOT_TOKEN or BOT_TOKEN environment variable, "
            "or set DEMO_TOKEN in code for development."
        )
    return token


def base_dir(project_root: Path) -> Path:
    configured = os.getenv("BOT_BASE_DIR")
    return Path(configured) if configured else project_root / ".demo_runtime"


def ensure_demo_environment(base: Path, user_data_file: Path, feedback_file: Path, summary_csv_file: Path, new_csv_file: Path, corrections_csv_file: Path, log_file_path: Path) -> None:
    for path in [base, user_data_file.parent, feedback_file.parent, summary_csv_file.parent, log_file_path.parent]:
        path.mkdir(parents=True, exist_ok=True)
    _write_csv_if_missing(user_data_file, DEMO_USERS)
    _write_csv_if_missing(feedback_file, [])
    _write_csv_if_missing(summary_csv_file, DEMO_COMPETITOR_ROWS)
    _write_csv_if_missing(new_csv_file, DEMO_COMPETITOR_ROWS)
    _write_csv_if_missing(corrections_csv_file, [{"timestamp": DEMO_NOW.strftime("%Y%m%d%H%M%S"), "status": "seeded"}])
    matrix_seed = base / "demo_competitor_matrix.csv"
    if not matrix_seed.exists():
        matrix_seed.write_text(DEMO_MATRIX_CSV, encoding="utf-8")


def _write_csv_if_missing(path: Path, rows: List[Dict[str, object]]) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def get_domain_user(nik: str) -> Optional[Dict[str, str]]:
    return DEMO_DOMAIN_USERS.get(str(nik))


def get_agency_names() -> List[str]:
    return DEMO_AGENCIES[:]


def matrix_csv_path(runtime_base_dir: Path) -> Path:
    return runtime_base_dir / "demo_competitor_matrix.csv"


def matrix_dataframe_csv() -> io.StringIO:
    return io.StringIO(DEMO_MATRIX_CSV)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


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


def fetch_payment_data_batched(bb_ids: List[str], table_name: str = None) -> Dict[str, str]:
    """Return synthetic payment data for multiple BB IDs.

    Returns a dict mapping bb_id -> last_payment_date for use in CVM heatmaps.
    """
    # table_name is ignored in demo mode - we generate synthetic data
    results = {}
    for bb_id in bb_ids:
        # Return dict keyed by bb_id with last_payment_date as value
        # Format matches production: {bb_id: last_payment_date}
        results[bb_id] = "2026-03-01"
    return results


def get_payment_history_table_name(end_date, user_id: int = None) -> str:
    """Return a synthetic payment history table name for demo purposes."""
    period = end_date.strftime('%Y%m')
    return f"bot_cb_profile_history_{period}"


ORDER_MAIN = {
    "order_id": "AO16670001",
    "c_wonum": "WO77889901",
    "region": "JATIM",
    "branch": "SURABAYA",
    "wok": "SURABAYA BARAT",
    "sto_co": "RKT",
    "kabupaten": "SURABAYA",
    "service_id": "152612345678",
    "product_commercial_name": "IndiHome 100 Mbps",
    "channel_name": "Channel Partner",
    "sf_code": "SPXM999",
    "sf_company_name": "Rajawali Demo Agency",
    "c_chief_name": "Budi Teknisi",
    "odp_name": "ODP-SBY-RAJ/001",
    "latitude": "-7.289300",
    "longitude": "112.734900",
    "order_ts": _iso(DEMO_NOW - timedelta(days=5, hours=4)),
    "re_ts": _iso(DEMO_NOW - timedelta(days=5, hours=2)),
    "ps_ts": _iso(DEMO_NOW - timedelta(days=3, hours=7)),
    "completed_ts": _iso(DEMO_NOW - timedelta(days=3, hours=1)),
    "fallout_reason": "Rute kabel penuh, survey alternatif pada -7.291100,112.735800",
}

ORDER_HISTORY_ROWS = [
    {**ORDER_MAIN, "order_rank": 1, "provi_group": "COMPLETED", "process_state": "COMPLETED", "last_update": _iso(DEMO_NOW - timedelta(days=3, hours=1)), "latest_update": _iso(DEMO_NOW - timedelta(days=3, hours=1)), "fallout_category": ""},
    {**ORDER_MAIN, "order_rank": 2, "provi_group": "INSTALLATION", "process_state": "ONSITE", "last_update": _iso(DEMO_NOW - timedelta(days=4, hours=2)), "latest_update": _iso(DEMO_NOW - timedelta(days=4, hours=2)), "fallout_category": ""},
    {**ORDER_MAIN, "order_rank": 3, "provi_group": "FALLOUT", "process_state": "SURVEY", "last_update": _iso(DEMO_NOW - timedelta(days=4, hours=5)), "latest_update": _iso(DEMO_NOW - timedelta(days=4, hours=5)), "fallout_category": "Capacity Constraint"},
]

CUSTOMER_HISTORY_ROWS = [
    {"periode": "202512", "bb_id": "152612345678", "customer_name": "PT Demo Retail Nusantara", "package_name": "IndiHome 100 Mbps", "bill_amount": "425000", "payment_status": "PAID", "payment_date": "2025-12-12", "usage_gb": "612", "usage_pct": "81%", "customer_address": "Jl. Rajawali Demo No. 12, Surabaya", "mobile_no": "081234567890", "latitude": "-7.289300", "longitude": "112.734900"},
    {"periode": "202601", "bb_id": "152612345678", "customer_name": "PT Demo Retail Nusantara", "package_name": "IndiHome 100 Mbps", "bill_amount": "425000", "payment_status": "PAID", "payment_date": "2026-01-13", "usage_gb": "655", "usage_pct": "87%", "customer_address": "Jl. Rajawali Demo No. 12, Surabaya", "mobile_no": "081234567890", "latitude": "-7.289300", "longitude": "112.734900"},
    {"periode": "202602", "bb_id": "152612345678", "customer_name": "PT Demo Retail Nusantara", "package_name": "IndiHome 100 Mbps", "bill_amount": "425000", "payment_status": "PAID", "payment_date": "2026-02-15", "usage_gb": "702", "usage_pct": "93%", "customer_address": "Jl. Rajawali Demo No. 12, Surabaya", "mobile_no": "081234567890", "latitude": "-7.289300", "longitude": "112.734900"},
    {"periode": "202603", "bb_id": "152612345678", "customer_name": "PT Demo Retail Nusantara", "package_name": "IndiHome 100 Mbps", "bill_amount": "425000", "payment_status": "UNBILLED", "payment_date": "", "usage_gb": "588", "usage_pct": "78%", "customer_address": "Jl. Rajawali Demo No. 12, Surabaya", "mobile_no": "081234567890", "latitude": "-7.289300", "longitude": "112.734900"},
]

MULTICON_ROW = {"bb_id": "152612345678", "customer_address": "Jl. Rajawali Demo No. 12, Surabaya", "mobile_no": "081234567890"}

TICKET_ROWS = [
    {"c_service_no": "152612345678", "c_id_ticket": "INC27512345", "c_ticket_id_gamas": "GMS-202603-1001", "datecreated": _iso(DEMO_NOW - timedelta(days=2, hours=5)), "datemodified": _iso(DEMO_NOW - timedelta(days=2, hours=1)), "c_details": "Gangguan redaman tinggi pada dropcore, teknisi melakukan resplicing dan normal kembali.", "c_action_status": "Closed"},
    {"c_service_no": "152612345678", "c_id_ticket": "INC27511111", "c_ticket_id_gamas": "GMS-202602-8891", "datecreated": _iso(DEMO_NOW - timedelta(days=14)), "datemodified": _iso(DEMO_NOW - timedelta(days=13, hours=20)), "c_details": "Modem reboot berulang akibat adaptor lemah.", "c_action_status": "Resolved"},
    {"c_service_no": "152612345678", "c_id_ticket": "INC27510002", "c_ticket_id_gamas": "", "datecreated": _iso(DEMO_NOW - timedelta(days=42)), "datemodified": _iso(DEMO_NOW - timedelta(days=41, hours=18)), "c_details": "Relokasi perangkat ke ruangan kasir.", "c_action_status": "Closed"},
]

ODP_HISTORY_ROWS = [
    {"odp_name": "ODP-SBY-RAJ/001", "latitude": -7.2891, "longitude": 112.7350, "sto": "RKT", "branch": "SURABAYA", "kab_tsel": "SURABAYA", "total_port": 16, "avai_port": 4, "used": 12, "occ_1": 0.75, "occ_2": "YELLOW", "status": "YELLOW", "golive_date": "2025-07-11", "month": "202603", "week": "W4", "event_date": "2026-03-26", "is_newodp": 1, "old_ct0_potential_port": 1, "avg_ct0_los": 2.5, "ct0_bb_id": "152612345678"},
    {"odp_name": "ODP-SBY-RAJ/001", "latitude": -7.2891, "longitude": 112.7350, "sto": "RKT", "branch": "SURABAYA", "kab_tsel": "SURABAYA", "total_port": 16, "avai_port": 5, "used": 11, "occ_1": 0.6875, "occ_2": "YELLOW", "status": "YELLOW", "golive_date": "2025-07-11", "month": "202603", "week": "W3", "event_date": "2026-03-19", "is_newodp": 1, "old_ct0_potential_port": 1, "avg_ct0_los": 2.0, "ct0_bb_id": "152612345678"},
    {"odp_name": "ODP-SBY-RAJ/001", "latitude": -7.2891, "longitude": 112.7350, "sto": "RKT", "branch": "SURABAYA", "kab_tsel": "SURABAYA", "total_port": 16, "avai_port": 8, "used": 8, "occ_1": 0.5, "occ_2": "GREEN", "status": "GREEN", "golive_date": "2025-07-11", "month": "202602", "week": "W4", "event_date": "2026-02-27", "is_newodp": 1, "old_ct0_potential_port": 0, "avg_ct0_los": 1.2, "ct0_bb_id": ""},
]

ODP_POINTS = [
    # SURABAYA
    {"odp_name": "ODP-SBY-RAJ/001", "odp_index": "001", "latitude": -7.2891, "longitude": 112.7350, "avai": 4, "status": "YELLOW", "occ_2": "YELLOW", "branch": "SURABAYA", "sto": "RKT", "kab_tsel": "SURABAYA", "is_total": 16, "used": 12, "golive_date": datetime(2025, 7, 11), "update_date": datetime(2026, 3, 26), "region_sap": "JATIM", "cluster": "Rajawali Core", "new_status": "New", "los_group": "6-12", "los_months": 9},
    {"odp_name": "ODP-SBY-RAJ/002", "odp_index": "002", "latitude": -7.2879, "longitude": 112.7362, "avai": 6, "status": "GREEN", "occ_2": "GREEN", "branch": "SURABAYA", "sto": "RKT", "kab_tsel": "SURABAYA", "is_total": 16, "used": 10, "golive_date": datetime(2024, 6, 5), "update_date": datetime(2026, 3, 24), "region_sap": "JATIM", "cluster": "Rajawali Core", "new_status": "Not_New", "los_group": "24-48", "los_months": 21},
    {"odp_name": "ODP-SBY-TIM/003", "odp_index": "003", "latitude": -7.2905, "longitude": 112.7410, "avai": 8, "status": "GREEN", "occ_2": "GREEN", "branch": "SURABAYA", "sto": "SBY", "kab_tsel": "SURABAYA", "is_total": 16, "used": 8, "golive_date": datetime(2024, 8, 15), "update_date": datetime(2026, 3, 25), "region_sap": "JATIM", "cluster": "Surabaya Timur", "new_status": "Not_New", "los_group": "12-24", "los_months": 15},
    {"odp_name": "ODP-SBY-UT/004", "odp_index": "004", "latitude": -7.2650, "longitude": 112.7380, "avai": 3, "status": "ORANGE", "occ_2": "ORANGE", "branch": "SURABAYA", "sto": "SBYUT", "kab_tsel": "SURABAYA", "is_total": 16, "used": 13, "golive_date": datetime(2025, 2, 20), "update_date": datetime(2026, 3, 27), "region_sap": "JATIM", "cluster": "Surabaya Utara", "new_status": "New", "los_group": "0-3", "los_months": 2},
    # SIDOARJO
    {"odp_name": "ODP-SDA-DMO/010", "odp_index": "010", "latitude": -7.4462, "longitude": 112.7182, "avai": 2, "status": "ORANGE", "occ_2": "ORANGE", "branch": "SIDOARJO", "sto": "SDA", "kab_tsel": "SIDOARJO", "is_total": 16, "used": 14, "golive_date": datetime(2025, 12, 17), "update_date": datetime(2026, 3, 27), "region_sap": "JATIM", "cluster": "Sidoarjo Urban", "new_status": "New", "los_group": "0-3", "los_months": 3},
    {"odp_name": "ODP-SDA-GEM/011", "odp_index": "011", "latitude": -7.4550, "longitude": 112.7250, "avai": 5, "status": "YELLOW", "occ_2": "YELLOW", "branch": "SIDOARJO", "sto": "GEM", "kab_tsel": "SIDOARJO", "is_total": 16, "used": 11, "golive_date": datetime(2024, 11, 10), "update_date": datetime(2026, 3, 26), "region_sap": "JATIM", "cluster": "Gedangan", "new_status": "Not_New", "los_group": "6-12", "los_months": 8},
    {"odp_name": "ODP-SDA-PRN/012", "odp_index": "012", "latitude": -7.4620, "longitude": 112.7120, "avai": 7, "status": "GREEN", "occ_2": "GREEN", "branch": "SIDOARJO", "sto": "PRN", "kab_tsel": "SIDOARJO", "is_total": 16, "used": 9, "golive_date": datetime(2024, 3, 5), "update_date": datetime(2026, 3, 25), "region_sap": "JATIM", "cluster": "Porong", "new_status": "Not_New", "los_group": "24-48", "los_months": 28},
    # MALANG
    {"odp_name": "ODP-MLG-KOT/020", "odp_index": "020", "latitude": -7.9662, "longitude": 112.6320, "avai": 6, "status": "GREEN", "occ_2": "GREEN", "branch": "MALANG", "sto": "MLG", "kab_tsel": "MALANG", "is_total": 16, "used": 10, "golive_date": datetime(2024, 5, 15), "update_date": datetime(2026, 3, 25), "region_sap": "JATIM", "cluster": "Malang Kota", "new_status": "Not_New", "los_group": "12-24", "los_months": 18},
    {"odp_name": "ODP-MLG-LMG/021", "odp_index": "021", "latitude": -7.9780, "longitude": 112.6450, "avai": 3, "status": "YELLOW", "occ_2": "YELLOW", "branch": "MALANG", "sto": "LMG", "kab_tsel": "MALANG", "is_total": 16, "used": 13, "golive_date": datetime(2025, 9, 8), "update_date": datetime(2026, 3, 26), "region_sap": "JATIM", "cluster": "Lawang", "new_status": "New", "los_group": "3-6", "los_months": 5},
    {"odp_name": "ODP-MLG-KDR/022", "odp_index": "022", "latitude": -7.9890, "longitude": 112.6580, "avai": 4, "status": "GREEN", "occ_2": "GREEN", "branch": "MALANG", "sto": "KDR", "kab_tsel": "MALANG", "is_total": 16, "used": 12, "golive_date": datetime(2024, 10, 20), "update_date": datetime(2026, 3, 24), "region_sap": "JATIM", "cluster": "Kediri", "new_status": "Not_New", "los_group": "6-12", "los_months": 10},
    # SEMARANG
    {"odp_name": "ODP-SMG-PON/030", "odp_index": "030", "latitude": -6.9662, "longitude": 110.4200, "avai": 5, "status": "GREEN", "occ_2": "GREEN", "branch": "SEMARANG", "sto": "SMG", "kab_tsel": "SEMARANG", "is_total": 16, "used": 11, "golive_date": datetime(2024, 4, 10), "update_date": datetime(2026, 3, 25), "region_sap": "JATENG-DIY", "cluster": "Semarang Pusat", "new_status": "Not_New", "los_group": "12-24", "los_months": 16},
    {"odp_name": "ODP-SMG-UT/031", "odp_index": "031", "latitude": -6.9550, "longitude": 110.4350, "avai": 2, "status": "RED", "occ_2": "RED", "branch": "SEMARANG", "sto": "SMGUT", "kab_tsel": "SEMARANG", "is_total": 16, "used": 14, "golive_date": datetime(2025, 1, 25), "update_date": datetime(2026, 3, 27), "region_sap": "JATENG-DIY", "cluster": "Semarang Utara", "new_status": "New", "los_group": "0-3", "los_months": 1},
    {"odp_name": "ODP-SMG-KDS/032", "odp_index": "032", "latitude": -6.9780, "longitude": 110.4120, "avai": 8, "status": "GREEN", "occ_2": "GREEN", "branch": "SEMARANG", "sto": "KDS", "kab_tsel": "SEMARANG", "is_total": 16, "used": 8, "golive_date": datetime(2024, 7, 18), "update_date": datetime(2026, 3, 24), "region_sap": "JATENG-DIY", "cluster": "Kendalsari", "new_status": "Not_New", "los_group": "24-48", "los_months": 22},
    # DENPASAR (BALI NUSRA)
    {"odp_name": "ODP-DPS-REN/040", "odp_index": "040", "latitude": -8.6500, "longitude": 115.2100, "avai": 4, "status": "YELLOW", "occ_2": "YELLOW", "branch": "DENPASAR", "sto": "DPS", "kab_tsel": "DENPASAR", "is_total": 16, "used": 12, "golive_date": datetime(2025, 3, 12), "update_date": datetime(2026, 3, 26), "region_sap": "BALI NUSRA", "cluster": "Denpasar Renon", "new_status": "New", "los_group": "6-12", "los_months": 10},
    {"odp_name": "ODP-DPS-UT/041", "odp_index": "041", "latitude": -8.6420, "longitude": 115.2250, "avai": 6, "status": "GREEN", "occ_2": "GREEN", "branch": "DENPASAR", "sto": "DPSUT", "kab_tsel": "DENPASAR", "is_total": 16, "used": 10, "golive_date": datetime(2024, 9, 5), "update_date": datetime(2026, 3, 25), "region_sap": "BALI NUSRA", "cluster": "Denpasar Utara", "new_status": "Not_New", "los_group": "12-24", "los_months": 14},
]

SITE_POINTS = [
    {"site_id": "EZNET-SBY-01", "latitude": -7.2895, "longitude": 112.7340, "kabupaten": "SURABAYA"},
    {"site_id": "EZNET-SDA-01", "latitude": -7.4468, "longitude": 112.7180, "kabupaten": "SIDOARJO"},
    {"site_id": "EZNET-MLG-01", "latitude": -7.9670, "longitude": 112.6330, "kabupaten": "MALANG"},
    {"site_id": "EZNET-SMG-01", "latitude": -6.9668, "longitude": 110.4210, "kabupaten": "SEMARANG"},
    {"site_id": "EZNET-DPS-01", "latitude": -8.6510, "longitude": 115.2110, "kabupaten": "DENPASAR"},
]


def _period_dates(period: str) -> List[datetime]:
    base = datetime.strptime(period, "%Y%m")
    return [base + timedelta(days=offset) for offset in (0, 6, 13, 20, 27)]


def _date_row(branch: str, region: str, day: datetime, io: int, re: int, ps: int, tgt: int, ps_total: int, run_rate: float, io_mom: float, re_mom: float, ps_mom: float, wok: Optional[str] = None) -> Dict[str, object]:
    ps_per_io = round((ps_total / io) * 100, 1) if io else 0
    ps_per_re = round((ps_total / re) * 100, 1) if re else 0
    ach = round((ps_total / tgt) * 100, 1) if tgt else 0
    return {
        "branch": branch,
        "wok": wok or f"{branch} CORE",
        "reg": region,
        "full_date": day.strftime("%Y-%m-%d"),
        "short_date": day.strftime("%d/%b"),
        "io": io,
        "re": re,
        "ps": ps,
        "tgt_fm": tgt,
        "tgt_sales": tgt,
        "ps_total": ps_total,
        "ps_per_io": ps_per_io,
        "ps_per_re": ps_per_re,
        "ach": ach,
        "run_rate": run_rate,
        "io_mom": io_mom,
        "re_mom": re_mom,
        "ps_mom": ps_mom,
        "last_updated": _iso(day.replace(hour=18)),
    }


def _build_reporting_rows() -> Dict[str, List[Dict[str, object]]]:
    rows: Dict[str, List[Dict[str, object]]] = {}
    period = "202603"
    days = _period_dates(period)
    rows["a3_branch_summary"] = [
        {"rank": 1, "branch": "surabaya", "region": "jatim", "tgt_fm": 7000, "ps_total": 1420, "ps_per_io": 56.2, "ps_per_re": 63.1, "ach": 20.3, "run_rate": 101.4, "io_mom": 8.1, "re_mom": 6.4, "ps_mom": 9.0, "short_date": "28/Mar", "last_updated": _iso(DEMO_NOW - timedelta(minutes=25))},
        {"rank": 2, "branch": "sidoarjo", "region": "jatim", "tgt_fm": 6100, "ps_total": 1210, "ps_per_io": 51.7, "ps_per_re": 60.5, "ach": 19.8, "run_rate": 98.7, "io_mom": 4.2, "re_mom": 3.8, "ps_mom": 5.1, "short_date": "28/Mar", "last_updated": _iso(DEMO_NOW - timedelta(minutes=20))},
        {"rank": 3, "branch": "malang", "region": "jatim", "tgt_fm": 5600, "ps_total": 1094, "ps_per_io": 48.4, "ps_per_re": 58.0, "ach": 19.5, "run_rate": 97.6, "io_mom": 3.5, "re_mom": 2.1, "ps_mom": 4.8, "short_date": "28/Mar", "last_updated": _iso(DEMO_NOW - timedelta(minutes=20))},
    ]
    rows["a3_daily"] = [
        _date_row("area3", "A3", days[0], 410, 360, 215, 7000, 215, 87.1, 4.2, 2.2, 4.8),
        _date_row("area3", "A3", days[1], 438, 381, 254, 7000, 469, 91.4, 5.1, 3.4, 6.1),
        _date_row("area3", "A3", days[2], 462, 403, 281, 7000, 750, 95.2, 6.2, 4.8, 7.3),
        _date_row("area3", "A3", days[3], 487, 422, 315, 7000, 1065, 98.7, 7.2, 5.4, 8.4),
        _date_row("area3", "A3", days[4], 501, 435, 355, 7000, 1420, 101.4, 8.1, 6.4, 9.0),
    ]
    rows["jatengdiy_daily"] = [_date_row("jatengdiy", "JATENG-DIY", d, io, re, ps, 6800, total, rr, 5.0, 3.9, pm) for d, io, re, ps, total, rr, pm in [(days[0], 210, 184, 124, 124, 82.0, 3.2), (days[1], 222, 193, 139, 263, 85.3, 3.6), (days[2], 235, 201, 152, 415, 88.6, 4.2), (days[3], 248, 212, 165, 580, 91.9, 4.9), (days[4], 260, 219, 178, 758, 94.0, 5.4)]]
    rows["jatim_daily"] = [_date_row("jatim", "JATIM", d, io, re, ps, 7500, total, rr, 7.2, 6.0, pm) for d, io, re, ps, total, rr, pm in [(days[0], 310, 280, 176, 176, 90.1, 5.1), (days[1], 328, 294, 190, 366, 93.4, 5.9), (days[2], 344, 307, 210, 576, 96.2, 6.8), (days[3], 359, 319, 228, 804, 99.1, 7.9), (days[4], 372, 331, 247, 1051, 102.3, 8.5)]]
    rows["balinusra_daily"] = [_date_row("balinusra", "BALI NUSRA", d, io, re, ps, 5300, total, rr, 4.1, 3.7, pm) for d, io, re, ps, total, rr, pm in [(days[0], 142, 126, 81, 81, 74.1, 2.4), (days[1], 151, 133, 90, 171, 77.0, 2.9), (days[2], 158, 141, 97, 268, 80.0, 3.4), (days[3], 166, 149, 108, 376, 82.6, 3.8), (days[4], 174, 156, 117, 493, 85.2, 4.1)]]
    rows["nas_summary"] = [
        {"rank": 1, "ar": "A3", "reg": "JTM", "io": 5120, "re": 4510, "ps": 3012, "ps_day": 118, "run_rate": 101.4, "ps_mom": 9.0, "event_date": "2026-03-28"},
        {"rank": 2, "ar": "A2", "reg": "JBB", "io": 4988, "re": 4301, "ps": 2891, "ps_day": 110, "run_rate": 99.6, "ps_mom": 6.5, "event_date": "2026-03-28"},
        {"rank": 3, "ar": "A1", "reg": "SMT", "io": 4720, "re": 4205, "ps": 2788, "ps_day": 104, "run_rate": 97.8, "ps_mom": 5.2, "event_date": "2026-03-28"},
    ]
    rows["branch_surabaya_daily"] = [_date_row("surabaya", "JATIM", d, io, re, ps, 1420, total, rr, 8.4, 6.8, pm, wok="SURABAYA BARAT") for d, io, re, ps, total, rr, pm in [(days[0], 82, 71, 40, 40, 88.2, 4.5), (days[1], 86, 74, 46, 86, 91.0, 5.1), (days[2], 91, 77, 53, 139, 94.5, 6.2), (days[3], 97, 83, 58, 197, 98.4, 7.5), (days[4], 104, 88, 63, 260, 101.9, 8.8)]]
    rows["branch_surabaya_woks"] = [_date_row("surabaya", "JATIM", d, io, re, ps, 720, total, rr, 7.1, 5.6, pm, wok="SURABAYA BARAT") for d, io, re, ps, total, rr, pm in [(days[0], 40, 36, 21, 21, 86.4, 4.1), (days[1], 44, 39, 24, 45, 89.8, 4.8), (days[2], 46, 41, 28, 73, 93.2, 5.9), (days[3], 49, 44, 30, 103, 96.6, 6.8), (days[4], 52, 47, 34, 137, 99.3, 7.7)]] + [_date_row("surabaya", "JATIM", d, io, re, ps, 700, total, rr, 7.4, 6.0, pm, wok="SURABAYA TIMUR") for d, io, re, ps, total, rr, pm in [(days[0], 42, 35, 19, 19, 87.1, 4.0), (days[1], 42, 35, 22, 41, 90.2, 4.7), (days[2], 45, 36, 25, 66, 93.0, 5.5), (days[3], 48, 39, 28, 94, 96.0, 6.6), (days[4], 52, 41, 29, 123, 98.8, 7.2)]]
    rows["wok_summary_jatim"] = [
        {"branch": "surabaya", "wok": "SURABAYA BARAT", "event_date": "2026-03-28", "tgt_sales": 720, "ps_total": 137, "ps_per_io": 61.4, "ps_per_re": 69.8, "ach": 19.0, "run_rate": 99.3, "io_mom": 7.1, "re_mom": 5.6, "ps_mom": 7.7},
        {"branch": "surabaya", "wok": "SURABAYA TIMUR", "event_date": "2026-03-28", "tgt_sales": 700, "ps_total": 123, "ps_per_io": 53.7, "ps_per_re": 66.8, "ach": 17.6, "run_rate": 98.8, "io_mom": 7.4, "re_mom": 6.0, "ps_mom": 7.2},
        {"branch": "sidoarjo", "wok": "SIDOARJO", "event_date": "2026-03-28", "tgt_sales": 610, "ps_total": 112, "ps_per_io": 49.8, "ps_per_re": 59.2, "ach": 18.4, "run_rate": 97.4, "io_mom": 4.3, "re_mom": 3.9, "ps_mom": 5.1},
    ]
    rows["agency_summary"] = [
        {"agency_name": "Rajawali Demo Agency", "company_name": "Rajawali Demo Agency", "wok": "SURABAYA BARAT", "spv_name": "SPV Demo Barat", "sf_code": "SPXM999", "sf_name": "Fajar Sales", "io": 42, "re": 38, "ps": 24, "ps_to_re": 63.2, "ps_mom": 5.4, "target_wok_agency": 120, "ps_cummulative": 57, "run_rate": 98.4, "formatted_date": "01 Mar 2026 - 28 Mar 2026", "region": "JATIM"},
        {"agency_name": "Rajawali Demo Agency", "company_name": "Rajawali Demo Agency", "wok": "SURABAYA BARAT", "spv_name": "SPV Demo Barat", "sf_code": "SPXM998", "sf_name": "Rina Sales", "io": 39, "re": 34, "ps": 21, "ps_to_re": 61.8, "ps_mom": 4.6, "target_wok_agency": 120, "ps_cummulative": 57, "run_rate": 98.4, "formatted_date": "01 Mar 2026 - 28 Mar 2026", "region": "JATIM"},
    ]
    rows["c3mr_area"] = [{"area_sales": "AREA 3", "event_date": "2026-03-28", "subs": 124500, "subs_with_payment": 109820, "subs_paying_rate": 0.882, "subs_paying_rate_m1": 0.866, "mom_ppt": 0.016}]
    rows["c3mr_region"] = [{"area_sales": "AREA 3", "region_sales": "JATIM", "event_date": "2026-03-28", "subs": 50500, "subs_with_payment": 45240, "subs_paying_rate": 0.896, "subs_paying_rate_m1": 0.875, "mom_ppt": 0.021}, {"area_sales": "AREA 3", "region_sales": "JATENG-DIY", "event_date": "2026-03-28", "subs": 41200, "subs_with_payment": 35680, "subs_paying_rate": 0.866, "subs_paying_rate_m1": 0.851, "mom_ppt": 0.015}]
    rows["c3mr_branch"] = [{"region_sales": "JATIM", "branch": "SURABAYA", "event_date": "2026-03-28", "subs": 14100, "subs_with_payment": 12720, "subs_paying_rate": 0.902, "subs_paying_rate_m1": 0.888, "mom_ppt": 0.014}]
    rows["c3mr_wok"] = [{"branch": "SURABAYA", "wok": "SURABAYA BARAT", "event_date": "2026-03-28", "subs": 6200, "subs_with_payment": 5660, "subs_paying_rate": 0.913, "subs_paying_rate_m1": 0.895, "mom_ppt": 0.018}]
    rows["pranpc_area"] = [{"area": "AREA 3", "event_date": "2026-03-01", "is_paid": "PAID", "count_pranpc": 3210, "previous_month_count": 2988, "mom_growth_rate": 0.074, "share_of_total_pct": 62.3}, {"area": "AREA 3", "event_date": "2026-03-01", "is_paid": "UNPAID", "count_pranpc": 1940, "previous_month_count": 2012, "mom_growth_rate": -0.036, "share_of_total_pct": 37.7}]
    rows["pranpc_region"] = [{"regional": "JATIM", "event_date": "2026-03-01", "is_paid": "PAID", "current_month_total": 1522, "previous_month_total": 1444, "mom_growth_rate": 0.054, "share_of_total_pct": 47.4}, {"regional": "JATENG-DIY", "event_date": "2026-03-01", "is_paid": "PAID", "current_month_total": 1111, "previous_month_total": 1048, "mom_growth_rate": 0.06, "share_of_total_pct": 34.6}]
    rows["pranpc_branch"] = [{"regional": "JATIM", "branch": "SURABAYA", "event_date": "2026-03-01", "is_paid": "PAID", "count_pranpc": 422, "previous_month_count": 399, "mom_growth_rate": 0.058, "share_of_total_pct": 27.7}]
    rows["pranpc_wok"] = [{"branch": "SURABAYA", "wok": "SURABAYA BARAT", "event_date": "2026-03-01", "is_paid": "PAID", "count_pranpc": 204, "previous_month_count": 194, "mom_growth_rate": 0.051, "share_of_total_pct": 48.3}]
    return rows


REPORTING_ROWS = _build_reporting_rows()


def fetch_bot_branch_a3_summary(period: str) -> List[Dict[str, object]]:
    return [dict(row) for row in REPORTING_ROWS["a3_branch_summary"]]


def fetch_bot_region_nas_summary(period: str) -> List[Dict[str, object]]:
    return [dict(row) for row in REPORTING_ROWS["nas_summary"]]


def fetch_bot_a3_daily(period: str) -> List[Dict[str, object]]:
    return [dict(row) for row in REPORTING_ROWS["a3_daily"]]


def fetch_bot_jatengdiy_daily(period: str) -> List[Dict[str, object]]:
    return [dict(row) for row in REPORTING_ROWS["jatengdiy_daily"]]


def fetch_bot_jatim_daily(period: str) -> List[Dict[str, object]]:
    return [dict(row) for row in REPORTING_ROWS["jatim_daily"]]


def fetch_bot_balinusra_daily(period: str) -> List[Dict[str, object]]:
    return [dict(row) for row in REPORTING_ROWS["balinusra_daily"]]


def fetch_bot_a3_period_branches(period: str, branch: str) -> List[Dict[str, object]]:
    return [dict(row) for row in REPORTING_ROWS.get(f"branch_{branch.lower()}_daily", [])]


def fetch_bot_a3_period_woks(period: str, branch: str) -> List[Dict[str, object]]:
    return [dict(row) for row in REPORTING_ROWS.get(f"branch_{branch.lower()}_woks", [])]


def fetch_bot_wok_summary(period: str, region: str) -> List[Dict[str, object]]:
    return [dict(row) for row in REPORTING_ROWS["wok_summary_jatim"] if region.lower().replace("_", "-") in {"jatim", "jtm"}]


def fetch_bot_agency_summary(period: str) -> List[Dict[str, object]]:
    return [dict(row) for row in REPORTING_ROWS["agency_summary"]]


def fetch_ordering_history_orderid(order_id: str) -> List[Dict[str, object]]:
    return [dict(row) for row in ORDER_HISTORY_ROWS] if order_id.upper() == ORDER_MAIN["order_id"] else []


def fetch_ordering_history_wonum(wonum: str) -> List[Dict[str, object]]:
    return [dict(row) for row in ORDER_HISTORY_ROWS] if wonum.upper() == ORDER_MAIN["c_wonum"] else []


def fetch_customer_history(bb_id: str) -> List[Dict[str, object]]:
    return [dict(row) for row in CUSTOMER_HISTORY_ROWS] if str(bb_id) == "152612345678" else []


def fetch_multicon(bb_id: str) -> Dict[str, str]:
    return dict(MULTICON_ROW) if str(bb_id) == "152612345678" else {}


def fetch_ticket_history_by_bbid(bb_id: str) -> List[Dict[str, object]]:
    return [dict(row) for row in TICKET_ROWS] if str(bb_id) == "152612345678" else []


def fetch_ticket_history_by_ticket(ticket_id: str) -> List[Dict[str, object]]:
    return [dict(row) for row in TICKET_ROWS if row["c_id_ticket"] == ticket_id.upper()]


def fetch_odp_history(odp_name: str) -> List[Dict[str, object]]:
    return [dict(row) for row in ODP_HISTORY_ROWS if row["odp_name"].upper() == odp_name.upper()]


def _generate_synthetic_odps(center_lat: float, center_lon: float, count: int = 10) -> List[Dict[str, object]]:
    """Generate synthetic ODP points around a center location."""
    import random
    results = []
    statuses = ["GREEN", "YELLOW", "ORANGE", "RED"]
    stos = ["RKT", "SBY", "SDA", "MLG", "SMG", "DPS"]

    for i in range(count):
        lat = round(center_lat + random.uniform(-0.005, 0.005), 6)
        lon = round(center_lon + random.uniform(-0.005, 0.005), 6)
        status = random.choice(statuses)
        is_total = random.randint(8, 16)
        used = random.randint(0, is_total)

        results.append({
            "odp_name": f"ODP-DEMO-{i+1:03d}",
            "odp_index": f"{i+1:03d}",
            "latitude": lat,
            "longitude": lon,
            "avai": is_total - used,
            "status": status,
            "occ_2": status,
            "branch": "SURABAYA",
            "sto": random.choice(stos),
            "kab_tsel": "SURABAYA",
            "is_total": is_total,
            "used": used,
            "golive_date": datetime(2024, random.randint(1, 12), random.randint(1, 28)),
            "update_date": datetime(2026, 3, random.randint(1, 28)),
            "region_sap": "JATIM",
            "cluster": "Demo Cluster",
            "new_status": random.choice(["New", "Not_New"]),
            "los_group": random.choice(["0-3", "3-6", "6-12", "12-24", "24-48"]),
            "los_months": random.randint(1, 36)
        })

    return results


def _generate_synthetic_sites(center_lat: float, center_lon: float, count: int = 5) -> List[Dict[str, object]]:
    """Generate synthetic competitor site points around a center location."""
    import random
    results = []
    isps = ["EZNET", "MYREP", "BIZNET", "FIRST", "INDIHOME"]

    for i in range(count):
        lat = round(center_lat + random.uniform(-0.004, 0.004), 6)
        lon = round(center_lon + random.uniform(-0.004, 0.004), 6)

        results.append({
            "site_id": f"{random.choice(isps)}-DEMO-{i+1:02d}",
            "latitude": lat,
            "longitude": lon,
            "kabupaten": "SURABAYA"
        })

    return results


def get_odps_in_bounding_box(min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> List[Dict[str, object]]:
    """Get ODP points within bounding box. Auto-generates if insufficient."""
    results = [dict(row) for row in ODP_POINTS if min_lat <= float(row["latitude"]) <= max_lat and min_lon <= float(row["longitude"]) <= max_lon]

    # Auto-generate if insufficient (minimum 5 for meaningful display)
    if len(results) < 5:
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        results = _generate_synthetic_odps(center_lat, center_lon, count=10)

    return results


def get_sites_in_bounding_box(min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> List[Dict[str, object]]:
    """Get competitor sites within bounding box. Auto-generates if insufficient."""
    results = [dict(row) for row in SITE_POINTS if min_lat <= float(row["latitude"]) <= max_lat and min_lon <= float(row["longitude"]) <= max_lon]

    # Auto-generate if insufficient (minimum 3 for meaningful display)
    if len(results) < 3:
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        results = _generate_synthetic_sites(center_lat, center_lon, count=5)

    return results


def fetch_odp_map_data(selected_branches=None, selected_odp_status=None, selected_los_groups=None, selected_new_status=None) -> List[Dict[str, object]]:
    """Fetch ODP map data. Auto-generates if insufficient for selected filters."""
    if not selected_branches or not selected_odp_status:
        return []
    if isinstance(selected_branches, str):
        selected_branches = [selected_branches]
    data = [dict(row) for row in ODP_POINTS if row["branch"] in selected_branches and row["status"] in selected_odp_status]
    if selected_los_groups:
        data = [row for row in data if row.get("los_group") in selected_los_groups]
    if selected_new_status:
        data = [row for row in data if row.get("new_status") in selected_new_status]

    # Auto-generate if insufficient (minimum 10 for meaningful map)
    if len(data) < 10:
        # Use first matching ODP location or default to Surabaya
        if data:
            center_lat = float(data[0]["latitude"])
            center_lon = float(data[0]["longitude"])
        else:
            center_lat, center_lon = -7.289, 112.735  # Default Surabaya
        data = _generate_synthetic_odps(center_lat, center_lon, count=15)

    return data


def fetch_summary_odp_map_data(selected_branches=None, selected_odp_status=None, selected_los_groups=None, selected_new_status=None) -> List[Dict[str, object]]:
    data = fetch_odp_map_data(selected_branches, selected_odp_status, selected_los_groups, selected_new_status)
    grouped = defaultdict(list)
    for row in data:
        grouped[(row["region_sap"], row["kab_tsel"], row["branch"], row["cluster"], row["sto"], row["status"])].append(row)
    summary = []
    for (region, city, branch, cluster, sto, status), rows in grouped.items():
        total_port = sum(int(row["is_total"]) for row in rows)
        total_used = sum(int(row["used"]) for row in rows)
        total_avai = sum(int(row["avai"]) for row in rows)
        summary.append({"region_sap": region, "kab_tsel": city, "branch": branch, "cluster": cluster, "sto": sto, "status": status, "new_status": rows[0]["new_status"], "los_group": rows[0]["los_group"], "avg_los_odp_month": 9.2 if rows[0]["los_group"] == "6-12" else 2.3, "odp_count": len(rows), "all_port": total_port, "total_used_port": total_used, "total_avai_port": total_avai, "avg_occ_sto": (total_used / total_port) if total_port else 0})
    return summary


def fetch_c3mr(level: str) -> List[Dict[str, object]]:
    return [dict(row) for row in REPORTING_ROWS[level]]


def fetch_pranpc(level: str) -> List[Dict[str, object]]:
    return [dict(row) for row in REPORTING_ROWS[level]]


def summary_payload(summary_type: str, territory_type: str, territory_name: str) -> Dict[str, Dict[str, object]]:
    territory_label = f"{territory_type}:{territory_name}"
    current = {"metadata": {"territory": territory_label, "generated_at": DEMO_NOW.isoformat(), "mode": "demo"}}
    previous = {"metadata": {"territory": territory_label, "generated_at": (DEMO_NOW - timedelta(days=30)).isoformat(), "mode": "demo"}}
    if summary_type == "sales":
        current.update({"header_summary": {"io": 5120, "re": 4510, "ps": 3012, "ach": 101.4}, "top_channel_group_ps": [{"channel": "Channel Partner", "ps": 912}], "top_product_commercial_ps": [{"product": "IndiHome 100 Mbps", "ps": 1331}]})
        previous.update({"header_summary": {"io": 4844, "re": 4235, "ps": 2762, "ach": 95.6}})
    elif summary_type == "driver":
        current.update({"get_header_summary": {"active_lis": 39721, "ct0": 412, "caps": 155, "growth_mom": 0.73}, "get_table_summary_branch_speed": [{"branch": territory_name, "mbps0": 4120, "mbps100": 1522}]})
        previous.update({"get_header_summary": {"active_lis": 39412, "ct0": 438, "caps": 162, "growth_mom": 0.51}})
    elif summary_type == "collection":
        current.update({"get_header_summary": {"ach_collection": 88.2, "nominal": 423251000}, "matrix_flag_1": {"m0": 100, "m1": 91, "m2": 84, "m3": 78}, "matrix_flag_2": {"m0": 100, "m1": 82, "m2": 71, "m3": 63}, "ten_seg_flag_1": [{"segment": "Late Payers", "paid": 1140, "unpaid": 620}]})
        previous.update({"get_header_summary": {"ach_collection": 86.6, "nominal": 405000000}})
    elif summary_type == "alpro":
        current.update({"golive_total": {"odp": 121, "port": 1936, "ach": 97.2}, "golive_greenfield": {"odp": 42, "port": 672}, "golive_brownfield": {"odp": 79, "port": 1264}, "microdemand": [{"city": "SURABAYA", "potential": 182}, {"city": "SIDOARJO", "potential": 133}]})
        previous.update({"golive_total": {"odp": 111, "port": 1776, "ach": 93.0}})
    return {"current": current, "previous": previous}


def fallback_summary_text(summary_type: str, territory_name: str, start_date: str, end_date: str, payload: Dict[str, Dict[str, object]]) -> str:
    current = payload.get("current", {})
    if summary_type == "sales":
        header = current.get("header_summary", {})
        return f"Ringkasan demo {territory_name} periode {start_date} s.d. {end_date}. IO {header.get('io', 0):,}, RE {header.get('re', 0):,}, PS {header.get('ps', 0):,}, achievement {header.get('ach', 0)}%. Channel Partner masih dominan dan produk 100 Mbps menjadi kontributor utama."
    if summary_type == "driver":
        header = current.get("get_header_summary", {})
        return f"Driver summary demo {territory_name}. Active LIS {header.get('active_lis', 0):,}, CT0 {header.get('ct0', 0):,}, CAPS {header.get('caps', 0):,}, growth MoM {header.get('growth_mom', 0)}%. Portofolio speed menengah masih dominan dan churn terkendali."
    if summary_type == "collection":
        header = current.get("get_header_summary", {})
        return f"Collection summary demo {territory_name}. Achievement collection {header.get('ach_collection', 0)}% dengan nominal Rp {header.get('nominal', 0):,}. Cohort channel Agency menunjukkan penurunan retention paling tajam pada M2-M3."
    header = current.get("golive_total", {})
    return f"Alpro summary demo {territory_name}. GoLive mencapai {header.get('odp', 0)} ODP atau {header.get('port', 0)} port dengan achievement {header.get('ach', 0)}%. Brownfield masih mendominasi dengan microdemand kuat di Surabaya dan Sidoarjo."


# Churn demo data
CHURN_COORDINATES_HIGH = [
    # SURABAYA - RKT
    {"latitude": -7.2891, "longitude": 112.7350, "sto": "RKT", "customer_segment": "CT1", "revenue": 425000, "risk_score": 0.89},
    {"latitude": -7.2905, "longitude": 112.7362, "sto": "RKT", "customer_segment": "CT2", "revenue": 385000, "risk_score": 0.82},
    {"latitude": -7.2878, "longitude": 112.7338, "sto": "RKT", "customer_segment": "CT1", "revenue": 510000, "risk_score": 0.91},
    {"latitude": -7.2912, "longitude": 112.7345, "sto": "RKT", "customer_segment": "CT3", "revenue": 320000, "risk_score": 0.78},
    # SURABAYA - SBY
    {"latitude": -7.2850, "longitude": 112.7400, "sto": "SBY", "customer_segment": "CT1", "revenue": 480000, "risk_score": 0.87},
    {"latitude": -7.2865, "longitude": 112.7415, "sto": "SBY", "customer_segment": "CT2", "revenue": 395000, "risk_score": 0.80},
    # SIDOARJO - SDA
    {"latitude": -7.4462, "longitude": 112.7182, "sto": "SDA", "customer_segment": "CT1", "revenue": 450000, "risk_score": 0.85},
    {"latitude": -7.4475, "longitude": 112.7195, "sto": "SDA", "customer_segment": "CT3", "revenue": 340000, "risk_score": 0.76},
    # MALANG - MLG
    {"latitude": -7.9662, "longitude": 112.6320, "sto": "MLG", "customer_segment": "CT1", "revenue": 420000, "risk_score": 0.88},
    {"latitude": -7.9678, "longitude": 112.6335, "sto": "MLG", "customer_segment": "CT2", "revenue": 365000, "risk_score": 0.79},
    # SEMARANG - SMG
    {"latitude": -6.9662, "longitude": 110.4200, "sto": "SMG", "customer_segment": "CT1", "revenue": 445000, "risk_score": 0.86},
    {"latitude": -6.9675, "longitude": 110.4215, "sto": "SMG", "customer_segment": "CT3", "revenue": 355000, "risk_score": 0.74},
    # SURABAYA - SBYUT
    {"latitude": -7.25, "longitude": 112.75, "sto": "SBYUT", "customer_segment": "CT1", "revenue": 465000, "risk_score": 0.88},
    {"latitude": -7.252, "longitude": 112.752, "sto": "SBYUT", "customer_segment": "CT2", "revenue": 378000, "risk_score": 0.81},
    # SIDOARJO - GEM
    {"latitude": -7.39, "longitude": 112.71, "sto": "GEM", "customer_segment": "CT1", "revenue": 432000, "risk_score": 0.84},
    {"latitude": -7.392, "longitude": 112.712, "sto": "GEM", "customer_segment": "CT3", "revenue": 325000, "risk_score": 0.75},
    # SIDOARJO - PRN
    {"latitude": -7.45, "longitude": 112.73, "sto": "PRN", "customer_segment": "CT1", "revenue": 418000, "risk_score": 0.83},
    {"latitude": -7.452, "longitude": 112.732, "sto": "PRN", "customer_segment": "CT2", "revenue": 352000, "risk_score": 0.77},
    # MALANG - LMG
    {"latitude": -7.90, "longitude": 112.62, "sto": "LMG", "customer_segment": "CT1", "revenue": 438000, "risk_score": 0.87},
    {"latitude": -7.902, "longitude": 112.622, "sto": "LMG", "customer_segment": "CT3", "revenue": 342000, "risk_score": 0.76},
    # MALANG - KDR
    {"latitude": -7.82, "longitude": 112.02, "sto": "KDR", "customer_segment": "CT1", "revenue": 428000, "risk_score": 0.85},
    {"latitude": -7.822, "longitude": 112.022, "sto": "KDR", "customer_segment": "CT2", "revenue": 368000, "risk_score": 0.78},
    # SEMARANG - SMGUT
    {"latitude": -6.94, "longitude": 110.43, "sto": "SMGUT", "customer_segment": "CT1", "revenue": 452000, "risk_score": 0.86},
    {"latitude": -6.942, "longitude": 110.432, "sto": "SMGUT", "customer_segment": "CT3", "revenue": 362000, "risk_score": 0.74},
    # SEMARANG - KDS
    {"latitude": -6.98, "longitude": 110.41, "sto": "KDS", "customer_segment": "CT1", "revenue": 442000, "risk_score": 0.85},
    {"latitude": -6.982, "longitude": 110.412, "sto": "KDS", "customer_segment": "CT2", "revenue": 372000, "risk_score": 0.79},
    # DENPASAR - DPS
    {"latitude": -8.65, "longitude": 115.22, "sto": "DPS", "customer_segment": "CT1", "revenue": 468000, "risk_score": 0.89},
    {"latitude": -8.652, "longitude": 115.222, "sto": "DPS", "customer_segment": "CT3", "revenue": 358000, "risk_score": 0.77},
    # DENPASAR - DPSUT
    {"latitude": -8.67, "longitude": 115.18, "sto": "DPSUT", "customer_segment": "CT1", "revenue": 455000, "risk_score": 0.88},
    {"latitude": -8.672, "longitude": 115.182, "sto": "DPSUT", "customer_segment": "CT2", "revenue": 388000, "risk_score": 0.82},
]

CHURN_COORDINATES_LOWMID = [
    # SURABAYA - RKT
    {"latitude": -7.2885, "longitude": 112.7358, "sto": "RKT", "customer_segment": "CT4", "revenue": 275000, "risk_score": 0.42},
    {"latitude": -7.2898, "longitude": 112.7341, "sto": "RKT", "customer_segment": "CT5", "revenue": 310000, "risk_score": 0.38},
    # SIDOARJO - SDA
    {"latitude": -7.4471, "longitude": 112.7175, "sto": "SDA", "customer_segment": "CT4", "revenue": 295000, "risk_score": 0.45},
    {"latitude": -7.4485, "longitude": 112.7200, "sto": "SDA", "customer_segment": "CT5", "revenue": 265000, "risk_score": 0.35},
    # MALANG - MLG
    {"latitude": -7.9670, "longitude": 112.6325, "sto": "MLG", "customer_segment": "CT4", "revenue": 285000, "risk_score": 0.40},
    {"latitude": -7.9685, "longitude": 112.6340, "sto": "MLG", "customer_segment": "CT5", "revenue": 255000, "risk_score": 0.32},
    # SEMARANG - SMG
    {"latitude": -6.9670, "longitude": 110.4205, "sto": "SMG", "customer_segment": "CT4", "revenue": 290000, "risk_score": 0.43},
    {"latitude": -6.9682, "longitude": 110.4220, "sto": "SMG", "customer_segment": "CT5", "revenue": 270000, "risk_score": 0.36},
    # SURABAYA - SBY
    {"latitude": -7.285, "longitude": 112.740, "sto": "SBY", "customer_segment": "CT4", "revenue": 285000, "risk_score": 0.42},
    {"latitude": -7.286, "longitude": 112.741, "sto": "SBY", "customer_segment": "CT5", "revenue": 260000, "risk_score": 0.36},
    # SURABAYA - SBYUT
    {"latitude": -7.25, "longitude": 112.75, "sto": "SBYUT", "customer_segment": "CT4", "revenue": 288000, "risk_score": 0.44},
    {"latitude": -7.252, "longitude": 112.752, "sto": "SBYUT", "customer_segment": "CT5", "revenue": 265000, "risk_score": 0.37},
    # SIDOARJO - GEM
    {"latitude": -7.39, "longitude": 112.71, "sto": "GEM", "customer_segment": "CT4", "revenue": 295000, "risk_score": 0.46},
    {"latitude": -7.392, "longitude": 112.712, "sto": "GEM", "customer_segment": "CT5", "revenue": 268000, "risk_score": 0.38},
    # SIDOARJO - PRN
    {"latitude": -7.45, "longitude": 112.73, "sto": "PRN", "customer_segment": "CT4", "revenue": 282000, "risk_score": 0.42},
    {"latitude": -7.452, "longitude": 112.732, "sto": "PRN", "customer_segment": "CT5", "revenue": 255000, "risk_score": 0.35},
    # MALANG - LMG
    {"latitude": -7.90, "longitude": 112.62, "sto": "LMG", "customer_segment": "CT4", "revenue": 298000, "risk_score": 0.45},
    {"latitude": -7.902, "longitude": 112.622, "sto": "LMG", "customer_segment": "CT5", "revenue": 272000, "risk_score": 0.39},
    # MALANG - KDR
    {"latitude": -7.82, "longitude": 112.02, "sto": "KDR", "customer_segment": "CT4", "revenue": 285000, "risk_score": 0.41},
    {"latitude": -7.822, "longitude": 112.022, "sto": "KDR", "customer_segment": "CT5", "revenue": 258000, "risk_score": 0.34},
    # SEMARANG - SMGUT
    {"latitude": -6.94, "longitude": 110.43, "sto": "SMGUT", "customer_segment": "CT4", "revenue": 292000, "risk_score": 0.44},
    {"latitude": -6.942, "longitude": 110.432, "sto": "SMGUT", "customer_segment": "CT5", "revenue": 268000, "risk_score": 0.37},
    # SEMARANG - KDS
    {"latitude": -6.98, "longitude": 110.41, "sto": "KDS", "customer_segment": "CT4", "revenue": 288000, "risk_score": 0.43},
    {"latitude": -6.982, "longitude": 110.412, "sto": "KDS", "customer_segment": "CT5", "revenue": 262000, "risk_score": 0.36},
    # DENPASAR - DPS
    {"latitude": -8.65, "longitude": 115.22, "sto": "DPS", "customer_segment": "CT4", "revenue": 305000, "risk_score": 0.47},
    {"latitude": -8.652, "longitude": 115.222, "sto": "DPS", "customer_segment": "CT5", "revenue": 278000, "risk_score": 0.40},
    # DENPASAR - DPSUT
    {"latitude": -8.67, "longitude": 115.18, "sto": "DPSUT", "customer_segment": "CT4", "revenue": 298000, "risk_score": 0.45},
    {"latitude": -8.672, "longitude": 115.182, "sto": "DPSUT", "customer_segment": "CT5", "revenue": 275000, "risk_score": 0.38},
]

CHURN_SUMMARY = [
    {"sto": "RKT", "customer_segment": "CT1", "user_count": 145, "paid_count": 89, "event_date": "2026-03-28"},
    {"sto": "RKT", "customer_segment": "CT2", "user_count": 112, "paid_count": 67, "event_date": "2026-03-28"},
    {"sto": "RKT", "customer_segment": "CT3", "user_count": 98, "paid_count": 54, "event_date": "2026-03-28"},
    {"sto": "SBY", "customer_segment": "CT1", "user_count": 88, "paid_count": 52, "event_date": "2026-03-28"},
    {"sto": "SBY", "customer_segment": "CT2", "user_count": 76, "paid_count": 45, "event_date": "2026-03-28"},
    {"sto": "SDA", "customer_segment": "CT1", "user_count": 78, "paid_count": 45, "event_date": "2026-03-28"},
    {"sto": "SDA", "customer_segment": "CT3", "user_count": 65, "paid_count": 38, "event_date": "2026-03-28"},
    {"sto": "MLG", "customer_segment": "CT1", "user_count": 92, "paid_count": 55, "event_date": "2026-03-28"},
    {"sto": "MLG", "customer_segment": "CT2", "user_count": 71, "paid_count": 42, "event_date": "2026-03-28"},
    {"sto": "SMG", "customer_segment": "CT1", "user_count": 85, "paid_count": 48, "event_date": "2026-03-28"},
    {"sto": "SMG", "customer_segment": "CT3", "user_count": 58, "paid_count": 32, "event_date": "2026-03-28"},
    # SURABAYA - SBYUT
    {"sto": "SBYUT", "customer_segment": "CT1", "user_count": 82, "paid_count": 48, "event_date": "2026-03-28"},
    {"sto": "SBYUT", "customer_segment": "CT2", "user_count": 68, "paid_count": 40, "event_date": "2026-03-28"},
    {"sto": "SBYUT", "customer_segment": "CT3", "user_count": 55, "paid_count": 32, "event_date": "2026-03-28"},
    {"sto": "SBYUT", "customer_segment": "CT4", "user_count": 42, "paid_count": 25, "event_date": "2026-03-28"},
    {"sto": "SBYUT", "customer_segment": "CT5", "user_count": 38, "paid_count": 22, "event_date": "2026-03-28"},
    # SIDOARJO - GEM
    {"sto": "GEM", "customer_segment": "CT1", "user_count": 75, "paid_count": 44, "event_date": "2026-03-28"},
    {"sto": "GEM", "customer_segment": "CT2", "user_count": 62, "paid_count": 36, "event_date": "2026-03-28"},
    {"sto": "GEM", "customer_segment": "CT3", "user_count": 52, "paid_count": 30, "event_date": "2026-03-28"},
    {"sto": "GEM", "customer_segment": "CT4", "user_count": 40, "paid_count": 23, "event_date": "2026-03-28"},
    {"sto": "GEM", "customer_segment": "CT5", "user_count": 35, "paid_count": 20, "event_date": "2026-03-28"},
    # SIDOARJO - PRN
    {"sto": "PRN", "customer_segment": "CT1", "user_count": 70, "paid_count": 41, "event_date": "2026-03-28"},
    {"sto": "PRN", "customer_segment": "CT2", "user_count": 58, "paid_count": 34, "event_date": "2026-03-28"},
    {"sto": "PRN", "customer_segment": "CT3", "user_count": 48, "paid_count": 28, "event_date": "2026-03-28"},
    {"sto": "PRN", "customer_segment": "CT4", "user_count": 36, "paid_count": 21, "event_date": "2026-03-28"},
    {"sto": "PRN", "customer_segment": "CT5", "user_count": 32, "paid_count": 18, "event_date": "2026-03-28"},
    # MALANG - LMG
    {"sto": "LMG", "customer_segment": "CT1", "user_count": 88, "paid_count": 52, "event_date": "2026-03-28"},
    {"sto": "LMG", "customer_segment": "CT2", "user_count": 72, "paid_count": 42, "event_date": "2026-03-28"},
    {"sto": "LMG", "customer_segment": "CT3", "user_count": 60, "paid_count": 35, "event_date": "2026-03-28"},
    {"sto": "LMG", "customer_segment": "CT4", "user_count": 45, "paid_count": 26, "event_date": "2026-03-28"},
    {"sto": "LMG", "customer_segment": "CT5", "user_count": 40, "paid_count": 23, "event_date": "2026-03-28"},
    # MALANG - KDR
    {"sto": "KDR", "customer_segment": "CT1", "user_count": 78, "paid_count": 46, "event_date": "2026-03-28"},
    {"sto": "KDR", "customer_segment": "CT2", "user_count": 65, "paid_count": 38, "event_date": "2026-03-28"},
    {"sto": "KDR", "customer_segment": "CT3", "user_count": 54, "paid_count": 31, "event_date": "2026-03-28"},
    {"sto": "KDR", "customer_segment": "CT4", "user_count": 42, "paid_count": 24, "event_date": "2026-03-28"},
    {"sto": "KDR", "customer_segment": "CT5", "user_count": 36, "paid_count": 21, "event_date": "2026-03-28"},
    # SEMARANG - SMGUT
    {"sto": "SMGUT", "customer_segment": "CT1", "user_count": 82, "paid_count": 48, "event_date": "2026-03-28"},
    {"sto": "SMGUT", "customer_segment": "CT2", "user_count": 68, "paid_count": 40, "event_date": "2026-03-28"},
    {"sto": "SMGUT", "customer_segment": "CT3", "user_count": 56, "paid_count": 32, "event_date": "2026-03-28"},
    {"sto": "SMGUT", "customer_segment": "CT4", "user_count": 44, "paid_count": 26, "event_date": "2026-03-28"},
    {"sto": "SMGUT", "customer_segment": "CT5", "user_count": 38, "paid_count": 22, "event_date": "2026-03-28"},
    # SEMARANG - KDS
    {"sto": "KDS", "customer_segment": "CT1", "user_count": 85, "paid_count": 48, "event_date": "2026-03-28"},
    {"sto": "KDS", "customer_segment": "CT2", "user_count": 65, "paid_count": 38, "event_date": "2026-03-28"},
    {"sto": "KDS", "customer_segment": "CT3", "user_count": 52, "paid_count": 30, "event_date": "2026-03-28"},
    {"sto": "KDS", "customer_segment": "CT4", "user_count": 42, "paid_count": 25, "event_date": "2026-03-28"},
    {"sto": "KDS", "customer_segment": "CT5", "user_count": 35, "paid_count": 20, "event_date": "2026-03-28"},
    # DENPASAR - DPS
    {"sto": "DPS", "customer_segment": "CT1", "user_count": 92, "paid_count": 55, "event_date": "2026-03-28"},
    {"sto": "DPS", "customer_segment": "CT2", "user_count": 78, "paid_count": 46, "event_date": "2026-03-28"},
    {"sto": "DPS", "customer_segment": "CT3", "user_count": 65, "paid_count": 38, "event_date": "2026-03-28"},
    {"sto": "DPS", "customer_segment": "CT4", "user_count": 52, "paid_count": 30, "event_date": "2026-03-28"},
    {"sto": "DPS", "customer_segment": "CT5", "user_count": 45, "paid_count": 26, "event_date": "2026-03-28"},
    # DENPASAR - DPSUT
    {"sto": "DPSUT", "customer_segment": "CT1", "user_count": 88, "paid_count": 52, "event_date": "2026-03-28"},
    {"sto": "DPSUT", "customer_segment": "CT2", "user_count": 74, "paid_count": 44, "event_date": "2026-03-28"},
    {"sto": "DPSUT", "customer_segment": "CT3", "user_count": 62, "paid_count": 36, "event_date": "2026-03-28"},
    {"sto": "DPSUT", "customer_segment": "CT4", "user_count": 48, "paid_count": 28, "event_date": "2026-03-28"},
    {"sto": "DPSUT", "customer_segment": "CT5", "user_count": 42, "paid_count": 24, "event_date": "2026-03-28"},
]

BRANCH_STO_MAPPING = {
    "SURABAYA": ["RKT", "SBY", "SBYUT"],
    "SIDOARJO": ["SDA", "GEM", "PRN"],
    "MALANG": ["MLG", "LMG", "KDR"],
    "SEMARANG": ["SMG", "SMGUT", "KDS"],
    "DENPASAR": ["DPS", "DPSUT"],
}


def get_branch_stos(branch: str) -> List[str]:
    """Get list of STOs for a branch."""
    return BRANCH_STO_MAPPING.get(branch.upper(), [])


def _get_city_for_sto(sto: str) -> str:
    """Helper to get city name for a given STO."""
    sto_city_mapping = {
        "RKT": "SURABAYA", "SBY": "SURABAYA", "SBYUT": "SURABAYA",
        "SDA": "SIDOARJO", "GEM": "SIDOARJO", "PRN": "SIDOARJO",
        "MLG": "MALANG", "LMG": "MALANG", "KDR": "KEDIRI",
        "SMG": "SEMARANG", "SMGUT": "SEMARANG", "KDS": "SEMARANG",
        "DPS": "DENPASAR", "DPSUT": "DENPASAR"
    }
    return sto_city_mapping.get(sto.upper(), "UNKNOWN")


def _get_default_coords_for_sto(sto: str) -> tuple:
    """Helper to get default coordinates for a given STO region."""
    sto_coords_mapping = {
        "RKT": (-7.289, 112.735), "SBY": (-7.285, 112.740), "SBYUT": (-7.25, 112.75),
        "SDA": (-7.447, 112.718), "GEM": (-7.39, 112.71), "PRN": (-7.45, 112.73),
        "MLG": (-7.967, 112.632), "LMG": (-7.90, 112.62), "KDR": (-7.82, 112.02),
        "SMG": (-6.967, 110.420), "SMGUT": (-6.94, 110.43), "KDS": (-6.98, 110.41),
        "DPS": (-8.65, 115.22), "DPSUT": (-8.67, 115.18)
    }
    return sto_coords_mapping.get(sto.upper(), (-7.25, 112.75))  # Default to Surabaya


def get_churn_stos() -> List[str]:
    """Get all available STOs for churn analysis."""
    stos = []
    for branch_stos in BRANCH_STO_MAPPING.values():
        stos.extend(branch_stos)
    return list(set(stos))


def fetch_ten_segment_cvm_summary(sto: str, months: List[str] = None) -> List[Dict[str, object]]:
    """Demo data for ten segment CVM summary."""
    return [dict(row) for row in CHURN_SUMMARY if row["sto"] == sto]


def fetch_ten_segment_cvm_summary_churnrisk(sto: str, months: List[str] = None) -> List[Dict[str, object]]:
    """Demo data for ten segment CVM summary with churn risk grouping."""
    return [dict(row) for row in CHURN_SUMMARY if row["sto"] == sto]


def fetch_available_segments_for_location_based(user_id: int = None) -> List[str]:
    """Demo data for available customer segments for location tracking."""
    return [
        "Early Tenure Customer",
        "Network Stability Issue",
        "Billing & Service Complainant",
        "Dormant User",
        "Late Payer",
        "Declined Usage",
        "Competitor Explorer",
        "Stable Usage",
        "Increased Usage",
        "Non-Optimal Experience"
    ]


def fetch_ten_segment_cvm_churn_high(sto: str, months: List[str] = None) -> List[Dict[str, object]]:
    """Demo data for high churn risk coordinates.

    Ensures at least 10 data points per STO for clustering analysis.
    """
    import random
    result = []
    base_coords = []

    for row in CHURN_COORDINATES_HIGH:
        if row["sto"] == sto:
            base_coords.append(row)

    # Use base coordinates if available
    for row in base_coords:
        item = {
            "bb_id": f"BB_{row['sto']}_{random.randint(1000, 9999)}",
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "customer_segment": row["customer_segment"],
            "sto": row["sto"],
            "rev_all": row["revenue"],
            "prop_cat": "03. High",
            "hvc_cat": "HVC" if row["risk_score"] > 0.8 else "MVC",
            "city": _get_city_for_sto(row["sto"]),
            "address": f"Jl. {row['sto']} Demo Address"
        }
        result.append(item)

    # Generate additional points if needed (minimum 10 for clustering)
    min_points = 10
    if len(result) < min_points:
        # Get base coordinates to generate around
        if base_coords:
            base_lat = base_coords[0]["latitude"]
            base_lon = base_coords[0]["longitude"]
        else:
            # Fallback coordinates based on STO region
            base_lat, base_lon = _get_default_coords_for_sto(sto)

        segments_high = ["CT1", "CT2", "CT3"]
        for i in range(min_points - len(result)):
            result.append({
                "bb_id": f"BB_{sto}_{random.randint(1000, 9999)}",
                "latitude": round(base_lat + random.uniform(-0.008, 0.008), 6),
                "longitude": round(base_lon + random.uniform(-0.008, 0.008), 6),
                "customer_segment": random.choice(segments_high),
                "sto": sto,
                "rev_all": random.randint(350000, 550000),
                "prop_cat": "03. High",
                "hvc_cat": random.choice(["HVC", "MVC"]),
                "city": _get_city_for_sto(sto),
                "address": f"Jl. {sto} Demo Address {i+1}"
            })

    return result


def fetch_ten_segment_cvm_churn_lowmid(sto: str, months: List[str] = None) -> List[Dict[str, object]]:
    """Demo data for low-mid churn risk coordinates.

    Ensures at least 10 data points per STO for clustering analysis.
    """
    import random
    result = []
    base_coords = []

    for row in CHURN_COORDINATES_LOWMID:
        if row["sto"] == sto:
            base_coords.append(row)

    # Use base coordinates if available
    for row in base_coords:
        item = {
            "bb_id": f"BB_{row['sto']}_{random.randint(1000, 9999)}",
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "customer_segment": row["customer_segment"],
            "sto": row["sto"],
            "rev_all": row["revenue"],
            "prop_cat": "02. Mid" if row["customer_segment"] == "CT4" else "01. Low",
            "hvc_cat": "MVC",
            "city": _get_city_for_sto(row["sto"]),
            "address": f"Jl. {row['sto']} Demo Address"
        }
        result.append(item)

    # Generate additional points if needed (minimum 10 for clustering)
    min_points = 10
    if len(result) < min_points:
        # Get base coordinates to generate around
        if base_coords:
            base_lat = base_coords[0]["latitude"]
            base_lon = base_coords[0]["longitude"]
        else:
            # Fallback coordinates based on STO region
            base_lat, base_lon = _get_default_coords_for_sto(sto)

        segments_lowmid = ["CT4", "CT5"]
        for i in range(min_points - len(result)):
            result.append({
                "bb_id": f"BB_{sto}_{random.randint(1000, 9999)}",
                "latitude": round(base_lat + random.uniform(-0.008, 0.008), 6),
                "longitude": round(base_lon + random.uniform(-0.008, 0.008), 6),
                "customer_segment": random.choice(segments_lowmid),
                "sto": sto,
                "rev_all": random.randint(250000, 350000),
                "prop_cat": "02. Mid" if random.random() > 0.5 else "01. Low",
                "hvc_cat": "MVC",
                "city": _get_city_for_sto(sto),
                "address": f"Jl. {sto} Demo Address {i+1}"
            })

    return result


def fetch_ten_segment_cvm(sto: str, segment: str, months: List[str] = None) -> List[Dict[str, object]]:
    """Demo data for specific segment CVM data with coordinates for heatmap."""
    import random
    result = []
    # Combine HIGH and LOWMID coordinates
    all_coords = CHURN_COORDINATES_HIGH + CHURN_COORDINATES_LOWMID
    for row in all_coords:
        if row["sto"] == sto and row["customer_segment"].upper() == segment.upper():
            item = {
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "customer_segment": row["customer_segment"],
                "sto": row["sto"],
                "bb_id": f"BB_{row['sto']}_{random.randint(1000, 9999)}",
                "ont_category": "RES",
                "city": "SURABAYA" if row["sto"] in ["RKT", "SBY", "SBYUT"] else
                        "SIDOARJO" if row["sto"] in ["SDA", "GEM", "PRN"] else
                        "MALANG" if row["sto"] in ["MLG", "LMG", "KDR"] else
                        "SEMARANG" if row["sto"] in ["SMG", "SMGUT", "KDS"] else "DENPASAR"
            }
            result.append(item)
    return result


def fetch_ten_segment_cvm_all(sto: str, months: List[str] = None) -> List[Dict[str, object]]:
    """Demo data for all ten segment CVM data with coordinates for heatmap."""
    import random
    result = []
    # Combine HIGH and LOWMID coordinates
    all_coords = CHURN_COORDINATES_HIGH + CHURN_COORDINATES_LOWMID
    for row in all_coords:
        if row["sto"] == sto:
            item = {
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "customer_segment": row["customer_segment"],
                "sto": row["sto"],
                "bb_id": f"BB_{row['sto']}_{random.randint(1000, 9999)}",
                "ont_category": "RES",
                "city": "SURABAYA" if row["sto"] in ["RKT", "SBY", "SBYUT"] else
                        "SIDOARJO" if row["sto"] in ["SDA", "GEM", "PRN"] else
                        "MALANG" if row["sto"] in ["MLG", "LMG", "KDR"] else
                        "SEMARANG" if row["sto"] in ["SMG", "SMGUT", "KDS"] else "DENPASAR"
            }
            result.append(item)
    # Also add summary data for segments not in coordinates
    for row in CHURN_SUMMARY:
        if row["sto"] == sto:
            # Generate approximate coordinates based on STO
            base_lat = -7.25 if row["sto"] in ["RKT", "SBY", "SBYUT"] else \
                       -7.42 if row["sto"] in ["SDA", "GEM", "PRN"] else \
                       -7.90 if row["sto"] in ["MLG", "LMG", "KDR"] else \
                       -6.96 if row["sto"] in ["SMG", "SMGUT", "KDS"] else -8.65
            base_lon = 112.74 if row["sto"] in ["RKT", "SBY", "SBYUT"] else \
                       112.72 if row["sto"] in ["SDA", "GEM", "PRN"] else \
                       112.63 if row["sto"] in ["MLG", "LMG", "KDR"] else \
                       110.42 if row["sto"] in ["SMG", "SMGUT", "KDS"] else 115.22
            item = {
                "latitude": base_lat + random.uniform(-0.01, 0.01),
                "longitude": base_lon + random.uniform(-0.01, 0.01),
                "customer_segment": row["customer_segment"],
                "sto": row["sto"],
                "bb_id": f"BB_{row['sto']}_{random.randint(1000, 9999)}",
                "ont_category": "RES",
                "city": "SURABAYA" if row["sto"] in ["RKT", "SBY", "SBYUT"] else
                        "SIDOARJO" if row["sto"] in ["SDA", "GEM", "PRN"] else
                        "MALANG" if row["sto"] in ["MLG", "LMG", "KDR"] else
                        "SEMARANG" if row["sto"] in ["SMG", "SMGUT", "KDS"] else "DENPASAR"
            }
            result.append(item)
    return result


def get_last_n_months_demo(n: int = 3) -> List[str]:
    """Get last n months in YYYYMM format for demo."""
    base = datetime(2026, 3, 1)  # Demo date is March 2026
    months = []
    for i in range(n):
        month = base.month - i
        year = base.year
        if month <= 0:
            month += 12
            year -= 1
        months.append(f"{year}{month:02d}")
    return list(reversed(months))


def fetch_segments_for_sto(sto: str) -> List[str]:
    """Get available customer segments for a STO."""
    return ["CT1", "CT2", "CT3", "CT4", "CT5"]


def fetch_segments_for_location(lat: float, lon: float) -> List[Dict[str, object]]:
    """Get segments near a location."""
    return [
        {"sto": "RKT", "segment": "CT1", "distance_km": 0.5},
        {"sto": "RKT", "segment": "CT2", "distance_km": 1.2},
    ]


def fetch_available_psdate() -> List[str]:
    """Get available PS dates for demo."""
    return ["2026-03-28", "2026-03-27", "2026-03-26"]


def fetch_all_branch_names() -> List[str]:
    """Get all branch names for demo."""
    return ["SURABAYA", "SIDOARJO", "MALANG", "SEMARANG", "DENPASAR"]


def get_nas_branches_name() -> List[Dict[str, object]]:
    """Demo data for NAS branches."""
    return [
        {"regional": "JATIM", "branch_new": "SURABAYA"},
        {"regional": "JATIM", "branch_new": "SIDOARJO"},
        {"regional": "JATIM", "branch_new": "MALANG"},
        {"regional": "JATENG-DIY", "branch_new": "SEMARANG"},
        {"regional": "JATENG-DIY", "branch_new": "SOLO"},
        {"regional": "BALI NUSRA", "branch_new": "DENPASAR"},
        {"regional": "BALI NUSRA", "branch_new": "MATARAM"},
    ]


def get_sto_names() -> List[Dict[str, object]]:
    """Demo data for STO names."""
    return [
        {"regional": "JATIM", "branch_new": "SURABAYA", "sto": "RKT"},
        {"regional": "JATIM", "branch_new": "SURABAYA", "sto": "SBY"},
        {"regional": "JATIM", "branch_new": "SURABAYA", "sto": "SBYUT"},
        {"regional": "JATIM", "branch_new": "SIDOARJO", "sto": "SDA"},
        {"regional": "JATIM", "branch_new": "SIDOARJO", "sto": "GEM"},
        {"regional": "JATIM", "branch_new": "SIDOARJO", "sto": "PRN"},
        {"regional": "JATIM", "branch_new": "MALANG", "sto": "MLG"},
        {"regional": "JATIM", "branch_new": "MALANG", "sto": "LMG"},
        {"regional": "JATIM", "branch_new": "MALANG", "sto": "KDR"},
        {"regional": "JATENG-DIY", "branch_new": "SEMARANG", "sto": "SMG"},
        {"regional": "JATENG-DIY", "branch_new": "SEMARANG", "sto": "SMGUT"},
        {"regional": "JATENG-DIY", "branch_new": "SEMARANG", "sto": "KDS"},
        {"regional": "BALI NUSRA", "branch_new": "DENPASAR", "sto": "DPS"},
        {"regional": "BALI NUSRA", "branch_new": "DENPASAR", "sto": "DPSUT"},
    ]


def get_stos_for_branch(branch: str) -> List[str]:
    """Demo data for STOs by branch."""
    sto_mapping = {
        "SURABAYA": ["RKT", "SBY", "SBYUT"],
        "SIDOARJO": ["SDA", "GEM", "PRN"],
        "MALANG": ["MLG", "LMG", "KDR"],
        "SEMARANG": ["SMG", "SMGUT", "KDS"],
        "DENPASAR": ["DPS", "DPSUT"],
    }
    return sto_mapping.get(branch.upper(), [])


def get_wok_for_branch(branch: str) -> List[str]:
    """Demo data for WOKs by branch."""
    wok_mapping = {
        "SURABAYA": ["SURABAYA BARAT", "SURABAYA TIMUR", "SURABAYA UTARA"],
        "SIDOARJO": ["SIDOARJO", "GEDANGAN", "PORONG"],
        "MALANG": ["MALANG KOTA", "LAWANG", "KEDIRI"],
        "SEMARANG": ["SEMARANG PUSAT", "SEMARANG UTARA", "KENDALSARI"],
        "DENPASAR": ["DENPASAR RENON", "DENPASAR UTARA"],
    }
    return wok_mapping.get(branch.upper(), [])


def get_region_names() -> List[str]:
    """Demo data for region names."""
    return ["JATIM", "JATENG-DIY", "BALI NUSRA"]


def get_churn_data_by_location_high(latitude: float, longitude: float) -> list:
    """Demo data for high churn risk coordinates near a location."""
    # Return data from CHURN_COORDINATES_HIGH that's within ~0.01 degrees
    nearby = []
    for entry in CHURN_COORDINATES_HIGH:
        if abs(entry['latitude'] - latitude) <= 0.01 and abs(entry['longitude'] - longitude) <= 0.01:
            nearby.append(dict(entry))
    return nearby


def get_visit_history_for_odps(odp_names: list) -> dict:
    """Demo data for visit history for ODPs."""
    import random
    from datetime import datetime, timedelta

    result = {}
    for odp in odp_names:
        result[odp] = {
            "count": random.randint(0, 5),
            "last_date": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
        }
    return result


def get_latest_ihld_table() -> str:
    """Demo data for latest ihld table name."""
    from datetime import datetime
    return datetime.now().strftime("ih_odp_ihld_%Y%m")


def get_odp_data_by_stos(sto_list: list) -> list:
    """Demo data for ODP data by STOs."""
    import random
    from datetime import datetime, timedelta

    statuses = ["GREEN", "BLUE", "WHITE"]
    branches = ["SURABAYA", "SIDOARJO", "MALANG", "SEMARANG", "DENPASAR"]

    result = []
    for sto in sto_list[:10]:  # Limit to 10 ODPs per STO
        for i in range(2):  # 2 ODPs per STO
            result.append({
                "odp_name": f"ODP-{sto}-{i+1:03d}",
                "latitude": -7.0 + random.uniform(-0.5, 0.5),
                "longitude": 112.5 + random.uniform(-0.5, 0.5),
                "occ_1": "RES",
                "occ_2": random.choice(statuses),
                "kab_tsel": "KOTA",
                "port_avail": random.randint(1, 8),
                "port_total": 8,
                "golive_date": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d'),
                "sto": sto,
                "branch": random.choice(branches),
                "regional": "JATIM"
            })
    return result


def get_odp_data_by_woks(wok_list: list, status_filters: list = None, los_filters: list = None) -> list:
    """Demo data for ODP data by WOKs."""
    import random
    from datetime import datetime, timedelta

    statuses = status_filters or ["GREEN", "BLUE", "WHITE"]

    result = []
    for wok in wok_list[:10]:  # Limit to 10 ODPs per WOK
        for i in range(2):  # 2 ODPs per WOK
            result.append({
                "odp_name": f"ODP-{wok[:3]}-{i+1:03d}",
                "latitude": -7.0 + random.uniform(-0.5, 0.5),
                "longitude": 112.5 + random.uniform(-0.5, 0.5),
                "occ_1": "RES",
                "occ_2": random.choice(statuses),
                "kab_tsel": "KOTA",
                "port_avail": random.randint(1, 8),
                "port_total": 8,
                "golive_date": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d'),
                "sto": wok[:3] if len(wok) >= 3 else "UNK",
                "branch": "SURABAYA",
                "regional": "JATIM",
                "wok": wok
            })
    return result


def get_odp_data_from_fallback_table(odp_names: list) -> list:
    """Demo data for ODP data from fallback table."""
    import random
    from datetime import datetime, timedelta

    result = []
    for odp in odp_names[:5]:
        result.append({
            "odp_name": odp,
            "latitude": -7.0 + random.uniform(-0.5, 0.5),
            "longitude": 112.5 + random.uniform(-0.5, 0.5),
            "occ_1": "RES",
            "occ_2": "GREEN",
            "kab_tsel": "KOTA",
            "port_avail": random.randint(1, 8),
            "port_total": 8,
            "golive_date": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d'),
            "sto": odp[4:7] if len(odp) >= 7 else "UNK",
            "branch": "SURABAYA",
            "regional": "JATIM",
            "wok": f"WOK-{odp[4:7]}"
        })
    return result


def get_odp_data_manual_assignment(odp_names: list) -> list:
    """Demo data for ODP data for manual assignment."""
    import random
    from datetime import datetime, timedelta

    result = []
    for odp in odp_names[:5]:
        result.append({
            "odp_name": odp,
            "latitude": -7.0 + random.uniform(-0.5, 0.5),
            "longitude": 112.5 + random.uniform(-0.5, 0.5),
            "occ_1": "RES",
            "occ_2": "GREEN",
            "kab_tsel": "KOTA",
            "port_avail": random.randint(1, 8),
            "port_total": 8,
            "golive_date": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d'),
            "sto": odp[4:7] if len(odp) >= 7 else "UNK",
            "branch": "SURABAYA",
            "regional": "JATIM",
            "wok": f"WOK-{odp[4:7]}"
        })
    return result


def get_csi_score_for_msisdn(msisdn: str) -> dict:
    """Demo data for CSI score lookup by MSISDN."""
    import random
    import hashlib

    # Generate deterministic but random-looking score based on msisdn
    hash_val = int(hashlib.md5(msisdn.encode()).hexdigest()[:8], 16)
    base_score = (hash_val % 100) / 100.0  # 0.0 to 0.99

    return {
        "msisdn": msisdn,
        "default_probability_score": round(0.05 + base_score * 0.90, 4)  # 0.05 to 0.95
    }


def get_cvm_data_by_location(latitude: float, longitude: float, segment: str, months: list) -> list:
    """Demo data for Ten Segment CVM data by location."""
    # Return data from CHURN_SUMMARY filtered by location proximity
    # For demo, return all data (no location filtering)
    result = []
    for row in CHURN_SUMMARY:
        result.append(dict(row))
    return result


def fetch_c3mr_payment(selected_period: str, bb_id_value: str) -> list:
    """Demo data for C3MR payment lookup."""
    import random
    from datetime import datetime, timedelta

    # Return mock payment date
    days_ago = random.randint(1, 60)
    payment_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    return [{"bb_id": bb_id_value, "paid_date": payment_date}]
