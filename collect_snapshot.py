# PHASE 2 — 수집 데모/검증 스크립트.
# PHASE 1의 full_dataset.json을 읽어 (a) 미국 65종목 전체 + 참고지표(BTC/ETH),
# (b) 한국 종목 중 priority=1(각 US-KR 관계에서 가장 핵심적인 대표종목) 대표 샘플만 수집한다.
# 한국 전체 유니버스(~250종목) 일괄 수집은 PHASE 3 스케줄러 몫으로 남겨둔다 — pykrx 로그인 세션을
# 인터랙티브 세션에서 과도하게 반복 호출하지 않기 위함 (project 메모리에 기록된 실제 장애 사례).

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from adapters.us_adapter import fetch_us_market_snapshot
from adapters.korea_adapter import fetch_korea_market_snapshot
from adapters.snapshot_store import save_snapshot

DATA_DIR = Path(__file__).parent / "data" / "generated"

YF_REFERENCE_MAP = {"BTC": "BTC-USD", "ETH": "ETH-USD"}


def load_dataset():
    with open(DATA_DIR / "full_dataset.json", "r", encoding="utf-8") as f:
        return json.load(f)


def collect(kr_sample_limit=40):
    ds = load_dataset()

    us_tickers = [s["ticker"] for s in ds["us_stocks"]]
    ref_tickers = [YF_REFERENCE_MAP[r["ticker"]] for r in ds["reference_indicators"]]
    print(f"[US] {len(us_tickers)}개 종목 + 참고지표 {len(ref_tickers)}개 수집 중...")
    us_rows = fetch_us_market_snapshot(us_tickers + ref_tickers)

    # priority=1 이면서 티커가 해결된 한국 종목만 대표 샘플로 뽑는다 (17개 섹터 전체를 대표하도록).
    priority1_tickers = []
    seen = set()
    for m in ds["us_korea_stock_mapping"]:
        if m["priority"] == 1 and m["korea_ticker"] and m["korea_ticker"] not in seen:
            seen.add(m["korea_ticker"])
            priority1_tickers.append(m["korea_ticker"])
    kr_tickers = priority1_tickers[:kr_sample_limit]
    print(f"[KR] priority=1 대표종목 {len(kr_tickers)}개 수집 중 (전체 유니버스는 PHASE 3 대상)...")
    kr_rows = fetch_korea_market_snapshot(kr_tickers)

    path = save_snapshot(us_rows, kr_rows, label="phase2_demo")
    print(f"저장 완료: {path}")

    us_ok = sum(1 for r in us_rows if r["quality"] not in ("MISSING",))
    kr_ok = sum(1 for r in kr_rows if r["quality"] not in ("MISSING",))
    print(f"US: {us_ok}/{len(us_rows)} 성공, KR: {kr_ok}/{len(kr_rows)} 성공")

    us_missing = [r["instrument_id"] for r in us_rows if r["quality"] == "MISSING"]
    kr_missing = [r["instrument_id"] for r in kr_rows if r["quality"] == "MISSING"]
    if us_missing:
        print("US MISSING:", us_missing)
    if kr_missing:
        print("KR MISSING:", kr_missing)

    return us_rows, kr_rows


if __name__ == "__main__":
    collect()
