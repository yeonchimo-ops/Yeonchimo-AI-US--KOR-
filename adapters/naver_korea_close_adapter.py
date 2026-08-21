"""네이버증권 공개 화면용 API 기반 한국 종목 장마감 수집기.

네이버증권은 KRX의 공식 원천이 아니라 사용자 지정 조회 소스다. 종가·시가총액·
거래대금은 polling API, 외국인/기관 순매수 수량은 mobile integration API에서
가져온다. 순매수 금액은 수량×종가의 명시적 추정값으로 저장한다.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import time

import requests


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://finance.naver.com/sise/",
}


def _number(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).replace(",", "").replace("%", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def _request_json(url, timeout=12, retries=3):
    last_error = None
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(0.4 * (2 ** attempt))
    raise RuntimeError(f"Naver Finance request failed: {url}: {last_error}")


def _total_info_map(integration):
    return {
        item.get("code"): item.get("value")
        for item in integration.get("totalInfos", [])
        if item.get("code")
    }


def fetch_naver_korea_close(ticker, expected_trade_date=None):
    polling_url = f"https://polling.finance.naver.com/api/realtime/domestic/stock/{ticker}"
    integration_url = f"https://m.stock.naver.com/api/stock/{ticker}/integration"
    polling = _request_json(polling_url)
    items = polling.get("datas") or []
    if not items:
        raise ValueError(f"{ticker}: Naver polling data 없음")
    item = items[0]
    integration = _request_json(integration_url)

    price = _number(item.get("closePriceRaw"))
    local_traded_at = item.get("localTradedAt")
    trade_date = local_traded_at[:10].replace("-", "") if local_traded_at else None
    if expected_trade_date and trade_date != expected_trade_date:
        raise ValueError(f"{ticker}: 기대일={expected_trade_date}, 조회일={trade_date} (stale/휴장일 가능)")

    flow = next(
        (row for row in integration.get("dealTrendInfos", []) if row.get("bizdate") == trade_date),
        None,
    )
    foreign_qty = _number(flow.get("foreignerPureBuyQuant")) if flow else None
    institution_qty = _number(flow.get("organPureBuyQuant")) if flow else None
    info = _total_info_map(integration)
    week52_high = _number(info.get("highPriceOf52Weeks"))
    week52_low = _number(info.get("lowPriceOf52Weeks"))

    market_code = (item.get("stockExchangeType") or {}).get("code")
    market = {"KS": "KOSPI", "KQ": "KOSDAQ"}.get(market_code, market_code or "UNKNOWN")
    market_cap = _number(item.get("marketValueFullRaw"))
    volume = _number(item.get("accumulatedTradingVolumeRaw"))
    traded_value = _number(item.get("accumulatedTradingValueRaw"))
    has_trade_data = volume is not None and traded_value is not None
    return {
        "id": f"SNAP_KR_{ticker}_{trade_date}",
        "market": "KR",
        "sub_market": market,
        "instrument_id": ticker,
        "name": item.get("stockName") or integration.get("stockName") or ticker,
        "as_of": local_traded_at or datetime.now(timezone.utc).isoformat(),
        "trade_date": trade_date,
        "market_status": item.get("marketStatus"),
        "price": price,
        "return_pct": _number(item.get("fluctuationsRatioRaw")),
        "market_cap": market_cap,
        "volume": volume,
        "traded_value": traded_value,
        "traded_value_growth": None,
        "open": _number(item.get("openPriceRaw")),
        "high": _number(item.get("highPriceRaw")),
        "low": _number(item.get("lowPriceRaw")),
        "foreign_net_quantity": foreign_qty,
        "institution_net_quantity": institution_qty,
        "foreign_net": foreign_qty * price if foreign_qty is not None and price is not None else None,
        "institution_net": institution_qty * price if institution_qty is not None and price is not None else None,
        "flow_value_method": "ESTIMATED_KRW_FROM_NET_QUANTITY_X_CLOSE",
        "program_net": None,
        "week52_high": week52_high,
        "week52_low": week52_low,
        "currency": "KRW",
        "data_source": "NAVER_FINANCE",
        "source_urls": [polling_url, integration_url],
        "quality": (
            "ACTUAL_CLOSE_WITH_ESTIMATED_FLOW_VALUE"
            if has_trade_data and market_cap is not None
            else ("PARTIAL" if has_trade_data else "MISSING_NO_TRADING_DATA")
        ),
    }


def fetch_naver_korea_close_snapshot(tickers, expected_trade_date=None, max_workers=8):
    """여러 종목을 조회한다. 일부 실패가 전체 평가 생성을 막지 않도록 MISSING row를 남긴다."""
    ordered = list(dict.fromkeys(tickers))
    rows_by_ticker = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_naver_korea_close, ticker, expected_trade_date): ticker
            for ticker in ordered
        }
        for future in as_completed(futures):
            ticker = futures[future]
            try:
                rows_by_ticker[ticker] = future.result()
            except Exception as exc:
                rows_by_ticker[ticker] = {
                    "id": f"SNAP_KR_{ticker}_{expected_trade_date or 'UNKNOWN'}",
                    "market": "KR",
                    "sub_market": None,
                    "instrument_id": ticker,
                    "name": ticker,
                    "as_of": datetime.now(timezone.utc).isoformat(),
                    "trade_date": expected_trade_date,
                    "price": None,
                    "return_pct": None,
                    "market_cap": None,
                    "volume": None,
                    "traded_value": None,
                    "foreign_net": None,
                    "institution_net": None,
                    "currency": "KRW",
                    "data_source": "NAVER_FINANCE",
                    "quality": "MISSING",
                    "error": str(exc),
                }
    return [rows_by_ticker[ticker] for ticker in ordered]
