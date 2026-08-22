# PHASE 3 단위 테스트 — 네트워크 호출 없이 순수 로직만 검증한다 (합성 데이터 사용).

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from score_engine.normalize import percentile_rank_0_100, reweight_for_missing
from score_engine.us_sector_score import compute_us_sector_scores, strength_label
from score_engine.sox_confirmation import compute_sox_confirmation


def test_percentile_rank_basic_ordering():
    ranks = percentile_rank_0_100({"a": 1, "b": 2, "c": 3})
    assert ranks["a"] < ranks["b"] < ranks["c"]
    assert ranks["c"] == 100.0
    assert ranks["a"] == 0.0


def test_percentile_rank_handles_missing():
    ranks = percentile_rank_0_100({"a": 1, "b": None, "c": 3})
    assert ranks["b"] is None
    assert ranks["a"] is not None and ranks["c"] is not None


def test_reweight_catalyst_missing_matches_spec_weights():
    # 명세 7.1: catalyst 10% 누락 시 나머지 90%(35/30/15/10)로 비례 재배분.
    components = [(0.35, 100.0), (0.30, 0.0), (0.15, 100.0), (0.10, 0.0), (0.10, None)]
    score, used_weight, quality = reweight_for_missing(components)
    assert used_weight == pytest.approx(0.90)
    assert quality == "PARTIAL"
    # (0.35*100 + 0.30*0 + 0.15*100 + 0.10*0) / 0.90
    assert score == pytest.approx((35 + 15) / 0.90, abs=0.01)


def test_reweight_all_missing_returns_missing():
    score, used_weight, quality = reweight_for_missing([(0.5, None), (0.5, None)])
    assert score is None
    assert quality == "MISSING"


def test_us_sector_score_all_members_present():
    sectors = [{"id": "S1", "name": "테스트섹터", "display_order": 1, "us_stocks": ["AAA", "BBB"]}]
    snapshot = [
        {"instrument_id": "AAA", "return_pct": 2.0, "market_cap": 100, "avg_volume_ratio": 1.5},
        {"instrument_id": "BBB", "return_pct": -1.0, "market_cap": 300, "avg_volume_ratio": 0.8},
    ]
    result = compute_us_sector_scores(sectors, snapshot)
    s1 = result["S1"]
    assert s1["member_count"] == 2
    assert s1["member_count_missing"] == 0
    assert s1["data_quality"] == "PARTIAL"  # catalyst가 항상 빠지므로 PHASE3에서는 항상 PARTIAL
    assert s1["score"] is not None
    assert 0 <= s1["score"] <= 100


def test_us_sector_score_missing_member_tracked():
    sectors = [{"id": "S1", "name": "테스트섹터", "display_order": 1, "us_stocks": ["AAA", "ZZZ_NO_DATA"]}]
    snapshot = [{"instrument_id": "AAA", "return_pct": 2.0, "market_cap": 100, "avg_volume_ratio": 1.5}]
    result = compute_us_sector_scores(sectors, snapshot)
    assert result["S1"]["member_count"] == 1
    assert result["S1"]["member_count_missing"] == 1


def test_strength_label_bands():
    assert strength_label(90) == "VERY_STRONG"
    assert strength_label(72) == "STRONG"
    assert strength_label(60) == "POSITIVE"
    assert strength_label(50) == "NEUTRAL"
    assert strength_label(35) == "WEAK"
    assert strength_label(10) == "VERY_WEAK"
    assert strength_label(None) == "MISSING"


def test_sox_confirmation_confirms_when_soxl_up_soxs_down():
    result = compute_sox_confirmation(1.0, {"return_pct": 2.0}, {"return_pct": -2.0})
    assert result["status"] == "CONFIRMS"
    assert result["adjustment"] > 0
    assert abs(result["adjustment"]) <= result["adjustment_cap"]


def test_sox_confirmation_contradicts_when_soxs_also_up():
    # SOX가 오르는데 SOXS(인버스)도 오르면 모순 신호 — 명세 4번 규칙 위반 상황을 감지해야 한다.
    result = compute_sox_confirmation(1.0, {"return_pct": 2.0}, {"return_pct": 2.0})
    assert result["status"] == "MIXED"


def test_sox_confirmation_adjustment_never_exceeds_cap():
    result = compute_sox_confirmation(5.0, {"return_pct": 15.0}, {"return_pct": -15.0})
    assert abs(result["adjustment"]) <= result["adjustment_cap"]


def test_sox_confirmation_missing_when_no_sox_index():
    result = compute_sox_confirmation(None, {"return_pct": 1.0}, {"return_pct": -1.0})
    assert result["status"] == "MISSING"


def test_prediction_run_immutable(tmp_path, monkeypatch):
    import prediction_run_store as store
    monkeypatch.setattr(store, "RUN_DIR", tmp_path)

    scores = {"S1": {"score": 50.0, "components_normalized": {}, "components_raw": {}, "data_quality": "PARTIAL"}}
    sox = {"status": "MISSING"}

    path1, run_id1 = store.save_prediction_run("20260101", scores, sox, "2026-01-01T00:00:00Z")
    assert path1.exists()

    with pytest.raises(FileExistsError):
        store.save_prediction_run("20260101", scores, sox, "2026-01-01T01:00:00Z")

    # force=True는 허용하되 이전 파일을 .superseded로 보존해야 한다.
    path2, run_id2 = store.save_prediction_run("20260101", scores, sox, "2026-01-01T02:00:00Z", force=True)
    superseded = list(tmp_path.glob("*.superseded.*.json"))
    assert len(superseded) == 1
    assert run_id1 != run_id2


def test_prediction_run_embeds_us_stock_snapshots(tmp_path, monkeypatch):
    import prediction_run_store as store
    monkeypatch.setattr(store, "RUN_DIR", tmp_path)
    scores = {"S1": {"score": 50.0, "components_normalized": {}, "components_raw": {}, "data_quality": "PARTIAL"}}
    snapshots = [{"instrument_id": "NVDA", "return_pct": 1.25}]

    path, _ = store.save_prediction_run(
        "20260102", scores, {"status": "MISSING"}, "2026-01-02T00:00:00Z",
        us_stock_snapshots=snapshots,
    )

    assert json.loads(path.read_text(encoding="utf-8"))["us_stock_snapshots"] == snapshots


def test_snapshot_filename_uses_explicit_trade_date(tmp_path, monkeypatch):
    import adapters.snapshot_store as store
    monkeypatch.setattr(store, "SNAPSHOT_DIR", tmp_path)

    path = store.save_snapshot([], [], label="0700", trade_date="20260103")

    assert path.name == "snapshot_20260103_0700.json"
