---
name: paraphrasing-korean-grammar
description: 한국어 맞춤법과 문체를 문장 단위로 교정한다. 예요/이에요, 되/돼, 안/않, 데/대, 든/던, 로서/로써, 율/률, 띄어쓰기 같은 맞춤법과, 종결문체 일관성·사물존칭·경어법 같은 문체를 국립국어원 기준으로 바로잡는다. 뜻은 한 글자도 바꾸지 않는다. 트리거 — "맞춤법 고쳐", "맞춤법 검사", "문체 통일", "존댓말 통일", "한국어 교정". 번역 문체까지: -trans / AI 문체까지: -ai / 전부: paraphrasing-korean.
---

# paraphrasing-korean-grammar — 맞춤법·문체 교정

한국어 맞춤법과 문체를 문장 단위로 바로잡아요. 국립국어원 기준을 따라요. 정규식으로 한꺼번에
바꾸지 않아요. 뜻·수치·고유명사·인용은 그대로 둬요.

스킬 디렉토리를 `$SKILL` 로 표기해요. Claude Code 는 `${CLAUDE_SKILL_DIR}` 나 `${CLAUDE_PLUGIN_ROOT}`.

## 절차

**Phase 0** — 상태 한 줄: `paraphrasing-korean-grammar 맞춤법·문체 / run_id: {YYYY-MM-DD-NNN}`
**Phase 1** — 입력을 `_workspace/{run_id}/01_input.txt` 저장.
**Phase 2** — `python3 $SKILL/scripts/segment.py _workspace/{run_id}/01_input.txt --outdir _workspace/{run_id}` → segments.json + worksheet.md, 문장 수 N 확인.
**Phase 2.5 선택** — `python3 $SKILL/scripts/scan.py _workspace/{run_id}/worksheet.md` → 의심 규칙을 `힌트:` 로 표시. 참고용이고 틀릴 수 있어요.
**Phase 3** — 룰북 로드: `$SKILL/references/grammar-rules.md` 와 `$SKILL/references/style-guide.md`, 공통 `$SKILL/references/prime-directives.md`. 먼저 글 전체의 우세 문체를 정해요. 해요체·합니다체·한다체 중 하나로.
**Phase 4** — worksheet.md 의 문장 칸을 위에서 아래로 읽으며 맞춤법 규칙 G-를 먼저 바로잡고 문체 규칙 ST-를 맞춰 **윤문/규칙** 채움. 고칠 게 없으면 원문 그대로 + `변경없음`. 문장 합치기·나누기·순서 바꾸기 금지, '그대로 둘 줄' 불가침, 건드리지 않는 것 보존.
**Phase 5** — `python3 $SKILL/scripts/reassemble.py _workspace/{run_id}/segments.json _workspace/{run_id}/worksheet.md --out _workspace/{run_id}/final.md`. 문장 수 불일치는 2, 과윤문은 3으로 멈춰요.
**Phase 6** — 반환: 상태 한 줄 / 바뀐 문장 전·후 표 / final.md / 자체검증 6가지.

## 옵션
- `장르: 칼럼|리포트|블로그|공적` · `강도: 보수|기본|적극` 기본값 기본

## 주의
맞춤법 교정은 뜻을 바꾸지 않아요. 문체는 입력의 격식을 따르되 글 안에서 일관되게 맞춰요. 한쪽으로
통일할 때 글 전체의 격식을 뒤집지 않아요. 사물존칭은 빼되 간접높임은 살려요.
