"""16:00 한국 장마감 평가를 날짜별 불변 파일로 보존한다."""

from datetime import datetime, timezone
import json
from pathlib import Path


EVALUATION_DIR = Path(__file__).parent / "data" / "actual_evaluations"


def evaluation_path(korea_trade_date):
    return EVALUATION_DIR / f"actual_evaluation_{korea_trade_date}.json"


def save_actual_evaluation(korea_trade_date, payload, force=False):
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    path = evaluation_path(korea_trade_date)
    if path.exists() and not force:
        raise FileExistsError(
            f"korea_trade_date={korea_trade_date} 장마감 평가가 이미 존재합니다 ({path}). "
            "날짜별 결과는 덮어쓰지 않습니다. 의도적인 재수집은 --force를 사용하세요."
        )
    if path.exists() and force:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path.rename(path.with_suffix(f".superseded.{stamp}.json"))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return path
