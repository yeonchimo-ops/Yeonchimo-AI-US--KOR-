# PHASE 1 Validation Script (명세 11.1)
# python validate.py 로 실행. 모든 체크를 통과해야 PHASE 1 완료 기준을 만족한다.

import json
import sys
from collections import defaultdict
from pathlib import Path

import master_data
from enums import MAPPING_STATUS, MAPPING_TYPE

OUT_DIR = Path(__file__).parent / "data" / "generated"
GOLDEN_PATH = Path(__file__).parent / "data" / "golden_confirmed_user_snapshot.json"


def load(name):
    with open(OUT_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


class Report:
    def __init__(self):
        self.results = []

    def check(self, name, passed, detail=""):
        self.results.append({"check": name, "passed": bool(passed), "detail": detail})

    def summary(self):
        total = len(self.results)
        failed = [r for r in self.results if not r["passed"]]
        return total, failed


def run():
    r = Report()

    us_sectors = load("us_master_sectors.json")
    us_stocks = load("us_stocks.json")
    us_membership = load("us_stock_sector_membership.json")
    korea_sectors = load("korea_master_sectors.json")
    korea_stocks = load("korea_stocks.json")
    stock_mapping = load("us_korea_stock_mapping.json")
    sector_mapping = load("us_korea_sector_mapping.json")

    # 1. US Master Sector 정확히 17개
    r.check("US Master Sector count == 17", len(us_sectors) == 17, f"actual={len(us_sectors)}")

    # 2. display_order 1~17 연속, 중복 없음
    orders = sorted(s["display_order"] for s in us_sectors)
    r.check("display_order == 1..17 연속/중복없음", orders == list(range(1, 18)), f"orders={orders}")

    # 3. 각 섹터 구성종목 누락 여부 (빈 섹터 없어야 함)
    empty_sectors = [s["name"] for s in us_sectors if not s.get("us_stocks")]
    r.check("모든 섹터에 구성종목 존재", len(empty_sectors) == 0, f"empty={empty_sectors}")

    # 4. ticker 형식 + delisted/alias 후보 flag
    bad_format = [t["ticker"] for t in us_stocks if not t["ticker"].isalnum()]
    r.check("US ticker 형식(영숫자)", len(bad_format) == 0, f"bad={bad_format}")
    flagged = [t["ticker"] for t in us_stocks if t.get("validation_warning")]
    r.check("[WARNING] 재검증 필요 US 티커 존재 (정상 — 명세 3.2 규정)", True,
            f"flagged={sorted(flagged)}")

    # 5. TSLA / NEE 중복 membership
    membership_by_ticker = defaultdict(list)
    for m in us_membership:
        membership_by_ticker[m["us_ticker"]].append(m["us_sector_id"])
    tsla_sectors = set(membership_by_ticker.get("TSLA", []))
    nee_sectors = set(membership_by_ticker.get("NEE", []))
    r.check("TSLA는 M7+전기차 중복 소속", tsla_sectors == {"US_01_M7", "US_16_EV"}, f"actual={tsla_sectors}")
    r.check("NEE는 태양광+풍력 중복 소속", nee_sectors == {"US_05_SOLAR", "US_06_WIND"}, f"actual={nee_sectors}")

    # 6. 한국 Target 미해결 목록 (실패 아님 — 명세가 요구하는 정상적 REQUIRED_BEFORE_IMPORT 상태)
    unresolved = [m for m in stock_mapping if m["ticker_resolution_status"] != "RESOLVED"]
    r.check(f"[INFO] 미해결 Korea ticker {len(unresolved)}건 (import 전 정규화 필요, 명세 10.2)", True,
            f"names={sorted({m['korea_name'] for m in unresolved})}")

    # 한국 Target 내부 중복(같은 US_ticker+context 안에서 같은 korea_name 두 번 나오면 오류)
    dup_targets = []
    by_group = defaultdict(list)
    for m in stock_mapping:
        key = (m["us_ticker"], m["us_sector_context_id"], tuple(m["transmission_paths"]))
        by_group[key].append(m)
    for key, rows in by_group.items():
        names = [row["korea_name"] for row in rows]
        if len(names) != len(set(names)):
            dup_targets.append(key)
    r.check("동일 그룹 내 Korea Target 이름 중복 없음", len(dup_targets) == 0, f"dup_groups={dup_targets}")

    # 7. priority: 그룹(동일 us_ticker + context + path) 내부 1부터 연속, 중복 없음
    bad_priority_groups = []
    for key, rows in by_group.items():
        pr = sorted(row["priority"] for row in rows)
        if pr != list(range(1, len(rows) + 1)):
            bad_priority_groups.append((key, pr))
    r.check("priority는 그룹별 1부터 연속/중복없음", len(bad_priority_groups) == 0, f"{bad_priority_groups}")

    # 8. mapping_type ENUM 검증
    bad_types = [m["id"] for m in stock_mapping if m["mapping_type"] not in MAPPING_TYPE]
    r.check("mapping_type ENUM 유효성", len(bad_types) == 0, f"bad={bad_types}")
    bad_status = [m["id"] for m in stock_mapping if m["status"] not in MAPPING_STATUS]
    r.check("status ENUM 유효성", len(bad_status) == 0, f"bad={bad_status}")

    # 9. weight 범위 0~1
    bad_weight = [m["id"] for m in stock_mapping if not (0 <= m["initial_weight"] <= 1)]
    r.check("weight 범위 0~1", len(bad_weight) == 0, f"bad={bad_weight}")

    # 10. transmission_path 빈 값 없음 (활성 매핑)
    empty_path = [m["id"] for m in stock_mapping if m["is_active"] and not m["transmission_paths"]]
    r.check("활성 매핑의 transmission_path 비어있지 않음", len(empty_path) == 0, f"bad={empty_path}")

    # 11. CONFIRMED_USER 값 변경 여부 (golden snapshot)
    confirmed_rows = sorted(
        [m for m in stock_mapping if m["status"] == "CONFIRMED_USER"],
        key=lambda m: m["id"],
    )
    confirmed_snapshot = [
        {"id": m["id"], "us_ticker": m["us_ticker"], "korea_name": m["korea_name"], "priority": m["priority"]}
        for m in confirmed_rows
    ]
    if not GOLDEN_PATH.exists():
        GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(GOLDEN_PATH, "w", encoding="utf-8") as f:
            json.dump(confirmed_snapshot, f, ensure_ascii=False, indent=2)
        r.check("CONFIRMED_USER golden snapshot 최초 생성", True, f"rows={len(confirmed_snapshot)}")
    else:
        with open(GOLDEN_PATH, "r", encoding="utf-8") as f:
            golden = json.load(f)
        r.check("CONFIRMED_USER 값이 golden snapshot과 일치", golden == confirmed_snapshot,
                "불일치 — 사용자 확정값이 변경되었습니다. 의도된 변경이면 golden 파일을 갱신하세요.")

    # 12. 비상장사가 상장 Target 점수에 포함되지 않았는지
    listed_targets = {m["korea_name"] for m in stock_mapping}
    non_listed_leak = [n for n in master_data.NON_LISTED_RELATIONSHIP_ONLY if n in listed_targets]
    r.check("비상장사가 Mapping Target에 섞이지 않음", len(non_listed_leak) == 0, f"leak={non_listed_leak}")

    # 13. HTS Pool과 Mapping Target 분리 유지 (역할 태그로 구분되는지)
    target_only_names = {m["korea_name"] for m in stock_mapping}
    pool_names = {n for names in master_data.KOREA_SECTOR_MASTER_POOLS.values() for n in names}
    both = target_only_names & pool_names
    r.check("[INFO] Target/Pool 동시 소속 종목 존재 (정상 — 자동승격 아님, 명세 5장)", True,
            f"count={len(both)}")

    # 14. 특정 alias/불확실 티커가 warning/resolve queue로 관리되는지
    preserved = set(master_data.FLAGGED_TICKERS_PRESERVE_AS_IS.keys())
    actually_flagged = {t["ticker"] for t in us_stocks if t.get("validation_warning")}
    r.check("GE/SPCX/AIFF/FLY 등 명세 3.2 지정 종목 모두 warning 처리됨",
            preserved.issubset(actually_flagged), f"missing={preserved - actually_flagged}")
    r.check("[INFO] alias 검증 대기열 상태", True,
            f"pending={master_data.ALIAS_VERIFICATION_NEEDED}  resolved={getattr(master_data, 'RESOLVED_ALIASES', [])}")

    # 추가: MSTR/MARA가 스테이블코인 전용 종목으로 확장되지 않았는지 (명세 4.17 금지 규칙)
    mstr_targets = {m["korea_name"] for m in stock_mapping if m["us_ticker"] in ("MSTR", "MARA")}
    leaked = mstr_targets & master_data.MSTR_MARA_MUST_NOT_INCLUDE
    r.check("MSTR/MARA가 스테이블코인 전용주로 확장되지 않음", len(leaked) == 0, f"leak={leaked}")

    return r


def main():
    r = run()
    total, failed = r.summary()
    for item in r.results:
        mark = "PASS" if item["passed"] else "FAIL"
        print(f"[{mark}] {item['check']}  {('- ' + item['detail']) if item['detail'] else ''}")
    print("-" * 70)
    print(f"TOTAL {total}  FAILED {len(failed)}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
