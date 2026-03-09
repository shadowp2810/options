# Options Open Interest Dashboard

A daily-updated dashboard that scans **S&P 500 IT + Nasdaq-100 stocks** for the highest open-interest options contracts, identifies what institutional ("smart money") investors are positioning for, and publishes an interactive HTML report automatically every trading day.

> **Live dashboard →** [options.pranavp.dev](https://options.pranavp.dev)

---

## What does it do?

Every weekday at 4:30 PM ET (after market close), the tool automatically:

1. Fetches the current price for every ticker in the universe (~130 stocks)
2. Pulls the full options chain from NASDAQ's public API — all expiry dates, all strike prices, with **real Open Interest (OI)** data
3. For each stock and each time horizon (This Friday, 7 Days, 1 Month, 45 Days, 60 Days, 90 Days, 6 Months, 1 Year), finds the **top 10 contracts ranked by OI**
4. Classifies each contract as a **BUY, SELL, HEDGE-C, or HEDGE-P** signal based on whether it's in-the-money or out-of-the-money
5. Calculates the forecasted % move implied by where the money is positioned
6. Generates an interactive HTML dashboard and pushes it live to GitHub Pages

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

The dashboard classifies every contract into one of four signals:

| Signal | What it is | What it means |
|---|---|---|
| **BUY** | Out-of-the-money (OTM) Call | The market is betting the stock goes *up* — someone paid to have the right to buy at a higher price |
| **SELL** | Out-of-the-money (OTM) Put | The market is betting the stock goes *down* — someone paid to have the right to sell at a lower price |
| **HEDGE-C** | In-the-money (ITM) Call | Smart money is *covering a short position* — not a directional bet |
| **HEDGE-P** | In-the-money (ITM) Put | Smart money is *insuring a long position* against downside — they own the stock but are scared |

**Example:** If TSLA is trading at $400 and there's huge OI on the $460 Call expiring in 7 days — that's a BUY signal with a forecasted +15% move. Someone is betting TSLA reaches $460.

**Example:** If TSLA is trading at $400 and there's massive OI on the $350 Put — that's a HEDGE-P. A fund that owns 1 million TSLA shares is worried the stock might crash. They bought the right to *sell* at $350, so even if TSLA drops to $200, they can still sell at $350 and limit their loss. They're not betting TSLA goes down — they already own it and are buying insurance.

**Example:** If MSFT is trading at $408 and there's huge OI on the $350 Call — that's a HEDGE-C. A hedge fund that shorted MSFT at $350 is now deeply underwater and bought these calls to cap their losses if the stock keeps rising. They're not betting on upside; they're limiting their downside on a bad short.

---

## Dashboard Walkthrough

### Header Bar
Shows how many Buy/Sell/Hedge signals exist across all tickers and all time horizons. The "Δ vs yesterday" indicator shows whether signals have changed since the previous day's run.

### Period Pills (This Friday / 7 Days / 1 Month / …)
Switches which time horizon is shown in the main table. The date shown below each pill is the actual expiry date that was matched.

### Signal Filter
Narrows the table to only show tickers where the top contract for the selected period is BUY, SELL, HEDGE-C, or HEDGE-P.

### Min OI Filter
Dims or hides contracts below your minimum OI threshold. Use **1K+** as your baseline — anything below 1,000 OI isn't worth serious attention.

### Main Chart
Bar chart of forecasted % moves for the selected period. Green = BUY, Red = SELL, Orange = HEDGE. Hover any bar for the full contract details.

### All Tickers Table
- Click any row to expand it
- The expanded view shows all 8 time horizons at once
- Each horizon shows the **top 3 contracts by OI** with signal, forecast %, and delta badges
- Below each horizon block is a **stacked bar chart**: green = call OI, red = put OI, grouped by strike — lets you see at a glance which strikes have the highest combined open interest
- Tickers with Mon/Wed expiries (e.g. TSLA, AAPL) show an **Intra-week Expiries** section with the same layout

### Earnings Flag
If a company's earnings date falls within a horizon's window, a ⚠ badge appears. Earnings announcements can invalidate the signal entirely — the OI from before earnings may reflect positions that get closed or rolled.

### Signal Flip Badge (↺)
If a ticker's top signal changed since the previous day's run (e.g. was BUY, now is SELL), a flip badge appears. These are worth paying close attention to.

---

## Project Structure

```
options/
├── main.py              # Entry point — orchestrates everything
├── universe.py          # List of tickers (S&P 500 IT + Nasdaq-100)
├── fetcher.py           # Fetches price, earnings, company info via yfinance
├── nasdaq_fetcher.py    # Fetches options chain (OI + volume) from NASDAQ public API
├── analyzer.py          # Core logic: finds top contracts, classifies signals, computes forecasts
├── exporter_html.py     # Generates the self-contained interactive HTML dashboard
├── requirements.txt     # Python dependencies
├── docs/
│   └── index.html       # Latest report — served by GitHub Pages
├── reports/
│   ├── latest_analysis.json          # Snapshot used for delta comparison
│   └── options_signals_*.html/xlsx   # All generated reports (gitignored)
└── .github/workflows/
    └── daily_report.yml  # GitHub Actions — runs at 4:30 PM ET on weekdays
```

---

## Running Locally

**Prerequisites:** Python 3.11+

```bash
# 1. Clone the repo
git clone https://github.com/shadowp2810/options-dashboard.git
cd options-dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run a quick test with a few tickers
python main.py --tickers AAPL TSLA MSFT NVDA

# 4. Run the full universe (~130 tickers, takes ~5 minutes)
python main.py

# 5. Open the generated HTML in your browser
open reports/options_signals_*.html
```

The `--tickers` flag is useful for quick testing or focusing on specific stocks you care about.

---

## How the Data Pipeline Works

```
yfinance (price, earnings, company info)
       +
NASDAQ Public API (full options chain: all expiries × all strikes × OI + volume)
       ↓
analyzer.py
  → For each ticker × each horizon:
      find the nearest expiry date
      rank all contracts by Open Interest
      take top 10
      classify signal (BUY/SELL/HEDGE-C/HEDGE-P)
      calculate forecasted % move
      compare to yesterday's snapshot → compute deltas
       ↓
exporter_html.py → self-contained HTML dashboard (Chart.js embedded)
main.py          → Excel report (.xlsx) with color-coded cells
```

---

## How the Daily Auto-Deploy Works

A GitHub Actions workflow (`.github/workflows/daily_report.yml`) runs every weekday at **9:30 PM UTC (4:30 PM ET)** — 30 minutes after NYSE closes so final OI settles.

```
GitHub Actions (free, runs in the cloud)
  → python main.py        (generates HTML + saves snapshot)
  → copies HTML to docs/index.html
  → git commit + git push
  → GitHub Pages serves docs/index.html at options.pranavp.dev
```

**To trigger a manual run:** Go to your GitHub repo → Actions tab → "Daily Options Report" → "Run workflow".

---

## Data Sources & Limitations

| Data | Source | Notes |
|---|---|---|
| Stock price | Yahoo Finance (yfinance) | Real-time during market hours |
| Options chain, OI, Volume | NASDAQ public API | ~15 min delayed during market hours; OI is always previous-day close |
| Earnings dates | Yahoo Finance | Best-effort; may occasionally be off by a day |
| Company name / sector | Yahoo Finance | Used in expanded view only |

**Important limitations to keep in mind:**

- **OI is always from the previous close.** Exchanges publish OI once per day. Even a "real-time" paid API gives you yesterday's OI.
- **The data is a snapshot, not a live feed.** It runs once at market close. If a major event happens mid-day (e.g. earnings surprise), the dashboard won't reflect it until the next run.
- **High OI ≠ guaranteed move.** It means someone has a large position. That position could be a hedge, a spread, or an institutional algo. Use signals as one input among many — never as the sole reason to trade.
- **Earnings change everything.** If earnings fall within a horizon, the pre-earnings OI was placed before the report. Post-earnings, contracts get repriced and OI shifts dramatically.

---

## Glossary

| Term | Meaning |
|---|---|
| **Strike price** | The price at which the option contract gives the right to buy/sell |
| **Expiry** | The date the contract expires — after this it's worthless |
| **Call** | Right to *buy* a stock at the strike price |
| **Put** | Right to *sell* a stock at the strike price |
| **OTM (Out of the Money)** | For a call: strike is *above* current price. For a put: strike is *below*. The stock has to move for the option to have value. |
| **ITM (In the Money)** | For a call: strike is *below* current price. For a put: strike is *above*. The option already has intrinsic value. |
| **Open Interest (OI)** | Total number of contracts currently open (not yet settled) |
| **Volume** | Contracts traded today |
| **Forecast %** | How far the stock would need to move to reach the strike from current price |
| **LEAPS** | Long-dated options (1 year+) — often used for large institutional bets |
| **Smart money** | Institutional investors (hedge funds, banks, large traders) whose large positions show up as high OI |
