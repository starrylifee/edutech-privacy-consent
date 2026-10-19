"""동의서 표를 클릭 복사용 HTML 한 장으로 만든다.

학교마다 가정통신문 양식이 달라서, 표만 뽑아 자기 양식(한글·워드)에 붙여 넣는 경우가 많다.
- 제품 칸을 누르면 그 제품 블록의 글이 복사된다.
- '표 전체 복사'는 표 모양(HTML)째 클립보드에 넣어 한글·워드에 붙이면 표로 들어간다.
- '[확인 필요]'는 노랗게 표시된다.
- 인터넷 연결·외부 요청 없음.

사용법: python build_html.py 설정.json -o 동의서표.html
"""
import argparse
import html
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_review import load_products  # noqa: E402

REFUSAL = ("개인정보 수집․이용에 대한 동의를 거부할 수 있습니다. 동의를 거부할 경우 해당 에듀테크를 "
           "활용한 맞춤형 학습 지원 및 수업 활동 참여가 제한될 수 있습니다.")
R = "해당 학년도 교육과정 종료 시까지"


def e(s):
    s = html.escape(str(s or ""))
    return s.replace("[확인 필요]", '<mark class="todo">[확인 필요]</mark>')


def line(label, value):
    return f'<p><span class="lb">{e(label)}</span> <b>{e(value)}</b></p>'


def block_lines(p):
    """제품 하나의 텍스트(복사용)와 HTML 조각을 함께 만든다."""
    name = p["name"].replace("\n", " ")
    tp = p.get("third_party") or {}
    items = p.get("items") or "성명, 학년, 반, 번호"
    purpose = p.get("purpose") or "교육과정 운영 및 교과 활동, 에듀테크 서비스 회원 가입 및 학습 관리"
    ret = p.get("retention") or R
    rows = []
    rows.append(("collect", [
        ("1. 수집·이용 목적:", purpose), ("2. 수집 항목:", items), ("3. 보유 및 이용 기간:", ret), ("4.", REFUSAL)],
        "개인정보 수집·이용에  □ 동의합니다.    □ 동의하지 않습니다."))
    rows.append(("third", [
        ("◆ 개인정보의 제3자 제공 고지", ""),
        ("1. 개인정보를 제공받는 자:", tp.get("receiver") or p.get("vendor") or name),
        ("2. 제공받는 자의 이용 목적:", tp.get("purpose") or "에듀테크 서비스 내 학생 계정 생성 및 서비스 제공"),
        ("3. 제공하는 개인정보 항목:", tp.get("items") or items),
        ("4. 제공받는 자의 보유 및 이용기간:", tp.get("retention") or ret)], None))
    if p.get("foreign"):
        tr = p.get("transfer") or {}
        country = p.get("country") or "국외"
        rows.append(("transfer", [
            ("◆ 개인정보 국외 이전 고지", ""),
            ("1. 개인정보를 이전받는 자 :", tr.get("receiver") or tp.get("receiver") or name),
            ("2. 이전되는 국가, 시기 및 방법 :", tr.get("country_method") or
             f"{name}({country})에서 제공하는 클라우드 서버에 저장(서비스 제공자의 서버 위치에 따라 변경 가능)"),
            ("3. 이전되는 개인정보 항목 :", tr.get("items") or tp.get("items") or items),
            ("4. 보유 및 이용 기간 :", tr.get("retention") or ret)], None))

    text = [f"■ 구분: {name}"]
    cells = []
    for kind, lines, agree in rows:
        cell = []
        for lb, val in lines:
            text.append((lb + " " + val).strip())
            if val == "":
                cell.append(f'<p class="hd">{e(lb)}</p>')
            else:
                cell.append(line(lb, val))
        if agree:
            text.append(agree)
            cell.append(f'<div class="agree">{e(agree)}</div>')
        cells.append((kind, "".join(cell)))
    return name, "\n".join(text), cells


def build(cfg, products):
    blocks = []
    all_text = []
    for i, p in enumerate(products):
        name, text, cells = block_lines(p)
        all_text.append(text)
        n = len(cells)
        trs = []
        for j, (kind, inner) in enumerate(cells):
            first = f'<td class="name" rowspan="{n}" data-copy="{html.escape(text)}" title="누르면 이 제품 블록 전체가 복사됩니다">{e(name)}</td>' if j == 0 else ""
            trs.append(f'<tr class="{kind}{" first" if j == 0 else ""}">{first}<td class="body">{inner}</td></tr>')
        blocks.append("".join(trs))
    table = ('<table id="consent"><thead><tr><th class="c1">구분</th><th>개인정보 수집·이용·제공 동의 및 제3자 제공 등 고지</th></tr></thead>'
             '<tbody>' + "".join(blocks) + '</tbody></table>')
    title = f"{cfg.get('school', '')} 에듀테크 개인정보 동의서 표".strip()
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<style>
:root{{--line:#444;--fill:#DFE6F7;--todo:#FFF3A3}}
body{{font-family:"HCR Dotum","함초롬돋움","Malgun Gothic",sans-serif;color:#111;margin:24px;background:#fff}}
h1{{font-size:18px;margin:0 0 6px}} .sub{{color:#555;font-size:13px;margin:0 0 14px}}
.bar{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}}
button{{font:inherit;font-size:14px;padding:7px 14px;border:1px solid #888;border-radius:6px;background:#f6f6f6;cursor:pointer}}
button:hover{{background:#e9e9e9}}
table{{border-collapse:collapse;width:100%;max-width:820px;font-size:13.5px;line-height:1.5}}
th{{background:var(--fill);border-top:1.5px solid var(--line);border-bottom:2px double var(--line);padding:6px;font-size:16px}}
th.c1,td.name{{width:84px;text-align:center}}
td{{border-bottom:1px solid var(--line);vertical-align:middle;padding:6px 8px}}
td.name{{border-right:1px solid var(--line);font-weight:700;cursor:pointer}}
td.name:hover{{background:#f3f6ff}}
tr.first td{{border-top:2px double var(--line)}}
tr.transfer td.body{{border-top:2px double var(--line)}}
td.body p{{margin:2px 0;padding-left:1.4em;text-indent:-1.4em}}
td.body p.hd{{font-weight:700;padding-left:0;text-indent:0;margin-top:4px}}
.lb{{font-weight:400}}
.agree{{margin:8px 6px 4px;padding:5px;border:1px solid var(--line);background:var(--fill);text-align:center;font-weight:700}}
mark.todo{{background:var(--todo);padding:0 3px}}
#toast{{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#222;color:#fff;padding:8px 14px;border-radius:6px;opacity:0;transition:.2s}}
#toast.on{{opacity:1}}
@media print{{.bar,.sub,#toast{{display:none}} body{{margin:0}}}}
</style></head><body>
<h1>{e(title)}</h1>
<p class="sub">제품 이름 칸을 누르면 그 블록의 글이 복사됩니다. "표 전체 복사"는 표 모양째 복사되어 한글·워드에 붙여 넣으면 표로 들어갑니다. 노란 [확인 필요]는 업체나 담당자에게 확인한 뒤 채우세요.</p>
<div class="bar"><button id="copyAll">표 전체 복사</button><button id="copyText">글자만 복사</button><button onclick="window.print()">인쇄</button></div>
{table}
<div id="toast">복사됨</div>
<script>
const ALL_TEXT = {json.dumps(chr(10).join(all_text), ensure_ascii=False)};
function toast(m){{const t=document.getElementById('toast');t.textContent=m;t.classList.add('on');setTimeout(()=>t.classList.remove('on'),1200);}}
async function copyText(s){{try{{await navigator.clipboard.writeText(s);toast('복사됨');}}catch(e){{const ta=document.createElement('textarea');ta.value=s;document.body.appendChild(ta);ta.select();document.execCommand('copy');ta.remove();toast('복사됨');}}}}
async function copyHtml(el){{const h=el.outerHTML, t=el.innerText;try{{await navigator.clipboard.write([new ClipboardItem({{'text/html':new Blob([h],{{type:'text/html'}}),'text/plain':new Blob([t],{{type:'text/plain'}})}})]);toast('표 복사됨 — 한글·워드에 붙여 넣으세요');}}catch(e){{copyText(t);}}}}
document.querySelectorAll('td.name').forEach(td=>td.addEventListener('click',()=>copyText(td.dataset.copy)));
document.getElementById('copyAll').addEventListener('click',()=>copyHtml(document.getElementById('consent')));
document.getElementById('copyText').addEventListener('click',()=>copyText(ALL_TEXT));
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    cfg, products = load_products(a.config)
    out = build(cfg, products)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(out)
    print("saved", a.out, len(products), "products")


if __name__ == "__main__":
    main()
