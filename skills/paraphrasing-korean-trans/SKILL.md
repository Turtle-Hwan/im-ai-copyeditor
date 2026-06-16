---
name: paraphrasing-korean-trans
description: 한국어 번역 문체를 문장 단위로 걷어 낸다. 피동태→능동, "가지다" 직역, "-로 인하여/-에 대하여/-을 통해", 무생물·추상 주어, 영어 대명사 남용, 관계절 좌향 수식 등을 자연스러운 한국어로. 뜻은 한 글자도 바꾸지 않는다. 트리거 — "번역 문체 고쳐", "번역체 자연스럽게", "영어 직역 티 빼줘", "번역 문체 제거". 문장 다이어트까지: -sentence / AI 문체까지: -ai / 맞춤법·문체: -grammar / 전부: paraphrasing-korean.
---

# paraphrasing-korean-trans — 번역 문체 제거

영어 직역 흔적을 문장 단위로 자연스러운 한국어로 바꾼다. 정규식으로 한꺼번에 바꾸지 않는다.
뜻·수치·고유명사·인용은 보존한다.

스킬 디렉토리를 `$SKILL` 로 표기한다. Claude Code 는 `${CLAUDE_SKILL_DIR}` 나 `${CLAUDE_PLUGIN_ROOT}`.

## 절차

**Phase 0** — 상태 한 줄: `paraphrasing-korean-trans — 번역 문체 / run_id: {YYYY-MM-DD-NNN}`
**Phase 1** — 입력을 `_workspace/{run_id}/01_input.txt` 저장.
**Phase 2** — `python3 $SKILL/scripts/segment.py _workspace/{run_id}/01_input.txt --outdir _workspace/{run_id}` → segments.json + worksheet.md, 문장 수 N 확인.
**Phase 2.5 선택** — `python3 $SKILL/scripts/scan.py _workspace/{run_id}/worksheet.md` → 의심 규칙을 `힌트:` 로 표시한다. 참고용이고 오탐이 있으며 윤문을 대신하지 않는다.
**Phase 3** — 룰북 로드: `$SKILL/references/translationese-rules.md` 와 공통 `$SKILL/references/prime-directives.md`.
**Phase 4** — worksheet.md 의 문장 칸을 위에서 아래로 읽으며 translationese-rules.md 의 적용 순서대로 다듬어 **윤문/규칙** 채움. 고칠 게 없으면 원문 그대로 + `변경없음`. 문장 합치기·나누기·순서 바꾸기 금지, '그대로 둘 줄' 불가침, 건드리지 않는 것 보존.
**Phase 5** — `python3 $SKILL/scripts/reassemble.py _workspace/{run_id}/segments.json _workspace/{run_id}/worksheet.md --out _workspace/{run_id}/final.md`. 문장 수 불일치는 2, 과윤문은 3으로 멈춘다. 고친 뒤 다시 실행.
**Phase 6** — 반환: 상태 한 줄 / 바뀐 문장 전·후 표 / final.md / 자체검증 6가지.

## 옵션
- `장르: 칼럼|리포트|블로그|공적` · `강도: 보수|기본|적극` 기본값 기본

## 주의
뜻 보존이 최상위다. 수치·고유명사·인용은 불가침이다. `-의` 자체는 번역 문체가 아니니 어색한 이중조사만 손본다.
