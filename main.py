"""
Options Volume Signal — Main Entry Point

Fetches options data for S&P 500 IT + Nasdaq-100 stocks, identifies the top-3
highest-volume contracts per expiry horizon (1d/3d/7d/14d/30d), computes
buy/sell signals and forecasted % moves, and exports a color-coded Excel file.

Usage:
    python main.py
    python main.py --tickers AAPL MSFT NVDA   # test with a subset
    python main.py --output my_report.xlsx
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side, numbers
)
from openpyxl.utils import get_column_letter

from universe import get_universe
from fetcher import fetch_all
from analyzer import analyze_all, HORIZONS, TOP_N
from exporter_html import write_html

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
GREEN_FILL   = PatternFill("solid", fgColor="C6EFCE")
RED_FILL     = PatternFill("solid", fgColor="FFC7CE")
YELLOW_FILL  = PatternFill("solid", fgColor="FFEB9C")
BLUE_FILL    = PatternFill("solid", fgColor="BDD7EE")
GREY_FILL    = PatternFill("solid", fgColor="D9D9D9")
HEADER_FILL  = PatternFill("solid", fgColor="1F4E79")
SUBHDR_FILL  = PatternFill("solid", fgColor="2E75B6")
RANK_FILLS   = [
    PatternFill("solid", fgColor="DDEBF7"),
    PatternFill("solid", fgColor="EBF3FB"),
    PatternFill("solid", fgColor="F5F9FE"),
]

WHITE_FONT   = Font(color="FFFFFF", bold=True)
BOLD_FONT    = Font(bold=True)
CENTER       = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT         = Alignment(horizontal="left", vertical="center")

THIN = Side(style="thin", color="BFBFBF")
THIN_BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

HORIZONS_ORDER = list(HORIZONS.keys())  # ["1d","3d","7d","14d","30d"]


# ---------------------------------------------------------------------------
# Build flat rows for Detail sheet
# ---------------------------------------------------------------------------
def build_detail_rows(analyzed: list[dict]) -> list[dict]:
    rows = []
    for item in analyzed:
        ticker = item["ticker"]
        price  = item["price"]
        for horizon in HORIZONS_ORDER:
            h_data = item["horizons"].get(horizon, {})
            expiry = h_data.get("expiry")
            contracts = h_data.get("contracts", [])
            for rank, contract in enumerate(contracts, 1):
                rows.append({
                    "Ticker":       ticker,
                    "Current Price": price,
                    "Horizon":      horizon,
                    "Rank":         rank,
                    "Expiry Date":  expiry or "N/A",
                    "Strike":       contract.get("strike"),
                    "Type":         contract.get("type"),
                    "Volume":       contract.get("volume"),
                    "Signal":       contract.get("signal"),
                    "Forecast %":   contract.get("forecast_pct"),
                })
    return rows


# ---------------------------------------------------------------------------
# Write Detail sheet (long format)
# ---------------------------------------------------------------------------
def write_detail_sheet(ws, rows: list[dict]):
    headers = ["Ticker", "Current Price", "Horizon", "Rank",
               "Expiry Date", "Strike", "Type", "Volume", "Signal", "Forecast %"]

    # Header row
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = HEADER_FILL
        cell.font = WHITE_FONT
        cell.alignment = CENTER
        cell.border = THIN_BORDER

    ws.row_dimensions[1].height = 30

    for r, row in enumerate(rows, 2):
        values = [
            row["Ticker"], row["Current Price"], row["Horizon"], row["Rank"],
            row["Expiry Date"], row["Strike"], row["Type"], row["Volume"],
            row["Signal"], row["Forecast %"],
        ]
        for c, val in enumerate(values, 1):
            cell = ws.cell(row=r, column=c, value=val)
            cell.alignment = CENTER
            cell.border = THIN_BORDER

            col_name = headers[c - 1]
            if col_name == "Signal":
                if val == "BUY":
                    cell.fill = GREEN_FILL
                    cell.font = Font(color="375623", bold=True)
                elif val == "SELL":
                    cell.fill = RED_FILL
                    cell.font = Font(color="9C0006", bold=True)
            elif col_name == "Forecast %":
                if val is not None:
                    cell.number_format = '0.00"%"'
                    if val > 0:
                        cell.fill = GREEN_FILL
                    elif val < 0:
                        cell.fill = RED_FILL
                    else:
                        cell.fill = YELLOW_FILL
            elif col_name == "Current Price" and val is not None:
                cell.number_format = '"$"#,##0.00'
            elif col_name == "Strike" and val is not None:
                cell.number_format = '"$"#,##0.00'
            elif col_name == "Volume" and val is not None:
                cell.number_format = '#,##0'
            elif col_name == "Rank":
                fills = [GREEN_FILL, YELLOW_FILL, PatternFill("solid", fgColor="FCE4D6")]
                cell.fill = fills[int(val) - 1] if val and 1 <= int(val) <= 3 else GREY_FILL

    # Column widths
    widths = [10, 13, 8, 6, 12, 10, 8, 10, 8, 11]
    for col, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(col)].width = w

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions


# ---------------------------------------------------------------------------
# Write Summary sheet (wide format)
# ---------------------------------------------------------------------------
def write_summary_sheet(ws, analyzed: list[dict]):
    """
    Layout:
    Row 1: main headers (Ticker, Current Price, then horizon group headers spanning 3*(TOP_N) cols each)
    Row 2: sub-headers (for each horizon: Vol#1 Strike, Vol#1 Type, ... Vol#3 Forecast%)
    Row 3+: data
    """
    # Build column structure
    # Fixed cols: Ticker (1), Current Price (2)
    # Per horizon: TOP_N ranks × 5 fields = 15 cols per horizon
    FIELDS = ["Strike", "Type", "Volume", "Signal", "Forecast %"]
    N_FIELDS = len(FIELDS)

    fixed_cols = 2
    cols_per_horizon = TOP_N * N_FIELDS

    # Row 1: top-level headers
    ws.cell(row=1, column=1, value="Ticker").fill = HEADER_FILL
    ws.cell(row=1, column=1).font = WHITE_FONT
    ws.cell(row=1, column=1).alignment = CENTER
    ws.cell(row=1, column=1).border = THIN_BORDER

    ws.cell(row=1, column=2, value="Current Price").fill = HEADER_FILL
    ws.cell(row=1, column=2).font = WHITE_FONT
    ws.cell(row=1, column=2).alignment = CENTER
    ws.cell(row=1, column=2).border = THIN_BORDER

    # Merge Row 1 cells: Ticker spans rows 1-2, Current Price spans rows 1-2
    ws.merge_cells(start_row=1, start_column=1, end_row=2, end_column=1)
    ws.merge_cells(start_row=1, start_column=2, end_row=2, end_column=2)

    horizon_label_map = {
        "1d":  "1 Day",
        "3d":  "3 Days",
        "7d":  "7 Days",
        "14d": "2 Weeks",
        "30d": "1 Month",
    }

    for h_idx, horizon in enumerate(HORIZONS_ORDER):
        start_col = fixed_cols + 1 + h_idx * cols_per_horizon
        end_col   = start_col + cols_per_horizon - 1

        # Row 1: horizon group label
        cell = ws.cell(row=1, column=start_col,
                       value=f"{horizon_label_map[horizon]}  ({horizon})")
        cell.fill = SUBHDR_FILL
        cell.font = WHITE_FONT
        cell.alignment = CENTER
        cell.border = THIN_BORDER
        ws.merge_cells(start_row=1, start_column=start_col,
                       end_row=1, end_column=end_col)

        # Row 2: rank sub-headers
        for rank in range(1, TOP_N + 1):
            for f_idx, field in enumerate(FIELDS):
                col = start_col + (rank - 1) * N_FIELDS + f_idx
                label = f"#{rank} {field}"
                cell = ws.cell(row=2, column=col, value=label)
                cell.fill = RANK_FILLS[rank - 1]
                cell.font = BOLD_FONT
                cell.alignment = CENTER
                cell.border = THIN_BORDER

    ws.row_dimensions[1].height = 28
    ws.row_dimensions[2].height = 36

    # Data rows
    for r_idx, item in enumerate(analyzed):
        row = r_idx + 3
        ticker = item["ticker"]
        price  = item["price"]

        cell = ws.cell(row=row, column=1, value=ticker)
        cell.font = BOLD_FONT
        cell.alignment = CENTER
        cell.border = THIN_BORDER

        price_cell = ws.cell(row=row, column=2, value=price)
        price_cell.alignment = CENTER
        price_cell.border = THIN_BORDER
        if price is not None:
            price_cell.number_format = '"$"#,##0.00'

        for h_idx, horizon in enumerate(HORIZONS_ORDER):
            h_data    = item["horizons"].get(horizon, {})
            contracts = h_data.get("contracts", [])
            start_col = fixed_cols + 1 + h_idx * cols_per_horizon

            for rank_idx, contract in enumerate(contracts):
                base_col = start_col + rank_idx * N_FIELDS
                strike   = contract.get("strike")
                opt_type = contract.get("type")
                volume   = contract.get("volume")
                signal   = contract.get("signal")
                forecast = contract.get("forecast_pct")
                rank_fill = RANK_FILLS[rank_idx]

                # Strike
                c = ws.cell(row=row, column=base_col, value=strike)
                c.fill = rank_fill; c.alignment = CENTER; c.border = THIN_BORDER
                if strike is not None:
                    c.number_format = '"$"#,##0.00'

                # Type
                c = ws.cell(row=row, column=base_col + 1, value=opt_type)
                c.fill = rank_fill; c.alignment = CENTER; c.border = THIN_BORDER

                # Volume
                c = ws.cell(row=row, column=base_col + 2, value=volume)
                c.fill = rank_fill; c.alignment = CENTER; c.border = THIN_BORDER
                if volume is not None:
                    c.number_format = '#,##0'

                # Signal
                c = ws.cell(row=row, column=base_col + 3, value=signal)
                c.alignment = CENTER; c.border = THIN_BORDER
                if signal == "BUY":
                    c.fill = GREEN_FILL
                    c.font = Font(color="375623", bold=True)
                elif signal == "SELL":
                    c.fill = RED_FILL
                    c.font = Font(color="9C0006", bold=True)
                else:
                    c.fill = GREY_FILL

                # Forecast %
                c = ws.cell(row=row, column=base_col + 4, value=forecast)
                c.alignment = CENTER; c.border = THIN_BORDER
                if forecast is not None:
                    c.number_format = '0.00"%"'
                    if forecast > 0:
                        c.fill = GREEN_FILL
                        c.font = Font(color="375623")
                    elif forecast < 0:
                        c.fill = RED_FILL
                        c.font = Font(color="9C0006")
                    else:
                        c.fill = YELLOW_FILL
                else:
                    c.fill = GREY_FILL

    # Column widths
    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 14
    col_widths = [10, 7, 9, 8, 10]  # Strike, Type, Volume, Signal, Forecast%
    for h_idx in range(len(HORIZONS_ORDER)):
        for rank in range(TOP_N):
            for f_idx, w in enumerate(col_widths):
                col = fixed_cols + 1 + h_idx * cols_per_horizon + rank * N_FIELDS + f_idx
                ws.column_dimensions[get_column_letter(col)].width = w

    ws.freeze_panes = "C3"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Options Volume Signal Report")
    parser.add_argument(
        "--tickers", nargs="+", default=None,
        help="Optional subset of tickers to test with (e.g. AAPL MSFT NVDA)"
    )
    parser.add_argument(
        "--output", default=None,
        help="Output Excel filename (default: options_signals_YYYYMMDD_HHMM.xlsx)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    tickers = args.tickers if args.tickers else get_universe()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = Path(args.output) if args.output else Path(f"options_signals_{timestamp}.xlsx")

    print(f"Options Volume Signal Report")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Tickers: {len(tickers)}")
    print(f"Output:  {output_path}\n")

    # Step 1: Fetch
    print("--- Fetching data ---")
    fetch_results = fetch_all(tickers)

    # Step 2: Analyze
    print("\n--- Analyzing ---")
    analyzed = analyze_all(fetch_results)

    # Step 3: Build detail rows
    detail_rows = build_detail_rows(analyzed)
    print(f"Detail rows: {len(detail_rows)}")

    # Step 4: Write Excel
    print(f"\n--- Writing Excel: {output_path} ---")
    wb = Workbook()

    # Summary sheet
    ws_summary = wb.active
    ws_summary.title = "Summary"
    write_summary_sheet(ws_summary, analyzed)

    # Detail sheet
    ws_detail = wb.create_sheet("Detail")
    write_detail_sheet(ws_detail, detail_rows)

    wb.save(output_path)
    print(f"Excel report: {output_path.resolve()}")

    html_path = output_path.with_suffix(".html")
    write_html(analyzed, html_path, timestamp)
    print(f"\nDone! Open the HTML file in your browser to explore interactively.")

    # Quick stats
    total_buy  = sum(1 for r in detail_rows if r["Signal"] == "BUY")
    total_sell = sum(1 for r in detail_rows if r["Signal"] == "SELL")
    total_na   = sum(1 for r in detail_rows if r["Signal"] is None)
    print(f"\nSignal breakdown across all tickers/horizons/ranks:")
    print(f"  BUY:  {total_buy}")
    print(f"  SELL: {total_sell}")
    print(f"  N/A:  {total_na}")


if __name__ == "__main__":
    main()
