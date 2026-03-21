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
    iso_timestamp: str = "",
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
    daily_oi_label = snapshot_info.get("daily_oi_label", "yesterday")  # e.g. "Friday", "yesterday"

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
<title>Options Open Interest Signal Dashboard</title>
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
  .trend-bar {{
    padding: 8px 20px 9px;
    border-bottom: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 5px;
    font-size: 11px;
    color: var(--text-muted);
    background: rgba(255,255,255,0.02);
  }}
  .trend-bar-row {{
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px 12px;
  }}
  .trend-section-label {{ font-weight: 600; color: var(--text-muted); text-transform: uppercase; font-size: 9px; letter-spacing: 0.07em; }}
  .trend-val {{ font-weight: 700; font-size: 11px; }}
  .trend-val.up {{ color: #4ade80; }}
  .trend-val.down {{ color: #f87171; }}
  .trend-val.flat {{ color: var(--text-muted); }}
  .trend-val.na {{ color: var(--text-muted); opacity: 0.5; }}
  .trend-sep {{ color: var(--border); padding: 0 2px; font-size: 13px; }}
  .oi-horizon-group {{
    display: inline-flex; align-items: center; gap: 4px;
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 6px; padding: 3px 7px;
    font-size: 10px;
  }}
  @media (max-width: 600px) {{
    .trend-bar-row {{
      flex-direction: column;
      align-items: flex-start;
      gap: 4px;
    }}
    .oi-horizon-group {{
      width: fit-content;
    }}
  }}
  .oi-horizon-label {{ font-weight: 700; color: var(--text-muted); margin-right: 2px; }}
  .oi-side {{ font-weight: 700; }}
  .oi-side.up {{ color: #4ade80; }}
  .oi-side.down {{ color: #f87171; }}
  .oi-side.flat {{ color: var(--text-muted); }}
  .oi-side.none {{ color: var(--text-muted); opacity: 0.4; }}
  .combo-badge {{
    font-size: 10px; font-weight: 700; padding: 2px 7px;
    border-radius: 4px; text-transform: uppercase; letter-spacing: 0.05em;
    vertical-align: middle; white-space: nowrap;
  }}
  .combo-badge.Bullish       {{ background: #16a34a33; color: #4ade80; border: 1px solid #4ade8055; }}
  .combo-badge.Bearish       {{ background: #dc262633; color: #f87171; border: 1px solid #f8717155; }}
  .combo-badge.HedgedRally   {{ background: #a16207aa; color: #fde047; border: 1px solid #fde04755; }}
  .combo-badge.ShortCovering {{ background: #0e748933; color: #67e8f9; border: 1px solid #67e8f955; }}
  .combo-badge.BuildUp       {{ background: #6d28d933; color: #c4b5fd; border: 1px solid #c4b5fd55; }}
  .combo-badge.Unwinding     {{ background: #37415133; color: #94a3b8;  border: 1px solid #94a3b855; }}
  .intraweek-section {{ margin-top: 14px; border-top: 1px dashed #2e3250; padding-top: 10px; padding-bottom: 6px; }}
  .intraweek-header {{ font-size: 10px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #818cf8; margin-bottom: 8px; }}
  .intraweek-blocks {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  .intraweek-block {{ background: #13162a; border: 1px solid #2a2d4a; border-radius: 8px; padding: 8px 10px; min-width: 160px; flex: 0 0 auto; }}
  @media (max-width: 600px) {{
    .intraweek-section {{
      max-width: calc(100vw - 32px);
      /* overflow:clip clips visually without creating a scroll context,
         so it won't block child momentum scroll on iOS */
      overflow: clip;
    }}
    .intraweek-blocks {{
      flex-wrap: nowrap;
      overflow-x: scroll;
      -webkit-overflow-scrolling: touch;
      overscroll-behavior-x: contain;
      touch-action: pan-x;
      padding-bottom: 8px;
    }}
    .intraweek-block {{
      flex: 0 0 82vw;
      min-width: 0;
    }}
  }}
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
  .combo-legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    padding: 8px 20px 10px;
    border-bottom: 1px solid var(--border);
    background: #0f1226;
  }}
  .combo-legend-title {{
    width: 100%;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 2px;
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
  .legend-item .combo-badge {{ flex-shrink: 0; margin-top: 1px; }}
  .legend-desc strong {{ color: var(--text); }}
  .table-wrap {{
    overflow-x: scroll;
    -webkit-overflow-scrolling: touch;
    overscroll-behavior-x: contain;
  }}
  .table-scroll-top {{
    overflow-x: auto;
    overflow-y: hidden;
    height: 12px;
    /* only show when content actually overflows */
  }}
  .table-scroll-top-inner {{ height: 1px; }}
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
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 340px));
    gap: 16px;
    max-width: min(1440px, calc(100vw - 32px));
  }}
  .horizon-block {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    min-width: 0;
  }}
  /* Three-column layout inside each horizon block: OI | Volume | Momentum */
  .horizon-block-body {{
    display: flex;
    flex-direction: row;
    align-items: stretch;
  }}
  .horizon-block-left {{
    flex: 0 0 33%;
    min-width: 0;
    border-right: 1px solid var(--border);
  }}
  .horizon-block-middle {{
    flex: 0 0 33%;
    min-width: 0;
    border-right: 1px solid var(--border);
  }}
  /* Right column (momentum) height is driven by the left columns.
     The chart wrap is absolutely inset so Chart.js gets a fixed parent. */
  .horizon-block-right {{
    flex: 1;
    min-width: 0;
    position: relative;
    min-height: 220px;
  }}
  /* Small label above each rank list to distinguish OI vs Volume columns */
  .col-section-label {{
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-dim);
    padding: 4px 12px 3px;
    border-bottom: 1px solid var(--border);
  }}
  @media (max-width: 1000px) {{
    .detail-inner {{ grid-template-columns: repeat(2, 1fr); }}
  }}
  @media (max-width: 600px) {{
    .detail-inner {{
      display: flex;
      flex-direction: row;
      flex-wrap: nowrap;
      overflow-x: scroll;
      -webkit-overflow-scrolling: touch;
      overscroll-behavior-x: contain;
      touch-action: pan-x;
      gap: 10px;
      padding-bottom: 10px;
      max-width: min(1440px, calc(200vw - 32px));
    }}
    .horizon-block {{
      flex: 0 0 82vw;
    }}
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
    align-items: flex-start;
    gap: 8px;
    padding: 6px 12px;
    border-bottom: 1px solid var(--border);
    font-size: 11px;
  }}
  .rank-row:last-child {{ border-bottom: none; }}
  .rank-num-col {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
    flex-shrink: 0;
  }}
  .rank-num {{
    width: 18px;
    height: 18px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 9px;
    font-weight: 700;
  }}
  .rank-num.r1 {{ background: #f59e0b22; color: #f59e0b; border: 1px solid #f59e0b44; }}
  .rank-num.r2 {{ background: #64748b22; color: #94a3b8; border: 1px solid #64748b44; }}
  .rank-num.r3 {{ background: #7c3aed22; color: #a78bfa; border: 1px solid #7c3aed44; }}
  .rank-detail {{ flex: 1; display: flex; flex-direction: column; align-items: flex-start; gap: 1px; }}
  .rank-strike {{ color: var(--text); font-weight: 600; }}
  .rank-vol {{ font-size: 10px; color: var(--text-dim); }}
  .rank-label {{ font-size: 9px; opacity: 0.6; color: var(--text-dim); }}
  .vol-vlow  {{ color: #334155; }}
  .vol-low   {{ color: #64748b; }}
  .vol-med   {{ color: var(--text-dim); }}
  .vol-high  {{ color: #4ade80; }}
  .vol-vhigh {{ color: #22c55e; font-weight: 600; }}
  .rank-row-dimmed {{ opacity: 0.28; }}
  .period-cell-dimmed {{ opacity: 0.3; }}

  /* ---- OI bar chart inside horizon blocks ---- */
  .oi-chart-wrap {{
    padding: 6px 10px 12px;
    height: 160px;
    position: relative;
    border-top: 1px solid var(--border);
  }}
  .oi-chart-label {{
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-dim);
    margin-bottom: 4px;
  }}

  /* ---- OI Momentum line chart ---- */
  .momentum-chart-wrap {{
    position: absolute;
    inset: 0;
    padding: 6px 8px 10px;
    background: rgba(0,0,0,0.08);
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
  }}
  .momentum-chart-wrap canvas {{
    flex: 1;
    min-height: 0;
    /* Chart.js needs a positioned parent with explicit dimensions;
       absolute inset on the wrap gives exactly that */
  }}
  .momentum-chart-label {{
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #a78bfa;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 5px;
  }}
  .momentum-chart-label::before {{
    content: "↗";
    font-size: 10px;
  }}
  .momentum-expand-btn {{
    position: absolute;
    top: 6px;
    right: 8px;
    background: rgba(30,25,50,0.85);
    border: 1px solid #4c3a8a;
    border-radius: 4px;
    color: #a78bfa;
    font-size: 10px;
    padding: 2px 7px;
    cursor: pointer;
    line-height: 1.6;
    z-index: 10;
    transition: background 0.15s, border-color 0.15s;
  }}
  .momentum-expand-btn:hover {{
    background: rgba(167,139,250,0.18);
  }}
  /* ---- Custom floating stacked-bar tooltip for OI Momentum ---- */
  .mom-tooltip {{
    position: fixed;
    background: rgba(11,13,24,0.97);
    border: 1px solid #2e3250;
    border-radius: 8px;
    padding: 9px 11px 10px;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.08s;
    z-index: 9999;
    min-width: 190px;
  }}
  .mom-tt-date {{
    font-size: 9px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 7px;
  }}
  .mom-tt-row {{
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 4px;
  }}
  .mom-tt-strike {{
    color: #e2e8f0;
    font-weight: 700;
    font-size: 10px;
    width: 44px;
    flex-shrink: 0;
  }}
  .mom-tt-bars {{
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }}
  .mom-tt-bar-row {{
    display: flex;
    height: 7px;
    border-radius: 3px;
    overflow: hidden;
    background: #1a1d27;
  }}
  .mom-tt-call {{ background: #22c55e; height: 100%; }}
  .mom-tt-put  {{ background: #ef4444; height: 100%; }}
  .mom-tt-right {{
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    flex-shrink: 0;
    min-width: 56px;
  }}
  .mom-tt-total {{
    color: #94a3b8;
    font-size: 9px;
    text-align: right;
  }}
  .mom-tt-delta {{
    display: flex;
    gap: 3px;
    font-size: 8px;
    margin-top: 1px;
  }}
  .mom-tt-legend {{
    display: flex;
    gap: 8px;
    margin-top: 7px;
    padding-top: 6px;
    border-top: 1px solid #1e2235;
    font-size: 9px;
    color: #64748b;
  }}
  .mom-tt-legend span {{ display: flex; align-items: center; gap: 3px; }}
  .mom-tt-legend i {{
    display: inline-block; width: 8px; height: 8px; border-radius: 2px;
  }}

  /* ---- Momentum fullscreen modal ---- */
  #mom-modal {{
    display: none;
    position: fixed;
    inset: 0;
    z-index: 9999;
    background: rgba(0,0,0,0.82);
    backdrop-filter: blur(4px);
    align-items: center;
    justify-content: center;
  }}
  #mom-modal.open {{ display: flex; }}
  #mom-modal-box {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 20px 20px;
    width: min(96vw, 1200px);
    height: 92vh;
    display: flex;
    flex-direction: column;
    gap: 10px;
    box-shadow: 0 24px 80px rgba(0,0,0,0.7);
  }}
  #mom-modal-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12px;
    color: #a78bfa;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    flex-shrink: 0;
  }}
  #mom-modal-title {{ font-weight: 600; }}
  #mom-modal-close {{
    background: none;
    border: 1px solid #4c3a8a;
    border-radius: 6px;
    color: #a78bfa;
    font-size: 16px;
    padding: 2px 10px;
    cursor: pointer;
    line-height: 1.5;
  }}
  #mom-modal-close:hover {{ background: rgba(167,139,250,0.14); }}
  #mom-modal-canvas-wrap {{
    flex: 1;
    min-height: 0;
    position: relative;
  }}

  /* ---- Quick sort bar ---- */
  .quick-sort-bar {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 20px;
    border-bottom: 1px solid var(--border);
    overflow-x: scroll;
    -webkit-overflow-scrolling: touch;
    overscroll-behavior-x: contain;
    touch-action: pan-x;
    scrollbar-width: none;
  }}
  .quick-sort-bar::-webkit-scrollbar {{ display: none; }}
  .quick-sort-label {{
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-dim);
    white-space: nowrap;
    flex-shrink: 0;
  }}
  .quick-sort-btn {{
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-muted);
    font-size: 11px;
    padding: 3px 10px;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s, color 0.15s;
    white-space: nowrap;
    flex-shrink: 0;
  }}
  .quick-sort-btn:hover {{ background: #1e2235; color: var(--text); }}
  .quick-sort-btn.active {{
    background: #1e2a4a;
    border-color: #4a6fa5;
    color: #93c5fd;
  }}

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
<!-- Momentum fullscreen modal (single instance, reused) -->
<div id="mom-modal" role="dialog" aria-modal="true" aria-labelledby="mom-modal-title">
  <div id="mom-modal-box">
    <div id="mom-modal-header">
      <span id="mom-modal-title">OI Momentum</span>
      <button id="mom-modal-close" onclick="closeMomModal()" title="Close (Esc)">✕</button>
    </div>
    <div id="mom-modal-canvas-wrap">
      <canvas id="mom-modal-canvas"></canvas>
    </div>
  </div>
</div>

<div class="header">
    <div class="header-left">
    <h1>Options <span>Open Interest</span> Dashboard</h1>
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
      <button class="pill active" data-period="fri">This Friday</button>
      <button class="pill" data-period="7d">7 Days</button>
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
    <label>Min OI</label>
    <div class="pill-group" id="oi-pills">
      <button class="pill active" data-minoi="0">All</button>
      <button class="pill" data-minoi="500">500+</button>
      <button class="pill" data-minoi="1000">1K+</button>
      <button class="pill" data-minoi="5000">5K+</button>
      <button class="pill" data-minoi="10000">10K+</button>
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
        <div class="card-subtitle">Sorted highest gain → loss · Top contract ranked by OI · Vol shown for reference · Green = BUY · Red = SELL · Orange = HEDGE-C/P (ITM)</div>
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
    <div class="combo-legend">
      <div class="combo-legend-title">OI Trend Signals (expanded view) — based on call &amp; put OI change vs prior snapshot + price direction</div>
      <div class="legend-item">
        <span class="combo-badge Bullish">Bullish</span>
        <span class="legend-desc"><strong>C↑ P↓ + Price↑</strong> — new money entering on the upside</span>
      </div>
      <div class="legend-item">
        <span class="combo-badge Bearish">Bearish</span>
        <span class="legend-desc"><strong>P↑ C↓ + Price↓</strong> — new money entering on the downside</span>
      </div>
      <div class="legend-item">
        <span class="combo-badge HedgedRally">Hedged Rally</span>
        <span class="legend-desc"><strong>P↑ + Price↑</strong> — stock rising but institutions buying downside protection</span>
      </div>
      <div class="legend-item">
        <span class="combo-badge ShortCovering">Short Covering</span>
        <span class="legend-desc"><strong>C↑ + Price↓</strong> — price falling but call OI rising; shorts may be exiting</span>
      </div>
      <div class="legend-item">
        <span class="combo-badge BuildUp">Build-Up</span>
        <span class="legend-desc"><strong>C↑ P↑</strong> — both sides adding; big move expected, direction unclear</span>
      </div>
      <div class="legend-item">
        <span class="combo-badge Unwinding">Unwinding</span>
        <span class="legend-desc"><strong>C↓ P↓</strong> — both sides closing; calm period or approaching expiry</span>
      </div>
    </div>
    <div class="quick-sort-bar">
      <span class="quick-sort-label">Quick sort:</span>
      <button class="quick-sort-btn" id="btn-fri-call-oi" onclick="applyQuickSort('fri_call_oi', this)">
        ⚡ Fri Call OI vs <span class="oi-label-day"></span>
      </button>
      <button class="quick-sort-btn" id="btn-fri-put-oi" onclick="applyQuickSort('fri_put_oi', this)">
        ⚡ Fri Put OI vs <span class="oi-label-day"></span>
      </button>
    </div>
    <div class="table-scroll-top" id="table-scroll-top">
      <div class="table-scroll-top-inner" id="table-scroll-top-inner"></div>
    </div>
    <div class="table-wrap" id="table-wrap">
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
const DAILY_OI_LABEL = "{daily_oi_label}";  // "yesterday", "Friday", etc.
const TOP_N = {TOP_N};

let state = {{
  period: "fri",
  signal: "all",
  search: "",
  minOI: 0,
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
  return `<span class="pct ${{cls}}">${{sign}}${{v.toFixed(2)}}% <span style="font-weight:400;font-size:9px;opacity:0.7">to strike</span></span>`;
}}
// Variant for rank rows: % and "to strike" are separate flex children so each gets its own line
function fmtDetail(v) {{
  if (v == null) return '<span class="pct na">N/A</span>';
  const cls = v > 0 ? "pos" : v < 0 ? "neg" : "";
  const sign = v > 0 ? "+" : "";
  return `<span class="pct ${{cls}}">${{sign}}${{v.toFixed(2)}}%</span><span class="rank-label">to strike</span>`;
}}
function fmtPrice(v) {{
  if (v == null) return '<span class="pct na">N/A</span>';
  return `${{v.toLocaleString("en-US", {{minimumFractionDigits:2, maximumFractionDigits:2}})}}`;
}}
function fmtOI(v) {{
  if (v == null || v === 0) return '<span class="vol-vlow">—</span>';
  const s = v.toLocaleString("en-US");
  const cls = v < 500 ? "vol-vlow" : v < 1000 ? "vol-low" : v < 5000 ? "vol-med" : v < 10000 ? "vol-high" : "vol-vhigh";
  return `<span class="${{cls}}">${{s}}</span>`;
}}
function fmtVol(v) {{
  if (v == null || v === 0) return "";
  return `<span style="color:var(--text-dim);font-size:9px"> Vol: ${{v.toLocaleString("en-US")}}</span>`;
}}
function badge(signal) {{
  if (!signal) return '<span class="badge na">N/A</span>';
  const cls = signal === "BUY" ? "buy" : signal === "SELL" ? "sell"
    : signal === "HEDGE-C" ? "hedge-c" : signal === "HEDGE-P" ? "hedge-p" : "na";
  return `<span class="badge ${{cls}}">${{signal}}</span>`;
}}
// Compact badge for rank rows inside expanded view:
// BUY/SELL are omitted (% to strike already conveys direction);
// HEDGE-C/HEDGE-P are shown smaller so they don't dominate the row.
function badgeCompact(signal) {{
  if (!signal || signal === "BUY" || signal === "SELL") return "";
  const cls   = signal === "HEDGE-C" ? "hedge-c" : signal === "HEDGE-P" ? "hedge-p" : "na";
  const label = signal === "HEDGE-C" ? "HC" : signal === "HEDGE-P" ? "HP" : signal;
  return `<span class="badge ${{cls}}" style="font-size:8px;padding:1px 4px">${{label}}</span>`;
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
  }} else if (state.sortCol === "fri_call_oi") {{
    data.sort((a, b) => {{
      const pctA = Math.abs((a.horizons?.fri?.call_oi_pct) ?? 0);
      const pctB = Math.abs((b.horizons?.fri?.call_oi_pct) ?? 0);
      return pctB - pctA;
    }});
  }} else if (state.sortCol === "fri_put_oi") {{
    data.sort((a, b) => {{
      const pctA = Math.abs((a.horizons?.fri?.put_oi_pct) ?? 0);
      const pctB = Math.abs((b.horizons?.fri?.put_oi_pct) ?? 0);
      return pctB - pctA;
    }});
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
                `OI: ${{(c.open_interest ?? 0).toLocaleString("en-US")}}`,
                `Vol: ${{(c.volume ?? 0).toLocaleString("en-US")}}`,
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
      // clear any active quick-sort button
      document.querySelectorAll(".quick-sort-btn").forEach(b => b.classList.remove("active"));
      requestAnimationFrame(render);
    }});
  }});
}}

function periodCell(ticker, period) {{
  const h = ticker.horizons[period];
  const c = getTopContract(ticker, period);
  const ew = h ? h.earnings_in_window : false;
  if (!c || !c.signal) return `<td class="period-cell">${{earningsBadge(ew, ticker.earnings_date)}}<span class="pct na">N/A</span></td>`;
  const belowVol = state.minOI > 0 && (c.open_interest == null || c.open_interest < state.minOI);
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
    // Show top 3 in rank rows; all 10 are available for the chart below
    const rankRows = contracts.slice(0, 3).map((c, i) => {{
      if (!c || !c.signal) return `
        <div class="rank-row">
          <div class="rank-num ${{rankClasses[i]}}">${{i + 1}}</div>
          <div class="rank-detail"><span class="pct na">N/A</span></div>
        </div>`;
      const dimmed = state.minOI > 0 && (c.open_interest == null || c.open_interest < state.minOI);
      return `
        <div class="rank-row${{dimmed ? " rank-row-dimmed" : ""}}">
          <div class="rank-num-col">
            <div class="rank-num ${{rankClasses[i]}}">${{i + 1}}</div>
            ${{badgeCompact(c.signal)}}
          </div>
          <div class="rank-detail">
            <span class="rank-strike">$${{c.strike ?? "—"}}</span>
            ${{fmtDetail(c.forecast_pct)}}
            ${{flipBadge(c)}}
            <span class="rank-vol">OI: ${{fmtOI(c.open_interest)}}</span>
            ${{c.volume ? `<span class="rank-vol">Vol: ${{c.volume.toLocaleString("en-US")}}</span>` : ""}}
          </div>
        </div>`;
    }}).join("");

    const safeTickerId = ticker.ticker.replace(/[^A-Za-z0-9]/g,"-");
    const chartId    = `oi-chart-${{safeTickerId}}-${{h}}`;
    const volChartId = `vol-chart-${{safeTickerId}}-${{h}}`;
    const momentumId = `mom-chart-${{safeTickerId}}-${{h}}`;

    // OI chart
    const chartHtml = contracts.length > 0 ? `
      <div class="oi-chart-wrap">
        <div class="oi-chart-label">Top OI by strike</div>
        <canvas id="${{chartId}}" style="height:125px"></canvas>
      </div>` : "";

    // Volume column — top 3 by today's volume, then volume chart
    const contractsByVol = [...contracts].sort((a, b) => (b.volume ?? 0) - (a.volume ?? 0));
    const volRankRows = contractsByVol.slice(0, 3).map((c, i) => {{
      if (!c || !c.signal) return `
        <div class="rank-row">
          <div class="rank-num ${{rankClasses[i]}}">${{i + 1}}</div>
          <div class="rank-detail"><span class="pct na">N/A</span></div>
        </div>`;
      const dimmed = state.minOI > 0 && (c.open_interest == null || c.open_interest < state.minOI);
      return `
        <div class="rank-row${{dimmed ? " rank-row-dimmed" : ""}}">
          <div class="rank-num-col">
            <div class="rank-num ${{rankClasses[i]}}">${{i + 1}}</div>
            ${{badgeCompact(c.signal)}}
          </div>
          <div class="rank-detail">
            <span class="rank-strike">$${{c.strike ?? "—"}}</span>
            ${{fmtDetail(c.forecast_pct)}}
            <span class="rank-vol">Vol: ${{fmtOI(c.volume)}}</span>
            <span class="rank-vol">OI: ${{fmtOI(c.open_interest)}}</span>
          </div>
        </div>`;
    }}).join("");
    const volChartHtml = contractsByVol.some(c => (c.volume ?? 0) > 0) ? `
      <div class="oi-chart-wrap">
        <div class="oi-chart-label">Top Volume by strike</div>
        <canvas id="${{volChartId}}" style="height:125px"></canvas>
      </div>` : "";

    // OI momentum chart — only if there is expiry history (≥ 1 data point)
    const histForExpiry = expiry ? (ticker.expiry_history?.[expiry] ?? []) : [];
    const momentumHtml = histForExpiry.length >= 1 ? `
      <div class="momentum-chart-wrap">
        <div class="momentum-chart-label">OI Momentum</div>
        <button class="momentum-expand-btn" onclick="openMomModal('${{momentumId}}','${{ticker.ticker}} · ${{HORIZON_LABELS[h]}} · OI Momentum')">⤢ Expand</button>
        <canvas id="${{momentumId}}" style="height:135px"></canvas>
      </div>` : "";

    const rightCol = momentumHtml
      ? `<div class="horizon-block-right">${{momentumHtml}}</div>`
      : "";
    const bodyContent = rightCol
      ? `<div class="horizon-block-body">
          <div class="horizon-block-left">
            <div class="col-section-label">Open Interest</div>
            ${{rankRows}}${{chartHtml}}
          </div>
          <div class="horizon-block-middle">
            <div class="col-section-label">Today's Volume</div>
            ${{volRankRows}}${{volChartHtml}}
          </div>
          ${{rightCol}}
        </div>`
      : `<div class="col-section-label">Open Interest</div>${{rankRows}}${{chartHtml}}`;

    return `<div class="horizon-block">
      <div class="horizon-block-header">
        <span>${{HORIZON_LABELS[h]}} ${{earningsBadge(earningsInWin, ticker.earnings_date)}}</span>
        <span class="expiry">${{expiry ?? "N/A"}}</span>
      </div>
      ${{bodyContent}}
    </div>`;
  }}).join("");

  // Intra-week section (Mon/Wed/Thu, only for hyper-liquid stocks)
  let intraweekHtml = "";
  const iw = ticker.intraweek || [];
  if (iw.length > 0) {{
    const iwBlocks = iw.map(entry => {{
      const rankClasses = ["r1", "r2", "r3"];
      // Top 3 rank rows only
      const rows = entry.contracts.slice(0, 3).map((c, i) => {{
        if (!c || !c.signal) return `
          <div class="rank-row">
            <div class="rank-num ${{rankClasses[i]}}">${{i + 1}}</div>
            <div class="rank-detail"><span class="pct na">N/A</span></div>
          </div>`;
        const dimmed = state.minOI > 0 && (c.open_interest == null || c.open_interest < state.minOI);
        return `
          <div class="rank-row${{dimmed ? " rank-row-dimmed" : ""}}">
            <div class="rank-num-col">
              <div class="rank-num ${{rankClasses[i]}}">${{i + 1}}</div>
              ${{badgeCompact(c.signal)}}
            </div>
            <div class="rank-detail">
              <span class="rank-strike">$${{c.strike ?? "—"}}</span>
              ${{fmtDetail(c.forecast_pct)}}
              <span class="rank-vol">OI: ${{fmtOI(c.open_interest)}}</span>
              ${{c.volume ? `<span class="rank-vol">Vol: ${{c.volume.toLocaleString("en-US")}}</span>` : ""}}
            </div>
          </div>`;
      }}).join("");
      const iwChartId = `oi-chart-${{ticker.ticker.replace(/[^A-Za-z0-9]/g,"-")}}-iw-${{entry.expiry}}`;
      const iwChartHtml = entry.contracts.length > 0 ? `
        <div class="oi-chart-wrap">
          <div class="oi-chart-label">Top OI by strike</div>
          <canvas id="${{iwChartId}}" style="height:125px"></canvas>
        </div>` : "";
      return `<div class="intraweek-block">
        <div class="intraweek-block-header">
          <span class="intraweek-day">${{entry.day}}</span>
          <span class="intraweek-expiry">${{entry.expiry}}</span>
        </div>
        ${{rows}}
        ${{iwChartHtml}}
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

  // Price + OI trend bar
  function fmtPctChange(val) {{
    if (val === null || val === undefined) return {{ html: `<span class="trend-val na">N/A</span>`, cls: "na" }};
    const cls = val > 0 ? "up" : val < 0 ? "down" : "flat";
    const arrow = val > 0 ? "▲" : val < 0 ? "▼" : "→";
    const sign = val > 0 ? "+" : "";
    return {{ html: `<span class="trend-val ${{cls}}">${{arrow}} ${{sign}}${{val.toFixed(2)}}%</span>`, cls }};
  }}
  const ph = ticker.price_history || {{}};
  const p1d = fmtPctChange(ph.price_1d_pct);
  const p5d = fmtPctChange(ph.price_5d_pct);
  function fmtOISide(trend, pct, label, windowNote) {{
    // trend: "up"/"down"/"flat"/"none"
    // Returns HTML for one side (C or P)
    if (trend === "none" || trend === null || trend === undefined) {{
      return `<span class="oi-side none">${{label}}—</span>`;
    }}
    const arrow = trend === "up" ? "↑" : trend === "down" ? "↓" : "→";
    const sign  = pct > 0 ? "+" : "";
    const pctStr = pct !== null && pct !== undefined ? `${{sign}}${{pct}}%` : "";
    const win   = windowNote ? ` (${{windowNote}})` : "";
    const title = `${{label}} OI ${{pctStr}}${{win}}`;
    return `<span class="oi-side ${{trend}}" title="${{title}}">${{label}}${{arrow}}${{pctStr}}</span>`;
  }}

  const COMBO_TOOLTIPS = {{
    "Bullish":       "Call OI ↑ + Put OI ↓ + Price ↑ — new money entering on upside",
    "Bearish":       "Put OI ↑ + Call OI ↓ + Price ↓ — new money entering on downside",
    "Hedged Rally":  "Put OI ↑ + Price ↑ — rally but institutions buying downside protection",
    "Short Covering":"Call OI ↑ + Price ↓ — price falling but shorts may be exiting",
    "Build-Up":      "Both Call & Put OI ↑ — uncertainty, big move expected either way",
    "Unwinding":     "Both Call & Put OI ↓ — positions closing, calm or near expiry",
  }};

  const OI_WINDOW_LABEL = {{ "daily": "vs yesterday", "weekly": "vs 7 days ago", "suppress": "totals only" }};

  function buildOIGroup(h) {{
    const hd = (ticker.horizons || {{}})[h] || {{}};
    const shortLabel = h === "fri" ? "Fri" : h.toUpperCase();
    const oi_window  = hd.oi_window || "daily";
    const windowNote = OI_WINDOW_LABEL[oi_window] || "";

    if (oi_window === "suppress") {{
      const tc = hd.total_call_oi;
      const tp = hd.total_put_oi;
      const fmtK = v => v >= 1000 ? (v/1000).toFixed(0)+"k" : (v || 0).toString();
      const tip = `${{shortLabel}}: Call OI ${{fmtK(tc)}} | Put OI ${{fmtK(tp)}} (${{windowNote}})`;
      return `<span class="oi-horizon-group" title="${{tip}}" style="opacity:0.5">
        <span class="oi-horizon-label">${{shortLabel}}</span>
        <span class="oi-side flat">C ${{fmtK(tc)}}</span>
        <span class="oi-side flat">P ${{fmtK(tp)}}</span>
      </span>`;
    }}

    const cTrend = hd.call_oi_trend || "none";
    const pTrend = hd.put_oi_trend  || "none";
    const cPct   = hd.call_oi_pct ?? null;
    const pPct   = hd.put_oi_pct   ?? null;
    const combo  = hd.combo_signal;

    const cHtml = fmtOISide(cTrend, cPct, "C", windowNote);
    const pH    = fmtOISide(pTrend, pPct, "P", windowNote);
    const comboCls = combo ? combo.replace(/[^a-zA-Z]/g, "") : "";
    const comboHtml = combo
      ? `<span class="combo-badge ${{comboCls}}" title="${{COMBO_TOOLTIPS[combo] || combo}} (${{windowNote}})">${{combo}}</span>`
      : "";

    return `<span class="oi-horizon-group">
      <span class="oi-horizon-label">${{shortLabel}}</span>
      ${{cHtml}} ${{pH}}${{comboHtml ? " " + comboHtml : ""}}
    </span>`;
  }}

  // Group horizons by their OI comparison window
  const dailyHorizons    = HORIZONS.filter(h => ((ticker.horizons||{{}})[h]||{{}}).oi_window === "daily");
  const weeklyHorizons   = HORIZONS.filter(h => ((ticker.horizons||{{}})[h]||{{}}).oi_window === "weekly");
  const suppressHorizons = HORIZONS.filter(h => ((ticker.horizons||{{}})[h]||{{}}).oi_window === "suppress");

  const dailyGroupsHtml   = dailyHorizons.map(buildOIGroup).join(" ");
  const weeklyGroupsHtml  = weeklyHorizons.map(buildOIGroup).join(" ");
  const suppressGroupsHtml= suppressHorizons.map(buildOIGroup).join(" ");

  const trendBarHtml = `
    <div class="trend-bar">
      <div class="trend-bar-row">
        <span class="trend-section-label">Price</span>
        <span>1D: ${{p1d.html}}</span>
        <span>5D: ${{p5d.html}}</span>
      </div>
      ${{dailyGroupsHtml ? `<div class="trend-bar-row"><span class="trend-section-label">OI vs ${{DAILY_OI_LABEL.charAt(0).toUpperCase() + DAILY_OI_LABEL.slice(1)}}</span> ${{dailyGroupsHtml}}</div>` : ""}}
      ${{weeklyGroupsHtml ? `<div class="trend-bar-row"><span class="trend-section-label">OI vs 7 Days Ago</span> ${{weeklyGroupsHtml}}</div>` : ""}}
    </div>`;

  return `${{metaHtml}}${{trendBarHtml}}<div class="detail-inner">${{h_blocks}}</div>${{intraweekHtml}}`;
}}

const expandedTickers = new Set(); // persists across renders
const oiCharts = {{}}; // ticker -> [Chart, ...]

// ── Shared helper: build a Chart.js config with a linear x-axis ─────────────
// Uses numeric strike values on the x-axis so spacing reflects real distance
// (e.g. 410→420 is twice as wide as 420→425). Also draws a vertical dashed
// line at the current stock price so ITM/OTM boundary is immediately visible.
function buildOIChartConfig(strikes, byStrike, currentPrice) {{
  // Compute a sensible bar width: ~60% of the median inter-strike gap in pixels
  // We rely on Chart.js barThickness (px); pick something readable.
  const BAR_THICKNESS = 3;

  // Vertical "current price" line via Chart.js beforeDraw plugin
  const priceLinePlugin = {{
    id: "priceLine",
    beforeDraw(chart) {{
      const xScale = chart.scales.x;
      if (!xScale || currentPrice == null) return;
      const xPx = xScale.getPixelForValue(currentPrice);
      if (xPx < xScale.left || xPx > xScale.right) return;
      const ctx = chart.ctx;
      ctx.save();
      ctx.beginPath();
      ctx.setLineDash([4, 3]);
      ctx.strokeStyle = "rgba(250,204,21,0.7)";  // amber dashed line
      ctx.lineWidth = 1.5;
      ctx.moveTo(xPx, chart.chartArea.top);
      ctx.lineTo(xPx, chart.chartArea.bottom);
      ctx.stroke();
      ctx.restore();
    }}
  }};

  return {{
    type: "bar",
    plugins: [priceLinePlugin],
    data: {{
      datasets: [
        {{
          label: "Call OI",
          data: strikes.map(s => ({{ x: s, y: byStrike[s]?.call ?? 0 }})),
          backgroundColor: "rgba(34,197,94,0.75)",
          borderColor: "rgba(34,197,94,1)",
          borderWidth: 1, borderRadius: 2,
          barThickness: BAR_THICKNESS,
          stack: "oi",
        }},
        {{
          label: "Put OI",
          data: strikes.map(s => ({{ x: s, y: byStrike[s]?.put ?? 0 }})),
          backgroundColor: "rgba(239,68,68,0.75)",
          borderColor: "rgba(239,68,68,1)",
          borderWidth: 1, borderRadius: 2,
          barThickness: BAR_THICKNESS,
          stack: "oi",
        }},
      ]
    }},
    options: {{
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{
          display: true, position: "top", align: "end",
          labels: {{ color: "#94a3b8", boxWidth: 10, font: {{ size: 9 }}, padding: 6 }},
        }},
        tooltip: {{
          enabled: false,
          external(context) {{
            const {{chart, tooltip}} = context;
            const TTID = "oi-ext-tooltip";
            let el = document.getElementById(TTID);
            if (!el) {{
              el = document.createElement("div");
              el.id = TTID;
              el.style.cssText = [
                "position:fixed","pointer-events:none","z-index:9999",
                "background:#1a1d27","border:1px solid #2e3250","border-radius:6px",
                "padding:8px 10px","font-size:11px","line-height:1.6",
                "color:#94a3b8","white-space:nowrap","transition:opacity .1s",
              ].join(";");
              document.body.appendChild(el);
            }}
            if (tooltip.opacity === 0) {{ el.style.opacity = "0"; return; }}

            const dp = tooltip.dataPoints?.[0];
            if (!dp) {{ el.style.opacity = "0"; return; }}
            const s = dp.parsed.x;
            const d = byStrike[s] ?? {{}};

            let html = `<div style="color:#e2e8f0;font-weight:600;margin-bottom:4px">Strike $${{s}}</div>`;
            if (d.call > 0)
              html += `<div><span style="color:#22c55e">● Call OI:</span> ${{d.call.toLocaleString()}}` +
                      `${{d.callVol ? ` | Vol: ${{d.callVol.toLocaleString()}}` : ""}}` +
                      `${{d.callSig ? ` | ${{d.callSig}}` : ""}}</div>`;
            if (d.put > 0)
              html += `<div><span style="color:#ef4444">● Put  OI:</span> ${{d.put.toLocaleString()}}` +
                      `${{d.putVol  ? ` | Vol: ${{d.putVol.toLocaleString()}}`  : ""}}` +
                      `${{d.putSig  ? ` | ${{d.putSig}}`  : ""}}</div>`;
            if (currentPrice != null)
              html += `<div style="margin-top:4px;color:#facc15">Current price: $${{currentPrice}}</div>`;
            el.innerHTML = html;

            // Use fixed positioning via getBoundingClientRect so overflow:hidden parents can't clip it
            const rect  = chart.canvas.getBoundingClientRect();
            const tp    = tooltip.caretX + rect.left;
            const ty    = tooltip.caretY + rect.top;
            const vw    = window.innerWidth, vh = window.innerHeight;
            el.style.opacity = "1";
            el.style.left = "";
            el.style.right = "";
            el.style.top  = "";
            el.style.bottom = "";
            // Flip horizontally if too close to right edge
            if (tp + el.offsetWidth + 12 > vw) {{
              el.style.right = (vw - tp + 8) + "px";
            }} else {{
              el.style.left  = (tp + 12) + "px";
            }}
            // Flip vertically if too close to bottom
            if (ty + el.offsetHeight + 8 > vh) {{
              el.style.bottom = (vh - ty + 4) + "px";
            }} else {{
              el.style.top = (ty - el.offsetHeight / 2) + "px";
            }}
          }},
        }},
      }},
      scales: {{
        x: {{
          type: "linear",
          stacked: true,
          offset: true,          // leave small margin on edges
          ticks: {{
            color: "#64748b",
            font: {{ size: 9 }},
            maxRotation: 40,
            callback: v => `$${{v}}`,
            // Show at most ~8 tick labels regardless of how many strikes there are
            maxTicksLimit: 8,
          }},
          grid: {{ color: "#1e2235" }},
        }},
        y: {{
          stacked: true,
          ticks: {{
            color: "#64748b", font: {{ size: 9 }},
            callback: v => v >= 1000 ? (v / 1000).toFixed(0) + "k" : v,
          }},
          grid: {{ color: "#1e2235" }},
        }},
      }},
    }},
  }};
}}
// ─────────────────────────────────────────────────────────────────────────────
// Volume bar chart — same structure as OI chart but uses today's volume data.
// byStrike[s] = {{ call: callVol, put: putVol, callOI, putOI, callSig, putSig }}
function buildVolChartConfig(strikes, byStrike, currentPrice) {{
  const BAR_THICKNESS = 3;
  const priceLinePlugin = {{
    id: "priceLineVol",
    beforeDraw(chart) {{
      const xScale = chart.scales.x;
      if (!xScale || currentPrice == null) return;
      const xPx = xScale.getPixelForValue(currentPrice);
      if (xPx < xScale.left || xPx > xScale.right) return;
      const ctx = chart.ctx;
      ctx.save();
      ctx.beginPath();
      ctx.setLineDash([4, 3]);
      ctx.strokeStyle = "rgba(250,204,21,0.7)";
      ctx.lineWidth = 1.5;
      ctx.moveTo(xPx, chart.chartArea.top);
      ctx.lineTo(xPx, chart.chartArea.bottom);
      ctx.stroke();
      ctx.restore();
    }}
  }};

  return {{
    type: "bar",
    plugins: [priceLinePlugin],
    data: {{
      datasets: [
        {{
          label: "Call Vol",
          data: strikes.map(s => ({{ x: s, y: byStrike[s]?.call ?? 0 }})),
          backgroundColor: "rgba(96,165,250,0.75)",
          borderColor: "rgba(96,165,250,1)",
          borderWidth: 1, borderRadius: 2,
          barThickness: BAR_THICKNESS,
          stack: "vol",
        }},
        {{
          label: "Put Vol",
          data: strikes.map(s => ({{ x: s, y: byStrike[s]?.put ?? 0 }})),
          backgroundColor: "rgba(251,146,60,0.75)",
          borderColor: "rgba(251,146,60,1)",
          borderWidth: 1, borderRadius: 2,
          barThickness: BAR_THICKNESS,
          stack: "vol",
        }},
      ]
    }},
    options: {{
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{
          display: true, position: "top", align: "end",
          labels: {{ color: "#94a3b8", boxWidth: 10, font: {{ size: 9 }}, padding: 6 }},
        }},
        tooltip: {{
          enabled: false,
          external(context) {{
            const {{chart, tooltip}} = context;
            const TTID = "vol-ext-tooltip";
            let el = document.getElementById(TTID);
            if (!el) {{
              el = document.createElement("div");
              el.id = TTID;
              el.style.cssText = [
                "position:fixed","pointer-events:none","z-index:9999",
                "background:#1a1d27","border:1px solid #2e3250","border-radius:6px",
                "padding:8px 10px","font-size:11px","line-height:1.6",
                "color:#94a3b8","white-space:nowrap","transition:opacity .1s",
              ].join(";");
              document.body.appendChild(el);
            }}
            if (tooltip.opacity === 0) {{ el.style.opacity = "0"; return; }}
            const dp = tooltip.dataPoints?.[0];
            if (!dp) {{ el.style.opacity = "0"; return; }}
            const s = dp.parsed.x;
            const d = byStrike[s] ?? {{}};

            let html = `<div style="color:#e2e8f0;font-weight:600;margin-bottom:4px">Strike $${{s}}</div>`;
            if (d.call > 0)
              html += `<div><span style="color:#60a5fa">● Call Vol:</span> ${{d.call.toLocaleString()}}` +
                      `${{d.callOI ? ` | OI: ${{d.callOI.toLocaleString()}}` : ""}}` +
                      `${{d.callSig ? ` | ${{d.callSig}}` : ""}}</div>`;
            if (d.put > 0)
              html += `<div><span style="color:#fb923c">● Put  Vol:</span> ${{d.put.toLocaleString()}}` +
                      `${{d.putOI  ? ` | OI: ${{d.putOI.toLocaleString()}}`  : ""}}` +
                      `${{d.putSig ? ` | ${{d.putSig}}`  : ""}}</div>`;
            if (currentPrice != null)
              html += `<div style="margin-top:4px;color:#facc15">Current price: $${{currentPrice}}</div>`;
            el.innerHTML = html;

            const rect = chart.canvas.getBoundingClientRect();
            const tp   = tooltip.caretX + rect.left;
            const ty   = tooltip.caretY + rect.top;
            const vw   = window.innerWidth, vh = window.innerHeight;
            el.style.opacity = "1";
            el.style.left = ""; el.style.right = "";
            el.style.top  = ""; el.style.bottom = "";
            if (tp + el.offsetWidth + 12 > vw) {{
              el.style.right = (vw - tp + 8) + "px";
            }} else {{
              el.style.left  = (tp + 12) + "px";
            }}
            if (ty + el.offsetHeight + 8 > vh) {{
              el.style.bottom = (vh - ty + 4) + "px";
            }} else {{
              el.style.top = (ty - el.offsetHeight / 2) + "px";
            }}
          }},
        }},
      }},
      scales: {{
        x: {{
          type: "linear",
          stacked: true,
          offset: true,
          ticks: {{
            color: "#64748b",
            font: {{ size: 9 }},
            maxRotation: 40,
            callback: v => `$${{v}}`,
            maxTicksLimit: 8,
          }},
          grid: {{ color: "#1e2235" }},
        }},
        y: {{
          stacked: true,
          ticks: {{
            color: "#64748b", font: {{ size: 9 }},
            callback: v => v >= 1000 ? (v / 1000).toFixed(0) + "k" : v,
          }},
          grid: {{ color: "#1e2235" }},
        }},
      }},
    }},
  }};
}}
// ─────────────────────────────────────────────────────────────────────────────

// ── Plugin: label at first data point of each momentum line ──────────────────
const momentumFirstLabelPlugin = {{
  id: "momFirstLabel",
  afterDraw(chart) {{
    const ctx = chart.ctx;
    ctx.save();
    chart.data.datasets.forEach((ds, di) => {{
      const meta = chart.getDatasetMeta(di);
      if (meta.hidden) return;
      // Find last non-null, non-zero point
      let lastIdx = -1;
      for (let i = ds.data.length - 1; i >= 0; i--) {{
        if (ds.data[i] != null && ds.data[i] > 0) {{ lastIdx = i; break; }}
      }}
      if (lastIdx < 0) return;
      const pt = meta.data[lastIdx];
      if (!pt) return;

      const isCall = ds.label && ds.label.endsWith(" C");
      const fontSize = Math.max(8, Math.min(10, chart.chartArea.width / 60));
      ctx.font = `bold ${{fontSize}}px monospace`;
      ctx.fillStyle = ds.borderColor;

      // Draw to the right of the last point; fall back to left if near edge
      const rightEdge = chart.chartArea.right;
      const labelWidth = ctx.measureText(ds.label).width;
      const spaceRight = rightEdge - pt.x;
      if (spaceRight >= labelWidth + 6) {{
        ctx.textAlign    = "left";
        ctx.textBaseline = "middle";
        ctx.fillText(ds.label, pt.x + 5, pt.y);
      }} else {{
        // Not enough room to the right — draw above (call) or below (put)
        ctx.textAlign = "center";
        if (isCall) {{
          ctx.textBaseline = "bottom";
          ctx.fillText(ds.label, pt.x, pt.y - 4);
        }} else {{
          ctx.textBaseline = "top";
          ctx.fillText(ds.label, pt.x, pt.y + 4);
        }}
      }}
    }});
    ctx.restore();
  }}
}};
// ─────────────────────────────────────────────────────────────────────────────

// ── OI Momentum line chart config ────────────────────────────────────────────
// Shows how Open Interest for each strike evolves day-by-day over the tracked
// window (up to 7 days).  Calls are green shades, puts are red shades.
// A fast-growing strike mid-week (a "rising star") will show a steep upward line.
function buildMomentumChartConfig(historyArr) {{
  // historyArr: [{{date:"2026-03-10", strikes:{{"420.0":{{call:x,put:y}}, ...}}}}, ...]
  if (!historyArr || historyArr.length === 0) return null;

  // Normalize strike keys: Python serialises floats as "220.0" but JS
  // parseFloat("220.0").toString() === "220" (drops the trailing .0).
  // Standardise everything to JS float format so lookups always match.
  const normHist = historyArr.map(e => ({{
    date: e.date,
    strikes: Object.fromEntries(
      Object.entries(e.strikes ?? {{}}).map(([k, v]) => [parseFloat(k).toString(), v])
    ),
  }}));

  const dates = normHist.map(e => e.date);

  // Gather all strikes that appear in ANY day, rank by peak OI across all history.
  // This ensures a strike that was huge earlier (then unwound) still appears on the
  // chart — its disappearance is itself a meaningful signal.
  const peakOI = {{}};  // strike → {{ peak, latestOI }}
  normHist.forEach(e => {{
    Object.entries(e.strikes ?? {{}}).forEach(([k, d]) => {{
      const total = (d.call ?? 0) + (d.put ?? 0);
      if (!peakOI[k]) peakOI[k] = {{ peak: 0, latestOI: 0 }};
      if (total > peakOI[k].peak) peakOI[k].peak = total;
    }});
  }});
  // Also record each strike's latest-day OI so today's big ones rank first on ties
  const latestStrikes = normHist[normHist.length - 1].strikes ?? {{}};
  Object.entries(latestStrikes).forEach(([k, d]) => {{
    if (peakOI[k]) peakOI[k].latestOI = (d.call ?? 0) + (d.put ?? 0);
  }});
  const ranked = Object.entries(peakOI)
    .filter(([, v]) => v.peak > 0)
    // Sort by peak OI (across all history days) so a strike that was huge earlier
    // but unwound still ranks high and appears on the chart, even if today it is 0.
    .sort(([, a], [, b]) => b.peak - a.peak)
    .slice(0, 8)
    .map(([s]) => {{
      const latest = latestStrikes[s] ?? {{}};
      return {{ strike: parseFloat(s), oi: (latest.call ?? 0) + (latest.put ?? 0),
               call: latest.call ?? 0, put: latest.put ?? 0 }};
    }});

  if (ranked.length === 0) return null;

  // Colour palettes: 8 greens for calls, 8 reds for puts
  const callColors = ["#16a34a","#22c55e","#4ade80","#86efac","#6ee7b7","#34d399","#10b981","#059669"];
  const putColors  = ["#dc2626","#ef4444","#f87171","#fca5a5","#fb923c","#f97316","#ea580c","#c2410c"];

  const datasets = [];
  ranked.forEach((item, idx) => {{
    const sKey = item.strike.toString();  // already normalised via parseFloat above
    // Call line
    const callData = dates.map(date => {{
      const snap = normHist.find(e => e.date === date);
      const val  = snap?.strikes?.[sKey]?.call ?? null;
      return val && val > 0 ? val : null;
    }});
    // Put line
    const putData = dates.map(date => {{
      const snap = normHist.find(e => e.date === date);
      const val  = snap?.strikes?.[sKey]?.put ?? null;
      return val && val > 0 ? val : null;
    }});

    const hasCallData = callData.some(v => v != null && v > 0);
    const hasPutData  = putData.some(v => v != null && v > 0);

    if (hasCallData) {{
      datasets.push({{
        label: `$${{item.strike}} C`,
        data: callData,
        borderColor: callColors[idx % callColors.length],
        backgroundColor: "transparent",
        borderWidth: 1.5,
        pointRadius: 3,
        pointHoverRadius: 3,
        tension: 0.25,
        spanGaps: false,
      }});
    }}
    if (hasPutData) {{
      datasets.push({{
        label: `$${{item.strike}} P`,
        data: putData,
        borderColor: putColors[idx % putColors.length],
        backgroundColor: "transparent",
        borderWidth: 1.5,
        borderDash: [4, 3],
        pointRadius: 3,
        pointHoverRadius: 3,
        tension: 0.25,
        spanGaps: false,
      }});
    }}
  }});

  if (datasets.length === 0) return null;

  // Friendly date labels (e.g. "Mon 3/10")
  const dayNames = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
  const shortDates = dates.map(d => {{
    const dt = new Date(d + "T12:00:00");
    return `${{dayNames[dt.getDay()]}} ${{dt.getMonth()+1}}/${{dt.getDate()}}`;
  }});

  const crosshairPlugin = {{
    id: "momCrosshair",
    afterDraw(chart) {{
      const {{ ctx, tooltip, chartArea: {{ top, bottom }} }} = chart;
      if (!tooltip || !tooltip._active || !tooltip._active.length) return;
      const x = tooltip._active[0].element.x;
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(x, top);
      ctx.lineTo(x, bottom);
      ctx.lineWidth = 1;
      ctx.strokeStyle = "rgba(148,163,184,0.3)";
      ctx.setLineDash([3, 3]);
      ctx.stroke();
      ctx.restore();
    }},
  }};

  return {{
    type: "line",
    plugins: [momentumFirstLabelPlugin, crosshairPlugin],
    data: {{ labels: shortDates, datasets }},
    options: {{
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          enabled: false,
          mode: "index",
          intersect: false,
          filter: item => item.parsed.y != null && !isNaN(item.parsed.y) && item.parsed.y > 0,
          external(context) {{
            const {{ chart, tooltip }} = context;
            const wrap = chart.canvas.parentNode;
            let el = wrap.querySelector(".mom-tooltip");
            if (!el) {{
              el = document.createElement("div");
              el.className = "mom-tooltip";
              wrap.appendChild(el);
            }}
            if (tooltip.opacity === 0 || !tooltip.dataPoints?.length) {{
              el.style.opacity = "0";
              return;
            }}
            // Index into normHist for current and previous day
            const dataIdx = tooltip.dataPoints[0].dataIndex;
            const prevSnap = dataIdx > 0 ? (normHist[dataIdx - 1]?.strikes ?? {{}}) : null;

            // Group datapoints by strike, separate call vs put
            const byStrike = {{}};
            tooltip.dataPoints.forEach(item => {{
              const m = (item.dataset.label || "").match(/\$?([\d.]+)\s+(C|P)$/);
              if (!m) return;
              const [, strike, type] = m;
              if (!byStrike[strike]) byStrike[strike] = {{ call: 0, put: 0 }};
              const v = item.parsed.y;
              if (v > 0) (type === "C" ? byStrike[strike].call = v : byStrike[strike].put = v);
            }});
            const sorted = Object.entries(byStrike)
              .map(([s, d]) => ({{ strike: s, call: d.call, put: d.put, total: d.call + d.put }}))
              .filter(x => x.total > 0)
              .sort((a, b) => b.total - a.total);
            if (!sorted.length) {{ el.style.opacity = "0"; return; }}

            const maxTotal = sorted[0].total;
            const fmtAbs = v => (Math.abs(v)/1000).toFixed(1)+"k";
            const fmtDelta = v => (v >= 0 ? "+" : "-") + fmtAbs(v);
            const date = tooltip.title?.[0] ?? "";

            let html = `<div class="mom-tt-date">${{date}}</div>`;
            sorted.forEach(({{ strike, call, put, total }}) => {{
              const cw = maxTotal > 0 ? Math.round(call / maxTotal * 100) : 0;
              const pw = maxTotal > 0 ? Math.round(put  / maxTotal * 100) : 0;

              // Delta vs previous day
              let deltaHtml = "";
              if (prevSnap) {{
                const prev = prevSnap[strike] ?? {{ call: 0, put: 0 }};
                const dC = call - (prev.call ?? 0);
                const dP = put  - (prev.put  ?? 0);
                if (dC !== 0 || dP !== 0) {{
                  const cStr = dC !== 0 ? `<span style="color:${{dC>0?"#4ade80":"#f87171"}}">${{fmtDelta(dC)}}C</span>` : "";
                  const pStr = dP !== 0 ? `<span style="color:${{dP>0?"#4ade80":"#f87171"}}">${{fmtDelta(dP)}}P</span>` : "";
                  deltaHtml = `<div class="mom-tt-delta">${{cStr}}${{pStr}}</div>`;
                }}
              }}

              html += `<div class="mom-tt-row">
                <div class="mom-tt-strike">$${{strike}}</div>
                <div class="mom-tt-bars">
                  <div class="mom-tt-bar-row">
                    <div class="mom-tt-call" style="width:${{cw}}%"></div>
                    <div class="mom-tt-put"  style="width:${{pw}}%"></div>
                  </div>
                </div>
                <div class="mom-tt-right">
                  <div class="mom-tt-total">${{fmtAbs(total)}}</div>
                  ${{deltaHtml}}
                </div>
              </div>`;
            }});
            html += `<div class="mom-tt-legend">
              <span><i style="background:#22c55e"></i>Calls</span>
              <span><i style="background:#ef4444"></i>Puts</span>
            </div>`;
            el.innerHTML = html;
            el.style.opacity = "1";
            // Fixed positioning so overflow:hidden parents don't clip
            const rect = chart.canvas.getBoundingClientRect();
            const ttW = 210;
            let left = rect.left + tooltip.caretX + 14;
            if (left + ttW > window.innerWidth - 8) left = rect.left + tooltip.caretX - ttW - 14;
            const top = Math.max(rect.top + 4, rect.top + tooltip.caretY - 40);
            el.style.left = Math.max(4, left) + "px";
            el.style.top  = top + "px";
          }},
        }},
      }},
      scales: {{
        x: {{
          ticks: {{ color: "#64748b", font: {{ size: 9 }}, maxRotation: 30 }},
          grid: {{ color: "#1e2235" }},
        }},
        y: {{
          ticks: {{
            color: "#64748b",
            font: {{ size: 9 }},
            callback: v => v >= 1000 ? (v/1000).toFixed(0)+"k" : v,
          }},
          grid: {{ color: "#1e2235" }},
        }},
      }},
    }},
  }};
}}
// ─────────────────────────────────────────────────────────────────────────────

function initOICharts(tickerStr, tickerData) {{
  // Destroy any previous instances for this ticker
  if (oiCharts[tickerStr]) {{
    oiCharts[tickerStr].forEach(c => {{ try {{ c.destroy(); }} catch(e) {{}} }});
  }}
  oiCharts[tickerStr] = [];

  const currentPrice = tickerData.price ?? null;

  HORIZONS.forEach(h => {{
    const safeId = tickerStr.replace(/[^A-Za-z0-9]/g, "-");
    const canvas = document.getElementById(`oi-chart-${{safeId}}-${{h}}`);
    if (!canvas) return;

    const hData = tickerData.horizons?.[h];
    const contracts = (hData?.contracts ?? []).filter(c => c && (c.open_interest ?? 0) > 0);
    if (contracts.length === 0) return;

    // Pick top 10 by OI, then group by strike for stacked call/put view
    const top10 = [...contracts].sort((a, b) => b.open_interest - a.open_interest).slice(0, 10);
    const strikes = [...new Set(top10.map(c => c.strike))].sort((a, b) => a - b);

    // Build a map: strike -> {{call: oi, put: oi, callVol, putVol}}
    const byStrike = {{}};
    top10.forEach(c => {{
      const k = c.strike;
      if (!byStrike[k]) byStrike[k] = {{ call: 0, put: 0, callVol: 0, putVol: 0, callSig: null, putSig: null }};
      if (c.type === "Call") {{
        byStrike[k].call    = c.open_interest ?? 0;
        byStrike[k].callVol = c.volume ?? 0;
        byStrike[k].callSig = c.signal;
      }} else {{
        byStrike[k].put    = c.open_interest ?? 0;
        byStrike[k].putVol = c.volume ?? 0;
        byStrike[k].putSig = c.signal;
      }}
    }});

    const chart = new Chart(canvas.getContext("2d"), buildOIChartConfig(strikes, byStrike, currentPrice));
    oiCharts[tickerStr].push(chart);
    canvas.addEventListener("mouseleave", () => {{
      const el = document.getElementById("oi-ext-tooltip");
      if (el) el.style.opacity = "0";
    }});

    // Volume chart for this horizon
    const volCanvas = document.getElementById(`vol-chart-${{safeId}}-${{h}}`);
    if (volCanvas) {{
      const allContracts = hData?.contracts ?? [];
      const top10Vol = [...allContracts].filter(c => (c.volume ?? 0) > 0)
        .sort((a, b) => (b.volume ?? 0) - (a.volume ?? 0)).slice(0, 10);
      if (top10Vol.length > 0) {{
        const volStrikes = [...new Set(top10Vol.map(c => c.strike))].sort((a, b) => a - b);
        const byStrikeVol = {{}};
        top10Vol.forEach(c => {{
          const k = c.strike;
          if (!byStrikeVol[k]) byStrikeVol[k] = {{ call: 0, put: 0, callOI: 0, putOI: 0, callSig: null, putSig: null }};
          if (c.type === "Call") {{
            byStrikeVol[k].call   = c.volume ?? 0;
            byStrikeVol[k].callOI = c.open_interest ?? 0;
            byStrikeVol[k].callSig = c.signal;
          }} else {{
            byStrikeVol[k].put    = c.volume ?? 0;
            byStrikeVol[k].putOI  = c.open_interest ?? 0;
            byStrikeVol[k].putSig = c.signal;
          }}
        }});
        const volChart = new Chart(volCanvas.getContext("2d"), buildVolChartConfig(volStrikes, byStrikeVol, currentPrice));
        oiCharts[tickerStr].push(volChart);
        volCanvas.addEventListener("mouseleave", () => {{
          const el = document.getElementById("vol-ext-tooltip");
          if (el) el.style.opacity = "0";
        }});
      }}
    }}
  }});

  // OI Momentum line charts (one per horizon)
  HORIZONS.forEach(h => {{
    const safeId   = tickerStr.replace(/[^A-Za-z0-9]/g, "-");
    const canvas   = document.getElementById(`mom-chart-${{safeId}}-${{h}}`);
    if (!canvas) return;
    const expiry   = tickerData.horizons?.[h]?.expiry;
    if (!expiry) return;
    const histArr  = tickerData.expiry_history?.[expiry] ?? [];
    if (histArr.length === 0) return;
    const cfg = buildMomentumChartConfig(histArr);
    if (!cfg) return;
    canvas._momHistData = histArr;   // store for modal rebuild
    const chart = new Chart(canvas.getContext("2d"), cfg);
    oiCharts[tickerStr].push(chart);
  }});

  // Intra-week charts (same logic, keyed by expiry date)
  const iwEntries = tickerData.intraweek ?? [];
  iwEntries.forEach(entry => {{
    const safeId  = tickerStr.replace(/[^A-Za-z0-9]/g, "-");
    const canvas  = document.getElementById(`oi-chart-${{safeId}}-iw-${{entry.expiry}}`);
    if (!canvas) return;

    const contracts = (entry.contracts ?? []).filter(c => c && (c.open_interest ?? 0) > 0);
    if (contracts.length === 0) return;

    const top10  = [...contracts].sort((a, b) => b.open_interest - a.open_interest).slice(0, 10);
    const strikes = [...new Set(top10.map(c => c.strike))].sort((a, b) => a - b);
    const byStrike = {{}};
    top10.forEach(c => {{
      const k = c.strike;
      if (!byStrike[k]) byStrike[k] = {{ call:0, put:0, callVol:0, putVol:0, callSig:null, putSig:null }};
      if (c.type === "Call") {{ byStrike[k].call=c.open_interest??0; byStrike[k].callVol=c.volume??0; byStrike[k].callSig=c.signal; }}
      else                   {{ byStrike[k].put =c.open_interest??0; byStrike[k].putVol =c.volume??0; byStrike[k].putSig =c.signal; }}
    }});

    const chart = new Chart(canvas.getContext("2d"), buildOIChartConfig(strikes, byStrike, currentPrice));
    oiCharts[tickerStr].push(chart);
    canvas.addEventListener("mouseleave", () => {{
      const el = document.getElementById("oi-ext-tooltip");
      if (el) el.style.opacity = "0";
    }});
  }});
}}

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
    if (cell) {{
      cell.innerHTML = buildDetailCellContent(t);
      requestAnimationFrame(() => initOICharts(ticker, t));
    }}
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
      const t = RAW.tickers.find(d => d.ticker === ticker);
      if (t) {{
        cell.innerHTML = buildDetailCellContent(t);
        requestAnimationFrame(() => initOICharts(ticker, t));
      }}
    }}
  }} else {{
    expandedTickers.delete(ticker);
    if (oiCharts[ticker]) {{
      oiCharts[ticker].forEach(c => {{ try {{ c.destroy(); }} catch(e) {{}} }});
      delete oiCharts[ticker];
    }}
    // Clear the cell so re-expanding always does a full rebuild.
    // Without this, the canvas elements remain in the DOM but have no Chart.js
    // instance attached, leaving blank charts on the next expand.
    const cell = detailRow.querySelector("td");
    if (cell) cell.innerHTML = "";
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

document.getElementById("oi-pills").addEventListener("click", e => {{
  const btn = e.target.closest("[data-minoi]");
  if (!btn) return;
  document.querySelectorAll("[data-minoi]").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  state.minOI = parseInt(btn.dataset.minoi, 10);
  // Re-render any open detail rows so dimming updates immediately
  expandedTickers.forEach(ticker => {{
    const t = RAW.tickers.find(d => d.ticker === ticker);
    const cell = document.querySelector(`#detail-${{ticker}} td`);
    if (t && cell) {{
      cell.innerHTML = buildDetailCellContent(t);
      requestAnimationFrame(() => initOICharts(ticker, t));
    }}
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

// ---- Momentum modal ----
let _momModalChart = null;

function openMomModal(sourceCanvasId, title) {{
  const sourceCanvas = document.getElementById(sourceCanvasId);
  if (!sourceCanvas) return;

  // Use the history data stored on the canvas to rebuild the config fresh.
  // JSON.parse/stringify would strip all functions (external tooltip, plugins etc.)
  const histArr = sourceCanvas._momHistData;
  if (!histArr || !histArr.length) return;

  document.getElementById("mom-modal-title").textContent = title || "OI Momentum";

  if (_momModalChart) {{ try {{ _momModalChart.destroy(); }} catch(e) {{}} _momModalChart = null; }}

  const modalCfg = buildMomentumChartConfig(histArr);
  if (!modalCfg) return;

  // Larger font sizes for the full-screen view
  try {{
    modalCfg.options.scales.x.ticks.font.size = 11;
    modalCfg.options.scales.x.ticks.maxRotation = 0;
    modalCfg.options.scales.y.ticks.font.size = 11;
  }} catch(e) {{}}

  const modalCanvas = document.getElementById("mom-modal-canvas");
  _momModalChart = new Chart(modalCanvas.getContext("2d"), modalCfg);

  const modal = document.getElementById("mom-modal");
  modal.classList.add("open");
  document.body.style.overflow = "hidden";
}}

function closeMomModal() {{
  document.getElementById("mom-modal").classList.remove("open");
  document.body.style.overflow = "";
  if (_momModalChart) {{ try {{ _momModalChart.destroy(); }} catch(e) {{}} _momModalChart = null; }}
}}

// Close on backdrop click or Escape key
document.getElementById("mom-modal").addEventListener("click", e => {{
  if (e.target === document.getElementById("mom-modal")) closeMomModal();
}});
document.addEventListener("keydown", e => {{
  if (e.key === "Escape") closeMomModal();
}});

// ---- Quick sort ----
function applyQuickSort(col, btn) {{
  const allBtns = document.querySelectorAll(".quick-sort-btn");
  if (state.sortCol === col) {{
    // toggle off — back to default
    state.sortCol = null;
    allBtns.forEach(b => b.classList.remove("active"));
  }} else {{
    state.sortCol = col;
    allBtns.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
  }}
  render();
}}

// ---- Top scrollbar mirror ----
(function() {{
  const top  = document.getElementById("table-scroll-top");
  const wrap = document.getElementById("table-wrap");
  const inner = document.getElementById("table-scroll-top-inner");

  function syncInnerWidth() {{
    const tableEl = document.getElementById("main-table");
    if (tableEl) inner.style.width = tableEl.offsetWidth + "px";
  }}

  let syncingFromTop = false, syncingFromWrap = false;
  top.addEventListener("scroll", () => {{
    if (syncingFromWrap) return;
    syncingFromTop = true;
    wrap.scrollLeft = top.scrollLeft;
    syncingFromTop = false;
  }});
  wrap.addEventListener("scroll", () => {{
    if (syncingFromTop) return;
    syncingFromWrap = true;
    top.scrollLeft = wrap.scrollLeft;
    syncingFromWrap = false;
  }});

  // Update inner width whenever the table re-renders
  const observer = new MutationObserver(syncInnerWidth);
  observer.observe(document.getElementById("table-body"), {{ childList: true, subtree: false }});
  syncInnerWidth();
}})();

// ---- Init ----
// Populate dynamic day label in quick-sort buttons
document.querySelectorAll(".oi-label-day").forEach(el => {{
  el.textContent = DAILY_OI_LABEL.charAt(0).toUpperCase() + DAILY_OI_LABEL.slice(1);
}});
initPillDates();
render();

</script>
</body>
</html>
"""

    output_path.write_text(html, encoding="utf-8")
    print(f"HTML viewer:  {output_path.resolve()}")
