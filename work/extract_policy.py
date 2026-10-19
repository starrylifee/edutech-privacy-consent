"""개인정보처리방침 본문(텍스트 파일)에서 동의서에 필요한 항목을 뽑아 JSON으로 만든다.

추출은 업스테이지 Solar Pro 4(무료 토큰)로 하고, 결과에는 근거 문장을 함께 남긴다.
Claude가 WebFetch/크롬으로 약관 본문을 받아 텍스트 파일로 저장한 뒤 이 스크립트를 돌린다.

사용법:
    python extract_policy.py 약관.txt --name "캔바" --vendor "Canva Pty Ltd" --url https://... -o ../data/products/canva.json
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SOLAR = r"C:\Users\forin\.claude\skills\solar\scripts\ask.py"  # 업스테이지 Solar 호출 스크립트(개인). 없으면 Claude가 직접 JSON 작성

PROMPT = """아래는 에듀테크 서비스 "{name}"의 개인정보처리방침(또는 개인정보 보호 고지) 전문이다.
학교가 학부모에게 보내는 '개인정보 수집·이용·제공 동의서'를 만들기 위해 다음 항목을 뽑아라.
반드시 본문에 적힌 내용만 쓰고, 없으면 "미기재"라고 적어라. 추측하지 마라.
규칙:
- 수집 항목은 "학생(아동) 계정" 또는 "학교·교사가 만들어 주는 학급 계정" 기준으로 뽑아라. 교사·통합회원·결제·마케팅 전용 항목은 빼고 notes에 뺐다고 적어라. 학생용 표가 따로 있으면 그 표를 우선한다.
- foreign은 "운영 회사가 해외 법인"이거나 "국외 이전 조항·국외 서버·해외 AI/클라우드 업체 이전"이 명시된 경우만 true. 본사 국가와 이전 국가를 country에 구분해 적어라(예: "본사 대한민국 / 일부 국외이전: 미국(OpenAI)").
- 국외 이전이 있으면 outsourcing에 이전받는 자·국가·항목을 꼭 적어라.
각 항목마다 근거가 된 조항 번호나 섹션 제목과 원문 한 문장을 quote에 그대로 적어라.

출력은 JSON 하나만. 다른 말은 하지 마라. 형식:
{{
  "vendor": {{"value": "운영 회사·기관명과 소재 국가", "quote": "..."}},
  "foreign": {{"value": true 또는 false (국외 사업자이거나 개인정보가 국외에 저장되면 true), "quote": "..."}},
  "country": {{"value": "서버 또는 본사 소재 국가(들)", "quote": "..."}},
  "items": {{"value": "회원가입·이용 시 수집하는 개인정보 항목(학생 계정 기준, 쉼표로 나열)", "quote": "..."}},
  "purpose": {{"value": "수집·이용 목적 요약(한 줄)", "quote": "..."}},
  "retention": {{"value": "보유·이용 기간", "quote": "..."}},
  "third_party": {{"value": "제3자 제공 대상과 목적(없으면 '동의 또는 법령 외 제공 없음')", "quote": "..."}},
  "outsourcing": {{"value": "처리 위탁 수탁사와 업무(쉼표 나열)", "quote": "..."}},
  "children": {{"value": "만 13세/14세 미만 아동 가입 정책과 법정대리인·학교 동의 방식", "quote": "..."}},
  "dpo": {{"value": "개인정보 보호책임자 또는 문의 연락처(국내대리인 포함)", "quote": "..."}},
  "notes": "동의서 작성 시 교사가 주의할 점 1~3줄"
}}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("policy_txt")
    ap.add_argument("--name", required=True)
    ap.add_argument("--vendor", default="")
    ap.add_argument("--url", default="")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--model", default="solar-pro4")
    ap.add_argument("--version", default="", help="약관 시행일·최종 수정일 (예: '2026-09-15 시행')")
    a = ap.parse_args()

    root = os.path.abspath(os.path.join(HERE, ".."))
    work_dir = os.path.join(root, "work")
    os.makedirs(work_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(a.out))[0]
    prompt_path = os.path.join(work_dir, stem + ".prompt.txt")
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(PROMPT.format(name=a.name))
    raw_path = os.path.join(work_dir, stem + ".solar.raw.txt")
    cmd = [sys.executable, "-X", "utf8", SOLAR, "--prompt-file", prompt_path, "--file", a.policy_txt,
           "--out", raw_path, "--model", a.model]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        sys.exit("Solar 호출 실패")
    raw = open(raw_path, encoding="utf-8").read()
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        sys.exit("JSON을 찾지 못함: " + raw[:300])
    data = json.loads(m.group(0))

    product = {
        "name": a.name,
        "vendor": a.vendor or data.get("vendor", {}).get("value", ""),
        "foreign": bool(data.get("foreign", {}).get("value", False)),
        "country": data.get("country", {}).get("value", ""),
        "purpose": "교육과정 운영 및 교과 활동, 에듀테크 서비스 회원 가입 및 학습 관리",
        "items": data.get("items", {}).get("value", ""),
        "retention": "해당 학년도 교육과정 종료 시까지",
        "third_party": {
            "receiver": a.vendor or data.get("vendor", {}).get("value", ""),
            "purpose": "에듀테크 서비스 내 학생 계정 생성 및 서비스 제공",
            "items": data.get("items", {}).get("value", ""),
            "retention": "해당 학년도 교육과정 종료 시까지"
        },
        "_extracted": data,
        "_source": {"url": a.url, "policy_version": a.version or "미기재",
                    "policy_file": os.path.relpath(os.path.abspath(a.policy_txt), root).replace("\\", "/"),
                    "extracted_at": datetime.date.today().isoformat(),
                    "method": f"Solar({a.model}) 추출 후 Claude 검수"},
        "_review_required": True
    }
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(product, f, ensure_ascii=False, indent=2)
    os.remove(prompt_path)
    print("saved", a.out)


if __name__ == "__main__":
    main()
