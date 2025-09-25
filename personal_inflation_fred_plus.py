#!/usr/bin/env python3
"""
personal_inflation_fred_plus.py

Fetch BLS "Average Price" series from FRED for a predefined basket,
compute unweighted inflation (arithmetic + geometric), show purchasing-power loss,
OPTIONALLY compute a weighted "necessities" index, write a CSV, and generate PNG charts.

Usage:
  export FRED_API_KEY=YOUR_KEY
  python3 personal_inflation_fred_plus.py --out fred_basket_2000_2024.csv
  python3 personal_inflation_fred_plus.py --year-a 2000 --year-b 2024 --out fred.csv --plot
  # with weighted index + show normalized weights actually used:
  python3 personal_inflation_fred_plus.py --weighted --print-weights
  # provide your own category weights via JSON mapping {category: weight}:
  python3 personal_inflation_fred_plus.py --weighted --weights my_weights.json
"""

import os
import sys
import csv
import math
import json
import argparse
from typing import Dict, Tuple, List

import requests

# Plotting (only used when --plot is set)
import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt

API = "https://api.stlouisfed.org/fred/series/observations"

# Map item -> (unit, FRED series id)
SERIES = {
    # Food at home
    "Bread (white, pan)": ("lb", "APU0000702111"),
    "Chicken breast, boneless": ("lb", "APU0000FF1101"),
    "Rice, white, long-grain": ("lb", "APU0000701312"),
    "Coffee, ground": ("lb", "APU0000717311"),
    "Potatoes": ("5 lb", "APU0000712112"),
    "Bananas": ("lb", "APU0000711211"),
    "Peanut butter": ("16 oz", "APU0000716141"),
    "Eggs, large": ("dozen", "APU0000708111"),
    "Milk (whole)": ("gallon", "APU0000709111"),
    "Ground beef (100% beef)": ("lb", "APU0000703112"),
    # Utilities / Energy
    "Electricity (residential)": ("cents/kWh", "APU000072610"),
    "Natural gas (residential), per therm": ("$/therm", "APU000072620"),
    "Gasoline, regular": ("gallon", "APU000074714"),
}

# ---- Category mapping (simple keyword rules) ----
CATEGORY_KEYWORDS = [
    ("food_at_home", ["bread", "chicken", "rice", "coffee", "potatoes", "banana", "peanut butter", "egg", "milk", "ground beef", "beef"]),
    ("utilities_electric", ["electricity"]),
    ("utilities_gas", ["natural gas", "per therm"]),
    ("transport_fuel", ["gasoline"]),
]

def categorize_item(name: str) -> str:
    n = (name or "").lower()
    for cat, needles in CATEGORY_KEYWORDS:
        for needle in needles:
            if needle in n:
                return cat
    return "unclassified"  # won’t be used in weighted calc

# ---- Default "necessities" category weights ----
# Target conceptual shares (if we also had shelter & healthcare):
#   shelter 35–40, food-at-home 20–25, utilities/energy 10–15, transport 10–15, healthcare 10
# In this script we only have: food-at-home, utilities (electric + gas), transport fuel.
# We renormalize the available buckets so they sum to 1.0.
DEFAULT_WEIGHTS = {
    "food_at_home": 0.45,         # emphasize groceries
    "utilities_electric": 0.20,   # electric
    "utilities_gas": 0.15,        # utility gas
    "transport_fuel": 0.20,       # gasoline
    # NOTE: if you add shelter/healthcare later, the script will normalize again over present categories
}

def get_key() -> str:
    key = os.environ.get("FRED_API_KEY")
    if not key:
        sys.exit("Set FRED_API_KEY in your environment (export FRED_API_KEY=...).")
    return key

def year_avg(series_id: str, year: int, key: str) -> float:
    params = {
        "series_id": series_id,
        "api_key": key,
        "file_type": "json",
        "observation_start": f"{year}-01-01",
        "observation_end": f"{year}-12-31",
        "frequency": "m",
        "units": "lin",
    }
    r = requests.get(API, params=params, timeout=30)
    r.raise_for_status()
    obs = [float(o["value"]) for o in r.json()["observations"] if o["value"] not in ("", ".")]
    return sum(obs)/len(obs) if obs else float("nan")

def compute_unweighted(rows: List[Tuple[str, float, float]]) -> Tuple[float, float]:
    """Return (arith_mean_pct_change, geo_mean_relative_minus_1)."""
    rels = []
    for _, a, b in rows:
        if a and b and a > 0 and b > 0:
            rels.append(b / a)
    if not rels:
        return (float("nan"), float("nan"))
    arith = sum((r - 1.0) for r in rels) / len(rels)
    geo = math.exp(sum(math.log(r) for r in rels) / len(rels)) - 1.0
    return arith, geo

def compute_weighted(rows: List[Tuple[str, float, float]],
                     cat_weights: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """
    Laspeyres-style: equal weight within category; category weights normalized to
    only the categories present. Returns (weighted_pct_change, normalized_category_weights_used)
    """
    # Build per-category lists of relatives
    by_cat: Dict[str, List[float]] = {}
    for item, a, b in rows:
        cat = categorize_item(item)
        if cat not in cat_weights:  # ignore categories with no weight
            continue
        if a and b and a>0 and b>0:
            by_cat.setdefault(cat, []).append(b/a)

    if not by_cat:
        return (float("nan"), {})

    # Normalize category weights over the cats present
    present = [c for c in by_cat.keys()]
    total_w = sum(cat_weights[c] for c in present)
    norm_w = {c: (cat_weights[c] / total_w) for c in present}

    # Equal weights within a category
    weighted = 0.0
    for c in present:
        rels = by_cat[c]
        if not rels:
            continue
        within = 1.0 / len(rels)
        cat_contrib = sum(((r - 1.0) * within) for r in rels)
        weighted += norm_w[c] * cat_contrib

    return weighted, norm_w

def purchasing_power_after(pct_change: float) -> Tuple[float, float]:
    if pct_change is None or math.isnan(pct_change):
        return (float('nan'), float('nan'))
    remaining = 1.0 / (1.0 + pct_change)
    return remaining, 1.0 - remaining

def plot_levels(items, base_vals, cmp_vals, year_a, year_b, outfile):
    plt.figure()
    x = range(len(items))
    width = 0.4
    plt.bar([i - width/2 for i in x], base_vals, width=width, label=str(year_a))
    plt.bar([i + width/2 for i in x], cmp_vals, width=width, label=str(year_b))
    plt.xticks(list(x), items, rotation=60, ha="right")
    plt.ylabel("Price (unit varies)")
    plt.title(f"Price levels by item: {year_a} vs {year_b}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outfile)
    plt.close()

def plot_pct_changes(items, pct_changes, outfile):
    pairs = sorted(zip(items, pct_changes), key=lambda t: t[1], reverse=True)
    items_sorted = [p[0] for p in pairs]
    pct_sorted = [p[1]*100.0 for p in pairs]
    plt.figure()
    plt.bar(range(len(items_sorted)), pct_sorted)
    plt.xticks(range(len(items_sorted)), items_sorted, rotation=60, ha="right")
    plt.ylabel("% change")
    plt.title("Percent change by item")
    plt.tight_layout()
    plt.savefig(outfile)
    plt.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year-a", type=int, default=2000, help="Base year (default 2000)")
    ap.add_argument("--year-b", type=int, default=2024, help="Compare year (default 2024)")
    ap.add_argument("--out", type=str, default="fred_basket.csv", help="CSV output path")
    ap.add_argument("--plot", action="store_true", help="Generate charts (PNG files)")

    # weighted index options
    ap.add_argument("--weighted", action="store_true", help="Compute weighted 'necessities' index")
    ap.add_argument("--weights", type=str, default=None,
                    help="Path to JSON mapping {category: weight}; categories: "
                         "food_at_home, utilities_electric, utilities_gas, transport_fuel")
    ap.add_argument("--print-weights", action="store_true", help="Print normalized weights actually used")
    args = ap.parse_args()

    key = get_key()

    rows_for_calc: List[Tuple[str, float, float]] = []   # (item, a, b)
    out_rows = []                                        # for CSV
    for item,(unit,sid) in SERIES.items():
        a = year_avg(sid, args.year_a, key)
        b = year_avg(sid, args.year_b, key)
        out_rows.append([item, unit,
                         f"{a:.3f}" if a==a else "",
                         f"{b:.3f}" if b==b else "",
                         f"BLS Average Price via FRED ({sid}); annual mean of monthly"])
        if a==a and b==b and a>0 and b>0:
            rows_for_calc.append((item, a, b))

    # Write CSV
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item","unit",f"year_{args.year_a}",f"year_{args.year_b}","source"])
        w.writerows(out_rows)
    print(f"Wrote CSV: {args.out}")

    # Compute and print (unweighted)
    arith, geo = compute_unweighted(rows_for_calc)
    print("\nPERSONAL INFLATION — {} to {}\n".format(args.year_a, args.year_b))
    print(f"Items used: {len(rows_for_calc)} (of {len(SERIES)})")
    print("- Unweighted (arithmetic mean of pct changes): {:6.2f}%".format(arith * 100.0))
    print("- Unweighted (geometric mean of relatives):   {:6.2f}%".format(geo * 100.0))

    pp_geo, loss_geo = purchasing_power_after(geo)
    print(f"\n- Implied purchasing power (geometric): ${pp_geo:.3f} per $1 (loss {loss_geo*100:.2f}%)")

    # Optional weighted index
    if args.weighted:
        cat_w = dict(DEFAULT_WEIGHTS)
        if args.weights:
            with open(args.weights, "r", encoding="utf-8") as fh:
                user_w = json.load(fh)
            cat_w.update(user_w)  # user values override defaults
        weighted_pct, norm_w = compute_weighted(rows_for_calc, cat_w)
        if weighted_pct == weighted_pct:  # not NaN
            print("\nWEIGHTED 'NECESSITIES' INDEX")
            print("- Weighted pct change: {:6.2f}%".format(weighted_pct * 100.0))
            pp_w, loss_w = purchasing_power_after(weighted_pct)
            print(f"- Implied purchasing power (weighted):  ${pp_w:.3f} per $1 (loss {loss_w*100:.2f}%)")
            if args.print_weights and norm_w:
                print("\nNormalized category weights actually used:")
                for k,v in norm_w.items():
                    print(f"  {k:20s}  {v:6.2%}")
        else:
            print("\nWeighted index: not computed (no mapped categories present).")

    # Top movers
    pct_changes = [(b/a - 1.0) for (_,a,b) in rows_for_calc]
    top_increases = sorted(zip([r[0] for r in rows_for_calc], pct_changes), key=lambda t: t[1], reverse=True)[:5]
    top_decreases = sorted(zip([r[0] for r in rows_for_calc], pct_changes), key=lambda t: t[1])[:5]
    print("\nTop item increases:")
    for name, pct in top_increases:
        print(f"  {name:40s}  +{pct*100:.1f}%")
    print("\nTop item decreases:")
    for name, pct in top_decreases:
        print(f"  {name:40s}  {pct*100:+.1f}%")

    # Plots
    if args.plot and rows_for_calc:
        items = [r[0] for r in rows_for_calc]
        base_vals = [r[1] for r in rows_for_calc]
        cmp_vals = [r[2] for r in rows_for_calc]
        pct = [(r[2]/r[1] - 1.0) for r in rows_for_calc]

        levels_png = f"levels_{args.year_a}_vs_{args.year_b}.png"
        changes_png = f"pct_changes_{args.year_a}_vs_{args.year_b}.png"

        plot_levels(items, base_vals, cmp_vals, args.year_a, args.year_b, levels_png)
        plot_pct_changes(items, pct, changes_png)
        print(f"\nSaved charts:\n  {levels_png}\n  {changes_png}")


if __name__ == "__main__":
    main()
