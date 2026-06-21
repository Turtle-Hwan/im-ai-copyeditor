---
name: im-ai-copyeditor-sentence
description: 책 『내 문장이 그렇게 이상한가요?』에서 영감을 받은 규칙으로 한국어 문장을 문장 단위로 첨삭한다. 적·의·것·들, 군더더기 "있다", 이중피동, 조사 정밀성, "수 있는"·"시작하다" 남용, 괄호·쉼표 남용을 덜어 내는 문장 간소화. 뜻은 한 글자도 바꾸지 않는다. 트리거 — "문장 간소화", "군더더기 빼줘", "적의것들", "문장 줄여줘", "문장 첨삭". 번역 문체까지: -trans / AI 문체까지: -ai / 맞춤법·문체: -grammar / 전부: im-ai-copyeditor.
---

# im-ai-copyeditor-sentence — 문장 간소화

책 『내 문장이 그렇게 이상한가요?』에서 영감을 받아 빼기 중심으로 첨삭한다. 문장 부호 단위로 잘라
한 문장씩 다듬는다. 정규식으로 한꺼번에 바꾸지 않는다. 뜻·수치·고유명사·인용은 그대로 둔다.

스킬 디렉토리를 `$SKILL` 로 표기한다. Claude Code 는 `${CLAUDE_SKILL_DIR}` 나 `${CLAUDE_PLUGIN_ROOT}`.

## 절차

**Phase 0** — 상태 한 줄: `im-ai-copyeditor-sentence 문장 간소화 / run_id: {YYYY-MM-DD-NNN}`
**Phase 1** — 입력을 `_workspace/{run_id}/01_input.txt` 저장.
**Phase 2** — `python3 $SKILL/scripts/segment.py _workspace/{run_id}/01_input.txt --outdir _workspace/{run_id}` → segments.json + worksheet.md, 문장 수 N 확인.
**Phase 2.5 선택** — `python3 $SKILL/scripts/scan.py _workspace/{run_id}/worksheet.md` → 힌트는 고정밀 맞춤법·표기 오타만 잡는다. 문장 간소화는 정규식으로 잡지 않으니(오탐 많음) 힌트가 거의 안 붙는다 — 정상이다. 군더더기는 Phase 3 룰북의 예시로 직접 판단한다. 건너뛰어도 된다.
**Phase 3** — 룰북 로드: `$SKILL/references/sentence-rules.md` 와 공통 `$SKILL/references/prime-directives.md`.
**Phase 4** — worksheet.md 의 문장 칸을 위에서 아래로, S-1 적·의·것·들 → S-2 있다 → S-3 이중피동 → S-9 수 있는 → S-10 시작하다 → 나머지 → S-15·S-16 괄호·쉼표 → S-14 만연체 순으로 적용해 **윤문/규칙** 채움. 고칠 게 없으면 원문 그대로 + `변경없음`. 문장 합치기·나누기·순서 바꾸기 금지, '그대로 둘 줄' 불가침, 건드리지 않는 것 보존.
**Phase 5** — `python3 $SKILL/scripts/reassemble.py _workspace/{run_id}/segments.json _workspace/{run_id}/worksheet.md --out _workspace/{run_id}/final.md`. 문장 수 불일치는 2, 과윤문은 3으로 멈춘다. 고친 뒤 다시 실행.
**Phase 6** — 반환: 상태 한 줄 / 바뀐 문장 전·후 표 / final.md / 자체검증 6가지.

## 옵션
- `장르: 칼럼|리포트|블로그|공적` · `강도: 보수|기본|적극` 기본값 기본

## 주의
뜻 보존이 최상위다. 이 책의 핵심 원칙대로 한 글자 더 써서 어색하면 뺀다. 수치·고유명사·인용은 불가침이다.
