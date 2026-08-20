# PHASE 3 부가기능 — 환전고시환율/국제시장환율/유가·금시세를 finance.naver.com/marketindex/에서 가져온다.
# (사용자 요청: 미국 3대지수 밑에 이 3개 섹션도 추가)
#
# /world/와 달리 이 페이지는 각 항목이 서버에서 실시간 값으로 렌더링돼 있어 (2026-08-20 확인,
# 예: 미국 USD 1,396.10원) 별도 JS 데이터 블롭 없이 정적 HTML을 바로 파싱하면 된다.

import sys

import requests
from bs4 import BeautifulSoup

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

URL = "https://finance.naver.com/marketindex/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

LIST_IDS = {
    "exchange": "exchangeList",       # 환전 고시 환율
    "world_exchange": "worldExchangeList",  # 국제 시장 환율
    "oil_gold": "oilGoldList",        # 유가·금시세
}

SECTION_LABELS = {
    "exchange": "환전 고시 환율",
    "world_exchange": "국제 시장 환율",
    "oil_gold": "유가·금시세",
}


def _parse_list(ul):
    items = []
    if ul is None:
        return items
    for li in ul.find_all("li"):
        h3 = li.find("h3")
        name = h3.get_text(strip=True) if h3 else None
        head = li.find("div", class_="head_info")
        if not name or not head:
            continue
        val = head.find("span", class_="value")
        chg = head.find("span", class_="change")
        classes = head.get("class", [])
        direction = "up" if "point_up" in classes else ("down" if "point_dn" in classes else "flat")
        items.append({
            "name": name,
            "value": val.get_text(strip=True) if val else None,
            "change": chg.get_text(strip=True) if chg else None,
            "direction": direction,
        })
    return items


def fetch_market_index_snapshot():
    """{"exchange": [...], "world_exchange": [...], "oil_gold": [...]} 형태로 반환한다.
    실패 시 status=MISSING과 함께 빈 리스트를 준다 (부가기능이라 리포트 전체를 막지 않는다)."""
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=10)
        resp.encoding = "euc-kr"
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception:
        return {key: {"status": "MISSING", "items": []} for key in LIST_IDS}

    result = {}
    for key, list_id in LIST_IDS.items():
        items = _parse_list(soup.find("ul", id=list_id))
        result[key] = {"status": "ACTUAL" if items else "MISSING", "items": items}
    return result


if __name__ == "__main__":
    data = fetch_market_index_snapshot()
    for key, section in data.items():
        print(f"--- {SECTION_LABELS[key]} ({section['status']}) ---")
        for item in section["items"]:
            print(" ", item["name"], item["value"], item["change"], item["direction"])
