---
name: im-ai-copyeditor-ai
description: >-
  AI가 쓴 한글의 "AI 문체"를 문장 단위로 걷어 낸다. 기계적 나열, 결말 공식, 과장 어휘, 이모지·과한 불릿·볼드, 비슷한 길이·종결 반복, 표현을 자꾸 누그러뜨리기, 문두 접속사 남발, "것이다" 식 맺음을 자연스럽게. 뜻은 한 글자도 바꾸지 않는다. 트리거 — "AI 문체 빼줘", "GPT 문체 자연스럽게", "AI 같은 글 사람처럼", "휴머나이즈". 문장 교정(번역투·군더더기)까지: -sentence / 맞춤법·문체: -grammar / 전부: im-ai-copyeditor.
compatibility: 문장 분절 스크립트 실행에 python3(없으면 python) 필요.
metadata:
  version: "0.3.0"
  openclaw:
    requires:
      anyBins: [python3, python]
  hermes:
    category: writing
    tags: [korean, proofreading, ai-style]
---

# im-ai-copyeditor-ai — AI 문체 제거

AI가 쓴 한글의 기계적 수사·구조·리듬을 문장 단위로 손본다. 정규식으로 한꺼번에 바꾸지 않는다.
말투·장르·뜻은 보존한다.

**우선 적용:** 보호 구간 밖의 중간점과 구분용 대시는 AI-6에 따라 먼저 풀어 쓴다. 다른 곳을 고쳤더라도 기호가 남으면 완료로 반환하지 않는다. 나머지 기존 규칙과 적용 순서는 유지한다.

스킬 디렉토리를 `$SKILL` 로 표기한다. Claude Code 는 `${CLAUDE_SKILL_DIR}` 나 `${CLAUDE_PLUGIN_ROOT}`.
아래 명령의 `python3` 는 환경에 `python3` 가 없으면 `python`(Windows 는 `py -3`)으로 바꿔 실행한다.

## 절차

**Phase 0** — 상태 한 줄: `im-ai-copyeditor-ai — AI 문체 / run_id: {YYYY-MM-DD-NNN}`
**Phase 1** — 입력을 `_workspace/{run_id}/01_input.txt` 저장.
**Phase 2** — `python3 $SKILL/scripts/segment.py _workspace/{run_id}/01_input.txt --outdir _workspace/{run_id}` → segments.json + worksheet.md, 문장 수 N 확인.**Phase 3** — 룰북 로드: `$SKILL/references/ai-tell-rules.md` 와 공통 `$SKILL/references/prime-directives.md`.
**Phase 4** — worksheet.md 의 문장 칸을 위에서 아래로 읽으며 ai-tell-rules.md 의 적용 순서대로 다듬어 **윤문/규칙** 채움. 고칠 게 없으면 원문 그대로 + `변경없음`. 문장을 합치거나 나누거나 순서를 바꾸지 않는다. '그대로 둘 줄'과 보호 정보는 보존한다.
**Phase 5** — `python3 $SKILL/scripts/reassemble.py _workspace/{run_id}/segments.json _workspace/{run_id}/worksheet.md --out _workspace/{run_id}/final.md --check-punctuation`. ID 중복·누락·추가, 빈 칸, 잘못된 `변경없음`은 2, 기본 변경률 상한 50% 초과는 3, 보호 표현/행·열 변경 또는 문장부호 잔존은 4로 멈춘다. 변경률 30% 초과는 의미 재검토 경고다. 요청에 별도 상한이 있으면 `--max-change`로 명시하며 임의로 높이지 않는다. 실패하면 고친 뒤 다시 실행하며, 이전 결과를 이번 결과로 반환하지 않는다. 통과하려고 검사 옵션을 빼지 않는다.
**Phase 6** — 반환: 상태 한 줄 / 바뀐 문장 전·후 표 / final.md / 자체검증 6가지.

제목·목록·표 셀의 텍스트도 윤문 대상이다. 중간점과 구분용 대시는 공통 약속 8절에 따라 반드시 풀어 쓴다.
보호할 고유명사·기술 표현은 분절 전에 `--preserve-text '원문의 정확한 표현'`으로 지정한다.
장식용 따옴표와 작성자 인용 블록의 편집 옵션, 제외된 HTML 처리, `부분 재조립` 보고는 공통 약속 2절을 따른다. 스크립트 통과 후에도 의미와 교정 누락을 별도로 검토한다.

## 옵션
- `장르: 칼럼|리포트|블로그|공적` · `강도: 보수|기본|적극` 기본값 기본

## 주의
뜻 보존이 최상위다. AI 문체는 맞춤법이 아니라 수사·구조·리듬의 문제다. 격식·반말 같은 말투는 그대로 둔다.
리듬·나열·구조 항목은 문단 흐름도 함께 본다. 수치·고유명사·인용은 불가침이다.
