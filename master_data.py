# PHASE 1 — MASTER MAPPING DATABASE 소스 오브 트루스
# YEONCHIMO_AI_MARKET_MASTER_SPEC.md 3~5장을 그대로 구조화한 것.
# 이 파일의 값(섹터명/구성종목/순서/Korea Target/순서/status)은 임의로 축약·재해석하지 않는다.
# type/weight가 명세에 개별 명시되지 않은 관계는 default_type_for_priority()로 계산하고
# weight_source="DEFAULT_BY_TYPE"으로 명시한다 (명세 2.2, 사용자 확정 규칙).

from enums import DEFAULT_WEIGHT_BY_TYPE

# ==========================================================================
# 1. US MASTER SECTOR (명세 3장 표, 17개, display_order 그대로 보존)
# ==========================================================================

US_MASTER_SECTORS = [
    {"id": "US_01_M7", "name": "M7", "display_order": 1,
     "us_stocks": ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"],
     "korea_sub_sectors": ["AI반도체", "HBM", "AI SW", "데이터센터", "전력인프라", "스마트폰·디스플레이", "EV·2차전지", "자율주행"]},
    {"id": "US_02_SEMICONDUCTOR", "name": "반도체", "display_order": 2,
     "us_stocks": ["SKHY", "MU", "SNDK", "MRVL", "STX", "TSM", "AVGO", "AMD", "INTC", "TXN", "ASML"],
     "korea_sub_sectors": ["반도체", "HBM", "DRAM", "NAND", "파운드리", "팹리스", "장비·소재", "PCB"]},
    {"id": "US_03_POWER_EQUIPMENT", "name": "발전설비", "display_order": 3,
     "us_stocks": ["GEV"],
     "korea_sub_sectors": ["전력기기", "발전설비", "변압기", "송배전", "가스터빈"]},
    {"id": "US_04_NUCLEAR_SMR", "name": "원전·SMR", "display_order": 4,
     "us_stocks": ["SMR", "OKLO", "CEG", "URA"],
     "korea_sub_sectors": ["원전", "SMR", "원전기자재", "원전 EPC"]},
    {"id": "US_05_SOLAR", "name": "태양광", "display_order": 5,
     "us_stocks": ["ENPH", "TAN", "NEE", "FSLR"],
     "korea_sub_sectors": ["셀·모듈", "폴리실리콘·소재", "장비", "페로브스카이트·탠덤", "발전·EPC"]},
    {"id": "US_06_WIND", "name": "풍력", "display_order": 6,
     "us_stocks": ["NEE", "GE", "CWEN", "BEP"],
     "korea_sub_sectors": ["터빈", "타워", "하부구조물", "베어링", "해저케이블", "발전·EPC"]},
    {"id": "US_07_OPTICAL", "name": "광통신", "display_order": 7,
     "us_stocks": ["LITE", "COHR", "GLW", "CIEN"],
     "korea_sub_sectors": ["광통신", "광트랜시버", "CPO", "광케이블", "AI 데이터센터"]},
    {"id": "US_08_DEFENSE", "name": "방산", "display_order": 8,
     "us_stocks": ["LMT"],
     "korea_sub_sectors": ["방산", "항공방산", "미사일", "레이더", "방산전자"]},
    {"id": "US_09_AEROSPACE", "name": "우주항공", "display_order": 9,
     "us_stocks": ["SPCX", "RKLB", "ASTS", "AIFF", "FLY", "LUNR", "PL"],
     "korea_sub_sectors": ["발사체·엔진", "위성", "위성통신", "위성 제작·관측", "우주전자·부품", "달 탐사"]},
    {"id": "US_10_LITHIUM", "name": "리튬", "display_order": 10,
     "us_stocks": ["ALB", "LAC", "LIT"],
     "korea_sub_sectors": ["리튬", "2차전지", "양극재", "배터리소재"]},
    {"id": "US_11_SOFC", "name": "SOFC·친환경", "display_order": 11,
     "us_stocks": ["BE"],
     "korea_sub_sectors": ["SOFC", "연료전지", "분산전원", "데이터센터 전력", "SOEC·수소"]},
    {"id": "US_12_PHARMA_BIO", "name": "제약·바이오", "display_order": 12,
     "us_stocks": ["MRNA", "LLY", "NVO", "PFE"],
     "korea_sub_sectors": ["mRNA", "백신", "항암백신", "GLP-1", "비만·당뇨", "CDMO", "신약개발"]},
    {"id": "US_13_SEMI_ETF", "name": "반도체 ETF", "display_order": 13,
     "us_stocks": ["SOXL", "SOXS"],
     "korea_sub_sectors": ["한국 반도체 전체 방향성과 위험선호 확인"]},
    {"id": "US_14_AI_SOFTWARE", "name": "AI·소프트웨어", "display_order": 14,
     "us_stocks": ["PLTR", "ORCL"],
     "korea_sub_sectors": ["AI SW", "SI", "AX", "Cloud", "DB", "데이터센터"]},
    {"id": "US_15_QUANTUM", "name": "양자컴퓨터", "display_order": 15,
     "us_stocks": ["IONQ", "RGTI", "QBTS"],
     "korea_sub_sectors": ["양자컴퓨터", "양자통신", "양자암호", "QKD", "PQC", "사이버보안"]},
    {"id": "US_16_EV", "name": "전기차", "display_order": 16,
     "us_stocks": ["TSLA", "RIVN", "LCID"],
     "korea_sub_sectors": ["EV", "2차전지", "ESS", "배터리소재", "FSD·자율주행", "전장", "로봇"]},
    {"id": "US_17_CRYPTO", "name": "가상화폐", "display_order": 17,
     "us_stocks": ["MSTR", "MARA", "COIN", "GLXY", "CRCL"],
     "korea_sub_sectors": ["Bitcoin", "Exchange", "Stablecoin", "Payment·Fintech", "STO·Tokenization"]},
]

assert len(US_MASTER_SECTORS) == 17, "명세 3장은 반드시 17개 US Master Sector여야 한다"

# 변경 이력 — 명세 원문 대비 사용자 승인 하에 삭제된 종목.
# AGR(Avangrid): PHASE 2 라이브 수집(yfinance) 중 "possibly delisted"로 확인됨 —
# 2024년 Iberdrola의 Avangrid 비상장화(take-private)로 실제 상장폐지된 것이 맞아 사용자가
# 삭제를 승인함 (2026-08-21). 풍력(US_06_WIND) 섹터 구성종목과 Stock Mapping에서 완전히 제거.
REMOVED_TICKERS_LOG = [
    {"ticker": "AGR", "removed_from": "US_06_WIND", "reason": "delisted (Avangrid take-private by Iberdrola, 2024)",
     "confirmed_via": "yfinance PHASE2 live collection", "approved_by": "user", "date": "2026-08-21"},
]

# 모든 섹터 행은 명세 3장 표에서 status=CONFIRMED_USER로 명시됨
# (어떤 섹터가 존재하는지, 구성종목이 무엇인지, 순서가 어떤지는 사용자 확정값).
US_SECTOR_ROW_STATUS = "CONFIRMED_USER"

# ==========================================================================
# 2. US_STOCK 마스터 (최대한의 공개 정보 기반 best-effort 이름. 정확한 거래소
#    표기/상장상태 확인은 PHASE 2 실시간 데이터 연동 시 재검증 대상이다.)
# ==========================================================================

# 명세 3.2에서 명시적으로 "자동 교정 금지, validation warning으로 보고"하라고
# 지정한 티커들. build.py가 이 목록을 그대로 warning으로 띄운다.
FLAGGED_TICKERS_PRESERVE_AS_IS = {
    "GE": "HTS 원본 풍력 목록 보존용. 실제 풍력사업 직접 신호는 GEV가 더 적합하나 자동 치환하지 않음 (명세 3.2)",
    "SPCX": "소스 시스템 표시값 보존. 상장 여부/정확한 티커 재검증 필요 (명세 3.2)",
    "AIFF": "소스 시스템 표시값 보존. 상장 여부/정확한 티커 재검증 필요 (명세 3.2)",
    "FLY": "소스 시스템 표시값 보존. 상장 여부/정확한 티커 재검증 필요 (명세 3.2)",
    "SKHY": "미국시장 SK하이닉스 직접 선행 신호로 취급하는 표시값. 실제 ADR 상장 여부 재검증 필요",
}

US_STOCK_NAMES = {
    "NVDA": ("NVIDIA Corporation", "EQUITY"),
    "AAPL": ("Apple Inc.", "EQUITY"),
    "MSFT": ("Microsoft Corporation", "EQUITY"),
    "GOOGL": ("Alphabet Inc. Class A", "EQUITY"),
    "AMZN": ("Amazon.com Inc.", "EQUITY"),
    "META": ("Meta Platforms Inc.", "EQUITY"),
    "TSLA": ("Tesla Inc.", "EQUITY"),
    "SKHY": ("SK hynix (ADR 표시값)", "ADR"),
    "MU": ("Micron Technology Inc.", "EQUITY"),
    "SNDK": ("SanDisk Corporation", "EQUITY"),
    "MRVL": ("Marvell Technology Inc.", "EQUITY"),
    "STX": ("Seagate Technology Holdings", "EQUITY"),
    "TSM": ("Taiwan Semiconductor Manufacturing (ADR)", "ADR"),
    "AVGO": ("Broadcom Inc.", "EQUITY"),
    "AMD": ("Advanced Micro Devices Inc.", "EQUITY"),
    "INTC": ("Intel Corporation", "EQUITY"),
    "TXN": ("Texas Instruments Inc.", "EQUITY"),
    "ASML": ("ASML Holding (ADR)", "ADR"),
    "GEV": ("GE Vernova Inc.", "EQUITY"),
    "SMR": ("NuScale Power Corporation", "EQUITY"),
    "OKLO": ("Oklo Inc.", "EQUITY"),
    "CEG": ("Constellation Energy Corporation", "EQUITY"),
    "URA": ("Global X Uranium ETF", "ETF"),
    "ENPH": ("Enphase Energy Inc.", "EQUITY"),
    "TAN": ("Invesco Solar ETF", "ETF"),
    "NEE": ("NextEra Energy Inc.", "EQUITY"),
    "FSLR": ("First Solar Inc.", "EQUITY"),
    "GE": ("General Electric Company", "EQUITY"),
    "CWEN": ("Clearway Energy Inc.", "EQUITY"),
    "BEP": ("Brookfield Renewable Partners", "EQUITY"),
    "LITE": ("Lumentum Holdings Inc.", "EQUITY"),
    "COHR": ("Coherent Corp.", "EQUITY"),
    "GLW": ("Corning Incorporated", "EQUITY"),
    "CIEN": ("Ciena Corporation", "EQUITY"),
    "LMT": ("Lockheed Martin Corporation", "EQUITY"),
    "SPCX": ("SpaceX (표시값, 상장상태 재검증 필요)", "EQUITY"),
    "RKLB": ("Rocket Lab USA Inc.", "EQUITY"),
    "ASTS": ("AST SpaceMobile Inc.", "EQUITY"),
    "AIFF": ("표시값 보존 (재검증 필요)", "EQUITY"),
    "FLY": ("표시값 보존 (재검증 필요)", "EQUITY"),
    "LUNR": ("Intuitive Machines Inc.", "EQUITY"),
    "PL": ("Planet Labs PBC", "EQUITY"),
    "ALB": ("Albemarle Corporation", "EQUITY"),
    "LAC": ("Lithium Americas Corp.", "EQUITY"),
    "LIT": ("Global X Lithium & Battery Tech ETF", "ETF"),
    "BE": ("Bloom Energy Corporation", "EQUITY"),
    "MRNA": ("Moderna Inc.", "EQUITY"),
    "LLY": ("Eli Lilly and Company", "EQUITY"),
    "NVO": ("Novo Nordisk (ADR)", "ADR"),
    "PFE": ("Pfizer Inc.", "EQUITY"),
    "SOXL": ("Direxion Daily Semiconductor Bull 3X Shares", "ETF"),
    "SOXS": ("Direxion Daily Semiconductor Bear 3X Shares", "ETF"),
    "PLTR": ("Palantir Technologies Inc.", "EQUITY"),
    "ORCL": ("Oracle Corporation", "EQUITY"),
    "IONQ": ("IonQ Inc.", "EQUITY"),
    "RGTI": ("Rigetti Computing Inc.", "EQUITY"),
    "QBTS": ("D-Wave Quantum Inc.", "EQUITY"),
    "RIVN": ("Rivian Automotive Inc.", "EQUITY"),
    "LCID": ("Lucid Group Inc.", "EQUITY"),
    "MSTR": ("Strategy Inc. (구 MicroStrategy)", "EQUITY"),
    "MARA": ("MARA Holdings Inc.", "EQUITY"),
    "COIN": ("Coinbase Global Inc.", "EQUITY"),
    "GLXY": ("Galaxy Digital Inc.", "EQUITY"),
    "CRCL": ("Circle Internet Group Inc.", "EQUITY"),
}

# 명세 3.2 — BTC/ETH는 17번 그룹 구성종목이 아니라 선택적 REFERENCE_INDICATOR.
# 섹터 membership을 만들지 않고 참고지표 엔티티로만 별도 보관한다.
REFERENCE_INDICATORS = [
    {"ticker": "BTC", "name": "Bitcoin", "asset_type": "CRYPTO_REFERENCE"},
    {"ticker": "ETH", "name": "Ethereum", "asset_type": "CRYPTO_REFERENCE"},
]

# ==========================================================================
# 3. STOCK-TO-STOCK MAPPING (명세 4장). 헬퍼로 priority/weight/status를 계산한다.
# ==========================================================================


def _split_path(path_str):
    return [seg.strip() for seg in path_str.split("→") if seg.strip()]


def _default_type_for_priority(i, overrides):
    """명세 4장 서문의 기본 규칙: 첫 Target=CORE, 나머지=INDUSTRY.
    명세 본문에 개별 권장 type이 명시된 경우만 overrides로 덮어쓴다."""
    if overrides and i in overrides:
        return overrides[i]
    return "CORE" if i == 1 else "INDUSTRY"


def stock_mapping_rows(us_sector_id, us_ticker, path_str, targets, status, type_overrides=None):
    """명세 4장의 한 표 행(US종목 1개 + Korea Target 여러 개)을
    US_KOREA_STOCK_MAPPING row 여러 개(Target당 1개)로 펼친다."""
    paths = _split_path(path_str)
    rows = []
    for i, korea_name in enumerate(targets, start=1):
        mtype = _default_type_for_priority(i, type_overrides)
        rows.append({
            "id": f"MAP_{us_ticker}_{us_sector_id.split('_')[1]}_{i:02d}",
            "us_sector_context_id": us_sector_id,
            "us_ticker": us_ticker,
            "korea_name": korea_name,
            "korea_ticker": None,  # build.py가 korea_lookup으로 채운다
            "ticker_resolution_status": None,  # build.py가 채운다
            "mapping_type": mtype,
            "initial_weight": DEFAULT_WEIGHT_BY_TYPE[mtype],
            "effective_weight": DEFAULT_WEIGHT_BY_TYPE[mtype],  # PHASE1: catalyst 조정 없음
            "weight_source": "DEFAULT_BY_TYPE",
            "transmission_paths": paths,
            "priority": i,
            "source": "USER_CONFIRMED" if status == "CONFIRMED_USER" else "MODEL_INITIAL",
            "status": status,
            "is_active": True,
        })
    return rows


# ---- 4.1 M7 (전부 CONFIRMED_USER, "확정본으로 잠금") ----
_M7 = [
    stock_mapping_rows("US_01_M7", "NVDA", "AI반도체 → HBM → AI서버·PCB → 전력인프라",
                        ["SK하이닉스", "삼성전자", "한미반도체", "이수페타시스", "HD현대일렉트릭"], "CONFIRMED_USER"),
    stock_mapping_rows("US_01_M7", "AAPL", "스마트폰 → OLED·디스플레이 → 카메라·부품",
                        ["LG이노텍", "BH", "삼성전기", "LX세미콘"], "CONFIRMED_USER"),
    stock_mapping_rows("US_01_M7", "MSFT", "생성형 AI → Cloud → AI 데이터센터·소프트웨어",
                        ["NAVER", "카카오", "한글과컴퓨터", "리노공업"], "CONFIRMED_USER"),
    stock_mapping_rows("US_01_M7", "GOOGL", "AI 서비스 → Cloud → 데이터센터",
                        ["NAVER", "카카오", "삼성SDS", "HD현대일렉트릭"], "CONFIRMED_USER"),
    stock_mapping_rows("US_01_M7", "AMZN", "e-Commerce → AWS·Cloud → 물류·데이터센터",
                        ["이마트", "CJ대한통운", "서진시스템"], "CONFIRMED_USER"),
    stock_mapping_rows("US_01_M7", "META", "AI 플랫폼 → 메타버스·소셜 → 디스플레이",
                        ["뉴프렉스", "선익시스템", "NAVER"], "CONFIRMED_USER"),
    stock_mapping_rows("US_01_M7", "TSLA", "EV → 2차전지 → 소재 → 자율주행",
                        ["LG에너지솔루션", "POSCO홀딩스", "에코프로비엠", "엘앤에프", "현대모비스"], "CONFIRMED_USER"),
]

# ---- 4.2 반도체 ----
_SEMI = [
    stock_mapping_rows("US_02_SEMICONDUCTOR", "SKHY", "HBM → DRAM·NAND → AI 메모리",
                        ["SK하이닉스", "삼성전자"], "CONFIRMED_USER"),
    stock_mapping_rows("US_02_SEMICONDUCTOR", "MU", "HBM → DRAM·NAND → AI 메모리",
                        ["SK하이닉스", "삼성전자", "ISC"], "INITIAL_MODEL"),
    stock_mapping_rows("US_02_SEMICONDUCTOR", "SNDK", "NAND → SSD → 데이터센터 스토리지",
                        ["삼성전자", "SK하이닉스", "심텍"], "INITIAL_MODEL"),
    stock_mapping_rows("US_02_SEMICONDUCTOR", "MRVL", "AI ASIC → HBM → 데이터센터 → 고속네트워크",
                        ["SK하이닉스", "삼성전자", "이수페타시스", "ISC", "삼성전기"], "CONFIRMED_USER"),
    stock_mapping_rows("US_02_SEMICONDUCTOR", "STX", "HDD → 데이터센터 스토리지",
                        ["SK하이닉스", "삼성전자"], "INITIAL_MODEL"),
    stock_mapping_rows("US_02_SEMICONDUCTOR", "TSM", "파운드리 → 첨단공정 → AI반도체",
                        ["삼성전자", "DB하이텍", "가온칩스", "에이직랜드"], "INITIAL_MODEL"),
    stock_mapping_rows("US_02_SEMICONDUCTOR", "AVGO", "AI ASIC → HBM → 네트워크 → 데이터센터",
                        ["삼성전자", "SK하이닉스", "이수페타시스", "가온칩스", "에이직랜드"], "CONFIRMED_USER"),
    stock_mapping_rows("US_02_SEMICONDUCTOR", "AMD", "AI GPU·CPU → HBM → AI서버",
                        ["SK하이닉스", "삼성전자", "ISC", "이수페타시스"], "INITIAL_MODEL"),
    stock_mapping_rows("US_02_SEMICONDUCTOR", "INTC", "CPU → 파운드리 → 첨단공정",
                        ["삼성전자", "DB하이텍", "가온칩스"], "INITIAL_MODEL"),
    stock_mapping_rows("US_02_SEMICONDUCTOR", "TXN", "아날로그 → 산업용·자동차 반도체",
                        ["DB하이텍", "LX세미콘", "텔레칩스"], "INITIAL_MODEL"),
    stock_mapping_rows("US_02_SEMICONDUCTOR", "ASML", "EUV → 첨단공정 → 반도체 CAPEX",
                        ["삼성전자", "SK하이닉스", "원익IPS", "주성엔지니어링", "동진쎄미켐"], "INITIAL_MODEL"),
]

# ---- 4.3 발전설비 (GEV 두 경로) ----
_POWER = [
    stock_mapping_rows("US_03_POWER_EQUIPMENT", "GEV", "가스터빈·발전설비",
                        ["두산에너빌리티"], "INITIAL_MODEL", type_overrides={1: "CORE"}),
    stock_mapping_rows("US_03_POWER_EQUIPMENT", "GEV", "전력망·변압기·전력기기",
                        ["HD현대일렉트릭", "효성중공업", "LS ELECTRIC"], "INITIAL_MODEL",
                        type_overrides={1: "CORE", 2: "INDUSTRY", 3: "INDUSTRY"}),
]

# ---- 4.4 원전·SMR ----
_NUCLEAR = [
    stock_mapping_rows("US_04_NUCLEAR_SMR", "SMR", "SMR → 원자로 주기기 → 원전 기자재·EPC",
                        ["두산에너빌리티", "삼성물산", "GS"], "INITIAL_MODEL", type_overrides={1: "DIRECT"}),
    stock_mapping_rows("US_04_NUCLEAR_SMR", "OKLO", "차세대 SMR·마이크로원자로 → AI 데이터센터 전력",
                        ["두산에너빌리티", "한전기술", "비에이치아이"], "INITIAL_MODEL",
                        type_overrides={1: "INDUSTRY", 2: "INDUSTRY", 3: "INDUSTRY"}),
    stock_mapping_rows("US_04_NUCLEAR_SMR", "CEG", "원자력발전 → 전력판매 → AI 데이터센터 전력",
                        ["한국전력", "한전KPS", "한전기술", "두산에너빌리티"], "INITIAL_MODEL",
                        type_overrides={1: "INDUSTRY", 2: "INDUSTRY", 3: "INDUSTRY", 4: "INDUSTRY"}),
    stock_mapping_rows("US_04_NUCLEAR_SMR", "URA", "우라늄 → 글로벌 원전 투자심리",
                        ["두산에너빌리티", "한전기술", "한전KPS", "비에이치아이"], "INITIAL_MODEL",
                        type_overrides={1: "INDUSTRY", 2: "INDUSTRY", 3: "INDUSTRY", 4: "INDUSTRY"}),
]

# ---- 4.5 태양광 ----
_SOLAR = [
    stock_mapping_rows("US_05_SOLAR", "ENPH", "인버터 → 주택용 태양광 → ESS",
                        ["한화솔루션", "HD현대에너지솔루션"], "INITIAL_MODEL"),
    stock_mapping_rows("US_05_SOLAR", "TAN", "글로벌 태양광 섹터 종합",
                        ["한화솔루션", "OCI홀딩스", "HD현대에너지솔루션", "주성엔지니어링"], "INITIAL_MODEL"),
    stock_mapping_rows("US_05_SOLAR", "NEE", "신재생 발전 → 태양광 → ESS·전력",
                        ["한화솔루션", "SK이터닉스", "HD현대에너지솔루션"], "INITIAL_MODEL"),
    stock_mapping_rows("US_05_SOLAR", "FSLR", "태양전지 셀·모듈 → 미국 제조 → CAPEX·장비",
                        ["한화솔루션", "OCI홀딩스", "HD현대에너지솔루션", "주성엔지니어링"], "INITIAL_MODEL"),
]

KOREA_SOLAR_MASTER_POOL = [
    "HD현대에너지솔루션", "OCI홀딩스", "주성엔지니어링", "한화솔루션", "신성이엔지", "선익시스템",
    "유니테스트", "에스에너지", "엘케이켐", "금양그린파워", "대명에너지", "SK이터닉스", "파루", "파인테크닉스",
]

# ---- 4.6 풍력 (절대 규칙: 모든 행 priority1 = SK이터닉스) ----
_WIND = [
    stock_mapping_rows("US_06_WIND", "NEE", "육상풍력 → 신재생 발전 → 전력망",
                        ["SK이터닉스", "씨에스윈드", "두산에너빌리티", "씨에스베어링", "대명에너지"], "CONFIRMED_USER"),
    stock_mapping_rows("US_06_WIND", "GE", "풍력 터빈 → 풍력 기자재",
                        ["SK이터닉스", "씨에스윈드", "씨에스베어링", "두산에너빌리티", "유니슨"], "CONFIRMED_USER"),
    stock_mapping_rows("US_06_WIND", "CWEN", "육상풍력 → 신재생 발전사업",
                        ["SK이터닉스", "씨에스윈드", "대명에너지", "씨에스베어링"], "CONFIRMED_USER"),
    stock_mapping_rows("US_06_WIND", "BEP", "글로벌 풍력 → 신재생 발전·투자",
                        ["SK이터닉스", "씨에스윈드", "SK오션플랜트", "대명에너지", "씨에스베어링"], "CONFIRMED_USER"),
]

KOREA_WIND_MASTER_POOL = [
    "씨에스윈드", "SK오션플랜트", "씨에스베어링", "두산에너빌리티", "LS마린솔루션", "세진중공업", "태웅",
    "동국S&C", "동국산업", "삼영엠텍", "대창솔루션", "대명에너지", "금양그린파워", "SK이터닉스", "유니슨",
]

# ---- 4.7 광통신 (절대 규칙: 모든 행 priority1 = 성호전자) ----
_OPTICAL = [
    stock_mapping_rows("US_07_OPTICAL", "LITE", "광원·레이저 → 광모듈 → CPO·AI 데이터센터",
                        ["성호전자", "RF머트리얼즈", "오이솔루션", "대한광통신", "이수페타시스"], "CONFIRMED_USER"),
    stock_mapping_rows("US_07_OPTICAL", "COHR", "광모듈·포토닉스 → 800G·1.6T → CPO",
                        ["성호전자", "오이솔루션", "RF머트리얼즈", "대한광통신", "이수페타시스"], "CONFIRMED_USER"),
    stock_mapping_rows("US_07_OPTICAL", "GLW", "광섬유 → CPO → AI 데이터센터 연결망",
                        ["성호전자", "대한광통신", "LS마린솔루션", "가온전선"], "CONFIRMED_USER",
                        type_overrides={1: "DIRECT"}),
    stock_mapping_rows("US_07_OPTICAL", "CIEN", "광네트워크 → DCI → 고속 광전송",
                        ["성호전자", "오이솔루션", "대한광통신", "이수페타시스"], "CONFIRMED_USER"),
]

# ---- 4.8 방산 ----
_DEFENSE = [
    stock_mapping_rows("US_08_DEFENSE", "LMT", "전투기·군용항공 → 미사일·방공 → 항공엔진·부품 → 레이더·C4I",
                        ["한국항공우주", "한화에어로스페이스", "LIG넥스원", "한화시스템"], "INITIAL_MODEL",
                        type_overrides={1: "DIRECT", 2: "INDUSTRY", 3: "INDUSTRY", 4: "INDUSTRY"}),
]

# ---- 4.9 우주항공 ----
_AEROSPACE = [
    stock_mapping_rows("US_09_AEROSPACE", "SPCX", "발사체 → 위성통신 → 우주인터넷",
                        ["한화에어로스페이스", "한화시스템", "쎄트렉아이", "인텔리안테크"], "INITIAL_MODEL"),
    stock_mapping_rows("US_09_AEROSPACE", "RKLB", "발사체 → 위성 플랫폼 → 우주부품",
                        ["한화에어로스페이스", "쎄트렉아이", "제노코", "AP위성"], "INITIAL_MODEL"),
    stock_mapping_rows("US_09_AEROSPACE", "ASTS", "위성통신 → Direct-to-Device → 우주통신",
                        ["인텔리안테크", "한화시스템", "AP위성", "쎄트렉아이"], "INITIAL_MODEL"),
    stock_mapping_rows("US_09_AEROSPACE", "AIFF", "소형 발사체 → 우주수송",
                        ["한화에어로스페이스", "제노코", "쎄트렉아이"], "INITIAL_MODEL"),
    stock_mapping_rows("US_09_AEROSPACE", "FLY", "소형 발사체 → 달 탐사 → 우주수송",
                        ["한화에어로스페이스", "쎄트렉아이", "제노코"], "INITIAL_MODEL"),
    stock_mapping_rows("US_09_AEROSPACE", "LUNR", "달 탐사·착륙선 → 우주 인프라",
                        ["한화에어로스페이스", "한화시스템", "쎄트렉아이", "제노코"], "INITIAL_MODEL"),
    stock_mapping_rows("US_09_AEROSPACE", "PL", "지구관측 위성 → 위성 데이터·영상분석",
                        ["쎄트렉아이", "한화시스템", "제노코"], "INITIAL_MODEL"),
]

# ---- 4.10 리튬 ----
_LITHIUM = [
    stock_mapping_rows("US_10_LITHIUM", "ALB", "리튬 가격 → 광산·정제 → 배터리 원재료",
                        ["POSCO홀딩스", "포스코퓨처엠", "LG에너지솔루션", "에코프로비엠"], "INITIAL_MODEL"),
    stock_mapping_rows("US_10_LITHIUM", "LAC", "미국 리튬광산 → 북미 배터리 공급망",
                        ["POSCO홀딩스", "LG에너지솔루션", "포스코퓨처엠"], "INITIAL_MODEL"),
    stock_mapping_rows("US_10_LITHIUM", "LIT", "글로벌 리튬·배터리 밸류체인",
                        ["LG에너지솔루션", "삼성SDI", "POSCO홀딩스", "포스코퓨처엠", "에코프로비엠"], "INITIAL_MODEL"),
]

# ---- 4.11 SOFC·친환경 ----
_SOFC = [
    stock_mapping_rows("US_11_SOFC", "BE", "SOFC → 분산발전 → 데이터센터 전력",
                        ["SK이터닉스", "두산퓨얼셀", "비나텍", "범한퓨얼셀", "아모센스"], "INITIAL_MODEL",
                        type_overrides={1: "DIRECT", 2: "CORE", 3: "INDUSTRY", 4: "INDUSTRY", 5: "DIRECT"}),
]

KOREA_SOFC_MASTER_POOL = [
    "두산퓨얼셀", "RFHIC", "RF머트리얼즈", "비나텍", "코세스", "코스텍시스", "범한퓨얼셀", "웨이비스",
    "에이프로", "마이언티바이오", "SK이터닉스", "아모센스",
]
# 명세 4.11 — RFHIC/RF머트리얼즈/코스텍시스는 전통 SOFC가 아니라 GaN·SiC/AI 데이터센터
# 전력반도체 경로로 분리 관리한다 (Master Pool에는 포함, 별도 sub-sector 태그로 구분).
KOREA_SOFC_GAN_SIC_SUBSET = ["RFHIC", "RF머트리얼즈", "코스텍시스"]
# 명세 4.11 — 비상장 SK에코플랜트는 관계 데이터만 저장하고 상장 Target 화면에서 제외.
NON_LISTED_RELATIONSHIP_ONLY = ["SK에코플랜트"]

# ---- 4.12 제약·바이오 ----
_PHARMA = [
    stock_mapping_rows("US_12_PHARMA_BIO", "MRNA", "mRNA 플랫폼·백신·항암백신 → CDMO",
                        ["삼성바이오로직스", "에스티팜", "파미셀"], "INITIAL_MODEL"),
    stock_mapping_rows("US_12_PHARMA_BIO", "MRNA", "RNA 전달체·DDS",
                        ["나이벡", "올릭스"], "INITIAL_MODEL"),
    stock_mapping_rows("US_12_PHARMA_BIO", "MRNA", "백신·mRNA 테마",
                        ["큐라티스", "녹십자", "진원생명과학"], "INITIAL_MODEL"),
    stock_mapping_rows("US_12_PHARMA_BIO", "LLY", "GLP-1·비만·당뇨 → 장기지속형 → 차세대 신약·바이오 플랫폼",
                        ["펩트론", "한미약품", "삼성바이오로직스", "에이비엘바이오"], "CONFIRMED_USER"),
    stock_mapping_rows("US_12_PHARMA_BIO", "NVO", "GLP-1 → 비만·당뇨",
                        ["한미약품", "펩트론", "디앤디파마텍"], "INITIAL_MODEL"),
    stock_mapping_rows("US_12_PHARMA_BIO", "PFE", "글로벌 제약 → 백신·항암",
                        ["삼성바이오로직스", "유한양행"], "INITIAL_MODEL"),
]

KOREA_MRNA_MASTER_POOL = [
    "나이벡", "마이진", "에스티팜", "큐라티스", "올릭스", "서린바이오", "파미셀", "녹십자",
    "한미약품", "이연제약", "진원생명과학",
]

# ---- 4.13 반도체 ETF (SOX=PRIMARY, SOXL/SOXS=CONFIRMATION, 명세 8장) ----
_SEMI_ETF = [
    stock_mapping_rows("US_13_SEMI_ETF", "SOXL", "미국 반도체 Risk-On 확인 신호",
                        ["SK하이닉스", "삼성전자", "한미반도체", "이수페타시스", "ISC"], "INITIAL_MODEL"),
    stock_mapping_rows("US_13_SEMI_ETF", "SOXS", "미국 반도체 Risk-Off 확인 신호 (상승 시 한국 반도체 음의 방향, 명세 8장)",
                        ["SK하이닉스", "삼성전자", "한미반도체", "이수페타시스", "ISC"], "INITIAL_MODEL"),
]

# ---- 4.14 AI·소프트웨어 ----
_AI_SW = [
    stock_mapping_rows("US_14_AI_SOFTWARE", "PLTR", "Enterprise AI → 데이터 분석 → AI 플랫폼·AX",
                        ["삼성SDS", "LG CNS", "현대오토에버", "포스코DX", "엑셈"], "INITIAL_MODEL"),
    stock_mapping_rows("US_14_AI_SOFTWARE", "ORCL", "Cloud·OCI → DB → Enterprise IT·데이터센터",
                        ["삼성SDS", "LG CNS", "NHN", "포스코DX", "롯데이노베이트"], "INITIAL_MODEL",
                        type_overrides={1: "DIRECT"}),
]

KOREA_AI_SW_MASTER_POOL = [
    "삼성에스디에스", "현대오토에버", "LG CNS", "포스코DX", "NHN", "아이티센글로벌", "클로봇",
    "롯데이노베이트", "신세계I&C", "마이크로디지탈", "엑셈", "비트플래닛", "SGA솔루션즈",
]

# ---- 4.15 양자컴퓨터 ----
_QUANTUM = [
    stock_mapping_rows("US_15_QUANTUM", "IONQ", "양자컴퓨터·양자네트워크 → QKD·양자통신 → PQC·사이버보안",
                        ["SK텔레콤", "엑스게이트", "KCS", "우리로", "드림시큐리티", "라온시큐어", "아톤", "케이사인"],
                        "INITIAL_MODEL", type_overrides={1: "DIRECT"}),
    stock_mapping_rows("US_15_QUANTUM", "RGTI", "초전도 양자컴퓨터·Quantum Cloud → 한국 양자·보안 테마",
                        ["엑스게이트", "드림시큐리티", "KCS", "우리로", "쏠리드"], "INITIAL_MODEL"),
    stock_mapping_rows("US_15_QUANTUM", "QBTS", "양자 어닐링·최적화 → 한국 양자·보안 테마",
                        ["엑스게이트", "드림시큐리티", "KCS", "우리로", "쏠리드"], "INITIAL_MODEL"),
]

KOREA_QUANTUM_SECURITY_MASTER_POOL = [
    "아톤", "가비아", "엑스게이트", "드림시큐리티", "라온시큐어", "케이사인", "SGA솔루션즈",
    "KCS", "우리로", "쏠리드",
]
# 명세 4.15 — KCS/케이씨에스 alias 여부는 최초 미검증이었으나 사용자가 네이버증권에서
# 직접 확인(KCS = 케이씨에스, 115500)해 data/user_verified_tickers.json에 반영됨.
ALIAS_VERIFICATION_NEEDED = []
RESOLVED_ALIASES = [("KCS", "케이씨에스", "115500", "USER_NAVER_FINANCE")]

# ---- 4.16 전기차 (Catalyst 분기는 PHASE 5 대상이라 여기서는 base row만) ----
_EV = [
    stock_mapping_rows("US_16_EV", "TSLA", "EV·배터리·ESS → 소재",
                        ["LG에너지솔루션", "삼성SDI", "엘앤에프", "포스코퓨처엠", "POSCO홀딩스"], "INITIAL_MODEL"),
    stock_mapping_rows("US_16_EV", "RIVN", "미국 EV·픽업·SUV → 배터리",
                        ["삼성SDI", "LG에너지솔루션", "에코프로비엠", "포스코퓨처엠"], "INITIAL_MODEL"),
    stock_mapping_rows("US_16_EV", "LCID", "프리미엄 EV → 고성능 배터리",
                        ["LG에너지솔루션", "삼성SDI", "에코프로비엠", "엘앤에프"], "INITIAL_MODEL"),
]

# ---- 4.17 가상화폐 (CRCL priority1 = 카카오페이 절대 규칙) ----
_CRYPTO = [
    stock_mapping_rows("US_17_CRYPTO", "MSTR", "Bitcoin 보유 → BTC 가격",
                        ["우리기술투자", "한화투자증권", "티사이언티픽"], "INITIAL_MODEL"),
    stock_mapping_rows("US_17_CRYPTO", "MARA", "Bitcoin 채굴 → BTC 가격",
                        ["우리기술투자", "한화투자증권", "티사이언티픽"], "INITIAL_MODEL"),
    stock_mapping_rows("US_17_CRYPTO", "COIN", "거래소·거래대금 → 가상자산 관련주 + USDC 생태계",
                        ["우리기술투자", "한화투자증권", "카카오페이", "다날"], "INITIAL_MODEL"),
    stock_mapping_rows("US_17_CRYPTO", "GLXY", "가상자산 금융·기관투자 → 토큰화",
                        ["우리기술투자", "갤럭시아머니트리", "아이티센글로벌"], "INITIAL_MODEL"),
    stock_mapping_rows("US_17_CRYPTO", "CRCL", "USDC → Stablecoin → 디지털결제 → 원화 스테이블코인",
                        ["카카오페이", "다날", "헥토파이낸셜", "쿠콘", "NHN KCP", "코나아이"], "CONFIRMED_USER"),
]

KOREA_STABLECOIN_MASTER_POOL = [
    "카카오", "카카오페이", "아이티센글로벌", "코나아이", "NHN KCP", "다날", "제주은행", "헥토파이낸셜",
    "쿠콘", "갤럭시아머니트리", "더즌", "핑거", "아톤", "서울옥션", "미투온", "뱅크웨어글로벌", "아이티센피엔",
]

# 명세 4.17 — MSTR/MARA는 스테이블코인주로 확장하지 않는다 (경고 규칙, validate.py에서 검사).
MSTR_MARA_MUST_NOT_INCLUDE = set(KOREA_STABLECOIN_MASTER_POOL) - {"카카오페이", "다날"}

ALL_STOCK_MAPPING_GROUPS = (
    _M7 + _SEMI + _POWER + _NUCLEAR + _SOLAR + _WIND + _OPTICAL + _DEFENSE + _AEROSPACE +
    _LITHIUM + _SOFC + _PHARMA + _SEMI_ETF + _AI_SW + _QUANTUM + _EV + _CRYPTO
)

# stock_mapping_rows()가 "행 하나 = 리스트"를 반환하므로 평탄화한다.
US_KOREA_STOCK_MAPPING = [row for group in ALL_STOCK_MAPPING_GROUPS for row in group]

KOREA_SECTOR_MASTER_POOLS = {
    "태양광": KOREA_SOLAR_MASTER_POOL,
    "풍력": KOREA_WIND_MASTER_POOL,
    "SOFC·친환경": KOREA_SOFC_MASTER_POOL,
    "mRNA": KOREA_MRNA_MASTER_POOL,
    "AI·소프트웨어": KOREA_AI_SW_MASTER_POOL,
    "양자컴퓨터·보안": KOREA_QUANTUM_SECURITY_MASTER_POOL,
    "스테이블코인": KOREA_STABLECOIN_MASTER_POOL,
}
