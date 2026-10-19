"""개인정보처리방침 페이지(HTML)를 받아 본문 텍스트로 저장한다.

사용법: python html2text.py URL 저장파일.txt            (curl로 받음, 브라우저 UA)
        python html2text.py 받아둔.html 저장파일.txt     (이미 받은 HTML 파일)
본문이 300자 미만이면 자바스크립트 렌더링·봇 차단일 가능성이 크니 WebFetch → 크롬 → 앱스토어 링크 순으로 시도한다.
"""
import html
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def to_text(raw):
    body = re.sub(r"<(script|style|noscript)[\s\S]*?</\1>", "", raw, flags=re.I)
    body = re.sub(r"<br\s*/?>|</p>|</li>|</tr>|</h\d>|</div>|</td>|</th>", "\n", body, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", body))
    t = re.sub(r"[ \t\u00a0]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    return t.strip()


def main():
    src, out = sys.argv[1], sys.argv[2]
    if src.startswith("http"):
        r = subprocess.run(["curl", "-sk", "-L", "-A", UA, "-w", "\n%{http_code} %{url_effective}", src],
                           capture_output=True)
        raw = r.stdout.decode("utf-8", errors="replace")
        raw, _, status = raw.rpartition("\n")
        print("HTTP", status)
    else:
        raw = open(src, encoding="utf-8", errors="replace").read()
    t = to_text(raw)
    open(out, "w", encoding="utf-8").write(t)
    print(f"saved {out} ({len(t)} chars)")
    if len(t) < 300:
        print("!! 본문이 거의 없음: JS 렌더링/봇 차단 가능성. WebFetch → 크롬 → 앱스토어 약관 링크 순으로 시도.")


if __name__ == "__main__":
    main()
