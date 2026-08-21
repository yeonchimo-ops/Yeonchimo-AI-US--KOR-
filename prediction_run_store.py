# PHASE 3 — PREDICTION_RUN 불변 저장소 (명세 1.2 "07:00 예상값은 사후 수정하지 않는다",
# 15장 "이 시점의 입력·출력·모델 버전을 불변 스냅샷으로 저장한다").
# 같은 trade_date로 두 번 저장을 시도하면 기본적으로 거부한다 — force=True로만 덮어쓸 수 있고,
# 그 경우에도 이전 파일을 .superseded로 보존해 이력이 사라지지 않게 한다.

import json
from pathlib import Path
from datetime import datetime, timezone

RUN_DIR = Path(__file__).parent / "data" / "prediction_runs"

SPEC_VERSION = "1.0.0"
MODEL_VERSION = "phase4-korea-expected-v1"


def _run_path(trade_date):
    return RUN_DIR / f"prediction_run_{trade_date}.json"


def save_prediction_run(
    trade_date,
    us_sector_scores,
    sox_confirmation,
    input_cutoff,
    force=False,
    korea_expected_records=None,
    korea_expected_edges=None,
):
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    path = _run_path(trade_date)

    if path.exists() and not force:
        raise FileExistsError(
            f"trade_date={trade_date}의 07:00 예상값이 이미 저장되어 있습니다 ({path}). "
            f"명세 1.2/15장에 따라 사후 수정이 금지되어 있습니다. "
            f"의도적으로 재계산해야 하면 force=True로 호출하세요 (이전 파일은 .superseded로 보존됩니다)."
        )

    if path.exists() and force:
        superseded_path = path.with_suffix(".superseded." + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json")
        path.rename(superseded_path)

    run_id = f"RUN_{trade_date}_{datetime.now(timezone.utc).strftime('%H%M%S%fZ')}"
    generated_at = datetime.now(timezone.utc).isoformat()

    score_records = [
        {
            "prediction_run_id": run_id,
            "entity_type": "US_MASTER_SECTOR",
            "entity_id": sid,
            "score_type": "US_SECTOR",
            "score": row["score"],
            "rank": None,  # 아래에서 채움
            "components": row["components_normalized"],
            "components_raw": row["components_raw"],
            "data_quality": row["data_quality"],
        }
        for sid, row in us_sector_scores.items()
    ]

    ranked = sorted([r for r in score_records if r["score"] is not None], key=lambda r: -r["score"])
    for i, r in enumerate(ranked, start=1):
        r["rank"] = i

    payload = {
        "prediction_run": {
            "id": run_id,
            "trade_date": trade_date,
            "generated_at": generated_at,
            "mapping_version": SPEC_VERSION,
            "model_version": MODEL_VERSION,
            "input_cutoff": input_cutoff,
            "status": "IMMUTABLE",
        },
        "us_sector_score_records": score_records,
        "sox_confirmation": sox_confirmation,
        "korea_expected_records": korea_expected_records or [],
        "korea_expected_edges": korea_expected_edges or [],
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return path, run_id


def load_prediction_run(trade_date):
    path = _run_path(trade_date)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
