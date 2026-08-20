# PHASE 3 부가기능 — 미국 3대 지수 미니차트를 finance.naver.com/world/에서 가져온다.
# (사용자 요청: 기존 프로젝트가 이미 쓰는 방식과 동일하게 Naver를 활용)
#
# /world/ 페이지 자체는 정적 HTML에 예시(구식) 값이 박혀있지만, 페이지 안의
# <script>에 실시간 데이터가 담긴 JS 객체(`americaData = jindo.$H({...})`)가 그대로 들어있어
# 그걸 정규식으로 뽑아 JSON으로 파싱한다. 스파크라인용 일별 시세는 종목별 상세페이지
# (/world/sise.naver?symbol=...)의 표를 파싱해서 얻는다.

import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

HEADERS = {"User-Agent": "Mozilla/5.0"}
WORLD_URL = "https://finance.naver.com/world/"
DETAIL_URL = "https://finance.naver.com/world/sise.naver?symbol={symbol}"

TARGET_INDICES = [
    {"symbol": "DJI@DJI", "name": "다우산업"},
    {"symbol": "NAS@IXIC", "name": "나스닥종합"},
    {"symbol": "SPI@SPX", "name": "S&P 500"},
]


def _fetch_america_data():
    resp = requests.get(WORLD_URL, headers=HEADERS, timeout=10)
    resp.encoding = "euc-kr"
    html = resp.text
    idx = html.find("americaData")
    if idx < 0:
        return {}
    start = html.find("{", idx)
    end = html.find(");", start)
    blob = html[start:end]
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return {}


def _fetch_daily_history(symbol, max_rows=10):
    resp = requests.get(DETAIL_URL.format(symbol=symbol), headers=HEADERS, timeout=10)
    resp.encoding = "euc-kr"
    soup = BeautifulSoup(resp.text, "html.parser")
    closes = []
    for tr in soup.select("table tr"):
        tds = tr.find_all("td")
        if len(tds) < 6:
            continue
        date_text = tds[0].get_text(strip=True)
        close_text = tds[1].get_text(strip=True).replace(",", "")
        if "." not in date_text or not close_text.replace(".", "").isdigit():
            continue
        try:
            closes.append(float(close_text))
        except ValueError:
            continue
        if len(closes) >= max_rows:
            break
    closes.reverse()  # 과거 -> 최신 순으로
    return closes


def fetch_us_major_indices_naver():
    """html_report.py가 기대하는 형식({name, ticker, status, price, change, change_pct,
    sparkline, as_of_bar})으로 반환한다 — us_adapter.fetch_us_major_indices()의 대체 구현."""
    america = _fetch_america_data()
    rows = []
    for target in TARGET_INDICES:
        data = america.get(target["symbol"])
        if not data:
            rows.append({"name": target["name"], "ticker": target["symbol"], "status": "MISSING"})
            continue
        try:
            history = _fetch_daily_history(target["symbol"])
        except Exception:
            history = []
        price = data["last"]
        if price not in history:
            history = history + [price]

        rows.append({
            "name": target["name"],
            "ticker": target["symbol"],
            "status": "ACTUAL",
            "price": price,
            "change": data["diff"],
            "change_pct": data["rate"],
            "sparkline": history,
            "as_of_bar": data.get("lastUpdTime", ""),
            "source": "finance.naver.com/world",
        })
    return rows


if __name__ == "__main__":
    for r in fetch_us_major_indices_naver():
        print(r["name"], r["status"], r.get("price"), r.get("change_pct"), "points:", len(r.get("sparkline", [])))
