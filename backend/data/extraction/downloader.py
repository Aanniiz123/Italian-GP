import fastf1 as f1
import pandas as pd
import os


# Anchor all paths to this script's location (backend/data/extraction/)
# so it works no matter what directory you run it from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "..", "raw")

f1.Cache.enable_cache(os.path.join(BASE_DIR, "f1_cache"))

years = range(2020, 2026)

os.makedirs(RAW_DIR, exist_ok=True)


def save_session_data(session, session_dir, session_name, include_messages=True):
    """Save laps, weather, messages, and results for a loaded session."""
    os.makedirs(session_dir, exist_ok=True)

    # --- Laps ---
    laps = session.laps
    if laps is not None and not laps.empty:
        laps_path = f"{session_dir}/laps.csv"
        laps.to_csv(laps_path, index=False)
        print(f"  Saved {session_name} laps -> {laps_path} ({len(laps)} rows)")
    else:
        print(f"  No {session_name} lap data")

    # --- Weather ---
    weather = session.weather_data
    if weather is not None and not weather.empty:
        weather_path = f"{session_dir}/weather.csv"
        weather.to_csv(weather_path, index=False)
        print(f"  Saved {session_name} weather -> {weather_path} ({len(weather)} rows)")
    else:
        print(f"  No {session_name} weather data")

    # --- Race control messages ---
    if include_messages:
        messages = session.race_control_messages
        if messages is not None and not messages.empty:
            messages_path = f"{session_dir}/messages.csv"
            messages.to_csv(messages_path, index=False)
            print(f"  Saved {session_name} messages -> {messages_path} ({len(messages)} rows)")
        else:
            print(f"  No {session_name} race control messages")

    # --- Session results (drivers, positions, points, etc.) ---
    results = session.results
    if results is not None and not results.empty:
        results_path = f"{session_dir}/results.csv"
        results.to_csv(results_path, index=False)
        print(f"  Saved {session_name} results -> {results_path} ({len(results)} rows)")


for year in years:
    print(f"Getting Italian GP {year}...")

    year_dir = os.path.join(RAW_DIR, str(year))
    os.makedirs(year_dir, exist_ok=True)

    try:
        # Race
        race = f1.get_session(year, "Italian Grand Prix", "R")
        race.load(
            laps=True,
            telemetry=False,
            weather=True,
            messages=True
        )
        save_session_data(race, os.path.join(year_dir, "race"), "race", include_messages=True)

        # Qualifying
        quali = f1.get_session(year, "Italian Grand Prix", "Q")
        quali.load(
            laps=True,
            telemetry=False,
            weather=True,
            messages=False
        )
        save_session_data(quali, os.path.join(year_dir, "quali"), "quali", include_messages=False)

    except Exception as e:
        print(f"  FAILED for {year}: {e}")
        continue

print("Done.")