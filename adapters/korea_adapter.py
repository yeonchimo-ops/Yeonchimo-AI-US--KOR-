# PHASE 2 — KOREA MARKET DATA ADAPTER
# 명세 10.1 MARKET_SNAPSHOT + 6.3(외국인/기관/52주 고저) 필드를 채운다.
# pykrx는 KRX 로그인이 필요하고 (KRX_ID/KRX_PW), 짧은 시간에 프로세스를 여러 번 나눠 호출하면
# 로그인 세션이 깨진 전례가 있다 (project 메모리 참고) — 이 어댑터는 한 프로세스 안에서
# 필요한 모든 pykrx 호출을 끝내도록 설계한다. 전체 유니버스(약 250종목) 일괄 수집은
# PHASE 3 스케줄러가 할 일이고, 여기서는 adapter 함수 자체의 정확성만 검증한다.

import sys
from datetime import datetime, timedelta

from pykrx import stock

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def _latest_business_day(max_back=10):
    """오늘부터 거슬러 올라가며 실제 종가가 채워진 최근 영업일을 찾는다.
    당일 장중/휴장일에는 pykrx가 빈 행(종가=0)만 있는 스켈레톤을 돌려주는 경우가 있어
    단순 '비어있지 않음'이 아니라 '실제 종가 데이터 존재'로 판정한다."""
    d = datetime.now()
    for _ in range(max_back):
        ds = d.strftime("%Y%m%d")
        df = stock.get_market_ohlcv_by_ticker(ds, market="ALL")
        if df is not None and not df.empty and (df["종가"] > 0).sum() > 100:
            return ds
        d -= timedelta(days=1)
    raise RuntimeError("최근 영업일 데이터를 찾지 못함 (최대 %d일 역탐색)" % max_back)


def fetch_korea_market_snapshot(tickers, date=None, with_investor_flow=True, with_52w=True):
    """명세 10.1 MARKET_SNAPSHOT(+6.3 확장 필드) 리스트를 반환한다 (market='KR').
    tickers는 6자리 코드 리스트. 대량 티커에 대해 investor_flow/52w를 켜면 pykrx 호출이
    티커당 1~2회씩 추가되므로, 큰 유니버스는 with_investor_flow/with_52w=False로 먼저 가격만
    빠르게 받고 필요한 종목만 별도로 보강하는 걸 권장한다."""
    date = date or _latest_business_day()
    now_iso = datetime.now().isoformat()

    ohlcv = stock.get_market_ohlcv_by_ticker(date, market="ALL")
    cap = stock.get_market_cap_by_ticker(date, market="ALL")
    kospi_set = set(stock.get_market_ticker_list(date, market="KOSPI"))
    kosdaq_set = set(stock.get_market_ticker_list(date, market="KOSDAQ"))

    rows = []
    for ticker in tickers:
        if ticker not in ohlcv.index:
            rows.append(_missing_row(ticker, now_iso, date, "당일 시세 없음(상장폐지/거래정지/코드오류 가능)"))
            continue

        o = ohlcv.loc[ticker]
        market_cap = float(cap.loc[ticker, "시가총액"]) if ticker in cap.index else None
        market = "KOSPI" if ticker in kospi_set else ("KOSDAQ" if ticker in kosdaq_set else "UNKNOWN")

        row = {
            "id": f"SNAP_KR_{ticker}_{date}",
            "market": "KR",
            "sub_market": market,
            "instrument_id": ticker,
            "as_of": now_iso,
            "trade_date": date,
            "price": float(o["종가"]),
            "return_pct": float(o["등락률"]),
            "market_cap": market_cap,
            "volume": float(o["거래량"]),
            "traded_value": float(o["거래대금"]),
            "avg_volume_ratio": None,  # 여러날 조회가 필요해 PHASE1 adapter 범위에서는 생략
            "currency": "KRW",
            "data_source": "pykrx",
            "quality": "ACTUAL" if market_cap is not None else "PARTIAL(시가총액 없음)",
            "foreign_net": None,
            "institution_net": None,
            "program_net": None,  # pykrx에 신뢰 가능한 엔드포인트 없음 (project 메모리 기록됨) — 인터페이스만 정의
            "week52_high": None,
            "week52_low": None,
            "pct_vs_week52_high": None,
            "pct_vs_week52_low": None,
        }
        rows.append(row)

    if with_investor_flow:
        _enrich_investor_flow(rows, date)
    if with_52w:
        _enrich_52w(rows, date)

    return rows


def _enrich_investor_flow(rows, date):
    for row in rows:
        if row["quality"] == "MISSING":
            continue
        ticker = row["instrument_id"]
        try:
            df = stock.get_market_trading_value_by_date(date, date, ticker, detail=False)
            if df is None or df.empty:
                continue
            last = df.iloc[-1]
            row["foreign_net"] = float(last["외국인합계"])
            row["institution_net"] = float(last["기관합계"])
        except Exception as e:
            row["investor_flow_error"] = str(e)


def _enrich_52w(rows, date):
    end = datetime.strptime(date, "%Y%m%d")
    start = (end - timedelta(days=365)).strftime("%Y%m%d")
    for row in rows:
        if row["quality"] == "MISSING":
            continue
        ticker = row["instrument_id"]
        try:
            hist = stock.get_market_ohlcv(start, date, ticker)
            hist = hist[hist["종가"] > 0]
            if hist.empty:
                continue
            high = float(hist["고가"].max())
            low = float(hist["저가"].min())
            price = row["price"]
            row["week52_high"] = high
            row["week52_low"] = low
            row["pct_vs_week52_high"] = round((price / high - 1) * 100, 2) if high else None
            row["pct_vs_week52_low"] = round((price / low - 1) * 100, 2) if low else None
        except Exception as e:
            row["week52_error"] = str(e)


def _missing_row(ticker, now_iso, date, reason):
    return {
        "id": f"SNAP_KR_{ticker}_{date}",
        "market": "KR", "sub_market": None, "instrument_id": ticker, "as_of": now_iso,
        "trade_date": date, "price": None, "return_pct": None, "market_cap": None,
        "volume": None, "traded_value": None, "avg_volume_ratio": None, "currency": "KRW",
        "data_source": "pykrx", "quality": "MISSING", "error": reason,
        "foreign_net": None, "institution_net": None, "program_net": None,
        "week52_high": None, "week52_low": None, "pct_vs_week52_high": None, "pct_vs_week52_low": None,
    }


if __name__ == "__main__":
    sample = ["005930", "000660", "043260", "475150", "377300"]  # 삼성전자/SK하이닉스/성호전자/SK이터닉스/카카오페이
    for r in fetch_korea_market_snapshot(sample):
        print(r["instrument_id"], r["sub_market"], r["quality"], r.get("price"), r.get("return_pct"),
              "외국인", r.get("foreign_net"), "52wH%", r.get("pct_vs_week52_high"))
