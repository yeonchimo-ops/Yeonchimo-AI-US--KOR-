# PHASE 3 — US CLOSE & 07:00 PIPELINE 오케스트레이션
# 미국 마감 데이터를 모아 US Sector Score를 계산하고, SOX confirmation을 붙여
# trade_date 하루에 한 번만 저장되는 불변 PREDICTION_RUN으로 남긴다.
# 실제 07:00 KST 자동 실행(스케줄러 등록)은 이 스크립트 실행과는 별개의 결정이라 여기 포함하지 않았다.

import json
import os
import sys
import warnings
from pathlib import Path
from datetime import datetime, timezone

# curl_cffi(브라우저 TLS 지문)가 CCR 클라우드 프록시에서 TLS reset("curl: (35)")을 당해
# 모든 티커 다운로드가 실패한다. yfinance 공식 스위치로 plain requests 백엔드를 강제한다
# (프록시 CA는 REQUESTS_CA_BUNDLE로 이미 신뢰됨). 반드시 yfinance import 전에 설정해야 한다.
if os.environ.get("CCR_AGENT_PROXY_ENABLED") or os.environ.get("HTTPS_PROXY"):
    os.environ.setdefault("YF_DISABLE_CURL_CFFI", "1")

sys.path.insert(0, str(Path(__file__).parent))
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore", category=DeprecationWarning)

import yfinance as yf

import master_data
from adapters.us_adapter import fetch_us_market_snapshot
from score_engine.us_sector_score import compute_us_sector_scores, strength_label
from score_engine.sox_confirmation import compute_sox_confirmation
from prediction_run_store import save_prediction_run, load_prediction_run
from adapters.snapshot_store import save_snapshot
from score_engine.korea_expected import compute_korea_expected


def fetch_sox_index_return():
    try:
        h = yf.Ticker("^SOX").history(period="1mo")
        h = h.dropna(subset=["Close"])
        if len(h) < 2:
            return None
        return round((h["Close"].iloc[-1] / h["Close"].iloc[-2] - 1) * 100, 4)
    except Exception:
        return None


def run(trade_date=None, force=False):
    trade_date = trade_date or datetime.now(timezone.utc).strftime("%Y%m%d")
    input_cutoff = datetime.now(timezone.utc).isoformat()

    all_us_tickers = sorted({t for s in master_data.US_MASTER_SECTORS for t in s["us_stocks"]})
    print(f"[1/4] US {len(all_us_tickers)}개 종목 스냅샷 수집 중...")
    us_rows = fetch_us_market_snapshot(all_us_tickers)
    snap_path = save_snapshot(us_rows, [], label="0700", trade_date=trade_date)
    print(f"    종목별 스냅샷 저장: {snap_path}")

    print("[2/4] ^SOX 지수 조회 중...")
    sox_return = fetch_sox_index_return()

    print("[3/4] US Sector Score 계산 중 (17개 섹터, Catalyst는 PHASE5 대상이라 제외/재배분)...")
    scores = compute_us_sector_scores(master_data.US_MASTER_SECTORS, us_rows)

    by_ticker = {r["instrument_id"]: r for r in us_rows}
    sox_conf = compute_sox_confirmation(sox_return, by_ticker.get("SOXL"), by_ticker.get("SOXS"))

    print("[4/5] 고정 Master Mapping으로 Korea Expected 계산 중...")
    with open(Path(__file__).parent / "data" / "generated" / "us_korea_stock_mapping.json", encoding="utf-8") as f:
        mappings = json.load(f)
    sector_names = {sector["id"]: sector["name"] for sector in master_data.US_MASTER_SECTORS}
    korea_expected, expected_edges = compute_korea_expected(
        mappings, scores, us_rows, sector_names=sector_names, sox_confirmation=sox_conf
    )

    print(f"[5/5] trade_date={trade_date} 불변 스냅샷 저장 중 (force={force})...")
    path, run_id = save_prediction_run(
        trade_date,
        scores,
        sox_conf,
        input_cutoff,
        force=force,
        korea_expected_records=korea_expected,
        korea_expected_edges=expected_edges,
        us_stock_snapshots=us_rows,
    )

    print(f"\n저장 완료: {path}")
    print(f"run_id: {run_id}")
    print("\n" + "=" * 78)
    print(f"{'섹터':<20}{'점수':>8}  {'등급':<14}{'품질':<10}{'구성원(수집/전체)'}")
    print("=" * 78)
    for row in sorted(scores.values(), key=lambda r: r["display_order"]):
        member_info = f"{row['member_count']}/{row['member_count'] + row['member_count_missing']}"
        score_str = f"{row['score']:.2f}" if row["score"] is not None else "MISSING"
        print(f"{row['name']:<20}{score_str:>8}  {row['strength_label']:<14}{row['data_quality']:<10}{member_info}")

    print("\n" + "=" * 78)
    print("SOX / SOXL / SOXS 확인 신호 (반도체 섹터 보조 필드, 명세 8장)")
    print("=" * 78)
    for k, v in sox_conf.items():
        print(f"  {k}: {v}")

    print("\nKorea Expected TOP 10")
    for row in korea_expected[:10]:
        print(f"  {row['rank']:>2}. {row['korea_name']}({row['korea_ticker']}) "
              f"{row['expected_score']:.2f} {row['expected_direction']}")

    return path, run_id


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="YYYYMMDD, 기본값 오늘(UTC)")
    parser.add_argument("--force", action="store_true", help="이미 저장된 trade_date를 의도적으로 재계산")
    args = parser.parse_args()
    run(trade_date=args.date, force=args.force)
