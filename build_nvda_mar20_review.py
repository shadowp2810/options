"""
build_nvda_mar20_review.py
Generates a standalone HTML page showing NVDA's Top OI by Strike and
Top Volume by Strike stacked bar charts for the Mar 20, 2026 expiry,
one column per day, from every available historical report.
"""
import json
import re
from datetime import datetime
from pathlib import Path

TARGET_TICKER  = "NVDA"
TARGET_EXPIRY  = "2026-03-20"
REPORTS_DIR    = Path(__file__).parent / "reports"
OUTPUT_PATH    = REPORTS_DIR / f"nvda_mar20_review.html"
TOP_N          = 10

DAY_NAMES = {
    "20260311": "Wed Mar 11",
    "20260312": "Thu Mar 12",
    "20260313": "Fri Mar 13",
    # "20260315": "Sun Mar 15",  # weekend — excluded
    "20260317": "Tue Mar 17",
    "20260318": "Wed Mar 18",
    "20260319": "Thu Mar 19",
    "20260320": "Fri Mar 20",
}

# ── collect data ──────────────────────────────────────────────────────────────
days = []
for path in sorted(REPORTS_DIR.glob("options_signals_2026031[0-9]_*.html")):
    daykey = path.stem.split("_")[2]       # e.g. "20260311"
    if daykey not in DAY_NAMES:            # skip weekends / excluded days
        continue
    html = path.read_text(encoding="utf-8")
    m = re.search(r"const RAW = (\{.*?\});", html, re.DOTALL)
    if not m:
        continue
    data = json.loads(m.group(1))
    nvda = next((t for t in data["tickers"] if t["ticker"] == TARGET_TICKER), None)
    if not nvda:
        continue

    contracts = None
    for hdata in nvda.get("horizons", {}).values():
        if hdata.get("expiry") == TARGET_EXPIRY:
            contracts = [c for c in hdata.get("contracts", []) if c.get("signal")]
            break

    if not contracts:
        continue

    # Build per-strike OI and Vol maps
    by_strike = {}
    for c in contracts:
        k = float(c["strike"])
        if k not in by_strike:
            by_strike[k] = dict(callOI=0, putOI=0, callVol=0, putVol=0)
        t = (c.get("type") or "").lower()
        if t == "call":
            by_strike[k]["callOI"]  = c.get("open_interest") or 0
            by_strike[k]["callVol"] = c.get("volume") or 0
        else:
            by_strike[k]["putOI"]   = c.get("open_interest") or 0
            by_strike[k]["putVol"]  = c.get("volume") or 0

    # Top 10 strikes by combined OI
    top_strikes = sorted(
        by_strike.keys(),
        key=lambda k: by_strike[k]["callOI"] + by_strike[k]["putOI"],
        reverse=True
    )[:TOP_N]
    top_strikes.sort()  # ascending for chart x-axis

    # Find current price from the ticker data
    price = nvda.get("price") or 0

    # Shared x-range
    if len(top_strikes) >= 2:
        gap_l = top_strikes[1] - top_strikes[0]
        gap_r = top_strikes[-1] - top_strikes[-2]
        xmin = top_strikes[0]  - gap_l * 0.6
        xmax = top_strikes[-1] + gap_r * 0.6
    else:
        xmin = (top_strikes[0] - 5) if top_strikes else 0
        xmax = (top_strikes[0] + 5) if top_strikes else 100

    days.append({
        "daykey":      daykey,
        "label":       DAY_NAMES.get(daykey, daykey),
        "top_strikes": top_strikes,
        "by_strike":   {(str(int(k)) if k == int(k) else str(k)): by_strike[k] for k in top_strikes},
        "price":       price,
        "xmin":        xmin,
        "xmax":        xmax,
    })

print(f"Found {len(days)} days of data for {TARGET_TICKER} / {TARGET_EXPIRY}")

# ── build HTML ────────────────────────────────────────────────────────────────
days_js = json.dumps(days, default=str)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NVDA · Mar 20 Expiry · Daily OI &amp; Volume Progression</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #0b0e1a;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    padding: 24px 20px 48px;
  }}
  h1 {{
    font-size: 20px;
    font-weight: 700;
    color: #e2e8f0;
    margin-bottom: 4px;
  }}
  h1 span {{ color: #818cf8; }}
  .subtitle {{
    font-size: 12px;
    color: #64748b;
    margin-bottom: 28px;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 20px;
  }}
  .day-card {{
    background: #13162a;
    border: 1px solid #2a2d4a;
    border-radius: 10px;
    overflow: hidden;
  }}
  .day-header {{
    background: #1a1f3a;
    padding: 8px 14px;
    font-size: 12px;
    font-weight: 700;
    color: #818cf8;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    border-bottom: 1px solid #2a2d4a;
  }}
  .chart-section {{
    padding: 10px 12px 6px;
    border-bottom: 1px solid #1e2240;
  }}
  .chart-section:last-child {{ border-bottom: none; }}
  .chart-label {{
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #475569;
    font-weight: 600;
    margin-bottom: 4px;
  }}
  .chart-wrap {{
    position: relative;
    height: 160px;
  }}
  canvas {{ display: block; }}
  .price-tag {{
    font-size: 10px;
    color: #64748b;
    margin-top: 3px;
    text-align: right;
  }}
  .price-tag span {{ color: #facc15; font-weight: 600; }}
</style>
</head>
<body>

<h1>NVDA · <span>Mar 20, 2026</span> Expiry — Daily OI &amp; Volume Progression</h1>
<p class="subtitle">
  Top OI by Strike and Top Volume by Strike for each trading day leading up to March 20 expiry.
  Yellow line = closing price on that day.
</p>

<div class="grid" id="grid"></div>

<script>
const DAYS = {days_js};

function buildPlugins(pluginId, strikes, currentPrice, xmin, xmax) {{
  return [
    {{
      id: pluginId + "_pl",
      beforeDraw(chart) {{
        const xScale = chart.scales.x;
        if (!xScale) return;
        const xPx = xScale.getPixelForValue(currentPrice);
        if (xPx < xScale.left || xPx > xScale.right) return;
        const ctx = chart.ctx;
        ctx.save();
        ctx.beginPath();
        ctx.setLineDash([4, 3]);
        ctx.strokeStyle = "rgba(250,204,21,0.8)";
        ctx.lineWidth = 1.5;
        ctx.moveTo(xPx, chart.chartArea.top);
        ctx.lineTo(xPx, chart.chartArea.bottom);
        ctx.stroke();
        ctx.restore();
      }}
    }},
    {{
      id: pluginId + "_xb",
      beforeUpdate(chart) {{
        const so = chart.options.scales.x;
        so.min = xmin;
        so.max = xmax;
      }}
    }}
  ];
}}

function commonScales() {{
  return {{
    x: {{
      type: "linear",
      stacked: true,
      ticks: {{ color: "#64748b", font: {{ size: 9 }}, maxRotation: 40, callback: v => `$${{v}}`, maxTicksLimit: 10 }},
      grid: {{ color: "rgba(255,255,255,0.04)" }},
      border: {{ display: false }}
    }},
    y: {{
      stacked: true,
      ticks: {{ color: "#475569", font: {{ size: 9 }}, maxTicksLimit: 4 }},
      grid: {{ color: "rgba(255,255,255,0.06)" }},
      border: {{ display: false }}
    }}
  }};
}}

function jsKey(k) {{ return k % 1 === 0 ? String(Math.round(k)) : String(k); }}

function buildOIChart(canvasId, day) {{
  const s = day.top_strikes;
  const b = day.by_strike;
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  new Chart(canvas.getContext("2d"), {{
    type: "bar",
    plugins: buildPlugins("oi_" + canvasId, s, day.price, day.xmin, day.xmax),
    data: {{
      datasets: [
        {{
          label: "Call OI",
          data: s.map(k => ({{ x: k, y: b[jsKey(k)]?.callOI ?? 0 }})),
          backgroundColor: "rgba(74,222,128,0.85)",
          borderColor: "rgba(74,222,128,1)",
          barThickness: 2,
        }},
        {{
          label: "Put OI",
          data: s.map(k => ({{ x: k, y: b[jsKey(k)]?.putOI ?? 0 }})),
          backgroundColor: "rgba(248,113,113,0.85)",
          borderColor: "rgba(248,113,113,1)",
          barThickness: 2,
        }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            title: items => "$" + items[0].parsed.x,
            label: item => item.dataset.label + ": " + (item.parsed.y / 1000).toFixed(1) + "k"
          }}
        }}
      }},
      scales: commonScales()
    }}
  }});
}}

function buildVolChart(canvasId, day) {{
  const s = day.top_strikes;
  const b = day.by_strike;
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  new Chart(canvas.getContext("2d"), {{
    type: "bar",
    plugins: buildPlugins("vol_" + canvasId, s, day.price, day.xmin, day.xmax),
    data: {{
      datasets: [
        {{
          label: "Call Vol",
          data: s.map(k => ({{ x: k, y: b[jsKey(k)]?.callVol ?? 0 }})),
          backgroundColor: "rgba(96,165,250,0.85)",
          borderColor: "rgba(96,165,250,1)",
          barThickness: 2,
        }},
        {{
          label: "Put Vol",
          data: s.map(k => ({{ x: k, y: b[jsKey(k)]?.putVol ?? 0 }})),
          backgroundColor: "rgba(251,146,60,0.85)",
          borderColor: "rgba(251,146,60,1)",
          barThickness: 2,
        }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            title: items => "$" + items[0].parsed.x,
            label: item => item.dataset.label + ": " + (item.parsed.y / 1000).toFixed(1) + "k"
          }}
        }}
      }},
      scales: commonScales()
    }}
  }});
}}

// Render grid
const grid = document.getElementById("grid");
DAYS.forEach((day, i) => {{
  const oiId  = "oi-"  + i;
  const volId = "vol-" + i;
  const card = document.createElement("div");
  card.className = "day-card";
  card.innerHTML = `
    <div class="day-header">${{day.label}}</div>
    <div class="chart-section">
      <div class="chart-label">Top OI by Strike</div>
      <div class="chart-wrap"><canvas id="${{oiId}}"></canvas></div>
    </div>
    <div class="chart-section">
      <div class="chart-label">Top Volume by Strike</div>
      <div class="chart-wrap"><canvas id="${{volId}}"></canvas></div>
      <div class="price-tag">Price: <span>$${{day.price?.toFixed(2) ?? "N/A"}}</span></div>
    </div>
  `;
  grid.appendChild(card);
  requestAnimationFrame(() => {{
    buildOIChart(oiId, day);
    buildVolChart(volId, day);
  }});
}});
</script>
</body>
</html>
"""

OUTPUT_PATH.write_text(html, encoding="utf-8")
print(f"Generated: {OUTPUT_PATH}")
