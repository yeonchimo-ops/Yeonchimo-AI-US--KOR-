# PHASE 3 부가기능 — 미국국채 수익률(2Y/10Y/30Y) 미니차트.
# Naver에는 이 데이터를 안정적으로 주는 페이지를 찾지 못해 yfinance를 쓴다 — 같은 프로젝트의
# market_intelligence_v3/global_overnight.py도 동일한 이유로 미국채는 yfinance(^TNX 등)를 쓴다.

import os
import sys
from datetime import datetime, timezone

import yfinance as yf

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# us_adapter.py와 동일한 클라우드(CCR) 프록시 우회 패치 — 별도 모듈이라 중복 적용해둔다.
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
        pass

TREASURIES = [
    {"ticker": "2YY=F", "name": "미국채 2년"},   # Yahoo에 현물 2년물이 없어 CBOT 선물로 대체
    {"ticker": "^TNX", "name": "미국채 10년"},
    {"ticker": "^TYX", "name": "미국채 30년"},
]


def fetch_us_treasury_yields():
    """html_report.py의 render_sparkline_svg가 기대하는 형식({name, ticker, status, price,
    change, change_pct, sparkline, as_of_bar})으로 반환한다. price/change 단위는 %(수익률)이고,
    change는 %p(=bp/100)이지 상대변화율이 아니다 — 채권수익률 관례를 따른다."""
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    for t in TREASURIES:
        ticker = t["ticker"]
        try:
            h = yf.Ticker(ticker).history(period="10d")
            h = h.dropna(subset=["Close"])
            if len(h) < 2:
                rows.append({"name": t["name"], "ticker": ticker, "status": "MISSING"})
                continue
            closes = [round(float(c), 3) for c in h["Close"]]
            price = closes[-1]
            change = round(price - closes[-2], 3)
            change_pct = change  # 수익률 자체가 %이므로 diff가 곧 %p 변화
            rows.append({
                "name": t["name"], "ticker": ticker, "status": "ACTUAL",
                "price": price, "change": change, "change_pct": change_pct,
                "sparkline": closes, "as_of_bar": now, "source": "yfinance", "unit": "%",
            })
        except Exception as e:
            rows.append({"name": t["name"], "ticker": ticker, "status": "MISSING", "error": str(e)})
    return rows


if __name__ == "__main__":
    for r in fetch_us_treasury_yields():
        print(r["name"], r["status"], r.get("price"), r.get("change"))
