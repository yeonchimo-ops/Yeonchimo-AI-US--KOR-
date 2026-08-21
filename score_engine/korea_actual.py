"""한국 장마감 Actual/Money Flow/Leader 점수와 US→KR 정합도를 계산한다."""

from collections import defaultdict

from score_engine.normalize import percentile_rank_0_100, reweight_for_missing


def _close_strength(row):
    price = row.get("price")
    low = row.get("low")
    high = row.get("high")
    if price is None or low is None or high is None or high <= low:
        return None
    return round((price - low) / (high - low) * 100, 2)


def compute_korea_actual_scores(rows):
    """명세 7.3 비중으로 Mapping Target universe 내 percentile 점수를 계산한다."""
    valid_rows = [row for row in rows if not str(row.get("quality", "MISSING")).startswith("MISSING")]
    by_ticker = {row["instrument_id"]: row for row in valid_rows}
    return_rank = percentile_rank_0_100({k: v.get("return_pct") for k, v in by_ticker.items()})
    value_rank = percentile_rank_0_100({k: v.get("traded_value") for k, v in by_ticker.items()})
    growth_rank = percentile_rank_0_100({k: v.get("traded_value_growth") for k, v in by_ticker.items()})
    # 거래가 전혀 없던 정지/무거래 종목의 0 수급이 음수 수급 종목보다 높은
    # percentile을 받아 대장으로 오르는 것을 막는다.
    foreign_rank = percentile_rank_0_100({
        k: (v.get("foreign_net") if (v.get("traded_value") or 0) > 0 else None)
        for k, v in by_ticker.items()
    })
    institution_rank = percentile_rank_0_100({
        k: (v.get("institution_net") if (v.get("traded_value") or 0) > 0 else None)
        for k, v in by_ticker.items()
    })
    close_rank = {
        k: (_close_strength(v) if (v.get("traded_value") or 0) > 0 else None)
        for k, v in by_ticker.items()
    }

    results = []
    for ticker, row in by_ticker.items():
        components = {
            "return": return_rank[ticker],
            "traded_value": value_rank[ticker],
            "traded_value_growth": growth_rank[ticker],
            "foreign_flow": foreign_rank[ticker],
            "institution_flow": institution_rank[ticker],
            "close_strength": close_rank[ticker],
        }
        score, used_weight, quality = reweight_for_missing([
            (0.30, components["return"]),
            (0.30, components["traded_value"]),
            (0.15, components["traded_value_growth"]),
            (0.10, components["foreign_flow"]),
            (0.10, components["institution_flow"]),
            (0.05, components["close_strength"]),
        ])
        results.append({
            "korea_ticker": ticker,
            "korea_name": row.get("name") or ticker,
            "actual_score": score,
            "rank": None,
            "components": components,
            "used_weight": round(used_weight, 2),
            "data_quality": quality,
            "market_snapshot": row,
        })

    results.sort(key=lambda item: (-(item["actual_score"] or -1), item["korea_name"]))
    for rank, result in enumerate(results, start=1):
        result["rank"] = rank
    return results


def _comparison_result(expected, actual):
    direction = expected["expected_direction"]
    actual_return = actual["market_snapshot"].get("return_pct")
    if direction == "NEUTRAL" or actual_return is None:
        return "NEUTRAL", None
    direction_match = (direction == "POSITIVE" and actual_return > 0) or (
        direction == "NEGATIVE" and actual_return < 0
    )
    if expected["expected_score"] < 55:
        return "WEAK_SIGNAL", direction_match
    if direction_match and (actual.get("actual_score") or 0) >= 55:
        return "HIT", True
    if direction_match:
        return "DIRECTION_HIT", True
    return "MISS", False


def build_actual_evaluation(expected_records, actual_records, sector_names):
    """예상 Target과 장마감 결과를 결합하고 US Sector별 연결 정합도를 집계한다."""
    actual_by_ticker = {row["korea_ticker"]: row for row in actual_records}
    comparisons = []
    impact_edges = []

    for expected in expected_records:
        actual = actual_by_ticker.get(expected["korea_ticker"])
        if not actual:
            continue
        result, direction_match = _comparison_result(expected, actual)
        comparisons.append({
            "korea_ticker": expected["korea_ticker"],
            "korea_name": expected["korea_name"],
            "expected_score": expected["expected_score"],
            "expected_rank": expected["rank"],
            "expected_direction": expected["expected_direction"],
            "actual_score": actual["actual_score"],
            "actual_rank": actual["rank"],
            "return_pct": actual["market_snapshot"].get("return_pct"),
            "traded_value": actual["market_snapshot"].get("traded_value"),
            "market_cap": actual["market_snapshot"].get("market_cap"),
            "foreign_net": actual["market_snapshot"].get("foreign_net"),
            "institution_net": actual["market_snapshot"].get("institution_net"),
            "result": result,
            "direction_match": direction_match,
            "transmission_paths": expected["transmission_paths"],
        })
        for edge in expected["source_edges"]:
            if edge["signal_role"] != "PRIMARY":
                continue
            edge_direction = edge["expected_direction"]
            actual_return = actual["market_snapshot"].get("return_pct")
            edge_match = None if actual_return is None or edge_direction == "NEUTRAL" else (
                (edge_direction == "POSITIVE" and actual_return > 0)
                or (edge_direction == "NEGATIVE" and actual_return < 0)
            )
            impact_edges.append({
                **{key: edge[key] for key in (
                    "mapping_id", "us_sector_id", "us_sector_name", "us_ticker",
                    "us_return_pct", "us_traded_value", "korea_ticker", "korea_name",
                    "mapping_type", "mapping_weight", "priority", "transmission_paths",
                    "us_sector_score", "base_expected", "expected_direction",
                    "counted_in_expected", "exclusion_reason",
                )},
                "korea_return_pct": actual_return,
                "korea_traded_value": actual["market_snapshot"].get("traded_value"),
                "korea_market_cap": actual["market_snapshot"].get("market_cap"),
                "korea_actual_score": actual["actual_score"],
                "direction_match": edge_match,
            })

    grouped = defaultdict(list)
    for edge in impact_edges:
        grouped[edge["us_sector_id"]].append(edge)

    sector_impacts = []
    for sector_id, edges in grouped.items():
        # 한 sector 안에서 같은 한국 종목의 거래대금을 중복 합산하지 않는다.
        target_by_ticker = {}
        for edge in edges:
            target_by_ticker.setdefault(edge["korea_ticker"], edge)
        targets = list(target_by_ticker.values())
        matches = [edge["direction_match"] for edge in edges if edge["direction_match"] is not None]
        hit_rate = round(sum(bool(value) for value in matches) / len(matches) * 100, 1) if matches else None
        actual_values = [edge["korea_actual_score"] for edge in targets if edge["korea_actual_score"] is not None]
        returns = [edge["korea_return_pct"] for edge in targets if edge["korea_return_pct"] is not None]
        leader = max(targets, key=lambda edge: edge["korea_actual_score"] or -1) if targets else None
        sector_impacts.append({
            "us_sector_id": sector_id,
            "us_sector_name": sector_names.get(sector_id, sector_id),
            "us_sector_score": edges[0]["us_sector_score"],
            "linked_target_count": len(targets),
            "linked_korea_avg_return_pct": round(sum(returns) / len(returns), 2) if returns else None,
            "linked_korea_traded_value": sum(edge["korea_traded_value"] or 0 for edge in targets),
            "linked_korea_avg_actual_score": round(sum(actual_values) / len(actual_values), 2) if actual_values else None,
            "direction_match_rate": hit_rate,
            "actual_leader": ({
                "korea_ticker": leader["korea_ticker"],
                "korea_name": leader["korea_name"],
                "actual_score": leader["korea_actual_score"],
                "return_pct": leader["korea_return_pct"],
                "traded_value": leader["korea_traded_value"],
            } if leader else None),
        })

    sector_impacts.sort(key=lambda row: (
        -(row["direction_match_rate"] if row["direction_match_rate"] is not None else -1),
        -(row["linked_korea_avg_actual_score"] or -1),
    ))
    comparisons.sort(key=lambda row: (row["expected_rank"], row["actual_rank"]))
    return {
        "comparisons": comparisons,
        "sector_impacts": sector_impacts,
        "impact_edges": impact_edges,
    }
