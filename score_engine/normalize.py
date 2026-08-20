# PHASE 3 — 정규화 유틸리티 (명세 7장 서문)
# "모든 원시 지표는 날짜·시장·섹터 내 robust percentile 또는 winsorized z-score로 0~100 정규화한다."
# 여기서는 robust percentile(순위 기반, 이상치에 덜 민감)을 사용한다.


def percentile_rank_0_100(values_by_key):
    """{key: raw_value} -> {key: 0~100 percentile rank}. None 값은 결과에서도 None으로 유지.
    표본이 1개뿐이면 50.0(중립)으로 처리한다."""
    valid = {k: v for k, v in values_by_key.items() if v is not None}
    if not valid:
        return {k: None for k in values_by_key}
    if len(valid) == 1:
        only_key = next(iter(valid))
        return {k: (50.0 if k == only_key else None) for k in values_by_key}

    ordered = sorted(valid.items(), key=lambda kv: kv[1])
    n = len(ordered)
    ranks = {}
    i = 0
    while i < n:
        j = i
        while j + 1 < n and ordered[j + 1][1] == ordered[i][1]:
            j += 1
        avg_rank = (i + j) / 2
        pct = round(avg_rank / (n - 1) * 100, 2) if n > 1 else 50.0
        for k in range(i, j + 1):
            ranks[ordered[k][0]] = pct
        i = j + 1

    return {k: ranks.get(k) for k in values_by_key}


def reweight_for_missing(weighted_components):
    """[(weight, value_0_100_or_None), ...] -> (final_score_0_100, used_weight_sum, data_quality).
    누락된 요소는 제외하고 남은 weight 합으로 나눠 비례 재배분한다 (명세 7장 서문)."""
    present = [(w, v) for w, v in weighted_components if v is not None]
    total_weight = sum(w for w, _ in weighted_components)
    used_weight = sum(w for w, _ in present)
    if used_weight == 0:
        return None, 0.0, "MISSING"

    score = sum(w * v for w, v in present) / used_weight
    quality = "ACTUAL" if used_weight == total_weight else "PARTIAL"
    return round(min(100, max(0, score)), 2), used_weight, quality
