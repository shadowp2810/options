"""
Fetches options chain data (with accurate Open Interest) from NASDAQ's
public API — the same endpoint that powers nasdaq.com.

No API key required. Free forever. One call per ticker returns the
complete chain across ALL expiry dates.

Returns data in the same format as yfinance's get_options_chain() so the
rest of the pipeline is unchanged.
"""

import time
import requests
import pandas as pd
from datetime import datetime
from typing import Optional


_SESSION: Optional[requests.Session] = None

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nasdaq.com/",
    "Origin": "https://www.nasdaq.com",
}


def _get_session() -> requests.Session:
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
        _SESSION.headers.update(_HEADERS)
    return _SESSION


def _parse_num(value) -> float:
    """Convert NASDAQ string values ('1,234' / '--' / None) to float."""
    if value is None or value == "--":
        return 0.0
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


def _parse_expiry(label: str) -> Optional[str]:
    """Convert 'March 13, 2026' -> '2026-03-13'. Returns None on failure."""
    try:
        return datetime.strptime(label.strip(), "%B %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


def get_options_chain_nasdaq(
    ticker: str,
    lookback_days: int = 400,
) -> tuple[list[str], dict[str, pd.DataFrame]]:
    """
    Fetches the complete options chain for `ticker` from NASDAQ's public API.

    One HTTP call returns ALL available expiry dates with all strikes,
    including volume and accurate Open Interest.

    Returns (expiry_dates_sorted, chain_dict) — same contract as
    yfinance's get_options_chain(), so the rest of the pipeline is
    unchanged.
    """
    from datetime import timedelta

    today = datetime.today()
    end_date = today + timedelta(days=lookback_days)
    from_str = today.strftime("%Y-%m-%d")
    to_str = end_date.strftime("%Y-%m-%d")

    url = f"https://api.nasdaq.com/api/quote/{ticker}/option-chain"
    params = {
        "assetclass": "stocks",
        "limit": 500,          # rows = unique strikes per expiry
        "fromdate": from_str,
        "todate": to_str,
        "expiryType": "all",
    }

    data = None
    for attempt in range(3):
        try:
            session = _get_session()
            resp = session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
            else:
                print(f"  [NASDAQ WARN] {ticker}: request failed after 3 attempts — {e}")
                return [], {}

    if not data or not isinstance(data, dict):
        return [], {}
    inner = data.get("data") or {}
    if not isinstance(inner, dict):
        return [], {}
    table = inner.get("table") or {}
    rows = table.get("rows") if isinstance(table, dict) else None
    if not rows:
        return [], {}

    # Parse rows into individual contracts
    # Row format: one row per strike with both call (c_*) and put (p_*) fields
    # Expiry date is carried in 'expirygroup' separator rows
    raw: dict[str, list[dict]] = {}
    current_expiry: Optional[str] = None

    for row in rows:
        group = row.get("expirygroup", "")
        if group:
            current_expiry = _parse_expiry(group)
        if not current_expiry:
            continue
        strike_str = row.get("strike")
        if not strike_str:
            continue  # separator row
        try:
            strike = float(str(strike_str).replace(",", ""))
        except ValueError:
            continue

        for side, oi_key, vol_key, last_key in (
            ("call", "c_Openinterest", "c_Volume", "c_Last"),
            ("put",  "p_Openinterest", "p_Volume", "p_Last"),
        ):
            raw.setdefault(current_expiry, []).append({
                "strike":       strike,
                "type":         side,
                "volume":       int(_parse_num(row.get(vol_key))),
                "openInterest": int(_parse_num(row.get(oi_key))),
                "lastPrice":    _parse_num(row.get(last_key)),
            })

    if not raw:
        return [], {}

    # Convert to DataFrames
    chain_dict: dict[str, pd.DataFrame] = {}
    for exp, contracts in raw.items():
        df = pd.DataFrame(contracts)
        df["volume"]       = pd.to_numeric(df["volume"],       errors="coerce").fillna(0).astype(int)
        df["openInterest"] = pd.to_numeric(df["openInterest"], errors="coerce").fillna(0).astype(int)
        chain_dict[exp] = df

    expirations = sorted(chain_dict.keys())
    return expirations, chain_dict
