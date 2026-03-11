# Options Open Interest Dashboard

A daily-updated dashboard that scans **S&P 500 IT + Nasdaq-100 stocks** for the highest open-interest options contracts, identifies what institutional ("smart money") investors are positioning for, and publishes an interactive HTML report automatically every trading day.

> **Live dashboard →** [options.pranavp.dev](https://options.pranavp.dev)

---

## What does it do?

Every weekday at 4:30 PM ET (after market close), the tool automatically:

1. Fetches the current price and **1-day / 5-day price change** for every ticker (~130 stocks)
2. Pulls the full options chain from NASDAQ's public API — all expiry dates, all strikes, with **real Open Interest (OI)** and volume
3. For each stock and each time horizon (This Friday → 1 Year), finds the **top 10 contracts ranked by OI**
4. Classifies each contract as **BUY, SELL, HEDGE-C, or HEDGE-P** based on moneyness
5. Calculates forecasted % move implied by where the money is positioned
6. Computes **OI trend signals** (call OI vs put OI changes vs prior snapshot) to show market sentiment shifts
7. Generates an interactive HTML dashboard, pushes it live to GitHub Pages, and **archives every day's report**

---

## Understanding Options (Quick Primer)

If you're new to options, here's the minimum you need to read the dashboard:

**What is an option?**
An option is a contract giving someone the right to buy (call) or sell (put) a stock at a specific price (the **strike**) before a certain date (**expiry**).

**Volume vs Open Interest — what's the difference?**

| Metric | What it means |
|---|---|
| **Volume** | How many contracts were traded *today* — resets to zero every morning |
| **Open Interest (OI)** | How many contracts are *currently open* — accumulates over time |

OI is more meaningful for spotting institutional positioning. A contract with OI of 10,000 means 10,000 contracts are sitting open — real money is on that bet.

**What's a good OI number?**

| OI Range | What it signals |
|---|---|
| < 500 | Basically illiquid — skip |
| 500 – 1,000 | Thin — proceed with caution |
| 1,000 – 5,000 | Good liquidity |
| 5,000 – 10,000 | Strong — institutional interest |
| > 10,000 | Major smart-money positioning |

---

## Reading the Signals

### Contract Signals (shown in the main table)

| Signal | What it is | What it means |
|---|---|---|
| **BUY** | Out-of-the-money (OTM) Call | The market is betting the stock goes *up* |
| **SELL** | Out-of-the-money (OTM) Put | The market is betting the stock goes *down* |
| **HEDGE-C** | In-the-money (ITM) Call | Smart money covering a profitable short position |
| **HEDGE-P** | In-the-money (ITM) Put | Smart money insuring a long position against downside |

**Example (BUY):** TSLA is at $400 and there's huge OI on the $460 Call expiring in 7 days. Someone is betting TSLA reaches $460 — forecasted +15% move.

**Example (SELL):** TSLA is at $400 and there's massive OI on the $340 Put expiring this Friday. Someone expects a significant drop — forecasted −15% move.

**Example (HEDGE-P):** TSLA is at $400 and there's massive OI on the $350 Put. A fund that owns 1 million TSLA shares bought the right to *sell* at $350 as insurance. If TSLA drops to $200, they can still sell at $350 and limit losses. They're not betting it goes down — they already own it and are hedging.

**Example (HEDGE-C):** MSFT is at $408 and there's huge OI on the $350 Call. A hedge fund that shorted MSFT at $350 is now underwater. They bought calls to cap further losses if the stock keeps rising. Not a bullish bet — it's limiting the pain on a bad short.

---

### OI Trend Signals (shown in the expanded view)

These appear in the trend bar when you expand a ticker row. They compare today's total call OI and put OI against a prior snapshot, combined with the current price direction, to derive a directional interpretation.

| Signal | Condition | What it means |
|---|---|---|
| **Bullish** | C↑ + P↓ + Price↑ | New money entering on the upside |
| **Bearish** | P↑ + C↓ + Price↓ | New money entering on the downside |
| **Hedged Rally** | P↑ + Price↑ | Stock rising but institutions buying downside protection |
| **Short Covering** | C↑ + Price↓ | Price falling but call OI rising — shorts may be exiting |
| **Build-Up** | C↑ + P↑ | Both sides adding positions — big move expected, direction unclear |
| **Unwinding** | C↓ + P↓ | Both sides closing — calm period or near expiry |

**Significance thresholds:** A signal only fires when the OI change is **both ≥ 5% and ≥ 500 contracts**. Smaller moves are shown as flat (→) to avoid noise from a single order.

**Comparison windows by horizon:**

| Horizon | OI compared against | Price direction used |
|---|---|---|
| This Friday, 7 Days | Yesterday's snapshot | 1-day price change |
| 30D, 45D, 60D, 90D | 7-day-old snapshot | 5-day price change |
| 180D, 1Y | Not compared — totals shown only | — |

Shorter-dated options move daily and react to near-term catalysts, so yesterday is the right reference. Longer-dated options build positions slowly — a single day's OI change is noise; a week's shift is meaningful.

---

## Dashboard Walkthrough

### Header Bar
Shows how many Buy/Sell/Hedge signals exist across all tickers and time horizons. Also displays the snapshot age so you know how fresh the data is.

### Period Pills (This Friday / 7 Days / 1 Month / …)
Switches which time horizon is shown in the main table. The date shown below each pill is the actual expiry date that was matched. Selecting a period also highlights that column in the All Tickers table.

### Signal Filter
Narrows the table to only show tickers where the top contract for the selected period is BUY, SELL, HEDGE-C, or HEDGE-P.

### Min OI Filter
Dims contracts below your minimum OI threshold. Use **1K+** as your baseline — anything below 1,000 OI isn't worth serious attention.

### Main Bar Chart
Forecasted % moves for the selected period. Green = BUY, Red = SELL, Orange = HEDGE. Hover any bar for full contract details.

### All Tickers Table
Each row shows the top contract's signal and forecasted % for the currently selected period.

**Expanding a row** reveals:

- **Company name, sector, industry**
- **Price trend bar:**
  `PRICE  1D: ▲ +2.1%  5D: ▼ −3.4%`
- **OI trend bar** with labelled sections:
  - `OI VS YESTERDAY` — Fri and 7D pills showing call/put OI change vs yesterday
  - `OI VS 7 DAYS AGO` — 30D–90D pills showing call/put OI change vs one week ago
  - `LONG-DATED OI` — 180D/1Y showing raw call/put OI totals (no % trend)
  - Each pill that crosses the significance threshold shows a **combo badge** (Bullish / Bearish / Hedged Rally / Short Covering / Build-Up / Unwinding)
  - Hovering a pill shows the exact % change and which comparison window was used
- **8 horizon blocks** (This Friday → 1 Year), each showing:
  - Top 3 contracts by OI with signal, forecast %, OI count, volume, and delta badges
  - Earnings-in-window flag (⚠) if an earnings date falls before expiry
  - **Stacked bar chart** (calls = green, puts = red) for the top 10 contracts by OI:
    - X-axis uses **proportional spacing** — strikes that are far apart appear far apart visually, so clusters are immediately visible
    - A **dashed amber line** marks the current stock price (instant OTM/ITM boundary)
    - Hover any bar for OI, volume, and signal details
- **Intra-week Expiries** — for hyper-liquid stocks (TSLA, AAPL, etc.) that have Mon/Tue/Wed/Thu expiries, these appear as a separate section with the same layout

### Earnings Flag (⚠)
If a company's earnings date falls within a horizon's window, a ⚠ badge with the exact date appears inline. Earnings can invalidate signals — OI placed before the report may be closed or rolled immediately after.

### Signal Flip Badge (↺)
If a contract's signal changed since the previous day's run (e.g. BUY → SELL), a flip badge appears. These are worth close attention — a shift in where the large OI sits is a meaningful change in sentiment.

The badge only fires on directional flips (BUY ↔ SELL). Transitions involving HEDGE-C or HEDGE-P are ignored — hedges rolling or shifting don't indicate a sentiment reversal.

Rank 2 and 3 contracts can also show the badge, but only when their OI is **within 25% of rank 1's OI** (meaning they're competitive for the top spot). If rank 1 has 50,000 OI and rank 2 has 5,000, a flip on rank 2 is noise and is suppressed.

| Scenario | Flip shown? |
|---|---|
| Rank 1 flips BUY → SELL (any OI) | ✅ Always |
| Rank 2/3 flips, OI ≥ 75% of rank 1 (e.g. 12,000 vs 12,500) | ✅ Competitive — shown |
| Rank 2/3 flips, OI < 75% of rank 1 (e.g. 5,000 vs 50,000) | ❌ Noise — suppressed |
| Any rank flips BUY → HEDGE-C/P | ❌ Not a directional flip — ignored |

**Example:** MU is at $370. Monday's top contract is the $400 Call (OI 22,000) → **BUY +8.1%**. After a disappointing earnings report, Tuesday's top contract shifts to the $320 Put (OI 35,000) → **SELL −7.2% ↺**. The ↺ tells you this was bullish yesterday and is bearish today.

---

## Project Structure

```
options/
├── main.py              # Entry point — orchestrates fetch → analyze → export
├── universe.py          # Ticker lists (S&P 500 IT + Nasdaq-100)
├── fetcher.py           # Price, price history (1D/5D), earnings, company info (yfinance)
├── nasdaq_fetcher.py    # Full options chain (OI + volume) from NASDAQ public API
├── analyzer.py          # Top contracts, signals, forecasts, OI trends, deltas
├── exporter_html.py     # Self-contained interactive HTML dashboard (Chart.js)
├── requirements.txt     # Python dependencies
├── docs/
│   └── index.html       # Latest report — served by GitHub Pages at options.pranavp.dev
├── reports/
│   ├── latest_analysis.json          # Daily snapshot for OI delta computation
│   ├── weekly_analysis.json          # Weekly snapshot for 30D–90D OI comparison
│   └── options_signals_YYYYMMDD_HHMM.{html,xlsx}  # Archived daily reports
└── .github/workflows/
    └── daily_report.yml  # Runs at 4:30 PM ET every weekday
```

---

## Running Locally

**Prerequisites:** Python 3.11+

```bash
# 1. Clone the repo
git clone https://github.com/shadowp2810/options.git
cd options

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run a quick test with a few tickers
python main.py --tickers AAPL TSLA MSFT NVDA

# 4. Run the full universe (~130 tickers, takes ~5 minutes)
python main.py

# 5. Open the generated HTML in your browser
open reports/options_signals_*.html   # macOS
```

The `--tickers` flag is useful for quick testing or focusing on specific stocks.

---

## How the Data Pipeline Works

```
yfinance
  → current price
  → 1-day & 5-day price history
  → earnings date
  → company name / sector / industry

NASDAQ Public API (one call per ticker)
  → full options chain: all expiries × all strikes × OI + volume

analyzer.py
  → for each ticker × horizon:
      find nearest expiry date
      sum total call OI + put OI for that expiry (stable baseline)
      rank all contracts by OI → take top 10
      classify BUY / SELL / HEDGE-C / HEDGE-P
      calculate forecasted % move
      compare vs daily snapshot  → OI trend for Fri / 7D
      compare vs weekly snapshot → OI trend for 30D–90D
      derive combo signal (Bullish / Bearish / Hedged Rally / …)
      compare contracts vs yesterday's → strike delta + signal flip

exporter_html.py → self-contained HTML (all data embedded as JSON)
main.py          → Excel report (.xlsx) with colour-coded cells
```

---

## How the Daily Auto-Deploy Works

A GitHub Actions workflow runs every weekday at **9:30 PM UTC (4:30 PM ET)**:

```
GitHub Actions (free tier, cloud)
  → python main.py
      generates HTML + Excel
      saves / refreshes latest_analysis.json (daily snapshot)
      saves / refreshes weekly_analysis.json (refreshes every 7 days)
  → copies latest HTML to docs/index.html
  → git commit + git push:
      docs/index.html              ← live dashboard
      reports/latest_analysis.json ← daily snapshot
      reports/weekly_analysis.json ← weekly snapshot
      reports/options_signals_*.html ← permanent archive
      reports/options_signals_*.xlsx ← permanent archive
  → GitHub Pages serves docs/index.html at options.pranavp.dev
```

**Manual run:** GitHub repo → Actions tab → "Daily Options Report" → "Run workflow".

**Archive:** Every day's HTML and Excel are committed to the repo. You can browse historical reports directly on GitHub or clone the repo to access any past day.

---

## Data Sources & Limitations

| Data | Source | Notes |
|---|---|---|
| Stock price | Yahoo Finance (yfinance) | ~15 min delayed |
| Price history (1D, 5D) | Yahoo Finance | Used for OI trend signal direction |
| Options chain, OI, Volume | NASDAQ public API | OI is always previous-day close |
| Earnings dates | Yahoo Finance | Best-effort; may occasionally be off by a day |
| Company name / sector | Yahoo Finance | Used in expanded view |

**Important limitations:**

- **OI is always from the previous close.** Exchanges publish OI once per day. Even paid real-time APIs give you yesterday's OI.
- **The data is a snapshot, not a live feed.** It runs once at market close. If a major event happens mid-day, the dashboard won't reflect it until the next run.
- **High OI ≠ guaranteed move.** It means someone has a large position — which could be a hedge, a spread, or an institutional algo. Use signals as one input among many.
- **Earnings change everything.** OI placed before an earnings report may be closed or rolled immediately after. The ⚠ flag is your warning.
- **OI trend signals need a reference snapshot.** On the very first run (or after a long gap), OI vs Yesterday / vs 7 Days Ago will show `—` until a valid prior snapshot exists. The weekly comparison starts working 5 days after the first run.

---

## Glossary

| Term | Meaning |
|---|---|
| **Strike price** | The price at which the option gives the right to buy/sell |
| **Expiry** | The date the contract expires — after this it's worthless |
| **Call** | Right to *buy* a stock at the strike price |
| **Put** | Right to *sell* a stock at the strike price |
| **OTM (Out of the Money)** | Call: strike above current price. Put: strike below. Stock must move for the option to have value. |
| **ITM (In the Money)** | Call: strike below current price. Put: strike above. Option already has intrinsic value. |
| **Open Interest (OI)** | Total contracts currently open (not yet settled) |
| **Volume** | Contracts traded today |
| **Forecast %** | How far the stock must move from current price to reach the strike |
| **LEAPS** | Long-dated options (1 year+) — often large institutional bets |
| **Smart money** | Institutional investors (hedge funds, banks) whose large positions show up as high OI |
| **OI Trend** | Change in total call or put OI vs a prior snapshot — used to detect new positioning |
| **Combo signal** | Derived from (call OI trend) + (put OI trend) + (price direction) — e.g. Bullish, Bearish, Hedged Rally |
