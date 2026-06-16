---
name: paraphrasing-korean
description: 한국어 문장을 문장 단위로 첨삭·윤문하는 통합 명령. 맞춤법 → 번역 문체 → AI 문체 → 문장 다이어트 → 문체를 순서대로 한 문장씩 적용해, 뜻은 한 글자도 바꾸지 않고 사람 문체로 다듬는다. 트리거 — "한국어 첨삭", "문장 윤문", "글 다듬어줘", "paraphrasing korean", "문장 다이어트", "번역 문체+AI 문체 같이 다듬어줘". 국립국어원 맞춤법과 번역학·문체 논문에 근거하며, 문장 교정은 책 『내 문장이 그렇게 이상한가요?』에서 영감을 받았다. 세부 명령 — 문장 다이어트만: -sentence / 번역 문체만: -trans / AI 문체만: -ai / 맞춤법·문체만: -grammar.
---

# paraphrasing-korean — 통합 첨삭·윤문

한국어 텍스트를 **문장 부호 단위로 잘라** 한 문장씩 다듬는다. 정규식으로 일괄 치환하지 않고 워크시트의
각 문장 행을 읽고 다듬는다. 뜻·수치·고유명사·인용은 보존한다. 문장 다이어트 규칙은 책 『내 문장이 그렇게
이상한가요?』에서 영감을 받았다.

스킬 디렉토리를 `$SKILL` 로 표기한다. Claude Code 는 `${CLAUDE_SKILL_DIR}` 나 `${CLAUDE_PLUGIN_ROOT}`,
그 외 하니스는 이 SKILL.md 가 있는 폴더다.

## 절차

**Phase 0 — 상태 한 줄**
```
paraphrasing-korean 통합 맞춤법→번역 문체→AI 문체→문장 다이어트→문체 / run_id: {YYYY-MM-DD-NNN}
```
run_id 는 cwd 기준 `_workspace/{YYYY-MM-DD-NNN}/`. 당일 폴더가 있으면 NNN+1.

**Phase 1 — 입력 저장**
입력 텍스트나 파일을 `_workspace/{run_id}/01_input.txt` 로 저장.

**Phase 2 — 문장 분절. 유일한 비-LLM 도구다**
```
python3 $SKILL/scripts/segment.py _workspace/{run_id}/01_input.txt --outdir _workspace/{run_id}
```
→ 원본 구조 정보 `segments.json` + 작업 파일 `worksheet.md` 생성. 나온 문장 수 N 을 확인한다.

**Phase 2.5 — 정규식 후보 힌트. 선택 단계다**
```
python3 $SKILL/scripts/scan.py _workspace/{run_id}/worksheet.md
```
워크시트의 각 문장에 의심 규칙 ID를 `힌트:` 줄로 단다. 힌트는 **고정밀 맞춤법·표기 오류**만 잡는다.
예요/에요·됬·역활·-ㄹ께 같은 고정 오타로, 정규식이 룰북 예시보다 확실히 잘 잡는 영역이다.
번역 문체·AI 문체·문장 다이어트는 정규식이 느슨해 빼 두었으니 Phase 3 룰북의 예시로 직접 판단한다.
힌트가 없는 문장도 반드시 읽고 판단한다. 힌트는 윤문을 대신하지 않으며, 건너뛰어도 된다.

**Phase 3 — 룰북 로드. 다섯 개 모두**
순서대로 적용한다. 먼저 글 전체의 우세 문체를 정한다. 해요체·합니다체·한다체 중 하나로.
1. [맞춤법] `$SKILL/references/grammar-rules.md`
2. [번역 문체] `$SKILL/references/translationese-rules.md`
3. [AI 문체] `$SKILL/references/ai-tell-rules.md`
4. [문장 다이어트] `$SKILL/references/sentence-rules.md`
5. [문체] `$SKILL/references/style-guide.md`

공통 규칙은 `$SKILL/references/prime-directives.md` 를 따른다. 뜻 불변·건드리지 않는 것·변경량·자체검증.

**Phase 4 — 워크시트 행별 윤문. 정규식 일괄 치환 금지**
`worksheet.md` 의 각 문장 칸을 위에서 아래로 처리한다. 한 문장에:
- 맞춤법 → 번역 문체 → AI 문체 → 문장 다이어트 → 문체 순으로 룰을 적용해 **윤문:** 줄을 채운다.
- **규칙:** 줄에 적용한 번호를 적는다. G-1·T-2·AI-3·S-1·ST-1 처럼. 바꿀 게 없으면 윤문에 원문을 그대로 옮기고 규칙은 `변경없음`.
- 문장을 합치거나 나누거나 순서를 바꾸지 않는다. '그대로 둘 줄'은 절대 건드리지 않는다.
- 수치·고유명사·직접 인용·영어 약어·법령은 보존한다. 뜻이 흔들리면 원문을 유지한다.

**Phase 5 — 재조립 + 가드**
```
python3 $SKILL/scripts/reassemble.py _workspace/{run_id}/segments.json _workspace/{run_id}/worksheet.md --out _workspace/{run_id}/final.md
```
- 문장 수 불일치는 종료 코드 2다. 누락·병합된 문장을 워크시트에서 고치고 다시 실행한다.
- 변경량 50% 초과는 종료 코드 3이다. 과윤문이니 보수적으로 다시 다듬는다.

**Phase 6 — 반환**
1. 한 줄 상태: `완료. {N}문장 / 변경 {k}건 / 변경량 {x}% / 등급 {A~D}`
2. 바뀐 문장만 전·후 표로. 원문·윤문·규칙
3. `final.md` 본문
4. 자체검증 6가지 결과

## 옵션
- `장르: 칼럼|리포트|블로그|공적` — 말투·장르 보존 기준. 생략하면 자동 추정.
- `강도: 보수|기본|적극` — 윤문 강도. 기본값은 기본.

## 주의
- 뜻 불변이 최상위. 수치·고유명사·인용 불가침.
- 통합 명령은 다섯 룰북을 다 쓴다. 하나만 원하면 `-grammar` · `-trans` · `-ai` · `-sentence` 명령을 쓴다.
- 문체는 입력의 격식을 따르되 글 안에서 일관되게 맞춘다. 한쪽으로 통일할 때 글 전체의 격식을 뒤집지 않는다.
