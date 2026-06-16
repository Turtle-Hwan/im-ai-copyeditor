---
name: paraphrasing-korean-trans
description: 한국어 번역 문체를 문장 단위로 걷어 낸다. 피동태→능동, "가지다"(have) 직역, "-로 인하여/-에 대하여/-을 통해", 무생물·추상 주어, 영어 대명사(그/그녀/그것/그들) 남용, 관계절 좌향 수식 등을 자연스러운 한국어로. 뜻은 한 글자도 바꾸지 않는다. 트리거 — "번역 문체 고쳐", "번역체 자연스럽게", "영어 직역 티 빼줘", "번역 문체 제거". 문장 다이어트까지: -sentence / AI 문체까지: -ai / 맞춤법·문체: -grammar / 전부: paraphrasing-korean.
---

# paraphrasing-korean-trans — 번역 문체 제거

영어 직역 흔적을 문장 단위로 자연스러운 한국어로 바꾼다(grep 금지). 의미·수치·고유명사·인용 보존.

스킬 디렉토리를 `$SKILL` 로 표기한다(Claude Code: `${CLAUDE_SKILL_DIR}`/`${CLAUDE_PLUGIN_ROOT}`).

## 절차

**Phase 0** — 상태 한 줄: `paraphrasing-korean-trans (번역 문체) / run_id: {YYYY-MM-DD-NNN}`
**Phase 1** — 입력을 `_workspace/{run_id}/01_input.txt` 저장.
**Phase 2** — `python3 $SKILL/scripts/segment.py _workspace/{run_id}/01_input.txt --outdir _workspace/{run_id}` → segments.json + worksheet.md, 문장 수 N 확인.
**Phase 2.5 (선택)** — `python3 $SKILL/scripts/scan.py _workspace/{run_id}/worksheet.md` → 의심 규칙을 `힌트:` 로 표시(참고용, 오탐 가능, 윤문을 대신하지 않음).
**Phase 3** — 룰북 로드: `$SKILL/references/translationese-rules.md` + 공통 `$SKILL/references/prime-directives.md`.
**Phase 4** — worksheet.md 의 prose 행을 위에서 아래로, T-1(피동)→T-2(가지다)→T-5(무생물 주어)→T-3·T-4·T-6(인하여·대해·통해)→T-7(대명사)→T-8(관계절)→T-9(자잘한 치환) 순으로 적용해 **윤문/규칙** 채움. 바꿀 게 없으면 원문 그대로 + `변경없음`. 행 병합/분할/순서변경 금지, structure 줄 불가침, Do-NOT 보존.
**Phase 5** — `python3 $SKILL/scripts/reassemble.py _workspace/{run_id}/segments.json _workspace/{run_id}/worksheet.md --out _workspace/{run_id}/final.md`. 카운트 불일치(2)·과윤문(3)이면 수정 후 재실행.
**Phase 6** — 반환: 상태 한 줄 / before→after 표(바뀐 문장) / final.md / 자체검증 6항.

## 옵션
- `장르: 칼럼|리포트|블로그|공적` · `강도: 보수|기본|적극`(기본값 기본)

## 주의
의미 불변 최상위. 수치·고유명사·인용 불가침. `-의` 자체는 번역 문체가 아니다(어색한 이중조사만 손본다).
