---
name: im-ai-copyeditor
description: >-
  한국어 문장을 문장 단위로 첨삭·윤문하는 통합 명령. 맞춤법 → 문장(번역투·군더더기) → AI 문체 → 문체를 순서대로 한 문장씩 적용해, 뜻은 한 글자도 바꾸지 않고 사람 문체로 다듬는다. 트리거 — "한국어 첨삭", "문장 윤문", "글 다듬어줘", "im-ai-copyeditor", "문장 간소화", "번역체+AI 문체 같이 다듬어줘". 국립국어원 맞춤법과 번역학·문체 논문에 근거하며, 문장 교정은 책 『내 문장이 그렇게 이상한가요?』에서 영감을 받았다. 세부 명령 — 문장 교정(번역투·군더더기)만: -sentence / AI 문체만: -ai / 맞춤법·문체만: -grammar.
compatibility: 문장 분절 스크립트 실행에 python3(없으면 python) 필요.
metadata:
  version: "0.3.0"
  openclaw:
    requires:
      anyBins: [python3, python]
  hermes:
    category: writing
    tags: [korean, proofreading, humanize]
---

# im-ai-copyeditor — 통합 첨삭·윤문

한국어 텍스트를 **문장 부호 단위로 잘라** 한 문장씩 다듬는다. 정규식으로 일괄 치환하지 않고 워크시트의
각 문장 행을 읽고 다듬는다. 뜻·수치·고유명사·인용은 보존한다. 문장 간소화 규칙은 책 『내 문장이 그렇게
이상한가요?』에서 영감을 받았다.

스킬 디렉토리를 `$SKILL` 로 표기한다. Claude Code 는 `${CLAUDE_SKILL_DIR}` 나 `${CLAUDE_PLUGIN_ROOT}`,
그 외 하니스는 이 SKILL.md 가 있는 폴더다. 아래 명령의 `python3` 는 환경에 `python3` 가 없으면
`python`(Windows 는 `py -3`)으로 바꿔 실행한다.

## 절차

**Phase 0 — 상태 한 줄**
```
im-ai-copyeditor 통합 맞춤법→문장(번역투·군더더기)→AI 문체→문체 / run_id: {YYYY-MM-DD-NNN}
```
run_id 는 cwd 기준 `_workspace/{YYYY-MM-DD-NNN}/`. 당일 폴더가 있으면 NNN+1.

**Phase 1 — 입력 저장**
입력 텍스트나 파일을 `_workspace/{run_id}/01_input.txt` 로 저장.

**Phase 2 — 문장 분절**
```
python3 $SKILL/scripts/segment.py _workspace/{run_id}/01_input.txt --outdir _workspace/{run_id}
```
→ 원본 구조 정보 `segments.json` + 작업 파일 `worksheet.md` 생성. 나온 문장 수 N 을 확인한다.
제목·목록 행·표 셀도 텍스트 작업 칸으로 포함한다. N은 문장 수와 이 작업 칸을 합친 수다.
보호할 고유명사·기술 표현에 중간점이나 대시가 있으면 분절 전에 `--preserve-text '원문의 정확한 표현'`을 추가한다.
장식용 따옴표는 `--editable-quote '"정말"'`, 직접 인용이 아닌 작성자의 인용 블록은 `--edit-blockquotes`로 편집 대상에 포함한다. 분류 기준과 제외된 HTML 처리 방법은 공통 약속 2절을 따른다.

**Phase 3 — 룰북 로드. 네 개 모두**
순서대로 적용한다. 먼저 글 전체의 우세 문체를 정한다. 해요체·합니다체·한다체 중 하나로.
1. [맞춤법] `$SKILL/references/grammar-rules.md`
2. [문장 — 번역투·군더더기] `$SKILL/references/sentence-rules.md`
3. [AI 문체] `$SKILL/references/ai-tell-rules.md`
4. [문체] `$SKILL/references/style-guide.md`

공통 규칙은 `$SKILL/references/prime-directives.md` 를 따른다. 뜻 불변·건드리지 않는 것·변경량·자체검증.

**Phase 4 — 워크시트 행별 윤문. 정규식 일괄 치환 금지**
`worksheet.md` 의 각 문장 칸을 위에서 아래로 처리한다. 한 문장에:
- 맞춤법 → 문장(번역투·군더더기) → AI 문체 → 문체 순으로 룰을 적용해 **윤문:** 줄을 채운다.
- **규칙:** 줄에 적용한 번호를 적는다. G-1·S-1·AI-3·ST-1 처럼. 바꿀 게 없으면 윤문에 원문을 그대로 옮기고 규칙은 `변경없음`.
- 문장을 합치거나 나누거나 순서를 바꾸지 않는다. '그대로 둘 줄'은 건드리지 않는다.
- 제목·목록·표 셀의 텍스트도 빠짐없이 읽는다. 중간점과 구분용 대시는 공통 약속 8절에 따라 반드시 풀어 쓰되, 코드·인용·URL·숫자 범위·수식·지정한 고유명사는 보존한다.
- 수치·고유명사·직접 인용·영어 약어·법령은 보존한다. 뜻이 흔들리면 원문을 유지한다.

**Phase 5 — 재조립 + 가드**
```
python3 $SKILL/scripts/reassemble.py _workspace/{run_id}/segments.json _workspace/{run_id}/worksheet.md --out _workspace/{run_id}/final.md --check-punctuation
```
- ID 중복·누락·추가, 빈 윤문/규칙 칸, 잘못된 `변경없음` 표기는 종료 코드 2다. 작업표를 고치고 다시 실행한다. 칸 안의 문장 병합·분할과 의미 보존은 별도로 대조한다.
- 변경률 30% 초과는 의미 재검토 경고, 기본 상한 50% 초과는 종료 코드 3이다. 요청에 별도 상한이 있으면 `--max-change`로 명시한다. 통과하려고 임의로 높이지 않는다.
- 보호 표현/Markdown 행·열 변경 또는 중간점/구분용 대시 잔존은 종료 코드 4다. 해당 칸을 고치고 재검사한다. 통과하려고 검사 옵션을 빼거나 보호 예외를 늘리지 않는다.
- 검증 실패 시 기존 결과 파일은 유지된다. 이전 파일을 이번 실행의 결과로 반환하지 않는다.
- `부분 재조립`이면 제외 구간을 따로 검토한다. 스크립트 통과는 맞춤법·문체 교정 누락이 없다는 증명이 아니다.

**Phase 6 — 반환**
1. 한 줄 상태: `{완료|재검토|실패}. 텍스트 칸 {N}개 / 변경 {k}건 / 변경량 {x}%`. 공통 약속 7절에 따라 판정하며 변경률 0%도 정상이다.
2. 바뀐 문장만 전·후 표로. 원문·윤문·규칙
3. `final.md` 본문
4. 자체검증 6가지 결과

## 옵션
- `장르: 칼럼|리포트|블로그|공적` — 말투·장르 보존 기준. 생략하면 자동 추정.
- `강도: 보수|기본|적극` — 윤문 강도. 기본값은 기본.

## 주의
- 뜻 불변이 최상위. 수치·고유명사·인용 불가침.
- 통합 명령은 네 룰북을 다 쓴다. 하나만 원하면 `-grammar` · `-sentence` · `-ai` 명령을 쓴다.
- 문체는 입력의 격식을 따르되 글 안에서 일관되게 맞춘다. 한쪽으로 통일할 때 글 전체의 격식을 뒤집지 않는다.
