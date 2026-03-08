"""
Generates a self-contained HTML dashboard from analyzed options data.
Chart.js is loaded from CDN. All data is embedded as a JSON blob.
No server required — just open the file in a browser.
"""

import json
from pathlib import Path
from analyzer import HORIZONS, TOP_N

HORIZONS_ORDER = list(HORIZONS.keys())
HORIZON_LABELS = {"1d": "1 Day", "3d": "3 Days", "7d": "7 Days", "14d": "2 Weeks", "30d": "1 Month"}


def write_html(analyzed: list[dict], output_path: Path, timestamp: str) -> None:
    data_payload = json.dumps(
        {"generated": timestamp, "tickers": analyzed},
        default=str,
    )

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
  .rank-vol {{ color: var(--text-dim); font-size: 10px; }}

  /* ---- Empty state ---- */
  .empty-state {{
    text-align: center;
    padding: 60px 20px;
    color: var(--text-dim);
  }}
  .empty-state p {{ margin-top: 8px; font-size: 12px; }}

  /* ---- Scrollbar ---- */
  ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
  ::-webkit-scrollbar-track {{ background: var(--bg); }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
  ::-webkit-scrollbar-thumb:hover {{ background: var(--text-dim); }}
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <h1>Options <span>Volume Signal</span> Dashboard</h1>
    <p>Generated: {timestamp} &nbsp;·&nbsp; S&amp;P 500 IT + Nasdaq-100</p>
  </div>
  <div class="header-stats">
    <div class="stat"><div class="stat-val buy" id="stat-buy">—</div><div class="stat-lbl">Buy Signals</div></div>
    <div class="stat"><div class="stat-val sell" id="stat-sell">—</div><div class="stat-lbl">Sell Signals</div></div>
    <div class="stat"><div class="stat-val" id="stat-tickers">—</div><div class="stat-lbl">Tickers</div></div>
  </div>
</div>

<div class="controls">
  <div class="control-group">
    <label>Period</label>
    <div class="pill-group" id="period-pills">
      <button class="pill active" data-period="1d">1 Day</button>
      <button class="pill" data-period="3d">3 Days</button>
      <button class="pill" data-period="7d">7 Days</button>
      <button class="pill" data-period="14d">2 Weeks</button>
      <button class="pill" data-period="30d">1 Month</button>
    </div>
  </div>
  <div class="control-group">
    <label>Signal</label>
    <div class="pill-group" id="signal-pills">
      <button class="pill active" data-signal="all">All</button>
      <button class="pill buy" data-signal="BUY">BUY</button>
      <button class="pill sell" data-signal="SELL">SELL</button>
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
        <div class="card-subtitle">Sorted highest gain → loss · Green = BUY · Red = SELL</div>
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
const HORIZONS = ["1d","3d","7d","14d","30d"];
const HORIZON_LABELS = {{"1d":"1 Day","3d":"3 Days","7d":"7 Days","14d":"2 Weeks","30d":"1 Month"}};
const TOP_N = {TOP_N};

let state = {{
  period: "1d",
  signal: "all",
  search: "",
  sortCol: null,
  sortDir: 1,
}};

let chartInstance = null;

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
  return v.toLocaleString("en-US");
}}
function badge(signal) {{
  if (!signal) return '<span class="badge na">N/A</span>';
  const cls = signal === "BUY" ? "buy" : "sell";
  return `<span class="badge ${{cls}}">${{signal}}</span>`;
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
      if (!c || c.signal !== state.signal) return false;
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
    return c.signal === "BUY" ? "rgba(34,197,94,0.75)" : "rgba(239,68,68,0.75)";
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
    ${{HORIZONS.map(h => `
      <th class="th-horizon ${{state.sortCol === "pct_" + h ? "sorted" : ""}}" data-sort="pct_${{h}}">
        ${{HORIZON_LABELS[h]}} ${{sortIcon("pct_" + h)}}
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
      render();
    }});
  }});
}}

function periodCell(ticker, period) {{
  const c = getTopContract(ticker, period);
  if (!c || !c.signal) return `<td class="period-cell"><span class="pct na">N/A</span></td>`;
  return `<td class="period-cell">${{badge(c.signal)}} ${{fmt(c.forecast_pct)}}</td>`;
}}

function renderDetailRow(ticker, colSpan) {{
  const h_blocks = HORIZONS.map(h => {{
    const hData = ticker.horizons[h];
    const expiry = hData ? hData.expiry : null;
    const contracts = hData ? hData.contracts : [];
    const rankClasses = ["r1", "r2", "r3"];
    const rankRows = contracts.map((c, i) => {{
      if (!c || !c.signal) return `
        <div class="rank-row">
          <div class="rank-num ${{rankClasses[i]}}">${{i + 1}}</div>
          <div class="rank-detail"><span class="pct na">N/A</span></div>
        </div>`;
      return `
        <div class="rank-row">
          <div class="rank-num ${{rankClasses[i]}}">${{i + 1}}</div>
          <div class="rank-detail">
            <span class="rank-strike">$${{c.strike ?? "—"}}</span>
            ${{badge(c.signal)}}
            ${{fmt(c.forecast_pct)}}
            <span class="rank-vol">Vol: ${{fmtVol(c.volume)}}</span>
          </div>
        </div>`;
    }}).join("");

    return `<div class="horizon-block">
      <div class="horizon-block-header">
        <span>${{HORIZON_LABELS[h]}}</span>
        <span class="expiry">${{expiry ?? "N/A"}}</span>
      </div>
      ${{rankRows}}
    </div>`;
  }}).join("");

  return `<tr class="detail-row" id="detail-${{ticker.ticker}}">
    <td class="detail-cell" colspan="${{colSpan}}">
      <div class="detail-inner">${{h_blocks}}</div>
    </td>
  </tr>`;
}}

function renderTableBody(data) {{
  const tbody = document.getElementById("table-body");
  const colSpan = 2 + HORIZONS.length;

  if (data.length === 0) {{
    tbody.innerHTML = "";
    document.getElementById("empty-state").style.display = "block";
    return;
  }}
  document.getElementById("empty-state").style.display = "none";

  tbody.innerHTML = data.map(t => `
    <tr class="main-row" data-ticker="${{t.ticker}}">
      <td><div class="ticker-cell"><span class="expand-icon">▶</span>${{t.ticker}}</div></td>
      <td class="price-cell">${{fmtPrice(t.price)}}</td>
      ${{HORIZONS.map(h => periodCell(t, h)).join("")}}
    </tr>
    ${{renderDetailRow(t, colSpan)}}
  `).join("");

  tbody.querySelectorAll(".main-row").forEach(row => {{
    row.addEventListener("click", () => {{
      const ticker = row.dataset.ticker;
      const detailRow = document.getElementById(`detail-${{ticker}}`);
      const expanded = detailRow.classList.toggle("visible");
      row.classList.toggle("expanded", expanded);
    }});
  }});
}}

function updateStats(data) {{
  let buy = 0, sell = 0;
  data.forEach(t => {{
    HORIZONS.forEach(h => {{
      const contracts = t.horizons[h]?.contracts ?? [];
      contracts.forEach(c => {{
        if (c?.signal === "BUY") buy++;
        else if (c?.signal === "SELL") sell++;
      }});
    }});
  }});
  document.getElementById("stat-buy").textContent = buy.toLocaleString();
  document.getElementById("stat-sell").textContent = sell.toLocaleString();
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
document.getElementById("period-pills").addEventListener("click", e => {{
  const btn = e.target.closest("[data-period]");
  if (!btn) return;
  document.querySelectorAll("[data-period]").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  state.period = btn.dataset.period;
  state.sortCol = null;
  render();
}});

document.getElementById("signal-pills").addEventListener("click", e => {{
  const btn = e.target.closest("[data-signal]");
  if (!btn) return;
  document.querySelectorAll("[data-signal]").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  state.signal = btn.dataset.signal;
  render();
}});

document.getElementById("search-input").addEventListener("input", e => {{
  state.search = e.target.value;
  render();
}});

// ---- Init ----
render();
</script>
</body>
</html>
"""

    output_path.write_text(html, encoding="utf-8")
    print(f"HTML viewer:  {output_path.resolve()}")
