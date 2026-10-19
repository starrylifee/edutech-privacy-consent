---
name: 에듀테크동의서
description: 수업에 쓸 에듀테크(캔바·패들렛·구글 워크스페이스·클래스팅·띵커벨·엔트리·미리캔버스·똑똑수학탐험대 등) 이름만 받아, 각 서비스의 개인정보처리방침을 찾아 읽고 수집항목·목적·보유기간·제3자 제공·국외이전·14세 미만 조항을 근거 문장과 함께 뽑은 뒤, 서울시교육청 양식(2026.3.5)으로 학부모용 「개인정보 수집·이용·제공 동의서」 hwpx와 교사 검토용 근거표를 만드는 스킬. 트리거 — "동의서 만들어줘", "개인정보 동의서", "에듀테크 동의서", "가정통신문 동의서", "캔바 패들렛 동의서", "학부모 동의서 hwpx", "개인정보 수집이용 동의서 생성". 학운위 심의안(에듀집 체크리스트)과는 별개 문서다.
---

# 에듀테크동의서 — 약관 → 학부모 동의서(hwpx)

학습지원 소프트웨어 학운위 심의와 별개로, 학생 개인정보를 수집하는 에듀테크를 쓰려면
학부모 동의를 받아야 한다(개인정보보호법 15·17·22·22조의2, 국외이전은 28조의8).
이 스킬은 제품명 → 약관 수집 → 추출 → 동의서 hwpx + 근거표까지 한 번에 한다.

이 스킬 폴더가 곧 저장소 루트다(scripts·template·data가 같이 들어 있다). 깃헙 starrylifee/edutech-privacy-consent.
사용자 PC에서는 `~/.claude/skills/에듀테크동의서` ↔ `C:\Project_Codes\20261019 학습지원소프트웨어` 정션(같은 폴더). 다른 PC는 `git clone`으로 설치.
아래 경로는 모두 이 폴더 기준. 설정 JSON의 `product_files`는 **설정 파일이 있는 폴더 기준** 상대경로.
Solar 추출 스크립트(`extract_policy.py`)는 사용자 PC의 업스테이지 스크립트를 호출한다. 다른 PC면 Claude가 같은 10개 항목을 직접 읽어 JSON을 쓴다(canva.json이 본보기).

## 절차

### 0. 입력 받기 (대화)
- 필수: 제품명 목록. 선택: 학교명, 제출 기한, 발송 날짜.
- 기본값: 학교 "○○초등학교", 기한 "OO월 OO일(요일)", 수집항목 "성명, 학년, 반, 번호", 보유기간 "해당 학년도 교육과정 종료 시까지".

### 1. 제품 DB 확인
`data/products/*.json`에 있으면 그대로 쓴다. `_source.extracted_at`이 6개월 넘었거나 `policy_version`이 오래됐으면 약관 페이지에서 시행일만 다시 확인한다.
보유(2026-10-19 기준 8종): canva, padlet, google_workspace_edu, miricanvas, classting, iscream_tkbell, entry, toctocmath.

### 2. 없는 제품은 약관 수집 → `data/policies/제품명_개인정보처리방침_YYYYMMDD.txt`
순서대로 시도한다. 본문 300자 미만이면 다음 방법으로.
1. `python scripts/html2text.py URL 저장.txt` (curl + 브라우저 UA). 국내 서비스 대부분 성공(toctocmath.kr/info-policy, tkbell.co.kr/user/privacy.do).
2. 홈이 리다이렉트되면 홈 HTML의 `href`에서 `privacy|개인정보` 링크를 grep 해서 찾는다.
3. 도움말센터(Zendesk)에 올라간 약관은 `https://도움말도메인/api/v2/help_center/ko/articles/글번호.json`이 curl로 열린다(미리캔버스). **검색 1위가 옛 버전일 수 있으니 시행일자를 비교해 최신본을 쓴다.**
4. WebFetch (리다이렉트 안내가 나오면 그 URL로 다시).
5. 봇 차단(403, "Security check")이면 크롬(claude-in-chrome)으로 열어 `get_page_text` (캔바·패들렛).
6. 사이트가 로그인 페이지로 넘기면 **앱스토어 페이지(apps.apple.com/kr/app/id…)의 "개인정보 처리방침" 링크**를 본다. 노션 등 외부 호스팅인 경우가 많다(클래스팅 → policies.classting.com).
7. Next.js 등 JS 전용 사이트는 번들 JS에서 약관 API(GraphQL 등)를 찾아 직접 호출할 수 있다(엔트리 playentry.org/terms/privacy → /graphql).
8. 그래도 못 받으면 사용자에게 앱 설정 화면의 처리방침 링크를 묻는다. **억지로 만들지 않는다.**
URL을 모르면 WebSearch `"제품명 개인정보처리방침"`. 해외 서비스는 영문 원문이 우선이고 한국어판은 참고.

### 3. 추출 → `data/products/제품id.json`
```
python scripts/extract_policy.py 약관.txt --name "제품명" --vendor "회사" --url URL --version "2026-09-15 시행" -o data/products/제품id.json
```
Solar가 10개 항목 + 근거 문장(quote)을 `_extracted`에 넣는다(1~2분). 그 다음 **Claude가 반드시 검수**한다:
- quote가 본문에 실제로 있는지 grep. 없거나 비면 본문을 읽고 고친다.
- 상단 필드(동의서에 찍히는 값)는 **학부모가 읽는 글**이다. 다음 규칙으로 다듬는다.
  - `items`: 학교가 계정 만들 때 넘기는 것 기준. "성명, 학년, 반, 번호" + 그 서비스 고유 항목(학교 계정 이메일, 작품, 학습 이력 등). IP·쿠키·OS·기기정보 같은 자동수집 항목, 교사·결제·마케팅 항목은 넣지 않는다(근거표의 `_extracted.items`에만 남긴다). 60자 안팎.
  - `retention`: 학교 기준 "해당 학년도 교육과정 종료 시까지"만. 서비스 자체 기간은 `_extracted.retention`에.
  - `purpose`: "교육과정 운영 및 ○○ 교과 활동, ○○ 학생 계정 생성 및 학습 관리" 꼴 한 줄.
  - `third_party.receiver`: 운영사(국가). `third_party.purpose`: "○○ 서비스 내 학생 계정 생성 및 서비스 제공".
  - **국외이전(`foreign: true` + `transfer`)을 넣는 조건**: ①운영사가 해외 법인 ②약관에 국외 이전 조항 ③해외 서버·클라우드 명시 ④해외 AI·클라우드 업체에 이전(위탁) 명시, 넷 중 하나라도 근거가 있을 때. 국내 회사인데 일부 위탁만 해외면 `transfer.receiver`에 그 업체(국가)를 적고 `country`는 "본사 대한민국 / 일부 국외이전: 미국(OpenAI)"처럼 구분한다. 근거가 없으면 넣지 않는다.
  - 서버 국가가 불명확하면 서울교육청 메모대로 "제품(국가)에서 제공하는 클라우드 서버에 저장(서비스 제공자의 서버 위치에 따라 변경 가능)".
  - 약관에 없어 채울 수 없는 값은 **"[확인 필요]"**라고 적는다(지어내지 않는다). 근거표 `notes`에 무엇을 누구에게 확인할지 적는다.
- `name`은 7자 안팎으로 줄을 나눈다: `"구글\n워크스페이스\n(교육용)"`, `"패들렛\n(Padlet)"`.
- `_source`: url, policy_version(시행일), policy_file(상대경로), extracted_at, method. `_review_required: true`.

### 4. 동의서 생성
설정 JSON(예: `data/example.json`, `data/all8.json`):
```json
{"school":"○○초등학교","deadline":"3월 10일(화)","date":"2026. 3. 3.",
 "product_files":["products/canva.json","products/padlet.json"]}
```
```
python scripts/build_consent.py 설정.json -o out/동의서_학교명_날짜.hwpx
python scripts/make_review.py   설정.json -o out/근거표_학교명_날짜.md
python scripts/build_html.py    설정.json -o out/동의서표_학교명_날짜.html
```
출력 JSON의 `leftover`가 `[]`여야 한다. HTML은 표만 담은 클릭 복사판이다(학교 자체 가정통신문 양식에 붙일 때 씀. 제품 칸 클릭 → 블록 복사, "표 전체 복사" → 한글·워드에 표로 붙음).

### 5. 렌더 검증 (필수, 한 번에 하나만 — 한글 COM은 동시 실행 금지)
```
python scripts/render_check.py out/동의서_….hwpx 110 ; taskkill /F /IM Hwp.exe
```
PNG를 열어 ①제품마다 [수집·이용 동의+체크박스][제3자 제공 고지][해외면 국외이전 고지] 블록 ②빨간 글씨·"(예시)"·"A에듀테크" 잔재 없음 ③제품명 칸 줄바꿈 ④서명란·학교장 귀하 ⑤학부모가 읽기에 너무 긴 항목은 없는지 확인. 제품 8종이면 5쪽쯤 나온다.

### 6. 전달
hwpx + 근거표를 주고, **배부 전 교사가 근거표로 대조**해야 한다고 한 줄 알린다. "[확인 필요]"가 남아 있으면 무엇을 확인해야 하는지 목록으로 준다. 법적 책임은 학교에 있고 약관은 수시로 바뀐다.

## 산출물 규칙
- hwpx는 `template/서울교육청_동의서양식_20260305.hwpx`를 껍데기로 쓴다(교육청 메모 10개 제거, 상단 교사용 안내 표 제거, 제품 행 복제). 글자 모양은 라벨 charPr 17 / 내용 18 / 제품명 24로 통일해 양식의 빨간 강조를 없앤다.
- 줄바꿈 문자를 `<hp:t>`에 넣지 않는다. 여러 줄은 문단 복제(`set_cell_lines`).
- mimetype STORE 첫 항목, 수정 문단의 linesegarray 제거 — hwpx 스킬 규칙 그대로.
- 여러 하위 에이전트로 제품을 병렬 추출할 때는 각자 JSON까지만 만들고 렌더·커밋은 메인이 한다.

## 알려진 한계
- 에듀집 체크리스트 자동 수집은 안 한다(심의안은 별도).
- 해외 서비스의 아동 조항은 "교사·학교가 보호자 동의를 대리"하는 구조가 많다(캔바·클래스팅). 동의서의 보호자 서명이 그 근거가 되므로 빠뜨리지 않는다.
- 구글 워크스페이스 고지에는 보유기간·서버 위치·수탁사 명단이 없다. 학교가 학년 말 계정 삭제로 보유기간을 지키는 구조다.
