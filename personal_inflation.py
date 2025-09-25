#!/usr/bin/env python3
import os, sys, csv, math, datetime as dt
import requests

API = "https://api.stlouisfed.org/fred/series/observations"
KEY = os.environ.get("FRED_API_KEY")
if not KEY:
    sys.exit("Set FRED_API_KEY in your environment")

# Map item -> (unit, FRED series id)
SERIES = {
    # Food at home
    "Bread (white, pan)": ("lb", "APU0000702111"),
    "Chicken breast, boneless": ("lb", "APU0000FF1101"),
    "Rice, white, long-grain (uncooked)": ("lb", "APU0000701312"),
    "Coffee, ground (100%)": ("lb", "APU0000717311"),
    "Potatoes, white": ("lb", "APU0000712112"),
    "Bananas": ("lb", "APU0000711211"),
    "Peanut butter, creamy, all sizes": ("lb", "APU0000716141"),
    # Household fuels
    "Electricity (residential)": ("cents/kWh", "APU000072610"),
    "Natural gas (residential), per therm": ("$/therm", "APU000072620"),
    # Already in your file but included for completeness:
    "Milk (whole)": ("gallon", "APU0000709111"),          # whole milk, per gallon
    "Ground beef (100% beef)": ("lb", "APU0000703112"),   # ground beef, per lb
    "Eggs, large": ("dozen", "APU0000708111"),
}

YEARS = [2000, 2024]

def year_avg(series_id, year):
    params = {
        "series_id": series_id,
        "api_key": KEY,
        "file_type": "json",
        "observation_start": f"{year}-01-01",
        "observation_end": f"{year}-12-31",
        "frequency": "m",  # monthly
        "units": "lin",
    }
    r = requests.get(API, params=params, timeout=30)
    r.raise_for_status()
    obs = [float(o["value"]) for o in r.json()["observations"] if o["value"] not in ("", ".")]
    return sum(obs)/len(obs) if obs else math.nan

def main():
    w = csv.writer(sys.stdout)
    w.writerow(["item","unit","year_2000","year_2024","source"])
    for item,(unit,sid) in SERIES.items():
        y2000 = year_avg(sid, 2000)
        y2024 = year_avg(sid, 2024)
        src = f"BLS Average Price series via FRED ({sid}); annual mean of monthly"
        w.writerow([item, unit,
                    f"{y2000:.3f}" if not math.isnan(y2000) else "",
                    f"{y2024:.3f}" if not math.isnan(y2024) else "",
                    src])

if __name__ == "__main__":
    main()
