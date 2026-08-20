# PHASE 1 빌드 스크립트: master_data.py의 파이썬 구조를 한국 티커까지 정규화해서
# data/generated/*.json 으로 내보낸다. 실시간 API 호출 없음 (PHASE 1 범위 제한).

import json
from pathlib import Path

import master_data
import korea_lookup
from enums import DEFAULT_WEIGHT_BY_TYPE

OUT_DIR = Path(__file__).parent / "data" / "generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def resolve_stock_mappings(rows):
    resolve_report = []
    for row in rows:
        ticker, status = korea_lookup.resolve(row["korea_name"])
        row["korea_ticker"] = ticker
        row["ticker_resolution_status"] = status
        if status != "RESOLVED":
            resolve_report.append({
                "us_ticker": row["us_ticker"],
                "korea_name": row["korea_name"],
                "priority": row["priority"],
                "mapping_id": row["id"],
            })
    return resolve_report


def build_us_stocks():
    stocks = []
    referenced_tickers = set()
    for sector in master_data.US_MASTER_SECTORS:
        referenced_tickers.update(sector["us_stocks"])
    for ticker in sorted(referenced_tickers):
        name, asset_type = master_data.US_STOCK_NAMES.get(ticker, (ticker, "EQUITY"))
        stocks.append({
            "ticker": ticker,
            "name": name,
            "asset_type": asset_type,
            "exchange": None,
            "is_active": True,
            "validation_warning": master_data.FLAGGED_TICKERS_PRESERVE_AS_IS.get(ticker),
        })
    return stocks


def build_us_stock_sector_membership():
    rows = []
    for sector in master_data.US_MASTER_SECTORS:
        for order, ticker in enumerate(sector["us_stocks"], start=1):
            rows.append({
                "us_ticker": ticker,
                "us_sector_id": sector["id"],
                "display_order": order,
                "role": "MEMBER",
                "is_active": True,
            })
    return rows


def build_korea_master_sectors():
    """명세 3장 표의 'Korea 연결 Master Sector/Sub-Sector' 콤마 목록을 KOREA_MASTER_SECTOR
    엔티티로 펼친다. parent_sector = 대응하는 US Master Sector 한글명, sub_sector = 개별 항목.
    display_order는 명세서 등장 순서를 그대로 보존한다 (전역 시퀀스)."""
    rows = []
    order = 1
    for sector in master_data.US_MASTER_SECTORS:
        for sub in sector["korea_sub_sectors"]:
            rows.append({
                "id": f"KR_{sector['id']}_{order:03d}",
                "name": sub,
                "parent_sector": sector["name"],
                "sub_sector": sub,
                "display_order": order,
                "us_sector_id": sector["id"],
                "is_active": True,
            })
            order += 1
    return rows


def build_us_korea_sector_mapping(korea_sectors):
    """명세 3장: 섹터 행 자체는 CONFIRMED_USER(구성 sub-sector 집합/순서 확정)이지만
    개별 엣지의 type/weight는 명세에 없으므로 DEFAULT_BY_TYPE(INDUSTRY, 0.65)를 적용하고
    명시적으로 default임을 표시한다."""
    rows = []
    for kr in korea_sectors:
        rows.append({
            "id": f"SECTORMAP_{kr['id']}",
            "us_sector_id": kr["us_sector_id"],
            "korea_sector_id": kr["id"],
            "mapping_type": "INDUSTRY",
            "initial_weight": DEFAULT_WEIGHT_BY_TYPE["INDUSTRY"],
            "weight_source": "DEFAULT_BY_TYPE",
            "transmission_paths": [],
            "source": "USER_CONFIRMED",
            "status": master_data.US_SECTOR_ROW_STATUS,
            "is_active": True,
            "note": "섹터 membership(어떤 sub-sector가 연결되는지)은 명세 3장에서 확정. "
                    "mapping_type/weight는 개별 명시가 없어 기본값(DEFAULT_BY_TYPE)을 적용함.",
        })
    return rows


def build_korea_stocks(stock_mapping_rows, master_pools):
    """Mapping Target으로 등장한 종목 + Master Pool에만 등장한 종목을 모두 KOREA_STOCK으로 등록.
    두 출처를 구분해 HTS Master Pool과 Mapping Target을 동일시하지 않는다 (명세 5장)."""
    stocks = {}

    def upsert(name, ticker, res_status, role):
        if name not in stocks:
            stocks[name] = {
                "name": name,
                "ticker": ticker,
                "ticker_resolution_status": res_status,
                "market": "KOSPI/KOSDAQ (미확인, PHASE1 미조회)",
                "is_listed": True,
                "is_active": True,
                "roles": set(),
            }
        stocks[name]["roles"].add(role)

    for row in stock_mapping_rows:
        upsert(row["korea_name"], row["korea_ticker"], row["ticker_resolution_status"], "MAPPING_TARGET")

    for pool_name, names in master_pools.items():
        for name in names:
            ticker, status = korea_lookup.resolve(name)
            upsert(name, ticker, status, f"MASTER_POOL:{pool_name}")

    out = []
    for s in stocks.values():
        s["roles"] = sorted(s["roles"])
        out.append(s)
    out.sort(key=lambda s: s["name"])
    return out


def build_korea_stock_sector_membership(master_pools):
    rows = []
    for pool_name, names in master_pools.items():
        for name in names:
            ticker, status = korea_lookup.resolve(name)
            rows.append({
                "korea_name": name,
                "korea_ticker": ticker,
                "ticker_resolution_status": status,
                "korea_sector_pool": pool_name,
                "source": "USER_HTS",
                "is_active": True,
            })
    return rows


def main():
    us_stocks = build_us_stocks()
    us_membership = build_us_stock_sector_membership()
    korea_sectors = build_korea_master_sectors()
    us_korea_sector_mapping = build_us_korea_sector_mapping(korea_sectors)

    stock_mapping = [dict(r) for r in master_data.US_KOREA_STOCK_MAPPING]
    resolve_report = resolve_stock_mappings(stock_mapping)

    korea_stocks = build_korea_stocks(stock_mapping, master_data.KOREA_SECTOR_MASTER_POOLS)
    korea_stock_pool_membership = build_korea_stock_sector_membership(master_data.KOREA_SECTOR_MASTER_POOLS)

    dataset = {
        "spec_version": "1.0.0",
        "us_master_sectors": [
            {k: v for k, v in s.items() if k not in ("korea_sub_sectors",)} | {"status": master_data.US_SECTOR_ROW_STATUS}
            for s in master_data.US_MASTER_SECTORS
        ],
        "us_stocks": us_stocks,
        "us_stock_sector_membership": us_membership,
        "reference_indicators": master_data.REFERENCE_INDICATORS,
        "korea_master_sectors": korea_sectors,
        "korea_stocks": korea_stocks,
        "korea_stock_sector_master_pool_membership": korea_stock_pool_membership,
        "us_korea_sector_mapping": us_korea_sector_mapping,
        "us_korea_stock_mapping": stock_mapping,
    }

    for name, payload in [
        ("us_master_sectors.json", dataset["us_master_sectors"]),
        ("us_stocks.json", dataset["us_stocks"]),
        ("us_stock_sector_membership.json", dataset["us_stock_sector_membership"]),
        ("reference_indicators.json", dataset["reference_indicators"]),
        ("korea_master_sectors.json", dataset["korea_master_sectors"]),
        ("korea_stocks.json", dataset["korea_stocks"]),
        ("korea_stock_sector_master_pool_membership.json", dataset["korea_stock_sector_master_pool_membership"]),
        ("us_korea_sector_mapping.json", dataset["us_korea_sector_mapping"]),
        ("us_korea_stock_mapping.json", dataset["us_korea_stock_mapping"]),
        ("full_dataset.json", dataset),
    ]:
        with open(OUT_DIR / name, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    with open(OUT_DIR / "resolve_report.json", "w", encoding="utf-8") as f:
        json.dump({
            "unresolved_count": len(resolve_report),
            "unresolved": resolve_report,
        }, f, ensure_ascii=False, indent=2)

    print(f"US Master Sector: {len(dataset['us_master_sectors'])}")
    print(f"US Stock: {len(us_stocks)}")
    print(f"US-KR Sector Mapping: {len(us_korea_sector_mapping)}")
    print(f"US-KR Stock Mapping rows: {len(stock_mapping)}")
    print(f"Korea Stock (target+pool 통합): {len(korea_stocks)}")
    print(f"미해결 한국 티커: {len(resolve_report)}개 (resolve_report.json 참고)")


if __name__ == "__main__":
    main()
