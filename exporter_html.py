"""
Generates a self-contained HTML dashboard from analyzed options data.
Chart.js is loaded from CDN. All data is embedded as a JSON blob.
No server required — just open the file in a browser.
"""

import json
from pathlib import Path
from analyzer import HORIZONS, TOP_N

HORIZONS_ORDER = list(HORIZONS.keys())
HORIZON_LABELS = {
    "fri":  "This Friday",
    "7d":   "7 Days",
    "30d":  "1 Month",
    "45d":  "45 Days",
    "60d":  "60 Days",
    "90d":  "90 Days",
    "180d": "6 Months",
    "1y":   "1 Year",
}


def write_html(
    analyzed: list[dict],
    output_path: Path,
    timestamp: str,
    snapshot_info: dict | None = None,
) -> None:
    if snapshot_info is None:
        snapshot_info = {}

    data_payload = json.dumps(
        {"generated": timestamp, "tickers": analyzed},
        default=str,
    )

    # Build the delta context string shown in the header
    age_days = snapshot_info.get("age_days")
    suppressed = snapshot_info.get("suppressed", False)
    snap_generated = snapshot_info.get("generated")

    if suppressed:
        delta_context = f'<span class="delta-stale">⚠ Δ suppressed — snapshot is {age_days}d old (limit: {snapshot_info.get("max_age", 3)}d)</span>'
    elif age_days is None:
        delta_context = '<span class="delta-none">Δ no previous snapshot</span>'
    elif age_days == 0:
        delta_context = '<span class="delta-fresh">Δ vs earlier today</span>'
    elif age_days == 1:
        delta_context = '<span class="delta-fresh">Δ vs yesterday</span>'
    else:
        delta_context = f'<span class="delta-fresh">Δ vs {age_days} days ago</span>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Options Volume Signal Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #22263a;
    --border: #2e3250;
    --accent: #4f7ef8;
    --green: #22c55e;
    --green-dim: #166534;
    --green-bg: #052e16;
    --red: #ef4444;
    --red-dim: #991b1b;
    --red-bg: #2d0b0b;
    --yellow: #f59e0b;
  --orange: #f97316;
  --orange-dim: #9a3412;
  --orange-bg: #2c1206;
    --text: #e2e8f0;
    --text-muted: #94a3b8;
    --text-dim: #64748b;
    --radius: 10px;
    --font: 'Inter', system-ui, sans-serif;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    font-size: 13px;
    min-height: 100vh;
  }}

  /* ---- Header ---- */
  .header {{
    background: linear-gradient(135deg, #1a1d27 0%, #0f1117 100%);
    border-bottom: 1px solid var(--border);
    padding: 18px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(10px);
  }}
  .header-left h1 {{
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.3px;
    color: #fff;
  }}
  .header-left h1 span {{ color: var(--accent); }}
  .header-left p {{ color: var(--text-muted); font-size: 11px; margin-top: 2px; }}
  .header-stats {{ display: flex; gap: 20px; }}
  .stat {{
    text-align: right;
    line-height: 1.3;
  }}
  .stat-val {{ font-size: 18px; font-weight: 700; }}
  .stat-lbl {{ font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }}
  .stat-val.buy {{ color: var(--green); }}
  .stat-val.sell {{ color: var(--red); }}

  /* ---- Controls bar ---- */
  .controls {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 28px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
  }}
  .control-group {{ display: flex; align-items: center; gap: 6px; }}
  .control-group label {{ color: var(--text-muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; }}
  .pill-group {{ display: flex; gap: 3px; }}
  .pill-date {{ display: block; font-size: 0.65rem; opacity: 0.72; font-weight: 400; line-height: 1.1; margin-top: 1px; }}
  .ticker-meta {{
    padding: 10px 20px 12px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: baseline;
    gap: 10px;
    flex-wrap: wrap;
  }}
  .ticker-meta-name {{ font-size: 14px; font-weight: 700; color: var(--text); }}
  .ticker-meta-tags {{ display: flex; gap: 6px; flex-wrap: wrap; }}
  .ticker-meta-tag {{
    font-size: 10px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 2px 7px;
    color: var(--text-muted);
  }}
  .intraweek-section {{ margin-top: 14px; border-top: 1px dashed #2e3250; padding-top: 10px; padding-bottom: 6px; }}
  .intraweek-header {{ font-size: 10px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #818cf8; margin-bottom: 8px; }}
  .intraweek-blocks {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  .intraweek-block {{ background: #13162a; border: 1px solid #2a2d4a; border-radius: 8px; padding: 8px 10px; min-width: 160px; flex: 0 0 auto; }}
  .intraweek-block-header {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; }}
  .intraweek-day {{ font-size: 11px; font-weight: 700; color: #818cf8; }}
  .intraweek-expiry {{ font-size: 10px; color: var(--text-dim); }}
  .pill {{
    padding: 5px 13px;
    border-radius: 20px;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    font-size: 12px;
    font-weight: 500;
    transition: all 0.15s;
  }}
  .pill:hover {{ border-color: var(--accent); color: var(--text); }}
  .pill.active {{ background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 600; }}
  .pill.active.buy {{ background: var(--green); border-color: var(--green); }}
  .pill.active.sell {{ background: var(--red); border-color: var(--red); }}
  .pill.active.hedge {{ background: var(--orange); border-color: var(--orange); }}
  .pill.active.hedge-p {{ background: var(--orange); border-color: var(--orange); }}
  .search-input {{
    padding: 6px 12px;
    border-radius: 20px;
    border: 1px solid var(--border);
    background: var(--surface2);
    color: var(--text);
    font-size: 12px;
    width: 160px;
    outline: none;
    transition: border-color 0.15s;
  }}
  .search-input::placeholder {{ color: var(--text-dim); }}
  .search-input:focus {{ border-color: var(--accent); }}
  .controls-right {{ margin-left: auto; display: flex; align-items: center; gap: 8px; }}
  .result-count {{ color: var(--text-dim); font-size: 11px; }}

  /* ---- Main layout ---- */
  .main {{ padding: 20px 28px; display: flex; flex-direction: column; gap: 20px; }}

  /* ---- Chart card ---- */
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
  }}
  .card-header {{
    padding: 14px 18px 10px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}
  .card-title {{ font-size: 13px; font-weight: 600; color: var(--text); }}
  .card-subtitle {{ font-size: 11px; color: var(--text-muted); margin-top: 2px; }}
  .chart-wrap {{ padding: 16px 18px; height: 280px; position: relative; }}

  /* ---- Table ---- */
  .signal-legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    padding: 10px 20px 12px;
    border-bottom: 1px solid var(--border);
    background: #13162a;
  }}
  .legend-item {{
    display: flex;
    align-items: flex-start;
    gap: 7px;
    font-size: 11px;
    color: var(--text-muted);
    line-height: 1.4;
  }}
  .legend-item .badge {{ flex-shrink: 0; margin-top: 1px; }}
  .legend-desc strong {{ color: var(--text); }}
  .table-wrap {{ overflow-x: auto; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }}
  thead tr {{
    background: var(--surface2);
    position: sticky;
    top: 0;
    z-index: 10;
  }}
  th {{
    padding: 10px 12px;
    text-align: left;
    color: var(--text-muted);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    white-space: nowrap;
    border-bottom: 1px solid var(--border);
    cursor: pointer;
    user-select: none;
    transition: color 0.15s;
  }}
  th:hover {{ color: var(--text); }}
  th.sorted {{ color: var(--accent); }}
  th .sort-icon {{ margin-left: 3px; opacity: 0.5; font-size: 9px; }}
  th.sorted .sort-icon {{ opacity: 1; }}
  tbody tr {{
    border-bottom: 1px solid var(--border);
    transition: background 0.1s;
    cursor: pointer;
  }}
  tbody tr:hover {{ background: var(--surface2); }}
  tbody tr.expanded {{ background: var(--surface2); }}
  td {{
    padding: 9px 12px;
    white-space: nowrap;
    vertical-align: middle;
  }}
  .ticker-cell {{
    font-weight: 700;
    font-size: 13px;
    color: var(--accent);
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .expand-icon {{
    font-size: 9px;
    color: var(--text-dim);
    transition: transform 0.2s;
    display: inline-block;
  }}
  tr.expanded .expand-icon {{ transform: rotate(90deg); }}
  .price-cell {{ color: var(--text); font-weight: 600; }}

  /* signal badge */
  .badge {{
    display: inline-flex;
    align-items: center;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
  }}
  .badge.buy {{ background: var(--green-bg); color: var(--green); border: 1px solid var(--green-dim); }}
  .badge.sell {{ background: var(--red-bg); color: var(--red); border: 1px solid var(--red-dim); }}
  .badge.hedge-c {{ background: var(--orange-bg); color: var(--orange); border: 1px solid var(--orange-dim); }}
  .badge.hedge-p {{ background: var(--orange-bg); color: var(--orange); border: 1px solid var(--orange-dim); }}
  .badge.na {{ background: var(--surface2); color: var(--text-dim); border: 1px solid var(--border); }}

  /* forecast % coloring */
  .pct {{ font-weight: 600; }}
  .pct.pos {{ color: var(--green); }}
  .pct.neg {{ color: var(--red); }}
  .pct.na {{ color: var(--text-dim); }}

  /* horizon column header group */
  .th-horizon {{
    text-align: center;
    color: var(--accent);
    font-size: 11px;
    border-left: 1px solid var(--border);
    padding: 8px 12px;
  }}
  .th-horizon.active-period {{
    background: rgba(99,102,241,0.12);
    color: #a5b4fc;
    border-bottom: 2px solid var(--accent);
  }}
  .th-date {{ display: block; font-size: 10px; font-weight: 400; color: var(--text-dim); margin-top: 2px; opacity: 0.8; }}
  td.period-cell {{ border-left: 1px solid var(--border); }}

  /* ---- Expanded detail rows ---- */
  .detail-row {{ display: none; }}
  .detail-row.visible {{ display: table-row; }}
  .detail-cell {{
    padding: 0 !important;
    background: #131622;
    border-bottom: 2px solid var(--accent) !important;
  }}
  .detail-inner {{
    padding: 14px 20px;
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
  }}
  .horizon-block {{
    flex: 1;
    min-width: 160px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }}
  .horizon-block-header {{
    background: var(--surface2);
    padding: 7px 12px;
    font-size: 11px;
    font-weight: 600;
    color: var(--text-muted);
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .horizon-block-header .expiry {{ font-size: 10px; color: var(--text-dim); font-weight: 400; }}
  .rank-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-bottom: 1px solid var(--border);
    font-size: 11px;
  }}
  .rank-row:last-child {{ border-bottom: none; }}
  .rank-num {{
    width: 18px;
    height: 18px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 9px;
    font-weight: 700;
    flex-shrink: 0;
  }}
  .rank-num.r1 {{ background: #f59e0b22; color: #f59e0b; border: 1px solid #f59e0b44; }}
  .rank-num.r2 {{ background: #64748b22; color: #94a3b8; border: 1px solid #64748b44; }}
  .rank-num.r3 {{ background: #7c3aed22; color: #a78bfa; border: 1px solid #7c3aed44; }}
  .rank-detail {{ flex: 1; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }}
  .rank-strike {{ color: var(--text); font-weight: 600; }}
  .rank-vol {{ font-size: 10px; }}
  .vol-vlow  {{ color: #334155; }}
  .vol-low   {{ color: #64748b; }}
  .vol-med   {{ color: var(--text-dim); }}
  .vol-high  {{ color: #4ade80; }}
  .vol-vhigh {{ color: #22c55e; font-weight: 600; }}
  .rank-row-dimmed {{ opacity: 0.28; }}
  .period-cell-dimmed {{ opacity: 0.3; }}

  /* ---- Empty state ---- */
  .empty-state {{
    text-align: center;
    padding: 60px 20px;
    color: var(--text-dim);
  }}
  .empty-state p {{ margin-top: 8px; font-size: 12px; }}

  /* ---- Earnings warning ---- */
  .earnings-badge {{
    display: inline-flex; align-items: center; gap: 3px;
    background: #2d1f00; color: #f59e0b;
    border: 1px solid #78450044; border-radius: 4px;
    padding: 1px 6px; font-size: 10px; font-weight: 700;
    letter-spacing: 0.3px;
  }}

  /* ---- Delta indicators ---- */
  .delta {{
    font-size: 10px; font-weight: 600;
    padding: 1px 5px; border-radius: 3px;
    white-space: nowrap;
  }}
  .delta.up {{ color: var(--green); background: var(--green-bg); }}
  .delta.down {{ color: var(--red); background: var(--red-bg); }}
  .delta.flat {{ color: var(--text-dim); }}

  /* ---- Snapshot age labels ---- */
  .delta-fresh {{
    font-size: 11px; font-weight: 600; color: var(--green);
    background: var(--green-bg); border: 1px solid var(--green-dim);
    border-radius: 4px; padding: 2px 8px;
  }}
  .delta-stale {{
    font-size: 11px; font-weight: 600; color: var(--yellow);
    background: #2d1f00; border: 1px solid #78450044;
    border-radius: 4px; padding: 2px 8px;
  }}
  .delta-none {{
    font-size: 11px; color: var(--text-dim);
    border: 1px solid var(--border); border-radius: 4px; padding: 2px 8px;
  }}

  /* ---- Signal flip alert ---- */
  .flip-badge {{
    display: inline-flex; align-items: center; gap: 3px;
    background: #1a0a2e; color: #a78bfa;
    border: 1px solid #4c1d9544; border-radius: 4px;
    padding: 1px 6px; font-size: 10px; font-weight: 700;
  }}

  /* ---- Scrollbar ---- */
  ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
  ::-webkit-scrollbar-track {{ background: var(--bg); }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
  ::-webkit-scrollbar-thumb:hover {{ background: var(--text-dim); }}

  /* ---- Mobile ---- */
  @media (max-width: 640px) {{
    .header {{
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;
      padding: 14px 16px;
      position: static;
    }}
    .header-stats {{
      width: 100%;
      justify-content: space-between;
    }}
    .stat {{ text-align: left; }}
    .stat-val {{ font-size: 16px; }}

    .controls {{
      padding: 10px 16px;
      gap: 10px;
    }}
    .control-group {{
      flex-direction: column;
      align-items: flex-start;
      width: 100%;
    }}
    .pill-group {{
      flex-wrap: wrap;
    }}
    .search-input {{
      width: 100%;
    }}
    .controls-right {{
      width: 100%;
      margin-left: 0;
    }}

    .main {{ padding: 12px 16px; }}

    .card-header {{ flex-direction: column; align-items: flex-start; gap: 6px; }}

    th, td {{ padding: 6px 8px; font-size: 11px; }}
    .th-horizon {{ padding: 6px 8px; }}

    .expand-icon {{ display: none; }}
    .ticker-cell {{ font-size: 12px; font-weight: 700; }}
    .price-cell {{ font-size: 11px; }}
  }}
</style>
</head>
<body>

<div class="header">
    <div class="header-left">
    <h1>Options <span>Volume Signal</span> Dashboard</h1>
    <p>Generated: {timestamp} &nbsp;·&nbsp; S&amp;P 500 IT + Nasdaq-100 &nbsp;·&nbsp; {delta_context}</p>
  </div>
  <div class="header-stats">
    <div class="stat"><div class="stat-val buy" id="stat-buy">—</div><div class="stat-lbl">Buy Signals</div></div>
    <div class="stat"><div class="stat-val sell" id="stat-sell">—</div><div class="stat-lbl">Sell Signals</div></div>
    <div class="stat"><div class="stat-val" style="color:var(--orange)" id="stat-hedge">—</div><div class="stat-lbl">Hedges (ITM)</div></div>
    <div class="stat"><div class="stat-val" id="stat-tickers">—</div><div class="stat-lbl">Tickers</div></div>
  </div>
</div>

<div class="controls">
  <div class="control-group">
    <label>Period</label>
    <div class="pill-group" id="period-pills">
      <button class="pill" data-period="fri">This Friday</button>
      <button class="pill active" data-period="7d">7 Days</button>
      <button class="pill" data-period="30d">1 Month</button>
      <button class="pill" data-period="45d">45 Days</button>
      <button class="pill" data-period="60d">60 Days</button>
      <button class="pill" data-period="90d">90 Days</button>
      <button class="pill" data-period="180d">6 Months</button>
      <button class="pill" data-period="1y">1 Year</button>
    </div>
  </div>
  <div class="control-group">
    <label>Signal</label>
    <div class="pill-group" id="signal-pills">
      <button class="pill active" data-signal="all">All</button>
      <button class="pill buy" data-signal="BUY">BUY</button>
      <button class="pill sell" data-signal="SELL">SELL</button>
      <button class="pill hedge" data-signal="HEDGE-C">HEDGE-C</button>
      <button class="pill hedge-p" data-signal="HEDGE-P">HEDGE-P</button>
    </div>
  </div>
  <div class="control-group">
    <label>Min Volume</label>
    <div class="pill-group" id="vol-pills">
      <button class="pill active" data-minvol="0">All</button>
      <button class="pill" data-minvol="500">500+</button>
      <button class="pill" data-minvol="1000">1K+</button>
      <button class="pill" data-minvol="2000">2K+</button>
      <button class="pill" data-minvol="10000">10K+</button>
    </div>
  </div>
  <div class="control-group">
    <label>Search</label>
    <input type="text" class="search-input" id="search-input" placeholder="e.g. AAPL, MSFT…">
  </div>
  <div class="controls-right">
    <span class="result-count" id="result-count"></span>
  </div>
</div>

<div class="main">

  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title" id="chart-title">Forecast % — 1 Day (Top-ranked contract per ticker)</div>
        <div class="card-subtitle">Sorted highest gain → loss · Green = BUY · Red = SELL · Orange = HEDGE-C (ITM Call) · Purple = HEDGE-P (ITM Put)</div>
      </div>
    </div>
    <div class="chart-wrap">
      <canvas id="mainChart"></canvas>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <div class="card-title">All Tickers</div>
    </div>
    <div class="signal-legend">
      <div class="legend-item">
        <span class="badge buy">BUY</span>
        <span class="legend-desc"><strong>OTM Call</strong> — market betting the stock goes up</span>
      </div>
      <div class="legend-item">
        <span class="badge sell">SELL</span>
        <span class="legend-desc"><strong>OTM Put</strong> — market betting the stock goes down</span>
      </div>
      <div class="legend-item">
        <span class="badge hedge-c">HEDGE-C</span>
        <span class="legend-desc"><strong>ITM Call</strong> — smart money covering a profitable short position</span>
      </div>
      <div class="legend-item">
        <span class="badge hedge-p">HEDGE-P</span>
        <span class="legend-desc"><strong>ITM Put</strong> — smart money insuring against further downside on a stock they hold</span>
      </div>
    </div>
    <div class="table-wrap">
      <table id="main-table">
        <thead id="table-head"></thead>
        <tbody id="table-body"></tbody>
      </table>
      <div class="empty-state" id="empty-state" style="display:none">
        <div style="font-size:32px">🔍</div>
        <p>No tickers match the current filters.</p>
      </div>
    </div>
  </div>

</div>

<script>
const RAW = {data_payload};
const HORIZONS = ["fri","7d","30d","45d","60d","90d","180d","1y"];
const HORIZON_LABELS = {{"fri":"This Friday","7d":"7 Days","30d":"1 Month","45d":"45 Days","60d":"60 Days","90d":"90 Days","180d":"6 Months","1y":"1 Year"}};
const TOP_N = {TOP_N};

let state = {{
  period: "7d",
  signal: "all",
  search: "",
  minVol: 0,
  sortCol: null,
  sortDir: 1,
}};

let chartInstance = null;
const horizonDates = {{}}; // populated by initPillDates(), reused in renderTableHead

// ---- Helpers ----
function fmt(v) {{
  if (v == null) return '<span class="pct na">N/A</span>';
  const cls = v > 0 ? "pos" : v < 0 ? "neg" : "";
  const sign = v > 0 ? "+" : "";
  return `<span class="pct ${{cls}}">${{sign}}${{v.toFixed(2)}}%</span>`;
}}
function fmtPrice(v) {{
  if (v == null) return '<span class="pct na">N/A</span>';
  return `${{v.toLocaleString("en-US", {{minimumFractionDigits:2, maximumFractionDigits:2}})}}`;
}}
function fmtVol(v) {{
  if (v == null) return "—";
  const s = v.toLocaleString("en-US");
  const cls = v < 500 ? "vol-vlow" : v < 2000 ? "vol-low" : v < 10000 ? "vol-med" : v < 50000 ? "vol-high" : "vol-vhigh";
  return `<span class="${{cls}}">${{s}}</span>`;
}}
function badge(signal) {{
  if (!signal) return '<span class="badge na">N/A</span>';
  const cls = signal === "BUY" ? "buy" : signal === "SELL" ? "sell"
    : signal === "HEDGE-C" ? "hedge-c" : signal === "HEDGE-P" ? "hedge-p" : "na";
  return `<span class="badge ${{cls}}">${{signal}}</span>`;
}}

function earningsBadge(inWindow, earningsDate) {{
  if (!inWindow) return "";
  const label = earningsDate ? `⚠ Earnings ${{earningsDate}}` : "⚠ Earnings";
  return `<span class="earnings-badge">${{label}}</span>`;
}}

function deltaBadge(c) {{
  if (c.strike_delta == null || c.prev_strike == null) return "";
  const sign = c.strike_delta > 0 ? "+" : "";
  const cls  = c.strike_delta > 0 ? "up" : c.strike_delta < 0 ? "down" : "flat";
  return `<span class="delta ${{cls}}" title="Was $${{c.prev_strike}}">${{sign}}$${{c.strike_delta.toFixed(2)}}</span>`;
}}

function flipBadge(c) {{
  if (!c.signal_flipped || !c.prev_signal) return "";
  return `<span class="flip-badge">↺ ${{c.prev_signal}}→${{c.signal}}</span>`;
}}
function getTopContract(ticker, period) {{
  const h = ticker.horizons[period];
  if (!h || !h.contracts || !h.contracts[0]) return null;
  return h.contracts[0];
}}
function getExpiry(ticker, period) {{
  const h = ticker.horizons[period];
  return h ? h.expiry : null;
}}

// ---- Filter & sort ----
function getVisible() {{
  let data = RAW.tickers.filter(t => {{
    const c = getTopContract(t, state.period);
    if (state.signal !== "all") {{
      const sig = c ? c.signal : null;
      if (!sig || sig !== state.signal) return false;
    }}
    if (state.search) {{
      if (!t.ticker.toLowerCase().includes(state.search.toLowerCase())) return false;
    }}
    return true;
  }});

  if (state.sortCol === "ticker") {{
    data.sort((a, b) => state.sortDir * a.ticker.localeCompare(b.ticker));
  }} else if (state.sortCol === "price") {{
    data.sort((a, b) => state.sortDir * ((a.price ?? -Infinity) - (b.price ?? -Infinity)));
  }} else if (state.sortCol && state.sortCol.startsWith("pct_")) {{
    const p = state.sortCol.replace("pct_", "");
    data.sort((a, b) => {{
      const ca = getTopContract(a, p);
      const cb = getTopContract(b, p);
      const pa = ca ? (ca.forecast_pct ?? -Infinity) : -Infinity;
      const pb = cb ? (cb.forecast_pct ?? -Infinity) : -Infinity;
      return state.sortDir * (pa - pb);
    }});
  }} else {{
    // default: sort by current period forecast desc
    data.sort((a, b) => {{
      const ca = getTopContract(a, state.period);
      const cb = getTopContract(b, state.period);
      const pa = ca ? (ca.forecast_pct ?? -Infinity) : -Infinity;
      const pb = cb ? (cb.forecast_pct ?? -Infinity) : -Infinity;
      return pb - pa;
    }});
  }}
  return data;
}}

// ---- Chart ----
function renderChart(data) {{
  const labels = data.map(t => t.ticker);
  const values = data.map(t => {{
    const c = getTopContract(t, state.period);
    return c ? (c.forecast_pct ?? 0) : 0;
  }});
  const colors = data.map(t => {{
    const c = getTopContract(t, state.period);
    if (!c || !c.signal) return "rgba(100,116,139,0.5)";
    if (c.signal === "BUY")   return "rgba(34,197,94,0.75)";
    if (c.signal === "SELL")  return "rgba(239,68,68,0.75)";
    if (c.signal === "HEDGE-C") return "rgba(249,115,22,0.75)";
    if (c.signal === "HEDGE-P") return "rgba(249,115,22,0.75)";
    return "rgba(100,116,139,0.5)";
  }});
  const borderColors = colors.map(c => c.replace("0.75", "1").replace("0.5", "0.9"));

  document.getElementById("chart-title").textContent =
    `Forecast % — ${{HORIZON_LABELS[state.period]}} (Top-ranked contract per ticker)`;

  if (chartInstance) chartInstance.destroy();

  const ctx = document.getElementById("mainChart").getContext("2d");
  chartInstance = new Chart(ctx, {{
    type: "bar",
    data: {{
      labels,
      datasets: [{{
        label: "Forecast %",
        data: values,
        backgroundColor: colors,
        borderColor: borderColors,
        borderWidth: 1,
        borderRadius: 3,
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            label(ctx) {{
              const t = data[ctx.dataIndex];
              const c = getTopContract(t, state.period);
              if (!c) return "N/A";
              return [
                `Strike: ${{c.strike ?? "N/A"}}`,
                `Type: ${{c.type ?? "N/A"}}`,
                `Volume: ${{fmtVol(c.volume)}}`,
                `Signal: ${{c.signal ?? "N/A"}}`,
                `Forecast: ${{c.forecast_pct != null ? (c.forecast_pct > 0 ? "+" : "") + c.forecast_pct.toFixed(2) + "%" : "N/A"}}`,
              ];
            }}
          }},
          backgroundColor: "#1a1d27",
          borderColor: "#2e3250",
          borderWidth: 1,
          titleColor: "#e2e8f0",
          bodyColor: "#94a3b8",
          padding: 10,
        }},
      }},
      scales: {{
        x: {{
          ticks: {{ color: "#64748b", font: {{ size: 10 }}, maxRotation: 60 }},
          grid: {{ color: "#1e2235" }},
        }},
        y: {{
          ticks: {{
            color: "#64748b",
            font: {{ size: 10 }},
            callback: v => (v > 0 ? "+" : "") + v.toFixed(1) + "%",
          }},
          grid: {{ color: "#1e2235" }},
        }},
      }},
    }}
  }});
}}

// ---- Table ----
function renderTableHead() {{
  const thead = document.getElementById("table-head");
  const sortIcon = (col) => {{
    const active = state.sortCol === col;
    const icon = active ? (state.sortDir === 1 ? "▲" : "▼") : "⇅";
    return `<span class="sort-icon">${{icon}}</span>`;
  }};

  thead.innerHTML = `<tr>
    <th class="${{state.sortCol === "ticker" ? "sorted" : ""}}" data-sort="ticker">Ticker ${{sortIcon("ticker")}}</th>
    <th class="${{state.sortCol === "price" ? "sorted" : ""}}" data-sort="price">Price ${{sortIcon("price")}}</th>
    <th>Earnings</th>
    ${{HORIZONS.map(h => `
      <th class="th-horizon ${{state.sortCol === "pct_" + h ? "sorted" : ""}} ${{state.period === h ? "active-period" : ""}}" data-sort="pct_${{h}}">
        ${{HORIZON_LABELS[h]}} ${{sortIcon("pct_" + h)}}
        ${{horizonDates[h] ? `<span class="th-date">${{new Date(horizonDates[h] + "T12:00:00").toLocaleDateString("en-US", {{month:"short",day:"numeric"}})}}</span>` : ""}}
      </th>`).join("")}}
  </tr>`;

  thead.querySelectorAll("th").forEach(th => {{
    th.addEventListener("click", () => {{
      const col = th.dataset.sort;
      if (state.sortCol === col) {{
        state.sortDir *= -1;
      }} else {{
        state.sortCol = col;
        state.sortDir = col === "ticker" ? 1 : -1;
      }}
      requestAnimationFrame(render);
    }});
  }});
}}

function periodCell(ticker, period) {{
  const h = ticker.horizons[period];
  const c = getTopContract(ticker, period);
  const ew = h ? h.earnings_in_window : false;
  if (!c || !c.signal) return `<td class="period-cell">${{earningsBadge(ew, ticker.earnings_date)}}<span class="pct na">N/A</span></td>`;
  const belowVol = state.minVol > 0 && (c.volume == null || c.volume < state.minVol);
  return `<td class="period-cell${{belowVol ? " period-cell-dimmed" : ""}}">
    ${{earningsBadge(ew, ticker.earnings_date)}}
    ${{badge(c.signal)}} ${{fmt(c.forecast_pct)}}
    ${{flipBadge(c)}}
  </td>`;
}}

function buildDetailCellContent(ticker) {{
  const h_blocks = HORIZONS.map(h => {{
    const hData = ticker.horizons[h];
    const expiry = hData ? hData.expiry : null;
    const earningsInWin = hData ? hData.earnings_in_window : false;
    const contracts = hData ? hData.contracts : [];
    const rankClasses = ["r1", "r2", "r3"];
    const rankRows = contracts.map((c, i) => {{
      if (!c || !c.signal) return `
        <div class="rank-row">
          <div class="rank-num ${{rankClasses[i]}}">${{i + 1}}</div>
          <div class="rank-detail"><span class="pct na">N/A</span></div>
        </div>`;
      const moneynessLabel = c.moneyness ? `<span style="font-size:9px;color:var(--text-dim);border:1px solid var(--border);border-radius:3px;padding:1px 4px;">${{c.moneyness}}</span>` : "";
      const dimmed = state.minVol > 0 && (c.volume == null || c.volume < state.minVol);
      return `
        <div class="rank-row${{dimmed ? " rank-row-dimmed" : ""}}">
          <div class="rank-num ${{rankClasses[i]}}">${{i + 1}}</div>
          <div class="rank-detail">
            <span class="rank-strike">$${{c.strike ?? "—"}}</span>
            ${{moneynessLabel}}
            ${{badge(c.signal)}}
            ${{fmt(c.forecast_pct)}}
            ${{deltaBadge(c)}}
            ${{flipBadge(c)}}
            <span class="rank-vol">Vol: ${{fmtVol(c.volume)}}</span>
          </div>
        </div>`;
    }}).join("");

    return `<div class="horizon-block">
      <div class="horizon-block-header">
        <span>${{HORIZON_LABELS[h]}} ${{earningsBadge(earningsInWin, ticker.earnings_date)}}</span>
        <span class="expiry">${{expiry ?? "N/A"}}</span>
      </div>
      ${{rankRows}}
    </div>`;
  }}).join("");

  // Intra-week section (Mon/Wed/Thu, only for hyper-liquid stocks)
  let intraweekHtml = "";
  const iw = ticker.intraweek || [];
  if (iw.length > 0) {{
    const iwBlocks = iw.map(entry => {{
      const rankClasses = ["r1", "r2", "r3"];
      const rows = entry.contracts.map((c, i) => {{
        if (!c || !c.signal) return `
          <div class="rank-row">
            <div class="rank-num ${{rankClasses[i]}}">${{i + 1}}</div>
            <div class="rank-detail"><span class="pct na">N/A</span></div>
          </div>`;
        const moneynessLabel = c.moneyness
          ? `<span style="font-size:9px;color:var(--text-dim);border:1px solid var(--border);border-radius:3px;padding:1px 4px;">${{c.moneyness}}</span>`
          : "";
        const dimmed = state.minVol > 0 && (c.volume == null || c.volume < state.minVol);
        return `
          <div class="rank-row${{dimmed ? " rank-row-dimmed" : ""}}">
            <div class="rank-num ${{rankClasses[i]}}">${{i + 1}}</div>
            <div class="rank-detail">
              <span class="rank-strike">$${{c.strike ?? "—"}}</span>
              ${{moneynessLabel}}
              ${{badge(c.signal)}}
              ${{fmt(c.forecast_pct)}}
              <span class="rank-vol">Vol: ${{fmtVol(c.volume)}}</span>
            </div>
          </div>`;
      }}).join("");
      return `<div class="intraweek-block">
        <div class="intraweek-block-header">
          <span class="intraweek-day">${{entry.day}}</span>
          <span class="intraweek-expiry">${{entry.expiry}}</span>
        </div>
        ${{rows}}
      </div>`;
    }}).join("");
    intraweekHtml = `<div class="intraweek-section">
      <div class="intraweek-header">⚡ Intra-week Expiries</div>
      <div class="intraweek-blocks">${{iwBlocks}}</div>
    </div>`;
  }}

  // Company meta bar
  const ci = ticker.company_info || {{}};
  const tags = [ci.sector, ci.industry].filter(Boolean);
  const metaHtml = (ci.name || tags.length) ? `
    <div class="ticker-meta">
      ${{ci.name ? `<span class="ticker-meta-name">${{ci.name}}</span>` : ""}}
      ${{tags.length ? `<div class="ticker-meta-tags">${{tags.map(t => `<span class="ticker-meta-tag">${{t}}</span>`).join("")}}</div>` : ""}}
    </div>` : "";

  return `${{metaHtml}}<div class="detail-inner">${{h_blocks}}</div>${{intraweekHtml}}`;
}}

const expandedTickers = new Set(); // persists across renders

function renderTableBody(data) {{
  const tbody = document.getElementById("table-body");
  const colSpan = 3 + HORIZONS.length;

  if (data.length === 0) {{
    tbody.innerHTML = "";
    document.getElementById("empty-state").style.display = "block";
    return;
  }}
  document.getElementById("empty-state").style.display = "none";

  // Render only main rows + empty detail placeholders (fast)
  tbody.innerHTML = data.map(t => {{
    const expanded = expandedTickers.has(t.ticker);
    return `
    <tr class="main-row${{expanded ? " expanded" : ""}}" data-ticker="${{t.ticker}}">
      <td><div class="ticker-cell"><span class="expand-icon">▶</span>${{t.ticker}}</div></td>
      <td class="price-cell">${{fmtPrice(t.price)}}</td>
      <td style="color:var(--text-muted);font-size:11px;white-space:nowrap">${{t.earnings_date ?? "—"}}</td>
      ${{HORIZONS.map(h => periodCell(t, h)).join("")}}
    </tr>
    <tr class="detail-row${{expanded ? " visible" : ""}}" id="detail-${{t.ticker}}">
      <td class="detail-cell" colspan="${{colSpan}}"></td>
    </tr>`;
  }}).join("");

  // Lazily populate content for already-expanded rows (usually 0-1, so fast)
  expandedTickers.forEach(ticker => {{
    const t = data.find(d => d.ticker === ticker);
    if (!t) return;
    const cell = document.querySelector(`#detail-${{ticker}} td`);
    if (cell) cell.innerHTML = buildDetailCellContent(t);
  }});
}}

function updateStats(data) {{
  let buy = 0, sell = 0, hedge = 0;
  data.forEach(t => {{
    HORIZONS.forEach(h => {{
      const contracts = t.horizons[h]?.contracts ?? [];
      contracts.forEach(c => {{
        if (c?.signal === "BUY")   buy++;
        else if (c?.signal === "SELL")   sell++;
        else if (c?.signal === "HEDGE-C" || c?.signal === "HEDGE-P") hedge++;
      }});
    }});
  }});
  document.getElementById("stat-buy").textContent = buy.toLocaleString();
  document.getElementById("stat-sell").textContent = sell.toLocaleString();
  document.getElementById("stat-hedge").textContent = hedge.toLocaleString();
  document.getElementById("stat-tickers").textContent = data.length;
  document.getElementById("result-count").textContent =
    `${{data.length}} of ${{RAW.tickers.length}} tickers`;
}}

// ---- Main render ----
function render() {{
  const data = getVisible();
  renderChart(data);
  renderTableHead();
  renderTableBody(data);
  updateStats(data);
}}

// ---- Event wiring ----

// Expand/collapse via event delegation — set up once, never re-attached
document.getElementById("table-body").addEventListener("click", e => {{
  const row = e.target.closest(".main-row");
  if (!row) return;
  const ticker = row.dataset.ticker;
  const detailRow = document.getElementById(`detail-${{ticker}}`);
  if (!detailRow) return;
  const expanded = detailRow.classList.toggle("visible");
  row.classList.toggle("expanded", expanded);
  if (expanded) {{
    expandedTickers.add(ticker);
    const cell = detailRow.querySelector("td");
    if (cell && !cell.innerHTML.trim()) {{
      // First time opening — find ticker in full dataset (not just filtered view)
      const t = RAW.tickers.find(d => d.ticker === ticker);
      if (t) cell.innerHTML = buildDetailCellContent(t);
    }}
  }} else {{
    expandedTickers.delete(ticker);
  }}
}});

document.getElementById("period-pills").addEventListener("click", e => {{
  const btn = e.target.closest("[data-period]");
  if (!btn) return;
  document.querySelectorAll("[data-period]").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  state.period = btn.dataset.period;
  state.sortCol = null;
  requestAnimationFrame(render);
}});

document.getElementById("signal-pills").addEventListener("click", e => {{
  const btn = e.target.closest("[data-signal]");
  if (!btn) return;
  document.querySelectorAll("[data-signal]").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  state.signal = btn.dataset.signal;
  requestAnimationFrame(render);
}});

document.getElementById("vol-pills").addEventListener("click", e => {{
  const btn = e.target.closest("[data-minvol]");
  if (!btn) return;
  document.querySelectorAll("[data-minvol]").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  state.minVol = parseInt(btn.dataset.minvol, 10);
  // Re-render any open detail rows so dimming updates immediately
  expandedTickers.forEach(ticker => {{
    const t = RAW.tickers.find(d => d.ticker === ticker);
    const cell = document.querySelector(`#detail-${{ticker}} td`);
    if (t && cell) cell.innerHTML = buildDetailCellContent(t);
  }});
  requestAnimationFrame(render);
}});

let searchTimer = null;
document.getElementById("search-input").addEventListener("input", e => {{
  state.search = e.target.value;
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => requestAnimationFrame(render), 150);
}});

// ---- Pill dates ----
function initPillDates() {{
  // Populate module-level horizonDates: first non-null expiry per horizon
  (RAW.tickers || []).forEach(t => {{
    HORIZONS.forEach(h => {{
      if (!horizonDates[h]) {{
        const expiry = t.horizons?.[h]?.expiry;
        if (expiry) horizonDates[h] = expiry;
      }}
    }});
  }});

  document.querySelectorAll("[data-period]").forEach(btn => {{
    const h = btn.dataset.period;
    const expiry = horizonDates[h];
    const label = HORIZON_LABELS[h] || h;
    if (expiry) {{
      const d = new Date(expiry + "T12:00:00");
      const dateStr = d.toLocaleDateString("en-US", {{ month: "short", day: "numeric" }});
      btn.innerHTML = `${{label}}<span class="pill-date">${{dateStr}}</span>`;
    }} else {{
      btn.textContent = label;
    }}
  }});
}}

// ---- Init ----
initPillDates();
render();
</script>
</body>
</html>
"""

    output_path.write_text(html, encoding="utf-8")
    print(f"HTML viewer:  {output_path.resolve()}")
