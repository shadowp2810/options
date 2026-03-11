"""
Analyzes options chains to find top 3 highest-volume contracts
for each target horizon. Computes buy/sell signal, forecasted % move,
earnings-in-window flag, and delta vs the previous run.
"""

from datetime import date, timedelta
import pandas as pd
from typing import Optional

HORIZONS: dict[str, int | None] = {
    "fri":  None,  # special: nearest Friday that hasn't expired yet
    "7d":   7,
    "30d":  30,
    "45d":  45,
    "60d":  60,
    "90d":  90,
    "180d": 180,
    "1y":   365,
}

# How each horizon's OI trend should be computed:
#   "daily"    → compare vs yesterday's snapshot, use price_1d for combo signal
#   "weekly"   → compare vs 7-day-old snapshot, use price_5d for combo signal
#   "suppress" → show C/P OI totals only, no trend % or combo signal
HORIZON_OI_WINDOW: dict[str, str] = {
    "fri":  "daily",
    "7d":   "daily",
    "30d":  "weekly",
    "45d":  "weekly",
    "60d":  "weekly",
    "90d":  "weekly",
    "180d": "suppress",
    "1y":   "suppress",
}


def next_friday(today: date) -> date:
    """
    Returns the next Friday from today that options haven't expired on yet.
    Since we run at/after market close, Friday itself is treated as expired —
    so on Fridays we target the following Friday (7 days out).
    """
    days_until = (4 - today.weekday()) % 7  # 0 if today is Friday
    if days_until == 0:
        days_until = 7  # today is Friday, options already expired at close
    return today + timedelta(days=days_until)

TOP_N = 10
MAX_EXPIRY_BUFFER_DAYS = 10  # how far past target we'll look for a valid expiry


def find_intraweek_expiries(expirations: list[str], today: date) -> list[str]:
    """
    Returns Mon/Tue/Wed/Thu expiry dates strictly between today and the next Friday.
    These intra-week expiries only exist on hyper-liquid stocks (AAPL, NVDA, TSLA…).
    """
    friday = next_friday(today)
    result = []
    for exp_str in expirations:
        try:
            exp_date = date.fromisoformat(exp_str)
        except ValueError:
            continue
        if today < exp_date < friday and exp_date.weekday() != 4:
            result.append(exp_str)
    result.sort()
    return result


def find_nearest_expiry(expirations: list[str], target_date: date) -> Optional[str]:
    """
    Returns the nearest Friday expiry date string that is >= target_date,
    within MAX_EXPIRY_BUFFER_DAYS of target.

    Filters to Fridays only (weekday == 4) so that Mon/Wed intra-week expiries
    available on hyper-liquid stocks (AAPL, NVDA, TSLA, etc.) are excluded.
    Falls back to any Friday >= target if none found within the buffer.
    Returns None if no Friday expiry exists at all.
    """
    cutoff = target_date + timedelta(days=MAX_EXPIRY_BUFFER_DAYS)
    candidates = []
    for exp_str in expirations:
        try:
            exp_date = date.fromisoformat(exp_str)
        except ValueError:
            continue
        if exp_date.weekday() != 4:  # skip non-Fridays
            continue
        if target_date <= exp_date <= cutoff:
            candidates.append((exp_date, exp_str))

    if not candidates:
        # relax buffer: nearest Friday >= target, no distance limit
        all_future = []
        for exp_str in expirations:
            try:
                exp_date = date.fromisoformat(exp_str)
            except ValueError:
                continue
            if exp_date.weekday() != 4:
                continue
            if exp_date >= target_date:
                all_future.append((exp_date, exp_str))
        if all_future:
            all_future.sort()
            return all_future[0][1]
        return None

    candidates.sort()
    return candidates[0][1]


def classify_signal(opt_type: str, strike: float, current_price: float) -> str:
    """
    Returns the directional signal for a contract:
    - OTM Call (strike > price)  → BUY    (bet on upside)
    - OTM Put  (strike < price)  → SELL   (bet on downside)
    - ITM Call (strike < price)  → HEDGE-C (smart money covering a profitable short)
    - ITM Put  (strike > price)  → HEDGE-P (smart money insuring against further downside)
    - ATM (strike == price)      → BUY for calls, SELL for puts
    """
    if opt_type == "call":
        return "BUY" if strike >= current_price else "HEDGE-C"
    else:  # put
        return "SELL" if strike <= current_price else "HEDGE-P"


def top_contracts(
    chain_df: pd.DataFrame,
    current_price: float,
    n: int = TOP_N,
) -> list[dict]:
    """
    Returns the top-N contracts ranked by Open Interest from a combined calls+puts DataFrame.
    Each entry: {strike, type, open_interest, volume, signal, moneyness, forecast_pct}
    OI = previous-day close snapshot (accurate from NASDAQ API).
    Volume = today's trades (shown as supplementary info).
    """
    df = chain_df.copy()
    df["openInterest"] = pd.to_numeric(df["openInterest"], errors="coerce").fillna(0)
    df["volume"]       = pd.to_numeric(df["volume"],       errors="coerce").fillna(0)
    df = df[df["openInterest"] > 0].copy()
    df = df.sort_values("openInterest", ascending=False).head(n)

    results = []
    for _, row in df.iterrows():
        strike = float(row["strike"])
        opt_type = str(row["type"])
        open_interest = int(row["openInterest"])
        volume = int(row["volume"]) if row["volume"] > 0 else 0
        signal = classify_signal(opt_type, strike, current_price)
        # Moneyness label for display
        if opt_type == "call":
            moneyness = "OTM" if strike > current_price else ("ATM" if strike == current_price else "ITM")
        else:
            moneyness = "OTM" if strike < current_price else ("ATM" if strike == current_price else "ITM")
        forecast_pct = round((strike - current_price) / current_price * 100, 2)
        results.append({
            "strike": strike,
            "type": opt_type.capitalize(),
            "open_interest": open_interest,
            "volume": volume,
            "signal": signal,
            "moneyness": moneyness,
            "forecast_pct": forecast_pct,
        })

    # Pad with N/A entries if fewer than n contracts with volume
    while len(results) < n:
        results.append({
            "strike": None,
            "type": None,
            "volume": None,
            "signal": None,
            "moneyness": None,
            "forecast_pct": None,
        })

    return results


def analyze_ticker(
    ticker: str,
    price: Optional[float],
    expirations: list[str],
    chains: dict[str, pd.DataFrame],
    earnings_date: Optional[str] = None,
    company_info: Optional[dict] = None,
    price_history: Optional[dict] = None,
    prev_horizons: Optional[dict] = None,        # yesterday's snapshot
    prev_horizons_weekly: Optional[dict] = None, # ~7-day-old snapshot
    today: Optional[date] = None,
) -> dict:
    """
    For each horizon, finds the nearest expiry and top-3 contracts.
    Adds earnings_in_window flag and delta vs previous run per contract.
    Returns a structured dict ready for export.
    """
    if today is None:
        today = date.today()

    market = "IN" if ticker.endswith(".NS") or ticker.endswith(".BO") else "US"

    result = {
        "ticker": ticker,
        "market": market,
        "price": price,
        "earnings_date": earnings_date,
        "company_info": company_info or {"name": None, "sector": None, "industry": None},
        "price_history": price_history or {"price_1d_pct": None, "price_5d_pct": None},
        "horizons": {},
        "intraweek": [],
    }

    empty_contract = {
        "strike": None, "type": None, "open_interest": None, "volume": None,
        "signal": None, "moneyness": None, "forecast_pct": None,
        "prev_strike": None, "strike_delta": None,
        "prev_signal": None, "signal_flipped": False,
    }

    if price is None or not expirations:
        for label in HORIZONS:
            result["horizons"][label] = {
                "expiry": None,
                "earnings_in_window": False,
                "contracts": [dict(empty_contract)] * TOP_N,
            }
        return result

    # Parse earnings date once
    parsed_earnings: Optional[date] = None
    if earnings_date:
        try:
            parsed_earnings = date.fromisoformat(earnings_date)
        except ValueError:
            pass

    for label, days in HORIZONS.items():
        target_date = next_friday(today) if days is None else today + timedelta(days=days)
        expiry = find_nearest_expiry(expirations, target_date)

        # Earnings flag: is there an earnings date between today and this expiry?
        earnings_in_window = False
        if parsed_earnings and expiry:
            try:
                expiry_date = date.fromisoformat(expiry)
                earnings_in_window = today < parsed_earnings <= expiry_date
            except ValueError:
                pass

        if expiry is None or expiry not in chains:
            contracts = [dict(empty_contract)] * TOP_N
            total_call_oi = 0
            total_put_oi  = 0
        else:
            contracts = top_contracts(chains[expiry], price)
            # Compute total call/put OI across ALL contracts in this expiry — much
            # more stable for day-over-day trend than summing only the top-N.
            chain_df = chains[expiry]
            total_call_oi = int(
                chain_df.loc[chain_df["type"].str.lower() == "call", "openInterest"]
                .pipe(pd.to_numeric, errors="coerce").fillna(0).sum()
            )
            total_put_oi = int(
                chain_df.loc[chain_df["type"].str.lower() == "put", "openInterest"]
                .pipe(pd.to_numeric, errors="coerce").fillna(0).sum()
            )

        # Attach delta vs previous run
        prev_contracts = []
        if prev_horizons and label in prev_horizons:
            prev_contracts = prev_horizons[label].get("contracts", [])

        for rank_idx, contract in enumerate(contracts):
            prev = prev_contracts[rank_idx] if rank_idx < len(prev_contracts) else None
            prev_strike = prev.get("strike") if prev else None
            prev_signal = prev.get("signal") if prev else None
            curr_strike = contract.get("strike")
            curr_signal = contract.get("signal")

            contract["prev_strike"] = prev_strike
            contract["strike_delta"] = (
                round(curr_strike - prev_strike, 2)
                if curr_strike is not None and prev_strike is not None
                else None
            )
            contract["prev_signal"] = prev_signal
            is_hedge = lambda s: s in ("HEDGE-C", "HEDGE-P")
            contract["signal_flipped"] = (
                prev_signal is not None
                and curr_signal is not None
                and prev_signal != curr_signal
                and not is_hedge(curr_signal)
                and not is_hedge(prev_signal)
            )

        # OI trend — window and price direction depend on horizon
        oi_window = HORIZON_OI_WINDOW.get(label, "daily")

        # Significance thresholds
        OI_SIG_PCT  = 5.0
        OI_SIG_ABS  = 500
        OI_MIN_BASE = 500   # minimum prev OI to compute a meaningful %

        def _oi_trend(curr: int, prev: int) -> tuple[str, float | None]:
            """Returns (trend, change_pct). trend is 'up'/'down'/'flat'/'none'."""
            if prev < OI_MIN_BASE:
                return "none", None
            delta = curr - prev
            pct = round(delta / prev * 100, 1)
            if abs(pct) >= OI_SIG_PCT and abs(delta) >= OI_SIG_ABS:
                return ("up" if delta > 0 else "down"), pct
            return "flat", pct

        def _extract_prev_ois(horizons_dict: Optional[dict]) -> tuple[Optional[int], Optional[int]]:
            """Pull total_call_oi/total_put_oi from a previous-run horizons dict."""
            if not horizons_dict or label not in horizons_dict:
                return None, None
            h = horizons_dict[label]
            c = h.get("total_call_oi")
            p = h.get("total_put_oi")
            # Back-compat: fall back to summing stored contracts
            if c is None:
                c = sum((x.get("open_interest") or 0) for x in h.get("contracts", [])
                        if (x.get("type") or "").lower() == "call")
            if p is None:
                p = sum((x.get("open_interest") or 0) for x in h.get("contracts", [])
                        if (x.get("type") or "").lower() == "put")
            return c, p

        call_oi_trend, call_oi_pct = "none", None
        put_oi_trend,  put_oi_pct  = "none", None
        combo_signal = None

        if oi_window != "suppress":
            # Pick the right snapshot
            ref_horizons = prev_horizons_weekly if oi_window == "weekly" else prev_horizons
            prev_call_oi, prev_put_oi = _extract_prev_ois(ref_horizons)

            if prev_call_oi is not None:
                call_oi_trend, call_oi_pct = _oi_trend(total_call_oi, prev_call_oi)
            if prev_put_oi is not None:
                put_oi_trend, put_oi_pct = _oi_trend(total_put_oi, prev_put_oi)

            # Price direction: 1D for daily horizons, 5D for weekly horizons
            ph = price_history or {}
            price_dir = ph.get("price_1d_pct") if oi_window == "daily" else ph.get("price_5d_pct")
            price_up = price_dir is not None and price_dir > 0
            price_dn = price_dir is not None and price_dir < 0
            c_up = call_oi_trend == "up"
            c_dn = call_oi_trend == "down"
            p_up = put_oi_trend == "up"
            p_dn = put_oi_trend == "down"

            if c_up and p_dn and price_up:   combo_signal = "Bullish"
            elif p_up and c_dn and price_dn: combo_signal = "Bearish"
            elif p_up and price_up:          combo_signal = "Hedged Rally"
            elif c_up and price_dn:          combo_signal = "Short Covering"
            elif c_up and p_up:              combo_signal = "Build-Up"
            elif c_dn and p_dn:              combo_signal = "Unwinding"

        result["horizons"][label] = {
            "expiry": expiry,
            "earnings_in_window": earnings_in_window,
            "contracts": contracts,
            "total_call_oi": total_call_oi,
            "total_put_oi":  total_put_oi,
            "oi_window":     oi_window,        # "daily" / "weekly" / "suppress"
            "call_oi_trend": call_oi_trend,
            "put_oi_trend":  put_oi_trend,
            "call_oi_pct":   call_oi_pct,
            "put_oi_pct":    put_oi_pct,
            "combo_signal":  combo_signal,
        }

    # Intra-week expiries (Mon–Thu) for hyper-liquid stocks
    for exp_str in find_intraweek_expiries(expirations, today):
        if exp_str in chains:
            iw_contracts = top_contracts(chains[exp_str], price)
            exp_date = date.fromisoformat(exp_str)
            result["intraweek"].append({
                "expiry": exp_str,
                "day": exp_date.strftime("%A"),
                "contracts": iw_contracts,
            })

    return result


def analyze_all(
    fetch_results: dict,
    prev_data: Optional[list] = None,
    prev_data_weekly: Optional[list] = None,
    suppress_delta: bool = False,
) -> list[dict]:
    """
    Runs analyze_ticker on every ticker in fetch_results.
    prev_data:        yesterday's snapshot (daily OI comparison for Fri/7D).
    prev_data_weekly: ~7-day-old snapshot (weekly OI comparison for 30D-90D).
    suppress_delta:   if True, skip delta computation (snapshot too old).
    """
    today = date.today()

    def _build_lookup(data: Optional[list]) -> dict[str, dict]:
        if not data or suppress_delta:
            return {}
        return {item["ticker"]: item.get("horizons", {})
                for item in data if item.get("ticker")}

    prev_lookup        = _build_lookup(prev_data)
    prev_lookup_weekly = _build_lookup(prev_data_weekly)

    analyzed = []
    for ticker, data in fetch_results.items():
        row = analyze_ticker(
            ticker=ticker,
            price=data.get("price"),
            expirations=data.get("expirations", []),
            chains=data.get("chains", {}),
            earnings_date=data.get("earnings_date"),
            company_info=data.get("company_info"),
            price_history=data.get("price_history"),
            prev_horizons=prev_lookup.get(ticker),
            prev_horizons_weekly=prev_lookup_weekly.get(ticker),
            today=today,
        )
        analyzed.append(row)

    analyzed.sort(key=lambda x: x["ticker"])
    return analyzed
