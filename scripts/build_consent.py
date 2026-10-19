"""에듀테크 개인정보 수집·이용·제공 동의서(가정통신문) hwpx 생성기.

서울시교육청 '(서식) 개인정보 수집이용제공 동의 안내 양식(예시)_0305' hwpx를 껍데기로 쓰고,
제품별 데이터(JSON)를 표 행으로 채워 넣는다.

사용법:
    python build_consent.py 입력.json -o 출력.hwpx [--template 양식.hwpx]

입력 JSON 구조는 ../data/example.json 참고.
"""
import argparse
import copy
import json
import math
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TEMPLATE = os.path.join(HERE, "..", "template", "서울교육청_동의서양식_20260305.hwpx")

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"

DEFAULT_REFUSAL = ("개인정보 수집․이용에 대한 동의를 거부할 수 있습니다. 동의를 거부할 경우 "
                   "해당 에듀테크를 활용한 맞춤형 학습 지원 및 수업 활동 참여가 제한될 수 있습니다.")
DEFAULT_RETENTION = "해당 학년도 교육과정 종료 시까지"
DEFAULT_TP_PURPOSE = "에듀테크 서비스 내 학생 계정 생성 및 서비스 제공"


# ---------------------------------------------------------------- 공통 유틸
def register_namespaces(xml_text):
    for prefix, uri in re.findall(r'xmlns:([\w\-]+)="([^"]+)"', xml_text[:4000]):
        ET.register_namespace(prefix, uri)


def build_parent_map(root):
    return {c: p for p in root.iter() for c in p}


def para_text(p):
    """메모 서브리스트를 제외한 문단 텍스트."""
    out = []

    def walk(e):
        if e.tag == HP + "fieldBegin" and e.get("type") == "MEMO":
            return
        if e.tag == HP + "t":
            out.append(e.text or "")
        for c in e:
            walk(c)

    walk(p)
    return "".join(out)


def strip_lineseg(p):
    for lsa in p.findall(HP + "linesegarray"):
        p.remove(lsa)


def text_runs(p):
    """표·컨트롤이 없는 순수 텍스트 run 목록."""
    runs = []
    for r in p.findall(HP + "run"):
        if r.find(HP + "tbl") is not None or r.find(HP + "ctrl") is not None or r.find(HP + "secPr") is not None:
            continue
        runs.append(r)
    return runs


def set_run_text(run, text):
    for c in list(run):
        run.remove(c)
    t = ET.SubElement(run, HP + "t")
    t.text = text


LABEL_CHARPR = "17"    # 보통 10pt 검정
CONTENT_CHARPR = "18"  # 굵게 10pt 검정
NAME_CHARPR = "24"     # 굵게 10pt 검정 (제품명 칸)


def set_para_labeled(p, label, content, label_cp=LABEL_CHARPR, content_cp=CONTENT_CHARPR):
    """문단을 [라벨 run][내용 run] 두 개로 정리하고 글자 모양을 통일한다
    (양식의 빨간 강조·밑줄 글자 모양을 지운다)."""
    runs = text_runs(p)
    if not runs:
        raise ValueError("텍스트 run이 없는 문단: " + para_text(p))
    r0 = runs[0]
    r1 = runs[1] if len(runs) > 1 else None
    for r in runs[2:]:
        p.remove(r)
    if label:
        set_run_text(r0, label)
        r0.set("charPrIDRef", label_cp)
        if r1 is None:
            r1 = copy.deepcopy(r0)
            idx = list(p).index(r0)
            p.insert(idx + 1, r1)
        set_run_text(r1, content)
        r1.set("charPrIDRef", content_cp)
    else:
        set_run_text(r0, content)
        r0.set("charPrIDRef", content_cp)
        if r1 is not None:
            p.remove(r1)
    strip_lineseg(p)


def set_cell_lines(tc, lines, cp):
    """셀의 첫 문단을 줄 수만큼 복제해 한 줄씩 넣는다(줄바꿈 문자를 넣지 않는 규칙)."""
    sub = tc.find(HP + "subList")
    base = sub.findall(HP + "p")[0]
    for extra in sub.findall(HP + "p")[1:]:
        sub.remove(extra)
    sub.remove(base)
    for line in lines:
        q = copy.deepcopy(base)
        set_para_labeled(q, None, line, content_cp=cp)
        sub.append(q)


def est_lines(text, width_hwp=40000, size=1000):
    """글자 폭 근사로 줄 수 추정 (전각 1000, 반각 500 HWPUNIT, 10pt 기준)."""
    w = 0
    for ch in text:
        w += size if ord(ch) > 0x2E80 else size * 0.5
    return max(1, math.ceil(w / width_hwp))


def cell_height_for(texts, line_h=1250, pad=550):
    return sum(est_lines(t) for t in texts) * line_h + pad


# ---------------------------------------------------------------- 메모 제거
def remove_memos(root):
    pm = build_parent_map(root)
    begin_ids = set()
    for ctrl in list(root.iter(HP + "ctrl")):
        fb = ctrl.find(HP + "fieldBegin")
        if fb is not None and fb.get("type") == "MEMO":
            begin_ids.add(fb.get("id"))
            pm[ctrl].remove(ctrl)
    pm = build_parent_map(root)
    for ctrl in list(root.iter(HP + "ctrl")):
        fe = ctrl.find(HP + "fieldEnd")
        if fe is not None and fe.get("beginIDRef") in begin_ids:
            pm[ctrl].remove(ctrl)
    return len(begin_ids)


# ---------------------------------------------------------------- 표 행 생성
class IdGen:
    def __init__(self, start):
        self.n = start

    def next(self):
        self.n += 1
        return str(self.n)


def renumber(elems, pid, tid):
    for e in elems:
        for p in e.iter(HP + "p"):
            p.set("id", pid.next())
        for t in e.iter(HP + "tbl"):
            t.set("id", tid.next())


def cell_of(tr, col):
    for tc in tr.findall(HP + "tc"):
        if tc.find(HP + "cellAddr").get("colAddr") == str(col):
            return tc
    return None


def cell_paras(tc):
    return tc.find(HP + "subList").findall(HP + "p")


def set_cell_size(tc, height=None, row_span=None, row_addr=None):
    if height is not None:
        tc.find(HP + "cellSz").set("height", str(int(height)))
    if row_span is not None:
        tc.find(HP + "cellSpan").set("rowSpan", str(row_span))
    if row_addr is not None:
        tc.find(HP + "cellAddr").set("rowAddr", str(row_addr))


def fill_product_rows(rows, prod):
    """rows: 복제한 tr 목록 (해외 3행 / 국내 2행). prod: 제품 dict."""
    name = prod["name"]
    purpose = prod.get("purpose") or "교육과정 운영 및 교과 활동, 에듀테크 서비스 회원 가입 및 학습 관리"
    items = prod.get("items") or "학년, 반, 번호, 성명"
    retention = prod.get("retention") or DEFAULT_RETENTION
    refusal = prod.get("refusal") or DEFAULT_REFUSAL
    tp = prod.get("third_party") or {}
    tp_receiver = tp.get("receiver") or prod.get("vendor") or name
    tp_purpose = tp.get("purpose") or DEFAULT_TP_PURPOSE
    tp_items = tp.get("items") or items
    tp_retention = tp.get("retention") or retention

    heights = []

    # 1행: 구분(제품명) + 수집·이용 동의
    c0 = cell_of(rows[0], 0)
    set_cell_lines(c0, [ln for ln in name.split("\n") if ln.strip()], NAME_CHARPR)
    c1 = cell_of(rows[0], 1)
    ps = cell_paras(c1)
    set_para_labeled(ps[0], "1. 수집·이용 목적: ", purpose)
    set_para_labeled(ps[1], "2. 수집 항목: ", items)
    set_para_labeled(ps[2], "3. 보유 및 이용 기간: ", retention)
    set_para_labeled(ps[3], "4. ", refusal)
    strip_lineseg(ps[4])  # 체크박스(중첩 표) 문단
    h = cell_height_for(["1. 수집·이용 목적: " + purpose, "2. 수집 항목: " + items,
                         "3. 보유 및 이용 기간: " + retention, "4. " + refusal]) + 2200
    set_cell_size(c1, height=h, row_addr=None)
    heights.append(h)

    # 2행: 제3자 제공 고지
    c1 = cell_of(rows[1], 1)
    ps = cell_paras(c1)
    strip_lineseg(ps[0])
    set_para_labeled(ps[1], "1. 개인정보를 제공받는 자: ", tp_receiver)
    set_para_labeled(ps[2], "2. 제공받는 자의 이용 목적: ", tp_purpose)
    set_para_labeled(ps[3], "3. 제공하는 개인정보 항목: ", tp_items)
    set_para_labeled(ps[4], "4. 제공받는 자의 보유 및 이용기간: ", tp_retention)
    h = cell_height_for(["◆ 개인정보의 제3자 제공 고지", "1. 개인정보를 제공받는 자: " + tp_receiver,
                         "2. 제공받는 자의 이용 목적: " + tp_purpose, "3. 제공하는 개인정보 항목: " + tp_items,
                         "4. 제공받는 자의 보유 및 이용기간: " + tp_retention])
    set_cell_size(c1, height=h)
    heights.append(h)

    # 3행: 국외 이전 고지 (해외 서비스만)
    if len(rows) == 3:
        tr = prod.get("transfer") or {}
        country = prod.get("country") or "국외"
        receiver = tr.get("receiver") or tp_receiver
        flat_name = name.replace("\n", "")
        method = tr.get("country_method") or (
            f"{flat_name}({country})에서 제공하는 클라우드 서버에 저장(서비스 제공자의 서버 위치에 따라 변경 가능)")
        t_items = tr.get("items") or tp_items
        t_ret = tr.get("retention") or tp_retention
        c1 = cell_of(rows[2], 1)
        ps = cell_paras(c1)
        strip_lineseg(ps[0])
        set_para_labeled(ps[1], "1. 개인정보를 이전받는 자 : ", receiver)
        set_para_labeled(ps[2], "2. 이전되는 국가, 시기 및 방법 : ", method)
        set_para_labeled(ps[3], "3. 이전되는 개인정보 항목 : ", t_items)
        set_para_labeled(ps[4], "4. 보유 및 이용 기간 : ", t_ret)
        h = cell_height_for(["◆ 개인정보 국외 이전 고지", "1. 개인정보를 이전받는 자 : " + receiver,
                             "2. 이전되는 국가, 시기 및 방법 : " + method, "3. 이전되는 개인정보 항목 : " + t_items,
                             "4. 보유 및 이용 기간 : " + t_ret])
        set_cell_size(c1, height=h)
        heights.append(h)

    set_cell_size(c0, height=sum(heights), row_span=len(rows))
    return rows


def rebuild_main_table(tbl, products, pid, tid):
    trs = tbl.findall(HP + "tr")
    header = trs[0]
    tpl_foreign = [copy.deepcopy(t) for t in trs[1:4]]
    tpl_domestic = [copy.deepcopy(t) for t in trs[4:6]]
    for t in trs:
        tbl.remove(t)
    tbl.append(header)
    row_addr = 1
    for prod in products:
        src = tpl_foreign if prod.get("foreign") else tpl_domestic
        rows = [copy.deepcopy(t) for t in src]
        fill_product_rows(rows, prod)
        renumber(rows, pid, tid)
        for r in rows:
            for tc in r.findall(HP + "tc"):
                set_cell_size(tc, row_addr=row_addr)
            tbl.append(r)
            row_addr += 1
    tbl.set("rowCnt", str(row_addr))


# ---------------------------------------------------------------- 본문 치환
def replace_text_everywhere(root, pairs):
    """모든 <hp:t>에서 단순 문자열 치환. 치환된 문단의 lineseg는 제거."""
    pm = build_parent_map(root)
    touched = set()
    for t in root.iter(HP + "t"):
        if not t.text:
            continue
        new = t.text
        for a, b in pairs:
            new = new.replace(a, b)
        if new != t.text:
            t.text = new
            e = t
            while e is not None and e.tag != HP + "p":
                e = pm.get(e)
            if e is not None:
                touched.add(e)
    for p in touched:
        strip_lineseg(p)


def drop_guidance_block(root):
    """첫 문단(secPr 문단)에 들어 있는 교육청 안내 표를 제거하고 빈 텍스트 run을 남긴다."""
    p0 = list(root)[0]
    runs = p0.findall(HP + "run")
    for r in runs:
        if r.find(HP + "tbl") is not None:
            p0.remove(r)
    first = runs[0]
    new_run = ET.Element(HP + "run", {"charPrIDRef": first.get("charPrIDRef", "0")})
    ET.SubElement(new_run, HP + "t")
    p0.insert(list(p0).index(first) + 1, new_run)
    lsa = p0.find(HP + "linesegarray")
    if lsa is not None:
        for ls in list(lsa):
            lsa.remove(ls)
        ET.SubElement(lsa, HP + "lineseg", {
            "textpos": "0", "vertpos": "0", "vertsize": "1000", "textheight": "1000", "baseline": "850",
            "spacing": "600", "horzpos": "0", "horzsize": "47736", "flags": "393216"})


# ---------------------------------------------------------------- 메인
def build(config, template, out_path):
    with zipfile.ZipFile(template) as z:
        names = z.namelist()
        raw = {n: z.read(n) for n in names}
    xml_text = raw["Contents/section0.xml"].decode("utf-8")
    register_namespaces(xml_text)
    root = ET.fromstring(xml_text)

    n_memo = remove_memos(root)
    drop_guidance_block(root)

    paras = list(root)
    # 본문 표(제품 목록): 'A에듀테크'가 들어 있는 최상위 표
    main_tbl = None
    for p in paras:
        for t in p.findall("./" + HP + "run/" + HP + "tbl"):
            if "A에듀테크" in "".join(x.text or "" for x in t.iter(HP + "t")):
                main_tbl = t
    if main_tbl is None:
        raise RuntimeError("양식에서 제품 목록 표를 찾지 못했습니다.")

    products = list(config.get("products", []))
    base_dir = os.path.dirname(os.path.abspath(config.get("_config_path", ".")))
    for pf in config.get("product_files", []):
        path = pf if os.path.isabs(pf) else os.path.join(base_dir, pf)
        with open(path, encoding="utf-8") as f:
            products.append(json.load(f))
    if not products:
        raise RuntimeError("products 또는 product_files가 비어 있습니다.")
    config["products"] = products

    pid, tid = IdGen(900000000), IdGen(910000000)
    rebuild_main_table(main_tbl, products, pid, tid)

    school = config.get("school", "○○학교")
    pairs = [
        ("(예시)", ""),
        ("OO월 OO일(요일)까지", config.get("deadline", "OO월 OO일(요일)") + "까지"),
        ("○○학교장 귀하", school + "장 귀하"),
        ("2026.    .      .", config.get("date", "2026.    .      .")),
    ]
    if config.get("title_line1"):
        pairs.append(("AI(생성형 AI 포함) 및 에듀테크 활용 교육을 위한", config["title_line1"]))
    if config.get("title_line2"):
        pairs.append(("회원 가입 및 개인정보 수집‧이용‧제공 동의 안내", config["title_line2"]))
    if config.get("intro"):
        pairs.append(("본교에서는 디지털 대전환 시대를 맞아 학생들의 미래 역량을 강화하기 위해 AI 및 에듀테크 활용 수업을 실시하고자 합니다.",
                      config["intro"]))
    replace_text_everywhere(root, pairs)

    # 선택 문단 제거: "항목이 많아 복잡해 보이실 수 있으나..." (서울 메모: 선택 사항)
    if config.get("drop_optional_paragraph", False):
        for p in list(root):
            if para_text(p).strip().startswith("항목이 많아 복잡해"):
                root.remove(p)

    # 메모 모양 참조 제거(메모를 지웠으므로)
    out_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>' + ET.tostring(root, encoding="unicode")

    # 미리보기 텍스트
    prv = []
    for p in root.iter(HP + "p"):
        t = para_text(p).strip()
        if t:
            prv.append(t)
    raw["Preview/PrvText.txt"] = "\n".join(prv)[:2000].encode("utf-8")
    raw["Contents/section0.xml"] = out_xml.encode("utf-8")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with zipfile.ZipFile(out_path, "w") as zo:
        zo.writestr(zipfile.ZipInfo("mimetype"), raw["mimetype"], compress_type=zipfile.ZIP_STORED)
        for n in names:
            if n == "mimetype":
                continue
            zo.writestr(n, raw[n], compress_type=zipfile.ZIP_DEFLATED)
    # 잔여 검사
    leftover = re.findall(r"[A-H]에듀테크|\(예시\)|OO월", out_xml)
    return {"memos_removed": n_memo, "products": len(config["products"]), "leftover": leftover, "out": out_path}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--template", default=DEFAULT_TEMPLATE)
    a = ap.parse_args()
    with open(a.config, encoding="utf-8") as f:
        config = json.load(f)
    config["_config_path"] = os.path.abspath(a.config)
    info = build(config, a.template, a.out)
    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    main()
