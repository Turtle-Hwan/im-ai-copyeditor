---
name: paraphrasing-korean-ai
description: AI(ChatGPT·Claude·Gemini)가 쓴 한글의 "AI 문체"를 문장 단위로 걷어 낸다. 기계적 나열(첫째/둘째), 결말 공식(결국/시사하는 바가 크다), 과장 어휘, 이모지·과한 불릿/볼드, 비슷한 길이·종결 반복, 표현을 자꾸 누그러뜨리기, 문두 접속사 남발, "것이다" 식 맺음을 자연스럽게. 뜻은 한 글자도 바꾸지 않는다. 트리거 — "AI 문체 빼줘", "GPT 문체 자연스럽게", "AI 같은 글 사람처럼", "휴머나이즈". 문장 다이어트까지: -sentence / 번역 문체까지: -trans / 맞춤법·문체: -grammar / 전부: paraphrasing-korean.
---

# paraphrasing-korean-ai — AI 문체 제거

AI가 쓴 한글의 기계적 수사·구조·리듬을 문장 단위로 손본다(grep 금지). 말투·장르·의미는 보존.

스킬 디렉토리를 `$SKILL` 로 표기한다(Claude Code: `${CLAUDE_SKILL_DIR}`/`${CLAUDE_PLUGIN_ROOT}`).

## 절차

**Phase 0** — 상태 한 줄: `paraphrasing-korean-ai (AI 문체) / run_id: {YYYY-MM-DD-NNN}`
**Phase 1** — 입력을 `_workspace/{run_id}/01_input.txt` 저장.
**Phase 2** — `python3 $SKILL/scripts/segment.py _workspace/{run_id}/01_input.txt --outdir _workspace/{run_id}` → segments.json + worksheet.md, 문장 수 N 확인.
**Phase 2.5 (선택)** — `python3 $SKILL/scripts/scan.py _workspace/{run_id}/worksheet.md` → 힌트는 고정밀 맞춤법·표기 오타만 잡는다. AI 문체는 정규식으로 잡지 않으니(오탐 많음) 힌트가 거의 안 붙는다 — 정상이다. AI 티는 Phase 3 룰북의 예시로 직접 판단한다. 건너뛰어도 된다.
**Phase 3** — 룰북 로드: `$SKILL/references/ai-tell-rules.md` + 공통 `$SKILL/references/prime-directives.md`.
**Phase 4** — worksheet.md 의 prose 행을 위에서 아래로, AI-8(형식명사)→AI-2(결말 공식)→AI-3(hype)→AI-6(hedging)→AI-7(접속사)→AI-4(시각 장식)→AI-1(병렬)·AI-5(리듬)·AI-9 순으로 적용해 **윤문/규칙** 채움. 바꿀 게 없으면 원문 그대로 + `변경없음`. 행 병합/분할/순서변경 금지, structure 줄 불가침, Do-NOT 보존.
**Phase 5** — `python3 $SKILL/scripts/reassemble.py _workspace/{run_id}/segments.json _workspace/{run_id}/worksheet.md --out _workspace/{run_id}/final.md`. 카운트 불일치(2)·과윤문(3)이면 수정 후 재실행.
**Phase 6** — 반환: 상태 한 줄 / before→after 표(바뀐 문장) / final.md / 자체검증 6항.

## 옵션
- `장르: 칼럼|리포트|블로그|공적` · `강도: 보수|기본|적극`(기본값 기본)

## 주의
의미 불변 최상위. AI 문체는 문법이 아니라 수사·구조·리듬의 문제다 — 말투(격식/반말)는 그대로 둔다.
리듬·병렬·구조 항목은 문단 흐름도 함께 본다. 수치·고유명사·인용 불가침.
