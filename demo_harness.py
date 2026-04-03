import asyncio
import time
from pathlib import Path

import demo_bot as bot


async def main() -> None:
    bot.initialize_project_structure()

    start_date = bot.datetime(2026, 3, 1)
    end_date = bot.datetime(2026, 3, 28)

    demo_user = await bot.get_cached_user_data(700000001)
    assert demo_user and demo_user["employer"] == "tsel"

    # Use unique IDs based on timestamp to avoid conflicts with previous runs
    unique_suffix = int(time.time()) % 1000000
    registration_user_id = 700000000 + unique_suffix
    unique_nik = f"99{unique_suffix % 10000:04d}"

    await bot.append_user_data(registration_user_id, "harness_user", unique_nik, "", "Harness User", "tsel", "jatim", "")
    approved, _, _ = await bot.approve_user_notification(unique_nik)
    assert approved

    a3 = await bot.format_a3_summary_message(start_date, end_date)
    nas = await bot.format_nas_summary_message(start_date, end_date)
    agency = await bot.format_agency_summary_message(start_date, end_date, user_employer="sf", user_sf_code="SPXM999", user_agency_name="Rajawali Demo Agency", user_region_level="")
    order = await bot.format_ordering_history("AO16670001", None, user_id=700000001)
    ticket = await bot.format_ticketing_history("152612345678", None, 700000001)
    odp_history = await bot.format_odp_history(await bot.fetch_odp_history("ODP-SBY-RAJ/001"))

    odps = bot.get_odps_in_bounding_box(-7.30, -7.28, 112.73, 112.74)
    nearest = bot.find_nearest_odp(-7.2893, 112.7349, odps, 300, offline_mode=True)
    html_path = await bot.generate_nearest_odp_html(
        700000001,
        -7.2893,
        112.7349,
        [],
        site_marker={"latitude": -7.2895, "longitude": 112.7340, "radius": 1000, "distance": 120},
        osrm_enabled=False,
    )
    summary_data = await bot.fetch_summary_odp_map_data(["SURABAYA"], ["YELLOW", "GREEN"], [], [])
    odp_map_data = await bot.fetch_odp_map_data(["SURABAYA"], ["YELLOW", "GREEN"], [], [])
    odp_points = await bot.format_odp_map_data(odp_map_data)
    kmz_path = await bot.generate_odp_map_kmz(700000001, odp_points, "SURABAYA", ["YELLOW", "GREEN"])
    csv_path = await bot.generate_odp_map_csv(odp_map_data, summary_data, "SURABAYA", ["YELLOW", "GREEN"])
    summary_text = bot.demo_backend.fallback_summary_text("sales", "AREA 3", "2026-03-01", "2026-03-28", bot.demo_backend.summary_payload("sales", "A", "AREA 3"))

    assert a3 and nas and agency and order and ticket and odp_history
    assert nearest
    assert Path(html_path).exists()
    assert Path(kmz_path).exists()
    assert Path(csv_path).exists()
    assert summary_text

    print("demo harness passed")


if __name__ == "__main__":
    asyncio.run(main())
