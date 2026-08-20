# PHASE 1 필수 단위 테스트 (명세 11.2, Test 1~17)
# 실행: cd ai_market && python -m pytest tests/ -v

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

OUT_DIR = Path(__file__).parent.parent / "data" / "generated"


def _load(name):
    with open(OUT_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def us_sectors():
    return _load("us_master_sectors.json")


@pytest.fixture(scope="module")
def us_membership():
    return _load("us_stock_sector_membership.json")


@pytest.fixture(scope="module")
def stock_mapping():
    return _load("us_korea_stock_mapping.json")


def _targets_for(stock_mapping, us_ticker, us_sector_context_id=None):
    rows = [m for m in stock_mapping if m["us_ticker"] == us_ticker]
    if us_sector_context_id:
        rows = [m for m in rows if m["us_sector_context_id"] == us_sector_context_id]
    rows.sort(key=lambda m: m["priority"])
    return [m["korea_name"] for m in rows]


# Test 1: 미국 Master Sector = 정확히 17개
def test_01_master_sector_count(us_sectors):
    assert len(us_sectors) == 17


# Test 2: TSLA는 M7 + 전기차 두 그룹에 모두 포함
def test_02_tsla_dual_membership(us_membership):
    sectors = {m["us_sector_id"] for m in us_membership if m["us_ticker"] == "TSLA"}
    assert sectors == {"US_01_M7", "US_16_EV"}


# Test 3: NEE는 태양광 + 풍력 두 그룹에 모두 포함
def test_03_nee_dual_membership(us_membership):
    sectors = {m["us_sector_id"] for m in us_membership if m["us_ticker"] == "NEE"}
    assert sectors == {"US_05_SOLAR", "US_06_WIND"}


# Test 4: 풍력 미국 전 종목의 한국 priority 1은 SK이터닉스
def test_04_wind_priority1_is_sk_eternix(stock_mapping):
    # AGR(Avangrid)은 2026-08-21 사용자 승인으로 삭제됨 — 2024년 Iberdrola의 비상장화로
    # 실제 delisted된 것을 PHASE2 라이브 수집(yfinance)에서 확인 (master_data.REMOVED_TICKERS_LOG).
    wind_us_tickers = ["NEE", "GE", "CWEN", "BEP"]
    for ticker in wind_us_tickers:
        targets = _targets_for(stock_mapping, ticker, "US_06_WIND")
        assert targets, f"{ticker} 풍력 매핑이 비어있음"
        assert targets[0] == "SK이터닉스", f"{ticker} priority1={targets[0]}"


# Test 5: LLY 한국 우선순위 = 펩트론, 한미약품, 삼성바이오로직스, 에이비엘바이오
def test_05_lly_priority_order(stock_mapping):
    targets = _targets_for(stock_mapping, "LLY")
    assert targets == ["펩트론", "한미약품", "삼성바이오로직스", "에이비엘바이오"]


# Test 6: SKHY는 SK하이닉스, 삼성전자 외 다른 Target이 임의 추가되지 않았는지
def test_06_skhy_only_two_targets(stock_mapping):
    targets = _targets_for(stock_mapping, "SKHY")
    assert targets == ["SK하이닉스", "삼성전자"]


# Test 7 (명세 11.2 목록의 7번, 본문 4.2 금지규칙과 연결): MRVL 순서 확인
def test_07_mrvl_priority_order(stock_mapping):
    targets = _targets_for(stock_mapping, "MRVL")
    assert targets == ["SK하이닉스", "삼성전자", "이수페타시스", "ISC", "삼성전기"]


# Test 8: AVGO 순서 확인
def test_08_avgo_priority_order(stock_mapping):
    targets = _targets_for(stock_mapping, "AVGO")
    assert targets == ["삼성전자", "SK하이닉스", "이수페타시스", "가온칩스", "에이직랜드"]


# Test 9: 모든 광통신 미국 종목의 priority 1 = 성호전자
def test_09_optical_priority1_is_seongho(stock_mapping):
    optical_us_tickers = ["LITE", "COHR", "GLW", "CIEN"]
    for ticker in optical_us_tickers:
        targets = _targets_for(stock_mapping, ticker, "US_07_OPTICAL")
        assert targets[0] == "성호전자", f"{ticker} priority1={targets[0]}"


# Test 10: CRCL priority 1 = 카카오페이
def test_10_crcl_priority1_is_kakaopay(stock_mapping):
    targets = _targets_for(stock_mapping, "CRCL")
    assert targets[0] == "카카오페이"


# Test 11: SOXS 상승은 Korea 반도체에 negative confirmation으로 계산 (명세 8장)
# PHASE1은 실제 점수 계산 엔진을 구현하지 않으므로, 최소한 SOXS 매핑에 방향성 메모가
# 남아있는지(향후 Score Engine이 이 신호를 negative로 다룰 수 있는 근거 데이터가 있는지)만 검증한다.
def test_11_soxs_marked_as_negative_confirmation(stock_mapping):
    soxs_rows = [m for m in stock_mapping if m["us_ticker"] == "SOXS"]
    assert soxs_rows, "SOXS 매핑이 존재하지 않음"
    assert any("음의 방향" in "".join(p) for r in soxs_rows for p in [r["transmission_paths"]]), \
        "SOXS 매핑에 negative-confirmation 근거(음의 방향 표기)가 없음"


# Test 12: SOX와 SOXL/SOXS가 독립 점수로 중복 합산되지 않는다.
# PHASE1 범위에서는 Score Engine이 없으므로, 매핑 데이터 상 SOX 자체(지수)는 별도 US_STOCK으로
# 존재하지 않고 SOXL/SOXS만 반도체ETF 섹터에 속해 있음을 확인해 "중복 합산 리스크 원천 차단"을 검증한다.
def test_12_no_sox_index_duplicated_as_stock(us_sectors):
    semi_etf_sector = next(s for s in us_sectors if s["id"] == "US_13_SEMI_ETF")
    assert semi_etf_sector["us_stocks"] == ["SOXL", "SOXS"]
    assert "SOX" not in semi_etf_sector["us_stocks"]


# Test 13: 07:00 prediction snapshot은 09:00 이후 update할 수 없다.
# PHASE1은 스냅샷/스케줄러를 구현하지 않으므로 skip 처리하고 사유를 남긴다 (명세 9번 "아직 하지 말 것").
@pytest.mark.skip(reason="PHASE 1 범위 제외: 07:00 스냅샷/스케줄러는 PHASE 3에서 구현")
def test_13_prediction_snapshot_immutable():
    pass


# Test 14: DISABLED mapping은 점수에서 제외되지만 audit/history 조회에는 남는다.
# PHASE1 데이터에는 DISABLED 상태 레코드가 아직 없으므로(사용자가 아직 비활성화한 관계가 없음),
# is_active 필드와 status enum이 DISABLED를 지원하는 구조인지만 구조적으로 검증한다.
def test_14_disabled_status_supported_in_schema():
    from enums import MAPPING_STATUS
    assert "DISABLED" in MAPPING_STATUS


# Test 15: 시장 데이터 누락 시 가중치 재배분 + data_quality 저하.
# PHASE1은 실시간 시장데이터/Score Engine을 구현하지 않으므로 skip.
@pytest.mark.skip(reason="PHASE 1 범위 제외: Score Engine은 PHASE 3~4에서 구현")
def test_15_missing_data_reweight():
    pass


# Test 16: look-ahead 방지 (미래 시각 데이터가 07:00 예측에 안 들어감).
# PHASE1은 시각 기반 파이프라인이 없으므로 skip.
@pytest.mark.skip(reason="PHASE 1 범위 제외: 07:00 파이프라인은 PHASE 3에서 구현")
def test_16_no_lookahead():
    pass


# Test 17: 같은 원천 종목이 두 섹터에 속해도 수익률이 이중 합산되지 않는다.
# PHASE1에는 점수 계산 로직이 없으므로, 데이터 레벨에서 "이중 합산을 막을 수 있는 근거 구조"만 검증한다:
# TSLA/NEE 같은 중복 소속 종목이 membership에서 서로 다른 sector_id로 명확히 구분되어 있어야
# 이후 Score Engine이 섹터별로 독립 계산할 수 있다.
def test_17_dual_membership_distinguishable_by_sector(us_membership):
    tsla_rows = [m for m in us_membership if m["us_ticker"] == "TSLA"]
    sector_ids = [m["us_sector_id"] for m in tsla_rows]
    assert len(sector_ids) == len(set(sector_ids)), "TSLA membership에 동일 섹터 중복 행이 있음"


# ---- 추가: 명세 3.1/4장 금지 규칙에 대한 golden regression ----

def test_skhy_forbidden_targets_absent(stock_mapping):
    targets = _targets_for(stock_mapping, "SKHY")
    assert "한미반도체" not in targets
    assert "한화세미텍" not in targets


def test_mrvl_forbidden_targets_absent(stock_mapping):
    targets = _targets_for(stock_mapping, "MRVL")
    forbidden = {"가온칩스", "에이직랜드", "성호전자", "RF머트리얼즈", "오이솔루션", "대한광통신"}
    assert not (set(targets) & forbidden)
