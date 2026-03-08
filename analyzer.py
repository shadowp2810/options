"""
Analyzes options chains to find top 3 highest-volume contracts
for each target horizon. Computes buy/sell signal and forecasted % move.
"""

from datetime import date, timedelta
import pandas as pd
from typing import Optional

HORIZONS: dict[str, int] = {
    "7d":   7,
    "30d":  30,
    "45d":  45,
    "60d":  60,
    "90d":  90,
    "180d": 180,
    "1y":   365,
}

TOP_N = 3
MAX_EXPIRY_BUFFER_DAYS = 10  # how far past target we'll look for a valid expiry


def find_nearest_expiry(expirations: list[str], target_date: date) -> Optional[str]:
    """
    Returns the nearest expiry date string that is >= target_date,
    within MAX_EXPIRY_BUFFER_DAYS of target. Returns None if none found.
    """
    cutoff = target_date + timedelta(days=MAX_EXPIRY_BUFFER_DAYS)
    candidates = []
    for exp_str in expirations:
        try:
            exp_date = date.fromisoformat(exp_str)
        except ValueError:
            continue
        if target_date <= exp_date <= cutoff:
            candidates.append((exp_date, exp_str))

    if not candidates:
        # relax: just take the nearest expiry >= target (no buffer limit)
        all_future = []
        for exp_str in expirations:
            try:
                exp_date = date.fromisoformat(exp_str)
            except ValueError:
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
    - OTM Call (strike > price)  → BUY   (bet on upside)
    - OTM Put  (strike < price)  → SELL  (bet on downside)
    - ITM Call (strike < price)  → HEDGE (already profitable call, likely covering)
    - ITM Put  (strike > price)  → HEDGE (insurance on existing long position)
    - ATM (strike == price)      → BUY for calls, SELL for puts
    """
    if opt_type == "call":
        return "BUY" if strike >= current_price else "HEDGE"
    else:  # put
        return "SELL" if strike <= current_price else "HEDGE"


def top_contracts(
    chain_df: pd.DataFrame,
    current_price: float,
    n: int = TOP_N,
) -> list[dict]:
    """
    Returns the top-N contracts by volume from a combined calls+puts DataFrame.
    Each entry: {strike, type, volume, signal, moneyness, forecast_pct}
    """
    df = chain_df[chain_df["volume"] > 0].copy()
    df = df.sort_values("volume", ascending=False).head(n)

    results = []
    for _, row in df.iterrows():
        strike = float(row["strike"])
        opt_type = str(row["type"])
        volume = int(row["volume"])
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
    today: Optional[date] = None,
) -> dict:
    """
    For each horizon, finds the nearest expiry and top-3 contracts.
    Returns a structured dict ready for export.
    """
    if today is None:
        today = date.today()

    result = {"ticker": ticker, "price": price, "horizons": {}}

    if price is None or not expirations:
        for label in HORIZONS:
            result["horizons"][label] = {
                "expiry": None,
                "contracts": [{"strike": None, "type": None, "volume": None,
                                "signal": None, "moneyness": None, "forecast_pct": None}] * TOP_N,
            }
        return result

    for label, days in HORIZONS.items():
        target_date = today + timedelta(days=days)
        expiry = find_nearest_expiry(expirations, target_date)

        if expiry is None or expiry not in chains:
            contracts = [{"strike": None, "type": None, "volume": None,
                          "signal": None, "moneyness": None, "forecast_pct": None}] * TOP_N
        else:
            contracts = top_contracts(chains[expiry], price)

        result["horizons"][label] = {"expiry": expiry, "contracts": contracts}

    return result


def analyze_all(fetch_results: dict) -> list[dict]:
    """
    Runs analyze_ticker on every ticker in fetch_results.
    Returns a list of analysis dicts.
    """
    today = date.today()
    analyzed = []
    for ticker, data in fetch_results.items():
        row = analyze_ticker(
            ticker=ticker,
            price=data.get("price"),
            expirations=data.get("expirations", []),
            chains=data.get("chains", {}),
            today=today,
        )
        analyzed.append(row)

    analyzed.sort(key=lambda x: x["ticker"])
    return analyzed
