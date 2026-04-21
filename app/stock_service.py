import time
import yfinance as yf

CACHE_TTL_SECONDS = 60
stock_cache: dict[str, dict] = {}


def _is_cache_valid(symbol: str) -> bool:
    cached = stock_cache.get(symbol)
    if not cached:
        return False
    return (time.time() - cached["timestamp"]) < CACHE_TTL_SECONDS


def get_stock_data(symbol: str) -> dict:
    symbol = symbol.upper()

    if _is_cache_valid(symbol):
        return stock_cache[symbol]["data"]

    ticker = yf.Ticker(symbol)
    info = ticker.info

    if not info:
        raise ValueError("Invalid symbol or no data found")

    current_price = info.get("currentPrice")
    previous_close = info.get("previousClose")

    day_percent_change = None
    if current_price is not None and previous_close not in (None, 0):
        day_percent_change = ((current_price - previous_close) / previous_close) * 100

    data = {
        "symbol": symbol,
        "name": info.get("longName"),
        "price": current_price,
        "previous_close": previous_close,
        "open": info.get("open"),
        "market_cap": info.get("marketCap"),
        "volume": info.get("volume"),
        "high_52_week": info.get("fiftyTwoWeekHigh"),
        "low_52_week": info.get("fiftyTwoWeekLow"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "day_percent_change": day_percent_change,
    }

    stock_cache[symbol] = {
        "timestamp": time.time(),
        "data": data,
    }

    return data


def get_cache_status() -> dict:
    return {
        "cached_symbols": list(stock_cache.keys()),
        "ttl_seconds": CACHE_TTL_SECONDS,
    }
