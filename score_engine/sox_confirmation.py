# PHASE 3 — SOX / SOXL / SOXS 중복 방지 처리 (명세 8장)
# 1. SOX는 반도체의 PRIMARY_SIGNAL이다.
# 2. SOXL/SOXS는 방향/강도를 확인하는 CONFIRMATION_SIGNAL이다.
# 3. SOX 상승과 SOXL 상승을 독립 강세로 단순 합산하지 않는다.
# 4. SOXS 상승은 한국 반도체에 음의 확인 신호다.
# 5. SOXL/SOXS는 confirmation adjustment에만 제한된 cap을 둔다.
# 이 모듈은 US Sector Score의 0.35/0.30/0.15/0.10/0.10 다섯 항목과는 별개의, 감사 가능한
# 보조 필드(sox_confirmation)로만 결과를 낸다 — 스코어 공식 안에 몰래 섞지 않는다.

CONFIRMATION_CAP = 3.0  # 최종 조정폭 상한 (점)


def compute_sox_confirmation(sox_return_pct, soxl_row, soxs_row):
    """sox_return_pct: ^SOX 지수 당일 등락률(%). soxl_row/soxs_row: us_adapter 스냅샷 행(또는 None)."""
    if sox_return_pct is None:
        return {"status": "MISSING", "reason": "SOX 지수 데이터 없음"}

    primary_direction = "UP" if sox_return_pct > 0 else ("DOWN" if sox_return_pct < 0 else "FLAT")

    soxl_return = soxl_row["return_pct"] if soxl_row and soxl_row.get("return_pct") is not None else None
    soxs_return = soxs_row["return_pct"] if soxs_row and soxs_row.get("return_pct") is not None else None

    confirms = []
    if soxl_return is not None:
        soxl_direction = "UP" if soxl_return > 0 else ("DOWN" if soxl_return < 0 else "FLAT")
        confirms.append(("SOXL", soxl_direction == primary_direction, soxl_return))
    if soxs_return is not None:
        # SOXS는 인버스 상품이라 SOX가 오르면 SOXS는 내려가는 게 "확인"이다 (규칙 4).
        soxs_expected_direction = "DOWN" if primary_direction == "UP" else ("UP" if primary_direction == "DOWN" else "FLAT")
        soxs_direction = "UP" if soxs_return > 0 else ("DOWN" if soxs_return < 0 else "FLAT")
        confirms.append(("SOXS", soxs_direction == soxs_expected_direction, soxs_return))

    if not confirms:
        return {
            "status": "PRIMARY_ONLY",
            "sox_return_pct": sox_return_pct,
            "primary_direction": primary_direction,
            "adjustment": 0.0,
            "note": "SOXL/SOXS 데이터 없어 SOX 단독 신호만 사용",
        }

    agree = sum(1 for _, ok, _ in confirms if ok)
    total = len(confirms)
    # 규칙 5: leveraged ETF는 확인 신호일 뿐이므로 조정폭을 강하게 제한한다.
    raw_adjustment = (agree - (total - agree)) / total * CONFIRMATION_CAP
    adjustment = max(-CONFIRMATION_CAP, min(CONFIRMATION_CAP, round(raw_adjustment, 2)))

    return {
        "status": "CONFIRMS" if agree == total else ("CONTRADICTS" if agree == 0 else "MIXED"),
        "sox_return_pct": sox_return_pct,
        "primary_direction": primary_direction,
        "confirmations": [{"ticker": t, "confirms_primary": ok, "return_pct": r} for t, ok, r in confirms],
        "adjustment": adjustment,
        "adjustment_cap": CONFIRMATION_CAP,
        "note": "이 adjustment는 US Sector Score(반도체, US_02_SEMICONDUCTOR)의 보조 필드로만 기록되며 "
                "7.1의 0.35/0.30/0.15/0.10/0.10 가중치 산식 자체에는 포함되지 않는다.",
    }
