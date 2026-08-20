# PHASE 2 — US MARKET DATA ADAPTER
# 명세 10.1 MARKET_SNAPSHOT 필드를 채운다. yfinance 배치 다운로드로 미국 종목의
# 종가/등락률/거래량/평균거래량대비/거래금액을 가져오고, 시가총액은 종목별 fast_info로 보강한다.
# PHASE 2는 "수집 adapter"만 대상이다 — 스코어 계산/스케줄러는 PHASE 3~4.

import os
import sys
import warnings
from datetime import datetime, timezone

import yfinance as yf

# yfinance 기본 백엔드(curl_cffi, 브라우저 TLS 지문 흉내)가 Claude Code 클라우드 루틴(CCR)의
# 정책 프록시에서 TLS reset을 당해 매번 실패하는 걸 2026-08-20에 실제로 확인했다
# ("curl: (35) Recv failure: Connection reset by peer"). 일반 requests는 같은 프록시를
# 문제없이 통과하므로, 프록시가 감지되면(로컬 실행 시엔 감지 안 되어 영향 없음) yfinance가
# 내부적으로 만드는 세션을 전부 일반 requests.Session()으로 강제한다.
if os.environ.get("CCR_AGENT_PROXY_ENABLED") or os.environ.get("HTTPS_PROXY"):
    try:
        import requests
        from yfinance import data as _yf_data

        _ca_bundle = os.environ.get("REQUESTS_CA_BUNDLE") or os.environ.get("CURL_CA_BUNDLE") or True

        def _proxy_friendly_session():
            s = requests.Session()
            s.verify = _ca_bundle
            return s

        _yf_data.new_session = _proxy_friendly_session
    except Exception:
        pass  # 패치 실패해도 원래 동작(에러)으로 넘어간다 — 침묵 실패로 데이터를 조작하지 않는다.

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


US_MAJOR_INDICES = [
    {"ticker": "^DJI", "name": "다우산업"},
    {"ticker": "^IXIC", "name": "나스닥종합"},
    {"ticker": "^GSPC", "name": "S&P 500"},
]


def fetch_us_major_indices():
    """미국 3대 지수의 최근 1거래일 인트라데이 흐름(스파크라인용)과 등락률을 가져온다.
    이건 명세서에 정의된 항목이 아니라 사용자가 요청한 추가 기능이다."""
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    for idx in US_MAJOR_INDICES:
        ticker = idx["ticker"]
        try:
            h = yf.Ticker(ticker).history(period="5d", interval="30m")
            h = h.dropna(subset=["Close"])
            if h.empty:
                rows.append({**idx, "status": "MISSING"})
                continue
            last_day = h.index[-1].date()
            day_bars = h[h.index.date == last_day]
            if len(day_bars) < 2:
                day_bars = h.tail(13)  # 하루치가 부족하면 최근 구간으로 대체

            closes = [round(float(c), 2) for c in day_bars["Close"]]
            price = closes[-1]
            prev_close_hist = h[h.index.date < last_day]
            prev_close = float(prev_close_hist["Close"].iloc[-1]) if not prev_close_hist.empty else closes[0]
            change = round(price - prev_close, 2)
            change_pct = round(change / prev_close * 100, 2) if prev_close else None

            rows.append({
                **idx, "status": "ACTUAL", "price": price, "change": change, "change_pct": change_pct,
                "sparkline": closes, "as_of_bar": day_bars.index[-1].isoformat(), "fetched_at": now,
            })
        except Exception as e:
            rows.append({**idx, "status": "MISSING", "error": str(e)})
    return rows


if __name__ == "__main__":
    sample = ["NVDA", "AAPL", "TSLA", "SOXL", "URA"]
    for r in fetch_us_market_snapshot(sample):
        print(r["instrument_id"], r["quality"], r.get("price"), r.get("return_pct"), r.get("market_cap"))
