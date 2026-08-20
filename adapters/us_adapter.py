# PHASE 2 — US MARKET DATA ADAPTER
# 명세 10.1 MARKET_SNAPSHOT 필드를 채운다. yfinance 배치 다운로드로 미국 종목의
# 종가/등락률/거래량/평균거래량대비/거래금액을 가져오고, 시가총액은 종목별 fast_info로 보강한다.
# PHASE 2는 "수집 adapter"만 대상이다 — 스코어 계산/스케줄러는 PHASE 3~4.

import sys
import warnings
from datetime import datetime, timezone

import yfinance as yf

warnings.filterwarnings("ignore", category=DeprecationWarning, module="yfinance")

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def _pct_change(series, n=1):
    if len(series) < n + 1:
        return None
    return round((series.iloc[-1] / series.iloc[-1 - n] - 1) * 100, 4)


def fetch_us_market_snapshot(tickers, period="3mo"):
    """명세 10.1 MARKET_SNAPSHOT 리스트를 반환한다 (market='US').
    실패한 개별 티커는 quality='MISSING'으로 남기고 나머지는 계속 처리한다 (43번 원칙과 동일한 정신)."""
    now = datetime.now(timezone.utc).isoformat()
    rows = []

    try:
        raw = yf.download(tickers, period=period, group_by="ticker", auto_adjust=False,
                           progress=False, threads=True)
    except Exception as e:
        return [_missing_row(t, now, f"batch download 실패: {e}") for t in tickers]

    for ticker in tickers:
        try:
            df = raw[ticker] if len(tickers) > 1 else raw
            df = df.dropna(subset=["Close"])
            if df.empty or len(df) < 2:
                rows.append(_missing_row(ticker, now, "가격 히스토리 부족"))
                continue

            close = df["Close"]
            volume = df["Volume"]
            price = float(close.iloc[-1])
            return_pct = _pct_change(close, 1)
            avg_volume_20d = float(volume.iloc[-21:-1].mean()) if len(volume) >= 21 else float(volume.mean())
            today_volume = float(volume.iloc[-1])
            avg_volume_ratio = round(today_volume / avg_volume_20d, 3) if avg_volume_20d else None
            traded_value = round(price * today_volume, 2)

            market_cap = None
            try:
                fi = yf.Ticker(ticker).fast_info
                mc = fi.get("marketCap")
                market_cap = float(mc) if mc else None
            except Exception:
                pass

            rows.append({
                "id": f"SNAP_US_{ticker}_{now[:10]}",
                "market": "US",
                "instrument_id": ticker,
                "as_of": now,
                "price": round(price, 4),
                "return_pct": return_pct,
                "market_cap": market_cap,
                "volume": today_volume,
                "traded_value": traded_value,
                "avg_volume_ratio": avg_volume_ratio,
                "currency": "USD",
                "data_source": "yfinance",
                "quality": "ACTUAL" if market_cap is not None else "PARTIAL(시가총액 없음)",
            })
        except Exception as e:
            rows.append(_missing_row(ticker, now, str(e)))

    return rows


def _missing_row(ticker, now, reason):
    return {
        "id": f"SNAP_US_{ticker}_{now[:10]}",
        "market": "US",
        "instrument_id": ticker,
        "as_of": now,
        "price": None, "return_pct": None, "market_cap": None, "volume": None,
        "traded_value": None, "avg_volume_ratio": None, "currency": "USD",
        "data_source": "yfinance", "quality": "MISSING", "error": reason,
    }


if __name__ == "__main__":
    sample = ["NVDA", "AAPL", "TSLA", "SOXL", "URA"]
    for r in fetch_us_market_snapshot(sample):
        print(r["instrument_id"], r["quality"], r.get("price"), r.get("return_pct"), r.get("market_cap"))
