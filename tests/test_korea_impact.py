import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))

from score_engine.korea_actual import build_actual_evaluation, compute_korea_actual_scores
from score_engine.korea_expected import compute_korea_expected


def mapping(mapping_id, sector, us_ticker, kr_ticker="005930", kr_name="삼성전자", mapping_type="CORE"):
    return {
        "id": mapping_id,
        "us_sector_context_id": sector,
        "us_ticker": us_ticker,
        "korea_ticker": kr_ticker,
        "korea_name": kr_name,
        "ticker_resolution_status": "RESOLVED",
        "mapping_type": mapping_type,
        "initial_weight": 0.85,
        "effective_weight": 0.85,
        "status": "CONFIRMED_USER",
        "is_active": True,
        "priority": 1,
        "transmission_paths": ["AI", "HBM"],
    }


def test_same_us_source_in_two_sectors_is_counted_once():
    mappings = [
        mapping("M1", "US_01_M7", "TSLA"),
        mapping("M2", "US_16_EV", "TSLA"),
    ]
    scores = {
        "US_01_M7": {"score": 80},
        "US_16_EV": {"score": 75},
    }
    expected, edges = compute_korea_expected(
        mappings,
        scores,
        [{"instrument_id": "TSLA", "return_pct": 4.0, "traded_value": 100}],
    )
    assert expected[0]["independent_source_count"] == 1
    assert len([edge for edge in edges if edge["counted_in_expected"]]) == 1
    assert any(edge["exclusion_reason"] == "DUPLICATE_SOURCE_MEMBERSHIP" for edge in edges)


def test_soxl_soxs_are_confirmation_not_independent_expected_sources():
    mappings = [
        mapping("SOXL1", "US_13_SEMI_ETF", "SOXL"),
        mapping("SOXS1", "US_13_SEMI_ETF", "SOXS"),
    ]
    expected, edges = compute_korea_expected(
        mappings,
        {"US_13_SEMI_ETF": {"score": 90}},
        [
            {"instrument_id": "SOXL", "return_pct": 5.0},
            {"instrument_id": "SOXS", "return_pct": -5.0},
        ],
    )
    assert expected[0]["independent_source_count"] == 0
    assert all(edge["signal_role"] == "CONFIRMATION" for edge in edges)
    assert all(not edge["counted_in_expected"] for edge in edges)


def test_actual_score_uses_close_and_money_when_growth_is_missing():
    rows = [
        {
            "instrument_id": "A", "name": "A", "quality": "ACTUAL", "return_pct": 5,
            "traded_value": 1000, "traded_value_growth": None, "foreign_net": 50,
            "institution_net": 20, "price": 100, "low": 90, "high": 100,
        },
        {
            "instrument_id": "B", "name": "B", "quality": "ACTUAL", "return_pct": -2,
            "traded_value": 100, "traded_value_growth": None, "foreign_net": -30,
            "institution_net": -10, "price": 90, "low": 90, "high": 100,
        },
    ]
    actual = compute_korea_actual_scores(rows)
    assert actual[0]["korea_ticker"] == "A"
    assert actual[0]["actual_score"] > actual[1]["actual_score"]
    assert actual[0]["data_quality"] == "PARTIAL"
    assert actual[0]["used_weight"] == 0.85


def test_expected_actual_comparison_exposes_direction_match_and_sector_impact():
    mappings = [mapping("M1", "US_01_M7", "NVDA")]
    expected, _ = compute_korea_expected(
        mappings,
        {"US_01_M7": {"score": 80}},
        [{"instrument_id": "NVDA", "return_pct": 5.0, "traded_value": 1000}],
        sector_names={"US_01_M7": "M7"},
    )
    actual = compute_korea_actual_scores([
        {
            "instrument_id": "005930", "name": "삼성전자", "quality": "ACTUAL",
            "return_pct": 3.0, "traded_value": 1_000_000, "traded_value_growth": None,
            "foreign_net": 50_000, "institution_net": 20_000,
            "price": 103, "low": 99, "high": 104,
        }
    ])
    evaluation = build_actual_evaluation(expected, actual, {"US_01_M7": "M7"})
    assert evaluation["comparisons"][0]["direction_match"] is True
    assert evaluation["sector_impacts"][0]["us_sector_name"] == "M7"
    assert evaluation["sector_impacts"][0]["actual_leader"]["korea_name"] == "삼성전자"
