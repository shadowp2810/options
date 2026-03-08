"""
Fetches current stock price and options chain data via yfinance.
"""

import time
import yfinance as yf
import pandas as pd
from typing import Optional


def get_stock_data(ticker: str) -> tuple[Optional[float], Optional[yf.Ticker]]:
    """
    Returns (current_price, yf.Ticker object) for a given ticker.
    Returns (None, None) on failure.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        price = info.last_price
        if price is None or price == 0:
            hist = t.history(period="1d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
        return price, t
    except Exception as e:
        print(f"  [WARN] {ticker}: failed to fetch price — {e}")
        return None, None


def get_options_chain(ticker_obj: yf.Ticker, ticker: str) -> tuple[list[str], dict[str, pd.DataFrame]]:
    """
    Returns (expiry_dates, chain_dict) where chain_dict maps
    expiry_date_str -> combined calls+puts DataFrame with a 'type' column.
    """
    try:
        expirations = ticker_obj.options
        if not expirations:
            return [], {}

        chain_dict: dict[str, pd.DataFrame] = {}
        for exp in expirations:
            try:
                chain = ticker_obj.option_chain(exp)
                calls = chain.calls.copy()
                puts = chain.puts.copy()
                calls["type"] = "call"
                puts["type"] = "put"
                combined = pd.concat([calls, puts], ignore_index=True)
                combined = combined[["strike", "type", "volume", "lastPrice", "openInterest"]].copy()
                combined["volume"] = pd.to_numeric(combined["volume"], errors="coerce").fillna(0)
                chain_dict[exp] = combined
            except Exception:
                continue

        return list(expirations), chain_dict

    except Exception as e:
        print(f"  [WARN] {ticker}: failed to fetch options chain — {e}")
        return [], {}


def fetch_all(tickers: list[str], delay: float = 0.6) -> dict:
    """
    Fetches price + options chain for each ticker.
    Returns a dict: ticker -> {"price": float, "expirations": [...], "chains": {...}}
    """
    results = {}
    total = len(tickers)
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{total}] Fetching {ticker}...")
        price, ticker_obj = get_stock_data(ticker)
        if price is None or ticker_obj is None:
            results[ticker] = {"price": None, "expirations": [], "chains": {}}
            time.sleep(delay)
            continue

        expirations, chains = get_options_chain(ticker_obj, ticker)
        results[ticker] = {
            "price": round(price, 2),
            "expirations": expirations,
            "chains": chains,
        }
        time.sleep(delay)

    return results
