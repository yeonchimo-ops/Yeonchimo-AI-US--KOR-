# PHASE 3 — US Sector Score를 기존 'Yeonchimo AI Market · MI-V3' 대시보드와 같은
# 비주얼 언어(마스트헤드/히어로카드/아코디언 그룹)로 렌더링한다. 새 스타일을 만들지 않고
# 기존 프로젝트가 이미 쓰고 있는 CSS 토큰·클래스 구조를 그대로 재사용한다.

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
from adapters.us_adapter import fetch_us_major_indices

GEN_DIR = Path(__file__).parent / "data" / "generated"
RUN_DIR = Path(__file__).parent / "data" / "prediction_runs"

STRENGTH_STYLE = {
    "VERY_STRONG": ("up", "🟢🟢"),
    "STRONG": ("up", "🟢"),
    "POSITIVE": ("up", "🟢"),
    "NEUTRAL": ("flat", "⚪"),
    "WEAK": ("down", "🔴"),
    "VERY_WEAK": ("down", "🔴"),
    "MISSING": ("flat", "⚫"),
}

CSS = """
:root {
  --bg:#F6F5F0; --surface:#FFFFFF; --ink:#1B1C22; --ink-soft:#5C5F6B; --line:#E1DED3; --accent:#A8752E;
  --up:#D6483F; --up-soft:#FBE7E4; --down:#2D62D8; --down-soft:#E6ECFC;
  --hero-bg:#191B21; --hero-surface:#22252D; --hero-ink:#F3F1E9; --hero-accent:#E0AC55;
  --flat:#8B8E99; --ink-faint:#8B8E99; --surface-2:#EFEDE5;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg:#121317; --surface:#1A1C22; --ink:#ECEBE6; --ink-soft:#A5A8B3; --line:#2C2F38; --accent:#E0AC55;
    --up:#FF7A70; --up-soft:#3A2020; --down:#6E9BFF; --down-soft:#1E2740;
    --hero-bg:#0C0D10; --hero-surface:#17181D; --hero-ink:#F3F1E9; --hero-accent:#E9BB6C;
    --flat:#7C7F8B; --ink-faint:#6E7180; --surface-2:#22252C;
  }
}
:root[data-theme="dark"] {
  --bg:#121317; --surface:#1A1C22; --ink:#ECEBE6; --ink-soft:#A5A8B3; --line:#2C2F38; --accent:#E0AC55;
  --up:#FF7A70; --up-soft:#3A2020; --down:#6E9BFF; --down-soft:#1E2740;
  --hero-bg:#0C0D10; --hero-surface:#17181D; --hero-ink:#F3F1E9; --hero-accent:#E9BB6C;
  --flat:#7C7F8B; --ink-faint:#6E7180; --surface-2:#22252C;
}
:root[data-theme="light"] {
  --bg:#F6F5F0; --surface:#FFFFFF; --ink:#1B1C22; --ink-soft:#5C5F6B; --line:#E1DED3; --accent:#A8752E;
  --up:#D6483F; --up-soft:#FBE7E4; --down:#2D62D8; --down-soft:#E6ECFC;
  --hero-bg:#191B21; --hero-surface:#22252D; --hero-ink:#F3F1E9; --hero-accent:#E0AC55;
  --flat:#8B8E99; --ink-faint:#8B8E99; --surface-2:#EFEDE5;
}
* { box-sizing: border-box; }
html { background: var(--bg); }
body {
  background: var(--bg); color: var(--ink);
  font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Malgun Gothic', 'Apple SD Gothic Neo', system-ui, sans-serif;
  max-width: 760px; margin: 0 auto; padding: 0 18px 70px;
  line-height: 1.55; font-size: 15px;
}
.mono { font-family: 'SF Mono', 'Roboto Mono', ui-monospace, monospace; font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1; }
.up { color: var(--up); }
.down { color: var(--down); }
.flat { color: var(--flat); }
.muted { color: var(--ink-faint); font-size: 13px; }

.masthead { padding: 32px 0 20px; border-bottom: 1px solid var(--line); }
.wordmark { font-size: 13px; letter-spacing: 0.1em; color: var(--accent); text-transform: uppercase; font-weight: 700; }
.masthead h1 { font-size: 24px; margin: 6px 0 10px; font-weight: 700; text-wrap: balance; }
.masthead .date { font-family: 'SF Mono', ui-monospace, monospace; color: var(--ink-soft); font-size: 12.5px; }
.caveat { background: var(--surface-2); border-radius: 10px; padding: 10px 14px; font-size: 12.5px; color: var(--ink-soft); margin-top: 14px; }
.disclaimer { font-size: 12px; color: var(--ink-faint); margin-top: 8px; }

.card { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 22px; margin: 18px 0; }
.card h2 { font-size: 17px; margin: 0 0 14px; display:flex; align-items:center; gap:8px; }
.card h2 .idx { color: var(--ink-faint); font-weight: 500; font-size: 13px; }

.hero { background: var(--hero-bg); color: var(--hero-ink); border-radius: 16px; padding: 24px 22px; margin: 20px 0; }
.hero-kospi { display:flex; align-items:baseline; justify-content: space-between; margin-bottom: 18px; }
.hero-kospi .lbl { font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: #9DA0AC; }
.hero-kospi .val { font-family: 'SF Mono', ui-monospace, monospace; font-size: 30px; font-weight: 700; color: var(--hero-accent); }
.hero-section-lbl { font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #9DA0AC; margin: 16px 0 8px; }
.hero-top-item { display:flex; align-items:center; gap: 10px; padding: 7px 0; border-bottom: 1px solid #2A2D36; font-size: 13.5px; }
.hero-top-item:last-child { border-bottom: none; }
.hero-top-rank { font-family: 'SF Mono', monospace; color: var(--hero-accent); font-weight:700; width: 16px; }
.hero-top-name { flex: 1; }
.hero-top-val { font-family: 'SF Mono', monospace; font-weight: 700; }
.hero-divergence { margin-top: 14px; background: rgba(255,255,255,0.05); border-radius: 10px; padding: 10px 14px; }
.hero-div-label { font-size: 12.5px; font-weight: 700; color: var(--hero-accent); margin-bottom: 4px; }
.hero-divergence ul { margin: 0; padding-left: 18px; font-size: 12.5px; color: #C9CBD3; display:flex; flex-direction:column; gap: 3px; }
.hero-daycount { margin-top: 14px; font-size: 12px; color: #9DA0AC; }

.group-list { display:flex; flex-direction:column; gap: 2px; }
.group-item { border-bottom: 1px solid var(--line); }
.group-item:last-child { border-bottom: none; }
.group-item summary {
  display:flex; align-items:center; gap: 10px; padding: 11px 4px; cursor: pointer; list-style: none;
  font-size: 13.5px;
}
.group-item summary::-webkit-details-marker { display:none; }
.group-item summary::before { content: "▸"; color: var(--ink-faint); font-size: 11px; transition: transform 0.15s; flex-shrink:0; }
.group-item[open] summary::before { transform: rotate(90deg); }
.g-name { flex: 1.6; font-weight: 600; min-width: 0; }
.draft-tag { font-size: 9.5px; background: var(--surface-2); color: var(--ink-faint); border-radius: 4px; padding: 1px 5px; font-weight: 700; letter-spacing: 0.03em; margin-left: 4px; }
.g-score { flex: 0.7; text-align:right; font-family: 'SF Mono', monospace; font-weight: 700; }
.g-label { flex: 1.1; text-align:right; font-size: 11px; font-weight: 700; letter-spacing: 0.02em; }
.g-quality { flex: 0.9; text-align:right; color: var(--ink-faint); font-size: 11px; }

.stock-table-wrap { overflow-x: auto; margin: 4px 0 14px 18px; }
.stock-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.stock-table th { text-align:left; color: var(--ink-faint); font-weight:600; font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.03em; padding: 6px 8px; border-bottom: 1px solid var(--line); white-space:nowrap; }
.stock-table td { padding: 6px 8px; border-bottom: 1px solid var(--line); white-space:nowrap; }
.stock-table tr:last-child td { border-bottom: none; }
.stock-table .num { text-align:right; }
.muted-cell { color: var(--ink-faint); font-size: 11.5px; }
.component-line { font-size: 11.5px; color: var(--ink-soft); margin: 6px 0 12px 18px; }

.index-row { display:flex; gap: 10px; margin: 18px 0; }
.index-card { flex:1; background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 14px 14px 10px; min-width:0; }
.index-name { font-size: 12px; color: var(--ink-soft); font-weight: 600; margin-bottom: 4px; }
.index-price { font-family: 'SF Mono', ui-monospace, monospace; font-size: 17px; font-weight: 700; }
.index-change { font-family: 'SF Mono', ui-monospace, monospace; font-size: 11.5px; margin-top: 2px; }
.index-spark { width: 100%; height: 34px; margin-top: 8px; display:block; }
.index-asof { font-size: 9.5px; color: var(--ink-faint); margin-top: 4px; }

footer { margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--line); font-size: 11.5px; color: var(--ink-faint); display:flex; flex-direction:column; gap:5px; }
"""


def render_sparkline_svg(values, up):
    if not values or len(values) < 2:
        return '<svg class="index-spark"></svg>'
    w, h, pad = 200, 34, 3
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    n = len(values)
    points = []
    for i, v in enumerate(values):
        x = pad + (w - 2 * pad) * i / (n - 1)
        y = pad + (h - 2 * pad) * (1 - (v - lo) / span)
        points.append(f"{x:.1f},{y:.1f}")
    poly = " ".join(points)
    fill_pts = f"{pad},{h-pad} " + poly + f" {w-pad},{h-pad}"
    color = "var(--up)" if up else "var(--down)"
    return (
        f'<svg class="index-spark" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
        f'<polygon points="{fill_pts}" fill="{color}" opacity="0.12"></polygon>'
        f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="1.6" '
        f'stroke-linejoin="round" stroke-linecap="round"></polyline>'
        f'</svg>'
    )


def render_index_row():
    rows = fetch_us_major_indices()
    cards = []
    for r in rows:
        if r["status"] != "ACTUAL":
            cards.append(f'<div class="index-card"><div class="index-name">{r["name"]}</div>'
                         f'<div class="muted-cell">MISSING</div></div>')
            continue
        up = r["change"] >= 0
        cls = "up" if up else "down"
        arrow = "▲" if up else ("▼" if r["change"] < 0 else "")
        as_of = r["as_of_bar"][:16].replace("T", " ")
        cards.append(
            f'<div class="index-card"><div class="index-name">{r["name"]}</div>'
            f'<div class="index-price mono">{r["price"]:,.2f}</div>'
            f'<div class="index-change mono {cls}">{arrow} {r["change"]:+,.2f} ({r["change_pct"]:+.2f}%)</div>'
            f'{render_sparkline_svg(r["sparkline"], up)}'
            f'<div class="index-asof">{as_of} 기준 · yfinance</div>'
            f'</div>'
        )
    return f'<div class="index-row">{"".join(cards)}</div>'


def fmt_pct(v):
    if v is None:
        return "-"
    cls = "up" if v > 0 else ("down" if v < 0 else "flat")
    return f'<span class="num mono {cls}">{v:+.2f}%</span>'


def fmt_money_usd(v):
    if v is None:
        return '<span class="num mono muted-cell">-</span>'
    if v >= 1e9:
        return f'<span class="num mono">${v/1e9:,.2f}B</span>'
    return f'<span class="num mono">${v/1e6:,.1f}M</span>'


def render_sector_table(sector_stocks, members_lookup, name_ko_lookup):
    rows = []
    for ticker in sector_stocks:
        name_ko = name_ko_lookup.get(ticker, ticker)
        ticker_cell = f'<div>{name_ko}</div><div class="mono muted-cell">{ticker}</div>'
        m = members_lookup.get(ticker)
        if not m:
            rows.append(f'<tr><td>{ticker_cell}</td><td class="mono muted-cell">-</td>'
                        f'<td class="num muted-cell">MISSING</td><td class="num muted-cell">-</td>'
                        f'<td class="num muted-cell">-</td><td class="num muted-cell">-</td></tr>')
            continue
        price = f'{m["price"]:,.2f}' if m.get("price") is not None else "-"
        rows.append(
            f'<tr><td>{ticker_cell}</td><td class="mono muted-cell">{m.get("quality","")}</td>'
            f'<td>{fmt_pct(m.get("return_pct"))}</td>'
            f'<td class="num mono">{price}</td>'
            f'<td class="num mono">{fmt_money_usd(m.get("market_cap"))}</td>'
            f'<td class="num mono">{fmt_money_usd(m.get("traded_value"))}</td></tr>'
        )
    return "\n".join(rows)


def build_html(trade_date):
    run_path = RUN_DIR / f"prediction_run_{trade_date}.json"
    with open(run_path, "r", encoding="utf-8") as f:
        run_data = json.load(f)
    with open(GEN_DIR / "full_dataset.json", "r", encoding="utf-8") as f:
        full = json.load(f)

    snap_files = sorted((Path(__file__).parent / "data" / "snapshots").glob(f"snapshot_{trade_date}_*.json"))
    members_lookup = {}
    if snap_files:
        with open(snap_files[-1], "r", encoding="utf-8") as f:
            snap = json.load(f)
        members_lookup = {r["instrument_id"]: r for r in snap["us_snapshots"]}

    sector_meta = {s["id"]: s for s in full["us_master_sectors"]}
    name_ko_lookup = {s["ticker"]: s.get("name_ko", s["ticker"]) for s in full["us_stocks"]}
    sector_stocks = {}
    for m in full["us_stock_sector_membership"]:
        sector_stocks.setdefault(m["us_sector_id"], []).append(m["us_ticker"])

    scored = sorted(run_data["us_sector_score_records"], key=lambda r: sector_meta[r["entity_id"]]["display_order"])
    ranked_by_score = sorted([r for r in scored if r["score"] is not None], key=lambda r: -r["score"])[:3]

    pr = run_data["prediction_run"]
    sox = run_data["sox_confirmation"]

    top_html = "\n".join(
        f'<div class="hero-top-item"><span class="hero-top-rank">{i}</span>'
        f'<span class="hero-top-name">{sector_meta[r["entity_id"]]["name"]}</span>'
        f'<span class="hero-top-val up mono">{r["score"]:.1f}</span></div>'
        for i, r in enumerate(ranked_by_score, 1)
    )

    sox_status_kr = {"CONFIRMS": "SOX 방향과 SOXL/SOXS 일치", "MIXED": "SOX 확인신호 혼재",
                      "CONTRADICTS": "SOX 확인신호 모순", "MISSING": "SOX 데이터 없음",
                      "PRIMARY_ONLY": "SOX 단독 신호"}.get(sox.get("status"), sox.get("status"))
    sox_return = sox.get("sox_return_pct")
    sox_line = f'^SOX {sox_return:+.2f}%  ({sox_status_kr}, 보조조정 {sox.get("adjustment", 0):+.1f}점)' \
        if sox_return is not None else sox_status_kr

    rows_html = []
    for r in scored:
        sid = r["entity_id"]
        meta = sector_meta[sid]
        score = r["score"]
        label = r.get("data_quality")
        strength = _strength_from_score(score)
        cls, emoji = STRENGTH_STYLE.get(strength, ("flat", "⚪"))
        score_str = f"{score:.1f}" if score is not None else "MISSING"
        table_rows = render_sector_table(sector_stocks.get(sid, []), members_lookup, name_ko_lookup)
        components = r.get("components")
        comp_line = ""
        if components:
            parts = [f"{k}: {v:.1f}" if isinstance(v, (int, float)) else f"{k}: -" for k, v in components.items()]
            comp_line = f'<div class="component-line">구성요소(0~100) — {" · ".join(parts)}</div>'

        rows_html.append(f"""<details class="group-item">
<summary>
  <span class="g-name">{meta['name']}</span>
  <span class="g-score mono">{score_str}</span>
  <span class="g-label {cls}">{emoji} {strength}</span>
  <span class="g-quality">{label}</span>
</summary>
{comp_line}
<div class="stock-table-wrap">
<table class="stock-table">
<thead><tr><th>종목</th><th>상태</th><th class="num">등락률</th><th class="num">가격</th><th class="num">시가총액</th><th class="num">거래금액</th></tr></thead>
<tbody>
{table_rows}
</tbody>
</table>
</div>
</details>""")

    generated_kst = datetime.fromisoformat(pr["generated_at"].replace("Z", "+00:00")).astimezone(
        __import__("datetime").timezone(__import__("datetime").timedelta(hours=9))
    )

    html = f"""<title>Yeonchimo AI Market · US Sector Score — {trade_date}</title>
<style>{CSS}</style>

<div class="masthead">
  <div class="wordmark">Yeonchimo AI Market · PHASE 3</div>
  <h1>US Close Wrap — {trade_date[:4]}.{trade_date[4:6]}.{trade_date[6:]}</h1>
  <div class="date">{generated_kst.strftime('%Y년 %m월 %d일 %H:%M')} KST 발행 · run_id {pr['id']}</div>
  <div class="caveat">📌 이 스코어는 명세 7.1의 4개 구성요소(등락강도/거래금액강도/Breadth/핵심리더십)만 반영합니다. Catalyst(뉴스·실적)는 PHASE 5 대상이라 항상 제외되어 있어 모든 섹터가 PARTIAL 품질입니다.</div>
  <div class="disclaimer">본 리포트는 투자 조언이 아니며, 매수/매도 신호가 아닙니다. 데이터 출처: yfinance.</div>
</div>

{render_index_row()}

<div class="hero">
  <div class="hero-kospi">
    <div><div class="lbl">SOX 반도체지수</div></div>
    <div class="val {'up' if (sox_return or 0) >= 0 else 'down'}">{f'{sox_return:+.2f}%' if sox_return is not None else 'N/A'}</div>
  </div>
  <div class="hero-section-lbl">US Sector Score TOP 3</div>
  {top_html}
  <div class="hero-divergence">
    <div class="hero-div-label">SOX / SOXL / SOXS 확인 신호</div>
    <ul><li>{sox_line}</li></ul>
  </div>
  <div class="hero-daycount">17개 섹터 전체 표시 · 고정 display_order 유지 (명세 6.5)</div>
</div>

<div class="card">
  <h2><span class="idx">③</span>US SECTOR SCORE — 17개 섹터 (고정 순서)</h2>
  <p class="muted" style="margin-bottom:14px;">섹터명 / 점수(0~100) / 강도등급 / 데이터품질 — 항목을 눌러 구성종목별 상세를 확인하세요.</p>
  <div class="group-list">
{"".join(rows_html)}
  </div>
</div>

<footer>
  <div>mapping_version {pr['mapping_version']} · model_version {pr['model_version']}</div>
  <div>이 스냅샷은 불변입니다 — 07:00 이후 동일 trade_date로 재계산되지 않습니다.</div>
</footer>
"""
    return html


def _strength_from_score(score):
    if score is None:
        return "MISSING"
    bands = [(85, "VERY_STRONG"), (70, "STRONG"), (55, "POSITIVE"), (45, "NEUTRAL"), (30, "WEAK"), (0, "VERY_WEAK")]
    for threshold, label in bands:
        if score >= threshold:
            return label
    return "VERY_WEAK"


if __name__ == "__main__":
    import sys as _sys
    date_arg = _sys.argv[1] if len(_sys.argv) > 1 else "20260820"
    html = build_html(date_arg)
    out_path = Path(__file__).parent / "data" / f"report_{date_arg}.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"저장 완료: {out_path}")
