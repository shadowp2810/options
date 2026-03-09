"""
Stock universe definitions.
US: S&P 500 Information Technology sector + Nasdaq-100
India: Nifty 100 (Nifty 50 + Nifty Next 50) via NSE (.NS suffix)
"""

# ---------------------------------------------------------------------------
# US — S&P 500 Information Technology
# ---------------------------------------------------------------------------
SP500_IT = [
    "AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CRM", "AMD", "QCOM", "TXN", "AMAT",
    "ACN", "IBM", "INTU", "MU", "LRCX", "ADI", "KLAC", "SNPS", "CDNS", "MRVL",
    "MSI", "FTNT", "ANSS", "ADSK", "TEL", "APH", "MPWR", "GEN", "CTSH", "IT",
    "KEYS", "AKAM", "ZBRA", "TDY", "ENPH", "TER", "SWKS", "QRVO", "FFIV", "EPAM",
    "JNPR", "NTAP", "HPE", "GLW", "STX", "WDC", "CSCO", "ANET", "PANW", "FSLR",
    "NOW", "TTWO", "EA", "PAYC", "VRSN", "LDOS", "SAIC", "DXC", "HPQ",
    "CDW", "GDDY", "PTC", "JKHY", "TRMB", "PCTY", "NSIT",
]

# ---------------------------------------------------------------------------
# US — Nasdaq-100
# ---------------------------------------------------------------------------
NASDAQ_100 = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "TSLA", "AVGO", "COST",
    "NFLX", "AMD", "PEP", "ADBE", "CSCO", "QCOM", "LIN", "TMUS", "INTU", "AMGN",
    "TXN", "AMAT", "CMCSA", "HON", "ISRG", "BKNG", "VRTX", "REGN", "ADI", "PANW",
    "SBUX", "GILD", "MU", "LRCX", "MDLZ", "INTC", "KLAC", "SNPS", "CDNS", "ASML",
    "MELI", "ADP", "MAR", "CTAS", "ABNB", "MNST", "FTNT", "MRVL", "PYPL", "ORLY",
    "PCAR", "CPRT", "ROST", "PAYX", "NXPI", "DXCM", "ODFL", "KDP", "WDAY", "FAST",
    "VRSK", "CRWD", "TEAM", "ZS", "ADSK", "MCHP", "CSX", "EA", "CEG", "BIIB",
    "WBD", "IDXX", "FANG", "EXC", "XEL", "GEHC", "KHC", "TTWO", "ON", "GFS",
    "DLTR", "ILMN", "SIRI", "ZM", "LCID", "DDOG", "OKTA", "RIVN", "RGEN", "NTES",
    "ANSS", "ALGN", "CDW", "HOLX", "MTCH", "SWKS", "INCY", "WBA", "PDD",
]

# ---------------------------------------------------------------------------
# India — NSE F&O (Futures & Options) segment stocks
# Only stocks approved by SEBI/NSE for derivatives trading have liquid options.
# Source: NSE F&O stock list (updated periodically by NSE).
# All tickers use the .NS suffix for yfinance (NSE).
# ---------------------------------------------------------------------------
INDIA_FNO = [
    # Nifty 50 — all have active F&O
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "ICICIBANK.NS",
    "INFOSYS.NS", "SBIN.NS", "HINDUNILVR.NS", "ITC.NS", "LT.NS",
    "KOTAKBANK.NS", "AXISBANK.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS",
    "TITAN.NS", "SUNPHARMA.NS", "WIPRO.NS", "ULTRACEMCO.NS", "NESTLEIND.NS",
    "NTPC.NS", "POWERGRID.NS", "ONGC.NS", "TATAMOTORS.NS", "TATASTEEL.NS",
    "HCLTECH.NS", "M&M.NS", "BAJAJFINSV.NS", "TECHM.NS", "GRASIM.NS",
    "JSWSTEEL.NS", "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS", "DIVISLAB.NS",
    "DRREDDY.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "INDUSINDBK.NS",
    "BRITANNIA.NS", "CIPLA.NS", "SBILIFE.NS", "HDFCLIFE.NS", "BPCL.NS",
    "TATACONSUM.NS", "APOLLOHOSP.NS", "BAJAJ-AUTO.NS", "VEDL.NS", "SHREECEM.NS",

    # Nifty Next 50 — confirmed F&O
    "ADANIGREEN.NS", "AMBUJACEM.NS", "ACC.NS", "BANKBARODA.NS", "BERGEPAINT.NS",
    "BOSCHLTD.NS", "CANBK.NS", "CHOLAFIN.NS", "COLPAL.NS", "DABUR.NS",
    "DLF.NS", "GAIL.NS", "GODREJCP.NS", "HAVELLS.NS", "ICICIPRULI.NS",
    "ICICIGI.NS", "INDUSTOWER.NS", "INDIGO.NS", "IOC.NS", "JINDALSTEL.NS",
    "LUPIN.NS", "MARICO.NS", "MOTHERSON.NS", "MUTHOOTFIN.NS", "NAUKRI.NS",
    "NHPC.NS", "NMDC.NS", "OFSS.NS", "PAGEIND.NS", "PIDILITIND.NS",
    "PNB.NS", "RECLTD.NS", "SAIL.NS", "SHRIRAMFIN.NS", "SIEMENS.NS",
    "TORNTPHARM.NS", "TRENT.NS", "TVSMOTOR.NS", "UPL.NS", "VOLTAS.NS",
    "ZOMATO.NS", "DMART.NS", "LICI.NS", "IRFC.NS",

    # Additional high-liquidity F&O stocks outside Nifty 100
    "TATAPOWER.NS", "TATACHEM.NS", "TATACOMM.NS",
    "PERSISTENT.NS", "LTIM.NS", "COFORGE.NS", "MPHASIS.NS",
    "FEDERALBNK.NS", "IDFCFIRSTB.NS", "BANDHANBNK.NS",
    "AUROPHARMA.NS", "BIOCON.NS", "ALKEM.NS",
    "GODREJPROP.NS", "OBEROIRLTY.NS", "PRESTIGE.NS",
    "IRCTC.NS", "RVNL.NS", "BEL.NS", "BHEL.NS",
    "ABCAPITAL.NS", "MFSL.NS", "CUMMINSIND.NS",
    "ASHOKLEY.NS", "CONCOR.NS", "ZYDUSLIFE.NS",
]


def get_universe() -> list[str]:
    """
    Returns deduplicated list of US tickers (S&P 500 IT + Nasdaq-100).

    India (INDIA_FNO) is defined above for future use but excluded here —
    yfinance does not provide NSE options chain data. A broker API
    (e.g. Zerodha Kite) is required to enable Indian options signals.
    """
    return sorted(set(SP500_IT + NASDAQ_100))


if __name__ == "__main__":
    tickers = get_universe()
    print(f"US tickers: {len(tickers)}")
    print(tickers)
