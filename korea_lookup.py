# 한국 종목명 -> 티커 정규화
# 신뢰 가능한 종목마스터: market_intelligence_v3/config/korea_watch_groups.yaml
# (2026-08-16 네이버 실시간 API로 68개 종목코드 전수 기술 검증 완료된 파일 — project_stock_market_automation.md 참고)
#
# 규칙: 이 파일에 없는 이름은 절대 추측 코드로 채우지 않는다. null + REQUIRED_BEFORE_IMPORT로 남기고
# resolve report에 기록한다 (PHASE 1은 실시간 KRX/공식 조회를 하지 않으므로 로컬 신뢰 소스만 사용).

from pathlib import Path
import json
import yaml

TRUSTED_SOURCE_PATH = (
    Path(__file__).parent.parent / "market_intelligence_v3" / "config" / "korea_watch_groups.yaml"
)
USER_VERIFIED_PATH = Path(__file__).parent / "data" / "user_verified_tickers.json"

# 표기가 다르지만 동일 종목임이 확실한 별칭만 등록한다 (코드를 추측하는 것이 아니라
# 신뢰 소스에 이미 존재하는 항목의 표기 차이를 흡수하는 것 뿐이다).
ALIAS_MAP = {
    "삼성SDS": "삼성에스디에스",
    "LG CNS": "LG씨엔에스",
    "포스코홀딩스": "POSCO홀딩스",
    "한국항공우주": "한국항공우주(KAI)",
    "LIG넥스원": "LIG디펜스앤에어로스페이스(구 LIG넥스원)",
}


def load_trusted_name_to_ticker():
    """korea_watch_groups.yaml 전체를 훑어서 {종목명: 티커} 딕셔너리를 만든다.
    같은 이름이 여러 그룹에 중복 등장해도(예: 삼성전자) 티커는 동일하므로 문제 없다."""
    with open(TRUSTED_SOURCE_PATH, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    name_to_ticker = {}
    for group in raw["watch_groups"].values():
        for stock in group["stocks"]:
            name_to_ticker[str(stock["name"])] = str(stock["ticker"])

    for alias, canonical in ALIAS_MAP.items():
        if canonical in name_to_ticker:
            name_to_ticker[alias] = name_to_ticker[canonical]

    return name_to_ticker


def load_user_verified_name_to_ticker():
    """연치모님이 네이버증권에서 직접 확인해 알려준 종목코드 (data/user_verified_tickers.json).
    명세서 표기(예: 'BH')와 실제 종목명(예: '비에이치') 둘 다로 조회 가능하게 등록한다."""
    if not USER_VERIFIED_PATH.exists():
        return {}
    with open(USER_VERIFIED_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    name_to_ticker = {}
    for spec_label, info in raw.get("entries", {}).items():
        name_to_ticker[spec_label] = info["ticker"]
        if info.get("name"):
            name_to_ticker[info["name"]] = info["ticker"]
    return name_to_ticker


NAME_TO_TICKER = load_trusted_name_to_ticker()
# 사용자 직접 검증값이 있으면 신뢰 yaml보다 우선 적용(더 최신/더 직접적인 확인이므로).
NAME_TO_TICKER.update(load_user_verified_name_to_ticker())


def resolve(korea_name):
    """(ticker, status) 튜플을 반환한다. 없으면 (None, 'REQUIRED_BEFORE_IMPORT')."""
    ticker = NAME_TO_TICKER.get(korea_name)
    if ticker:
        return ticker, "RESOLVED"
    return None, "REQUIRED_BEFORE_IMPORT"
