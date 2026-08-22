# PHASE 2 — MARKET_SNAPSHOT 저장소
# 하루 단위 JSON 파일로 저장한다 (daily_tracker.py와 동일한 "DB 없이 파일 하나" 철학).
# 시각은 저장은 UTC(as_of), 표시는 Asia/Seoul 원칙(명세 11.3)에 맞춰 as_of를 ISO-8601 UTC로 남긴다.

import json
from pathlib import Path
from datetime import datetime, timezone

SNAPSHOT_DIR = Path(__file__).parent.parent / "data" / "snapshots"


def save_snapshot(us_rows, kr_rows, label=None, trade_date=None):
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_date = trade_date or datetime.now(timezone.utc).strftime("%Y%m%d")
    label = label or "manual"
    path = SNAPSHOT_DIR / f"snapshot_{snapshot_date}_{label}.json"

    payload = {
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        "us_count": len(us_rows),
        "kr_count": len(kr_rows),
        "us_snapshots": us_rows,
        "kr_snapshots": kr_rows,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path
