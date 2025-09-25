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

Change this in `personal_inflation_fred_plus.py` to compile your own personal weights:

```py
DEFAULT_WEIGHTS = {
  "food_at_home": 0.45,
  "utilities_electric": 0.20,
  "utilities_gas": 0.15,
  "transport_fuel": 0.20
}
```

`my_weights.json` (for the FRED script):

```json
{ "food_at_home": 0.45, "utilities_electric": 0.2, "utilities_gas": 0.15, "transport_fuel": 0.2 }
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

> Weights automatically **normalize** to the categories actually present in your data; items within a category share equal weight.

---

## Data snapshot (2000 → 2024, staples basket)

This is the exact run behind `fred_basket_2000_2024.csv` and the saved charts:

- **Items used:** 10 (of 13 with data)
- **Unweighted inflation (arith):** **+128.66%**
- **Unweighted inflation (geometric):** **+119.14%**
- **Implied purchasing power (geometric):** **\$0.456 per \$1** (**−54.37%**)

| Item                                 | Unit      |  2000 |  2024 | % change |
| ------------------------------------ | --------- | ----: | ----: | -------: |
| Eggs, large                          | dozen     | 0.913 | 3.171 |  +247.2% |
| Ground beef (100% beef)              | lb        | 1.569 | 5.393 |  +243.6% |
| Potatoes                             | 5 lb      | 0.380 | 0.982 |  +158.5% |
| Gasoline, regular                    | gallon    | 1.510 | 3.449 |  +128.4% |
| Bread (white, pan)                   | lb        | 0.930 | 1.970 |  +111.8% |
| Rice, white, long-grain              | lb        | 0.490 | 1.034 |  +110.9% |
| Electricity (residential)            | cents/kWh | 0.087 | 0.176 |  +101.3% |
| Coffee, ground                       | lb        | 3.450 | 6.322 |   +83.3% |
| Natural gas (residential), per therm | \$/therm  | 0.803 | 1.428 |   +77.7% |
| Bananas                              | lb        | 0.501 | 0.620 |   +23.8% |

See the committed images for visuals:

- `levels_2000_vs_2024.png` — price levels per item (2000 vs 2024)
- `pct_changes_2000_vs_2024.png` — sorted % change per item

> **Note:** Chicken, milk, and peanut butter were excluded from the "used" set due to missing one of the endpoints in this particular run; once filled, they'll be included automatically.

---

## What this means

- On this staples basket, the dollar's **buying power is \~halved** since 2000 (≈ **−54%**).
- The **worst movers** are protein staples (eggs, ground beef) and **energy** (gasoline).
- Utilities rose strongly, groceries mixed (bananas barely moved; bread/rice surged).
- If you add **shelter** (rent) and **healthcare** with realistic weights, you should expect a **larger** purchasing-power loss than shown here; conversely, adding consumer tech often pulls it **down**.

**Caveats:**

- BLS "Average Price" series are **sticker levels** (annual mean of monthly observations). For change-over-time, BLS recommends CPI indexes; Average Price is **not quality-adjusted** and specs can drift.
- These are **U.S. city averages**; local reality (especially rent) can be far worse or better.
- Endpoints matter: 2000→2024 is a snapshot; 2000→2025 may differ.

---

## CSV schema

- `item` (string)
- `unit` (string) — free text ("lb", "gallon", "cents/kWh", etc.)
- `year_2000` (float) — price level in base year
- `year_2024` (float) — price level in compare year
- `source` (string) — e.g., `BLS Average Price via FRED (APU0000702111); annual mean of monthly`

---

## How inflation is computed

- **Unweighted (arithmetic):** mean of `(price_b / price_a) − 1` across items
- **Unweighted (geometric):** `exp(mean(log(price_b / price_a))) − 1` (used for purchasing power)
- **Weighted "necessities":** Laspeyres-style — normalize category weights over categories present; equal weight **within** category; sum contributions

**Implied purchasing power:** if cumulative inflation is `p` (e.g., 1.19 for +119%), then **\$1** in the base year ≈ **\$1 / (1 + p)** in the compare year.

---

## Reliability & caveats (TL;DR)

- **FRED mirrors official sources** (BLS/EIA/Census); values and revisions match origin.
- **Average Price** is great for **levels**; for **change**, CPI indexes are methodologically preferred.
- **Basket choice & weights dominate** the result. If you care about rent/healthcare, include and weight them accordingly.

---

## Reproducibility

Pin if you want identical runs:

```
requests==2.*
pandas==2.*
numpy==2.*
matplotlib==3.*
xlsxwriter==3.*
```

Keep `FRED_API_KEY` in your shell (not in the repo).

---

## Roadmap

- Add helpers for **rent** (ACS/ZORI), **healthcare OOP** (KFF/FAIR Health), **auto insurance/maintenance** (III/AAA), **childcare** (CCAoA).
- Multi-year runs (2000→2010→2015→2020→2024) and a time-series chart of your custom index.

Here you go—drop these sections into your README.

## Sources

- **FRED (Federal Reserve Bank of St. Louis)** — API mirror for official series (BLS/EIA/Census).

  - [FRED main](https://fred.stlouisfed.org/) - [API docs](https://fred.stlouisfed.org/docs/api/fred/)

- **BLS Average Price series (APU...)** — sticker-price levels (e.g., \$/lb, \$/dozen).

  - [BLS Average Price Database](https://www.bls.gov/cpi/tables/average-price-data.htm)

- **BLS CPI indexes** — official inflation indexes (quality-adjusted, chain-weighted).

  - [BLS CPI Home](https://www.bls.gov/cpi/)

- **EIA** — energy price series (electricity, natural gas).

  - [EIA Electricity](https://www.eia.gov/electricity/) - [EIA Natural Gas](https://www.eia.gov/naturalgas/)

- **Census/ACS** — rent, housing metrics (if you extend to shelter).

  - [American Community Survey](https://www.census.gov/programs-surveys/acs)

- **KFF Employer Health Benefits Survey** — premiums, deductibles, OOP (if you extend to healthcare).

  - [KFF EHBS](https://www.kff.org/ehbs/)

- **AAA "Your Driving Costs"** — maintenance per-mile, typical ownership costs.

  - [AAA YDC](https://newsroom.aaa.com/tag/your-driving-costs/)

- **III / NAIC** — auto insurance premiums.

  - [III Insurance Facts](https://www.iii.org/fact-statistic/facts-statistics-auto-insurance)

- **Zillow / ZORI** — rent indices (metro-level).

  - [ZORI](https://www.zillow.com/research/data/)

- **US Inflation Calculator** — annual averages compiled from BLS monthly data (handy cross-check).

  - [US Inflation Calculator](https://www.usinflationcalculator.com/)

- **Alternative/independent dashboards** _(interpret with care)_:

  - [Truflation](https://truflation.com/)
  - [Shadow Stats](https://www.shadowstats.com/) _(methodology diverges sharply from BLS; see caveats below)_

- **Recent commentary** _(ephemeral)_:

  - PYMNTS: _"Inflation's Impact Can't Be Seen Through CPI, Says Ex-Comptroller"_ (2025) — [link](https://www.pymnts.com/economy/2025/inflations-impact-cant-be-seen-through-cpi-says-ex-comptroller/)

## Conclusion

On the staples basket we pulled (food-at-home + energy/utilities), the **geometric inflation 2000→2024 is \~+119%**, implying the **dollar buys about \$0.456** of the same stuff—**roughly half** the purchasing power. If you expand the basket to include **shelter** (rent or entry PITI) and **healthcare** with realistic weights, your personal loss typically rises into the **high-50% range**. That gap versus **official CPI** (≈+88% since 2000, or ≈\$0.53 per 2000 dollar) mostly comes from **what you buy** and **how you weight it**—necessities and local housing pressures inflate faster than the national, quality-adjusted CPI bundle.

Do your own research, but keep the caveats in mind:

- **Method matters.** BLS **CPI indexes** are designed for change-over-time (quality adjustment, item substitution). **Average Price** series are great for sticker levels; using annual means is reasonable but **not quality-adjusted**.
- **Place matters.** National averages hide local variance. If your city's rent is \~2.6x (or more), a **shelter-heavy** personal index will show much worse inflation than CPI.
- **Composition matters.** Heavier weights on shelter/health premiums/childcare/auto insurance push inflation up; adding deflationary tech pulls it down.
- **Endpoints swing results.** 2000→2024 vs 2000→2025 can shift several points (eggs/energy are volatile).

About **Shadow Stats** and similar alternatives: they publish higher inflation estimates based on **non-BLS methodologies** (e.g., pre-1990s CPI rules or proprietary adjustments). They're useful as _dissenting benchmarks_, but they're **not** directly comparable to CPI and are **not** used by official statistical agencies. If you cite them, be explicit about the method differences. Tools like **Truflation** also diverge methodologically (on-chain/real-time data, different baskets); consider them **complements**, not substitutes.

Bottom line: this toolkit makes the **assumptions explicit**—your basket, your weights, reproducible data pulls—so you can show _why_ your personal inflation can be worse than headline CPI and by **how much**.
