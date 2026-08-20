# PHASE 3 — US SECTOR SCORE (명세 7.1)
# US Sector Score = 0.35*ReturnStrength + 0.30*TradedValueStrength + 0.15*Breadth
#                  + 0.10*CoreLeadership + 0.10*Catalyst
# Catalyst(뉴스/실적/가이던스)는 PHASE 5(Dynamic Catalyst Mapping) 대상이라 PHASE 3에서는
# 항상 누락 처리하고, 남은 4개 요소(90%)로 비례 재배분한다 (명세 7장 서문의 명시적 규칙).

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from score_engine.normalize import percentile_rank_0_100, reweight_for_missing

WEIGHTS = {"return_strength": 0.35, "traded_value_strength": 0.30, "breadth": 0.15, "core_leadership": 0.10,
           "catalyst": 0.10}

STRENGTH_BANDS = [
    (85, "VERY_STRONG"), (70, "STRONG"), (55, "POSITIVE"), (45, "NEUTRAL"), (30, "WEAK"), (0, "VERY_WEAK"),
]


def strength_label(score):
    if score is None:
        return "MISSING"
    for threshold, label in STRENGTH_BANDS:
        if score >= threshold:
            return label
    return "VERY_WEAK"


def _weighted_avg_return(member_rows):
    weighted_sum, weight_total, simple_sum, simple_n = 0.0, 0.0, 0.0, 0
    for r in member_rows:
        if r["return_pct"] is None:
            continue
        simple_sum += r["return_pct"]
        simple_n += 1
        if r.get("market_cap"):
            weighted_sum += r["return_pct"] * r["market_cap"]
            weight_total += r["market_cap"]
    if weight_total > 0:
        return weighted_sum / weight_total
    if simple_n > 0:
        return simple_sum / simple_n
    return None


def compute_us_sector_scores(us_master_sectors, us_snapshot_rows):
    """us_master_sectors: build.py가 만든 us_master_sectors.json 리스트(각 항목에 원본 us_stocks 필요 —
    Phase1 output에는 빠져있으므로 이 함수는 raw master_data 형태(us_stocks 포함)를 기대한다.
    us_snapshot_rows: us_adapter.fetch_us_market_snapshot()의 결과 리스트."""
    by_ticker = {r["instrument_id"]: r for r in us_snapshot_rows}

    raw_return, raw_traded_value_strength, raw_breadth, raw_leadership = {}, {}, {}, {}
    sector_members = {}

    for sector in us_master_sectors:
        sid = sector["id"]
        members = [by_ticker[t] for t in sector["us_stocks"] if t in by_ticker]
        sector_members[sid] = members
        if not members:
            raw_return[sid] = raw_traded_value_strength[sid] = raw_breadth[sid] = raw_leadership[sid] = None
            continue

        raw_return[sid] = _weighted_avg_return(members)

        ratios = [m["avg_volume_ratio"] for m in members if m.get("avg_volume_ratio") is not None]
        raw_traded_value_strength[sid] = (sum(ratios) / len(ratios)) if ratios else None

        with_return = [m for m in members if m["return_pct"] is not None]
        raw_breadth[sid] = (100.0 * sum(1 for m in with_return if m["return_pct"] > 0) / len(with_return)) \
            if with_return else None

        capped = [m for m in members if m.get("market_cap")]
        if capped:
            leader = max(capped, key=lambda m: m["market_cap"])
            raw_leadership[sid] = leader["return_pct"]
        else:
            raw_leadership[sid] = None

    return_pct_rank = percentile_rank_0_100(raw_return)
    traded_value_pct_rank = percentile_rank_0_100(raw_traded_value_strength)
    leadership_pct_rank = percentile_rank_0_100(raw_leadership)
    # breadth는 이미 0~100 비율이라 percentile이 아니라 값 그대로 사용한다 (명세 7.1 정의 그대로).

    results = {}
    for sector in us_master_sectors:
        sid = sector["id"]
        components = [
            (WEIGHTS["return_strength"], return_pct_rank.get(sid)),
            (WEIGHTS["traded_value_strength"], traded_value_pct_rank.get(sid)),
            (WEIGHTS["breadth"], raw_breadth.get(sid)),
            (WEIGHTS["core_leadership"], leadership_pct_rank.get(sid)),
            (WEIGHTS["catalyst"], None),  # PHASE 5 대상 — 항상 누락, 아래에서 재배분됨
        ]
        score, used_weight, quality = reweight_for_missing(components)
        results[sid] = {
            "us_sector_id": sid,
            "name": sector["name"],
            "display_order": sector["display_order"],
            "score": score,
            "strength_label": strength_label(score),
            "data_quality": quality,
            "used_weight": round(used_weight, 2),
            "components_raw": {
                "return_strength_raw": raw_return.get(sid),
                "traded_value_strength_raw": raw_traded_value_strength.get(sid),
                "breadth_pct": raw_breadth.get(sid),
                "core_leadership_return_pct": raw_leadership.get(sid),
                "catalyst": None,
            },
            "components_normalized": {
                "return_strength": return_pct_rank.get(sid),
                "traded_value_strength": traded_value_pct_rank.get(sid),
                "breadth": raw_breadth.get(sid),
                "core_leadership": leadership_pct_rank.get(sid),
                "catalyst": None,
            },
            "member_count": len(sector_members[sid]),
            "member_count_missing": len(sector["us_stocks"]) - len(sector_members[sid]),
        }
    return results
