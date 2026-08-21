"""PHASE 4 기반 — 미국 마감 신호를 한국 Mapping Target 예상값으로 전달한다.

오전 예측은 사용자 확정/초기 Master Mapping만 사용한다. 같은 미국 종목이 여러
Master Sector에 속하더라도 수익률 원천은 한 번만 반영하고, 나머지 context/path는
설명 정보로 보존한다. SOXL/SOXS는 독립 원천이 아니라 confirmation으로만 쓴다.
"""

from collections import defaultdict


def _clamp(value, low=0.0, high=100.0):
    return round(min(high, max(low, value)), 2)


def _sector_score_map(us_sector_scores):
    if isinstance(us_sector_scores, dict):
        return {
            sector_id: row.get("score")
            for sector_id, row in us_sector_scores.items()
        }
    return {
        row["entity_id"]: row.get("score")
        for row in us_sector_scores
        if row.get("score_type") == "US_SECTOR"
    }


def _direction(source_return, sector_score, ticker):
    value = source_return
    if ticker == "SOXS" and value is not None:
        value = -value
    if value is not None:
        if value > 0.2:
            return "POSITIVE", 1
        if value < -0.2:
            return "NEGATIVE", -1
        return "NEUTRAL", 0
    if sector_score is not None and sector_score >= 55:
        return "POSITIVE", 1
    if sector_score is not None and sector_score <= 45:
        return "NEGATIVE", -1
    return "NEUTRAL", 0


def compute_korea_expected(
    mappings,
    us_sector_scores,
    us_snapshots,
    sector_names=None,
    sox_confirmation=None,
):
    """한국 Mapping Target별 07:30 예상 강도와 설명 가능한 source edge를 반환한다.

    예상점수의 기준값은 명세의 ``US Sector Score × effective mapping weight``다.
    여러 독립 미국 티커의 방향 합의, 서로 다른 path, DIRECT 관계를 제한적으로
    보너스로 반영하고 반대 방향 원천은 conflict penalty로 기록한다.
    """
    sector_scores = _sector_score_map(us_sector_scores)
    sector_names = sector_names or {}
    us_by_ticker = {row.get("instrument_id"): row for row in us_snapshots}
    target_edges = defaultdict(list)
    all_edges = []

    for mapping in mappings:
        if not mapping.get("is_active", True) or mapping.get("status") == "DISABLED":
            continue
        if mapping.get("ticker_resolution_status") != "RESOLVED" or not mapping.get("korea_ticker"):
            continue

        sector_id = mapping["us_sector_context_id"]
        sector_score = sector_scores.get(sector_id)
        if sector_score is None:
            continue
        source = us_by_ticker.get(mapping["us_ticker"], {})
        source_return = source.get("return_pct")
        direction, direction_sign = _direction(source_return, sector_score, mapping["us_ticker"])
        weight = mapping.get("effective_weight")
        if weight is None:
            weight = mapping.get("initial_weight", 0.0)
        base = _clamp(sector_score * weight)
        direct_bonus = 0.0
        if mapping.get("mapping_type") == "DIRECT" and source_return is not None:
            direct_bonus = round(min(5.0, abs(source_return) * 0.75), 2)

        signal_role = "CONFIRMATION" if sector_id == "US_13_SEMI_ETF" else "PRIMARY"
        edge = {
            "mapping_id": mapping["id"],
            "us_sector_id": sector_id,
            "us_sector_name": sector_names.get(sector_id, sector_id),
            "us_ticker": mapping["us_ticker"],
            "us_return_pct": source_return,
            "us_traded_value": source.get("traded_value"),
            "korea_ticker": mapping["korea_ticker"],
            "korea_name": mapping["korea_name"],
            "mapping_type": mapping["mapping_type"],
            "mapping_weight": weight,
            "mapping_status": mapping["status"],
            "priority": mapping["priority"],
            "transmission_paths": mapping.get("transmission_paths", []),
            "us_sector_score": sector_score,
            "base_expected": base,
            "direct_stock_bonus": direct_bonus,
            "expected_direction": direction,
            "direction_sign": direction_sign,
            "signal_role": signal_role,
            "counted_in_expected": signal_role == "PRIMARY",
            "exclusion_reason": "ETF_CONFIRMATION_ONLY" if signal_role == "CONFIRMATION" else None,
        }
        target_edges[mapping["korea_ticker"]].append(edge)
        all_edges.append(edge)

    expected = []
    for korea_ticker, edges in target_edges.items():
        primary = [edge for edge in edges if edge["signal_role"] == "PRIMARY"]

        # 같은 US ticker의 여러 sector membership은 원천 신호를 한 번만 계산한다.
        unique_sources = []
        for us_ticker in sorted({edge["us_ticker"] for edge in primary}):
            candidates = [edge for edge in primary if edge["us_ticker"] == us_ticker]
            selected = max(
                candidates,
                key=lambda edge: (edge["base_expected"] + edge["direct_stock_bonus"], -edge["priority"]),
            )
            unique_sources.append(selected)
            for candidate in candidates:
                if candidate is not selected:
                    candidate["counted_in_expected"] = False
                    candidate["exclusion_reason"] = "DUPLICATE_SOURCE_MEMBERSHIP"

        signed_strength = sum(
            edge["direction_sign"] * (edge["base_expected"] + edge["direct_stock_bonus"])
            for edge in unique_sources
        )
        if signed_strength > 1:
            dominant_direction, dominant_sign = "POSITIVE", 1
        elif signed_strength < -1:
            dominant_direction, dominant_sign = "NEGATIVE", -1
        else:
            dominant_direction, dominant_sign = "NEUTRAL", 0

        agreeing = [edge for edge in unique_sources if edge["direction_sign"] == dominant_sign and dominant_sign]
        conflicting = [edge for edge in unique_sources if edge["direction_sign"] == -dominant_sign and dominant_sign]
        scoring_sources = agreeing or unique_sources
        base_expected = max((edge["base_expected"] for edge in scoring_sources), default=0.0)
        direct_bonus = max((edge["direct_stock_bonus"] for edge in scoring_sources), default=0.0)
        consensus_bonus = min(10.0, max(0, len(agreeing) - 1) * 2.5)
        path_sources = agreeing or unique_sources
        paths = sorted({path for edge in path_sources for path in edge["transmission_paths"]})
        multi_path_bonus = min(5.0, max(0, len(paths) - 1) * 0.5)
        conflict_penalty = min(10.0, len(conflicting) * 2.5)

        is_semiconductor_target = any(edge["us_sector_id"] == "US_02_SEMICONDUCTOR" for edge in primary)
        sox_adjustment = 0.0
        if is_semiconductor_target and sox_confirmation:
            sox_adjustment = float(sox_confirmation.get("adjustment") or 0.0)

        score = _clamp(
            base_expected
            + direct_bonus
            + consensus_bonus
            + multi_path_bonus
            - conflict_penalty
            + sox_adjustment
        )
        representative = max(edges, key=lambda edge: edge["base_expected"])
        expected.append({
            "korea_ticker": korea_ticker,
            "korea_name": representative["korea_name"],
            "expected_score": score,
            "expected_direction": dominant_direction,
            "rank": None,
            "components": {
                "base_expected": round(base_expected, 2),
                "direct_stock_bonus": round(direct_bonus, 2),
                "mapping_consensus_bonus": round(consensus_bonus, 2),
                "multi_benefit_bonus": round(multi_path_bonus, 2),
                "negative_conflict_penalty": round(conflict_penalty, 2),
                "sox_confirmation_adjustment": round(sox_adjustment, 2),
            },
            "independent_source_count": len(unique_sources),
            "agreeing_source_count": len(agreeing),
            "conflicting_source_count": len(conflicting),
            "transmission_paths": paths,
            "source_edges": edges,
        })

    expected.sort(key=lambda row: (-row["expected_score"], row["korea_name"]))
    for rank, row in enumerate(expected, start=1):
        row["rank"] = rank
    return expected, all_edges
