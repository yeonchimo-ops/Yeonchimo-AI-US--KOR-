"""16:00 KST 한국 장마감 평가 파이프라인.

07:30 prediction file은 수정하지 않고, 날짜별 actual_evaluation 파일을 별도로 쌓는다.
과거 PHASE 3 prediction처럼 한국 예상값이 저장되지 않은 경우에는 동일한 불변 미국
snapshot으로 재구성하되, 사후 예측이 아님을 metadata에 명시한다.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from actual_evaluation_store import evaluation_path, save_actual_evaluation
from adapters.naver_korea_close_adapter import fetch_naver_korea_close_snapshot
from score_engine.korea_actual import build_actual_evaluation, compute_korea_actual_scores
from score_engine.korea_expected import compute_korea_expected


ROOT = Path(__file__).parent


def _load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _latest_us_trade_date():
    files = sorted((ROOT / "data" / "prediction_runs").glob("prediction_run_*.json"))
    if not files:
        raise FileNotFoundError("prediction_run 파일이 없습니다")
    return files[-1].stem.rsplit("_", 1)[-1]


def _dominant_trade_date(rows):
    dates = [
        row.get("trade_date")
        for row in rows
        if not str(row.get("quality", "MISSING")).startswith("MISSING") and row.get("trade_date")
    ]
    if not dates:
        raise RuntimeError("한국 장마감 유효 데이터가 없습니다")
    return max(set(dates), key=dates.count)


def run(us_trade_date=None, korea_trade_date=None, force=False):
    us_trade_date = us_trade_date or _latest_us_trade_date()
    prediction_path = ROOT / "data" / "prediction_runs" / f"prediction_run_{us_trade_date}.json"
    snapshot_path = ROOT / "data" / "snapshots" / f"snapshot_{us_trade_date}_0700.json"
    prediction = _load_json(prediction_path)
    snapshot = _load_json(snapshot_path)
    mappings = _load_json(ROOT / "data" / "generated" / "us_korea_stock_mapping.json")
    sectors = _load_json(ROOT / "data" / "generated" / "us_master_sectors.json")
    sector_names = {row["id"]: row["name"] for row in sectors}

    if prediction.get("korea_expected_records"):
        expected = prediction["korea_expected_records"]
        expected_origin = "IMMUTABLE_0730_PREDICTION"
    else:
        expected, _ = compute_korea_expected(
            mappings,
            prediction["us_sector_score_records"],
            snapshot["us_snapshots"],
            sector_names=sector_names,
            sox_confirmation=prediction.get("sox_confirmation"),
        )
        expected_origin = "RECONSTRUCTED_AFTER_CLOSE_FROM_IMMUTABLE_US_SNAPSHOT"

    tickers = sorted({row["korea_ticker"] for row in mappings if row.get("ticker_resolution_status") == "RESOLVED"})
    print(f"[1/4] Naver Finance 한국 Mapping Target {len(tickers)}개 장마감 수집...")
    korea_rows = fetch_naver_korea_close_snapshot(tickers, expected_trade_date=korea_trade_date)
    resolved_korea_date = korea_trade_date or _dominant_trade_date(korea_rows)
    if korea_trade_date is None:
        today_seoul = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d")
        if resolved_korea_date != today_seoul:
            print(
                f"오늘({today_seoul}) 신규 장마감 데이터가 없습니다. "
                f"네이버 최근 거래일={resolved_korea_date}; 휴장일로 보고 저장을 건너뜁니다."
            )
            return None
    existing_path = evaluation_path(resolved_korea_date)
    if existing_path.exists() and not force:
        print(f"{resolved_korea_date} 장마감 평가가 이미 존재합니다. 불변 파일을 유지하고 종료합니다: {existing_path}")
        return existing_path
    korea_rows = [row for row in korea_rows if row.get("trade_date") == resolved_korea_date or row.get("quality") == "MISSING"]
    ok_count = sum(not str(row.get("quality", "MISSING")).startswith("MISSING") for row in korea_rows)
    print(f"[2/4] {resolved_korea_date} 유효 종목 {ok_count}/{len(korea_rows)} — Korea Actual 계산...")
    actual = compute_korea_actual_scores(korea_rows)
    evaluation = build_actual_evaluation(expected, actual, sector_names)
    print("[3/4] US Sector → Korea Close 연결 정합도 집계...")

    payload = {
        "evaluation_run": {
            "id": f"EVAL_{resolved_korea_date}_{datetime.now(timezone.utc).strftime('%H%M%S%fZ')}",
            "source_prediction_run_id": prediction["prediction_run"]["id"],
            "source_us_trade_date": us_trade_date,
            "korea_trade_date": resolved_korea_date,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "expected_origin": expected_origin,
            "status": "FINAL_CLOSE_EVALUATION",
            "data_source": "NAVER_FINANCE",
            "causality_notice": "사용자 확정 Mapping 기반 방향·강도 정합도이며 통계적 인과관계 확정값이 아님",
            "flow_value_notice": "외국인/기관 순매수 금액은 네이버 제공 순매수 수량×종가 추정값",
        },
        "summary": {
            "mapping_target_count": len(tickers),
            "collected_count": ok_count,
            "missing_count": len(korea_rows) - ok_count,
            "expected_count": len(expected),
            "actual_count": len(actual),
        },
        "korea_expected_records": expected,
        "korea_actual_records": actual,
        **evaluation,
    }
    print("[4/4] 날짜별 불변 장마감 평가 저장...")
    path = save_actual_evaluation(resolved_korea_date, payload, force=force)
    print(f"저장 완료: {path}")
    print(f"예상 원본: {expected_origin}")
    print(f"섹터 영향 비교: {len(evaluation['sector_impacts'])}개 / 종목 비교: {len(evaluation['comparisons'])}개")
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--us-date", default=None, help="연결할 미국 거래일 YYYYMMDD")
    parser.add_argument("--korea-date", default=None, help="검증할 한국 거래일 YYYYMMDD")
    parser.add_argument("--force", action="store_true", help="기존 장마감 파일을 superseded로 보존 후 재수집")
    args = parser.parse_args()
    run(args.us_date, args.korea_date, args.force)
