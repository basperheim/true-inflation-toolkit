# True Inflation Toolkit

Reproducible scripts to compute **your** inflation — not the headline CPI:

- Pull **BLS Average Price** series (and some EIA) via **FRED** for a staple basket.
- Or load your own **CSV** basket (rent, health premiums, etc.).
- Compute **unweighted** (arith & geometric) and **weighted** "necessities" inflation.
- Print **implied purchasing power** (how much of a 2000 dollar remains in 2024/2025).
- Generate **matplotlib** charts (levels and % changes).

> tl;dr: You decide the basket and the weights (e.g., shelter-heavy, healthcare included). The scripts stay transparent and reproducible.

---

## What's inside

- `personal_inflation_fred_plus.py`
  Fetches a predefined staple basket from **FRED** (bread, eggs, chicken, rice, coffee, potatoes, bananas, peanut butter, milk, ground beef, gasoline, residential electricity & utility gas).
  Prints unweighted inflation; **optionally** computes a **weighted "necessities" index** (food-at-home, utilities, transport fuel), and saves charts.

- `personal_inflation.py`
  CSV-driven calculator (no network). Computes unweighted + weighted inflation from your own basket. Can dump item and category breakdowns.

- `personal_inflation_plus.py`
  CSV-driven calculator that can **auto-fill** missing 2000/2024 values for known BLS items via **FRED**, then compute indices and (optionally) export breakdowns.

- `expanded_needs_basket_2000_2024.csv` (optional example)
  Scaffold for a broader basket (rent tiers, health premiums, OOP, childcare, auto insurance/maint, connectivity, etc.) with some cells intentionally blank to be filled via sources you choose.

---

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install requests pandas numpy matplotlib xlsxwriter
```

Python ≥ 3.9 recommended.

---

## Quickstart

### 1) FRED pull (staples basket)

```bash
export FRED_API_KEY=YOUR_KEY   # do NOT commit this
python personal_inflation_fred_plus.py --year-a 2000 --year-b 2024 --out fred_basket_2000_2024.csv --plot

# Optional: weighted "necessities" index with sensible defaults; print normalized weights
python personal_inflation_fred_plus.py --weighted --print-weights --out fred_basket_2000_2024.csv
# Or supply your own category weights:
python personal_inflation_fred_plus.py --weighted --weights my_weights.json
```

Outputs:

- `fred_basket_2000_2024.csv`
- `levels_2000_vs_2024.png`, `pct_changes_2000_vs_2024.png`
- Console summary with unweighted + (optional) weighted purchasing power.

### 2) CSV-first (your basket)

Prepare a CSV with header:

```
item,unit,year_2000,year_2024,source
```

Then:

```bash
python personal_inflation.py --csv my_basket.csv
# Write item/category breakdowns (CSV or XLSX):
python personal_inflation.py --csv my_basket.csv --out breakdown.csv
# Use custom weights:
python personal_inflation.py --csv my_basket.csv --weights my_weights.json
```

### 3) CSV + auto-fill missing BLS items from FRED

```bash
export FRED_API_KEY=YOUR_KEY
python personal_inflation_plus.py --csv expanded_needs_basket_2000_2024.csv --auto-fill --save-filled filled.csv
python personal_inflation_plus.py --csv filled.csv --out breakdown.csv
```

---

## Category weights (examples)

Change this code in the `personal_inflation_fred_plus.py` Python script:

```py
DEFAULT_WEIGHTS = {
    "food_at_home": 0.45,         # emphasize groceries
    "utilities_electric": 0.20,   # electric
    "utilities_gas": 0.15,        # utility gas
    "transport_fuel": 0.20,       # gasoline
    # NOTE: if you add shelter/healthcare later, the script will normalize again over present categories
}
```

`my_weights.json` (for the FRED script's categories):

```json
{
  "food_at_home": 0.45,
  "utilities_electric": 0.2,
  "utilities_gas": 0.15,
  "transport_fuel": 0.2
}
```

`my_weights.csv.json` (for the broader CSV calculator; categories are assigned by keyword, see code):

```json
{
  "housing_rent": 0.4,
  "food_at_home": 0.22,
  "utilities_electric": 0.07,
  "utilities_gas": 0.05,
  "transport_fuel": 0.06,
  "transport_vehicle": 0.04,
  "transport_insurance": 0.03,
  "transport_maint": 0.02,
  "health_premiums": 0.07,
  "health_oop": 0.04
}
```

> Weights automatically **normalize** to the categories actually present in your data, and items within a category share equal weight.

---

## CSV schema

- `item` (string)
- `unit` (string) — free text ("lb", "gallon", "cents/kWh", etc.)
- `year_2000` (float) — price level in base year
- `year_2024` (float) — price level in compare year
- `source` (string) — where you got it (FRED series ID, ACS table, KFF, etc.)

**Tip:** For FRED/BLS Average Price series, we use the **annual mean of monthly observations** for each year.

---

## How inflation is computed

- **Unweighted arithmetic**: mean of `(price_b / price_a) - 1` across items.
- **Unweighted geometric**: `exp(mean(log(price_b / price_a))) - 1` (more robust to outliers); used for the purchasing-power line by default.
- **Weighted "necessities"**: Laspeyres-style — normalize your category weights across the categories present; within a category, items share equal weight; then sum category contributions.

**Implied purchasing power:**
If cumulative inflation = `p` (e.g., 1.19 for +119%), then **\$1** in base year ≈ **\$1 / (1 + p)** in the compare year.

---

## Reliability & caveats

- **FRED is a mirror of official sources** (BLS/EIA/Census). You get the same values as the origin; revisions propagate.
- **BLS "Average Price" series** (APU...) are great for **sticker levels**, but BLS recommends **CPI indexes** for change-over-time due to item replacement/quality adjustment. We mitigate noise by using **annual averages**, but these series are **not quality-adjusted**.
- **National averages hide regional variance**, especially for **shelter**. If you care about your city, swap in local rent data (ACS/ZORI) and weight shelter heavily.
- **Basket choice and weights dominate** the result. A shelter-heavy, healthcare-included basket will show worse inflation than headline CPI; adding cheap tech drags it down.

---

## Reproducibility

- Pin dependencies if you want identical runs:

```
requests==2.*
pandas==2.*
numpy==2.*
matplotlib==3.*
xlsxwriter==3.*
```

- Keep **FRED API key** in your shell (`export FRED_API_KEY=...`), **never** in the repo.

---

## Roadmap (nice-to-haves)

- Add **rent tiers** (ACS/ZORI) and **healthcare OOP** (KFF/FAIR Health) helpers.
- Add **auto insurance** (III/NAIC), **AAA maintenance**, **childcare** (CCAoA).
- CLI flag for multi-year runs (2000→2010→2015→2020→2024) and a time-series chart of your "True CPI".
