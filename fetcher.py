"""
Fetches stock/options data.
- Price, earnings date, company info: yfinance
- Options chain (volume + accurate open interest): NASDAQ public API
  (falls back to yfinance if NASDAQ returns nothing)
"""

import time
import yfinance as yf
import pandas as pd
from typing import Optional
from nasdaq_fetcher import get_options_chain_nasdaq


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


def get_company_info(ticker_obj: yf.Ticker) -> dict:
    """
    Returns {name, sector, industry} from ticker.info.
    All fields default to None on failure (best-effort, one extra HTTP call).
    """
    try:
        info = ticker_obj.info
        return {
            "name":     info.get("longName") or info.get("shortName"),
            "sector":   info.get("sector"),
            "industry": info.get("industry"),
        }
    except Exception:
        return {"name": None, "sector": None, "industry": None}


def get_price_history(ticker_obj: yf.Ticker) -> dict:
    """
    Returns {price_1d_pct, price_5d_pct} — % change over 1 and 5 trading days.
    Uses last 10 calendar days of history to ensure 5 trading days are available.
    """
    try:
        hist = ticker_obj.history(period="10d")
        if hist.empty or len(hist) < 2:
            return {"price_1d_pct": None, "price_5d_pct": None}
        closes = hist["Close"].dropna()
        today_close = float(closes.iloc[-1])

        price_1d_pct = None
        if len(closes) >= 2:
            prev = float(closes.iloc[-2])
            price_1d_pct = round((today_close - prev) / prev * 100, 2) if prev else None

        price_5d_pct = None
        if len(closes) >= 6:
            base = float(closes.iloc[-6])
            price_5d_pct = round((today_close - base) / base * 100, 2) if base else None
        elif len(closes) >= 2:
            # Fewer than 5 days available (e.g. recently listed) — use whatever we have
            base = float(closes.iloc[0])
            price_5d_pct = round((today_close - base) / base * 100, 2) if base else None

        return {"price_1d_pct": price_1d_pct, "price_5d_pct": price_5d_pct}
    except Exception:
        return {"price_1d_pct": None, "price_5d_pct": None}


def get_earnings_date(ticker_obj: yf.Ticker) -> Optional[str]:
    """
    Returns the next earnings date as an ISO string (YYYY-MM-DD), or None.
    yfinance returns calendar as a dict with an 'Earnings Date' key.
    """
    try:
        cal = ticker_obj.calendar
        if not cal:
            return None
        earnings = cal.get("Earnings Date")
        if earnings is None:
            return None
        # May be a list of dates or a single value
        if isinstance(earnings, (list, tuple)) and len(earnings) > 0:
            d = earnings[0]
        else:
            d = earnings
        if hasattr(d, "date"):
            return str(d.date())
        return str(d)[:10]  # trim to YYYY-MM-DD if already a string
    except Exception:
        return None


def fetch_all(tickers: list[str], delay: float = 0.6) -> dict:
    """
    Fetches price, earnings date, and options chain for each ticker.
    Returns a dict: ticker -> {"price": float, "earnings_date": str|None,
                                "expirations": [...], "chains": {...}}
    """
    results = {}
    total = len(tickers)
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{total}] Fetching {ticker}...")
        price, ticker_obj = get_stock_data(ticker)
        if price is None or ticker_obj is None:
            results[ticker] = {"price": None, "earnings_date": None,
                               "expirations": [], "chains": {}}
            time.sleep(delay)
            continue

        earnings_date = get_earnings_date(ticker_obj)
        company_info  = get_company_info(ticker_obj)
        price_history = get_price_history(ticker_obj)

        # NASDAQ public API gives accurate OI for free; fall back to yfinance
        expirations, chains = get_options_chain_nasdaq(ticker)
        if not expirations:
            print(f"  [INFO] {ticker}: NASDAQ returned nothing, using yfinance fallback")
            expirations, chains = get_options_chain(ticker_obj, ticker)

        results[ticker] = {
            "price": round(price, 2),
            "earnings_date": earnings_date,
            "company_info": company_info,
            "price_history": price_history,
            "expirations": expirations,
            "chains": chains,
        }
        time.sleep(delay)

    return results
