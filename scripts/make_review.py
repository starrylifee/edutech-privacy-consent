"""동의서에 들어간 제품별 값과 약관 근거 문장을 나란히 적은 교사 검토용 근거표(md)를 만든다.

사용법: python make_review.py 설정.json -o 근거표.md
"""
import argparse
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

FIELDS = [
    ("vendor", "운영 회사·기관"),
    ("country", "국가(서버·본사)"),
    ("items", "수집 항목"),
    ("purpose", "수집·이용 목적"),
    ("retention", "보유 기간"),
    ("third_party", "제3자 제공"),
    ("outsourcing", "처리 위탁"),
    ("children", "14세 미만 아동 조항"),
    ("dpo", "보호책임자·연락처"),
]


def load_products(config_path):
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)
    base = os.path.dirname(os.path.abspath(config_path))
    products = list(cfg.get("products", []))
    for pf in cfg.get("product_files", []):
        path = pf if os.path.isabs(pf) else os.path.join(base, pf)
        with open(path, encoding="utf-8") as f:
            products.append(json.load(f))
    return cfg, products


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    cfg, products = load_products(a.config)

    lines = ["# 동의서 근거표 (배부 전 교사 검토용)", "",
             f"학교: {cfg.get('school', '')} / 제출 기한: {cfg.get('deadline', '')} / 발송일: {cfg.get('date', '')}", "",
             "동의서에 적힌 값(왼쪽)이 약관 원문(오른쪽 근거)과 맞는지 확인한 뒤 배부하세요. "
             "약관은 수시로 바뀌므로 `_source.url`에서 최신본을 한 번 더 확인하는 것이 안전합니다.", ""]
    for p in products:
        name = p["name"].replace("\n", " ")
        src = p.get("_source", {})
        ex = p.get("_extracted", {})
        lines += [f"## {name}", "",
                  f"- 약관 출처: {src.get('url', '미기재')} (확인일 {src.get('extracted_at', '')}, 약관 버전 {src.get('policy_version', '미기재')})",
                  f"- 국외 서비스: {'예 → 국외이전 고지 포함' if p.get('foreign') else '아니오'}", "",
                  "| 동의서 항목 | 동의서에 적은 값 | 약관에서 뽑은 값 | 근거 문장 |",
                  "|---|---|---|---|"]
        doc_vals = {
            "vendor": p.get("vendor", ""), "country": p.get("country", ""), "items": p.get("items", ""),
            "purpose": p.get("purpose", ""), "retention": p.get("retention", ""),
            "third_party": (p.get("third_party") or {}).get("receiver", ""),
            "outsourcing": "(동의서에는 미기재)", "children": "(보호자 서명란)", "dpo": "(동의서에는 미기재)",
        }
        for key, label in FIELDS:
            e = ex.get(key, {})
            val = e.get("value", "") if isinstance(e, dict) else e
            quote = e.get("quote", "") if isinstance(e, dict) else ""
            cell = lambda s: str(s).replace("|", "／").replace("\n", " ")
            lines.append(f"| {label} | {cell(doc_vals[key])} | {cell(val)} | {cell(quote)} |")
        if ex.get("notes"):
            lines += ["", f"**주의:** {ex['notes']}"]
        lines.append("")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("saved", a.out)


if __name__ == "__main__":
    main()
