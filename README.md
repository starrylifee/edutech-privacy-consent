# 에듀테크 개인정보 동의서 생성기

수업에 쓰는 에듀테크(캔바, 패들렛, 똑똑! 수학탐험대 …)의 개인정보처리방침을 읽어
학부모에게 보내는 「개인정보 수집·이용·제공 동의서」를 한글(hwpx) 파일로 만듭니다.
양식은 서울시교육청이 2026년 3월 5일 배포한 예시 양식을 그대로 씁니다.

학습지원 소프트웨어 학운위 심의(에듀집 체크리스트)와는 별개 절차입니다. 심의를 받았더라도
학생 개인정보를 수집하는 서비스는 보호자 동의가 따로 필요합니다(개인정보보호법 제15·17·22·22조의2).

## 무엇이 나오나

- `out/동의서_….hwpx` — 배부용 가정통신문. 제품마다 [수집·이용 동의 + 체크박스] [제3자 제공 고지] [해외 서비스면 국외이전 고지] 블록이 들어갑니다.
- `out/근거표_….md` — 교사 검토용. 동의서에 적은 값과 약관 원문 문장을 나란히 보여 줍니다.

![예시 1쪽](docs/sample_p1.png)

## 사용법

```
pip install pywin32 pymupdf      # 렌더 확인용(한글 설치 PC)
python scripts/build_consent.py data/example.json -o out/동의서_예시.hwpx
python scripts/make_review.py   data/example.json -o out/근거표_예시.md
python scripts/render_check.py  out/동의서_예시.hwpx 110   # 한글로 열어 PDF/PNG 확인
```

설정 파일(`data/example.json`):

```json
{
  "school": "○○초등학교",
  "deadline": "3월 10일(화)",
  "date": "2026. 3. 3.",
  "product_files": ["products/canva.json", "products/padlet.json", "products/toctocmath.json"]
}
```

## 새 제품 추가

1. 그 서비스의 개인정보처리방침 본문을 텍스트로 저장합니다 (`data/policies/`).
2. 추출: `python scripts/extract_policy.py 약관.txt --name "제품명" --vendor "회사" --url URL -o data/products/제품.json`
   (업스테이지 Solar API를 쓰는 개인 스크립트를 호출합니다. 없으면 `data/products/canva.json`을 본보기로 직접 작성하세요.)
3. `_extracted`의 근거 문장을 보고 상단 필드(수집항목·목적·기간·제3자 제공·국외이전)를 다듬습니다.
4. 설정 파일의 `product_files`에 추가하고 다시 생성합니다.

제품 JSON 필드:

| 필드 | 뜻 |
|---|---|
| `name` | 동의서 왼쪽 칸 제품명. 길면 `"패들렛\n(Padlet)"`처럼 줄을 나눕니다 |
| `foreign`, `country` | 해외 서비스 여부와 국가. `true`면 국외이전 고지 블록이 붙습니다 |
| `items`, `purpose`, `retention` | 수집항목·목적·보유기간 |
| `third_party` | 제공받는 자·목적·항목·기간 |
| `transfer` | 국외이전: 이전받는 자·국가와 방법·항목·기간 |
| `_extracted` | 약관에서 뽑은 값과 근거 문장(근거표에 쓰임) |

## 주의

- 약관 해석은 AI가 돕지만 **배부 전 교사가 근거표로 대조**해야 합니다. 법적 책임은 학교에 있습니다.
- 약관은 수시로 바뀝니다. `_source.extracted_at`이 오래됐으면 다시 확인하세요.
- 해외 서비스(캔바·패들렛)는 봇 차단 때문에 약관을 자동으로 못 받을 수 있습니다. 브라우저로 열어 본문을 복사해 저장하면 됩니다.

## 구조

```
template/   서울시교육청 동의서 양식(hwpx)
scripts/    build_consent.py(hwpx 생성) · make_review.py(근거표) · extract_policy.py(약관 추출) · render_check.py(렌더 확인)
data/       example.json(설정) · products/(제품별 추출 JSON) · policies/(약관 원문)
out/        생성물
```

양식 출처: 서울시교육청 창의미래교육과 「(서식) 개인정보 수집이용제공 동의 안내 양식(예시)」 2026.3.5.
