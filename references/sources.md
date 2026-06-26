# 근거 지도

이 문서는 룰북이 기대는 공개 자료를 한곳에 모은 지도다. 규칙 하나하나의 처방은 각 룰북에 두고,
여기서는 어느 자료를 어떤 범위에서 참고하는지만 정리한다.

## 국립국어원 핵심 자료

- [한국어 어문 규범](https://korean.go.kr/kornorms/main/main.do)
  - 한글 맞춤법, 표준어 규정, 외래어 표기법, 국어의 로마자 표기법을 확인한다.
  - `grammar-rules.md` 의 맞춤법, 표준어, 외래어 표기, 두음법칙, 사이시옷, 띄어쓰기 판단의 1차 기준이다.
- [문장 부호 해설](https://www.korean.go.kr/front/etcData/etcDataView.do?etc_seq=431)
  - 쉼표, 따옴표, 괄호, 줄표, 줄임표 같은 문장 부호의 쓰임을 확인한다.
  - `grammar-rules.md`, `sentence-rules.md`, `ai-tell-rules.md` 의 문장 부호 규칙을 보강한다.
- [표준국어대사전](https://stdict.korean.go.kr/main/main.do)
  - 표준어 여부, 뜻풀이, 활용, 발음, 순화 정보가 필요할 때 본다.
  - 혼동 어휘와 표준 표기를 판단할 때 `grammar-rules.md` 의 보조 기준으로 쓴다.
- [우리말샘](https://opendict.korean.go.kr/main)
  - 새말, 전문어, 생활 어휘의 실제 쓰임을 참고한다.
  - 표준국어대사전에 없는 표현은 바로 고치지 말고, 문맥과 장르를 함께 본다.
- [다듬은 말](https://www.korean.go.kr/front/imprv/refineList.do?mn_id=158)
  - 어려운 외래어, 일본어투, 행정 용어를 쉬운 우리말로 바꿀 때 참고한다.
  - `translationese-rules.md` 와 `style-guide.md` 의 공공언어 규칙을 보강한다.
- [쉬운 공문서 쓰기 길잡이](https://www.korean.go.kr/front/etcData/etcDataView.do?etc_seq=700)
  - 공문서와 안내문의 문장을 쉽고 명확하게 쓰는 기준으로 삼는다.
  - 공공 안내, 서비스 문구, 행정 문서에서는 쉬운 말과 짧은 구조를 우선한다.
- [꼭 가려 써야 할 일본어 투 용어 50개](https://www.korean.go.kr/front/etcData/etcDataView.do?etc_seq=698)
  - 일본어투 용어와 문장 틀을 가려낼 때 참고한다.
  - 영어 번역체와 섞어 보지 말고 `translationese-rules.md` 에서 별도 범주로 다룬다.
- [표준 언어 예절](https://www.korean.go.kr/front/search/searchAllList.do?searchQuery=%ED%91%9C%EC%A4%80%20%EC%96%B8%EC%96%B4%20%EC%98%88%EC%A0%88)
  - 호칭, 지칭, 인사말, 높임 표현을 볼 때 참고한다.
  - `style-guide.md` 의 사물존칭, 간접높임, 객체높임 규칙을 보강한다.
- [온라인가나다](https://www.korean.go.kr/front/onlineQna/onlineQnaList.do?mn_id=216)
  - 구체적인 높임법·띄어쓰기·표기 사례를 확인할 때 참고한다.
  - 개별 문맥에 대한 답변이므로 룰북에는 보수적으로 옮긴다.
- [언어정보나눔터](https://kli.korean.go.kr/)
  - 모두의 말뭉치, 인공지능(AI)말평, 온용어를 확인할 수 있다.
  - 지금 룰북의 직접 근거라기보다 나중에 평가셋과 용례 수집을 만들 때 쓴다.

## 룰북별 적용 범위

- `grammar-rules.md`
  - 한글 맞춤법, 표준어 규정, 외래어 표기법, 표준국어대사전을 우선한다.
  - 정답이 하나로 굳은 오류는 `S1`, 문맥·전문 분야·고유명사 여부를 봐야 하면 `S2` 로 둔다.
- `style-guide.md`
  - 표준 언어 예절과 온라인가나다의 답변을 참고하되, 개별 질의 답변은 일반 규칙으로 과장하지 않는다.
  - 높임의 대상이 사람인지, 그 사람과 연결된 소유물·신체·생각인지 먼저 본다.
- `translationese-rules.md`
  - 영어 직역, 일본어투, 어려운 공공언어를 나누어 본다.
  - 뜻을 바꾸지 않고 한국어 술어와 조사로 되살릴 수 있을 때만 고친다.
- `sentence-rules.md`
  - 국립국어원 규범의 오류 교정보다는 문장 교열 관점의 군더더기 줄이기다.
  - 규범이 아니라 문체 판단이므로 뜻이 흔들리면 고치지 않는다.
- `regex-patterns.json`
  - 국립국어원 기준으로 답이 거의 하나인 고정 표기 오류만 넣는다.
  - 번역체, AI 문체, 문장 간소화처럼 문맥이 필요한 항목은 정규식 힌트로 넣지 않는다.

## 보수적으로 남겨야 할 것

- 고유명사, 브랜드 표기, 제품명, 사람 이름, 단체명.
- 법령 조문, 표준 용어, 인용문, 논문·계약서의 정의어.
- 외래어 표기가 국립국어원 규범과 달라도 서비스·브랜드가 의도적으로 쓰는 표기.
- 온라인가나다의 개별 답변만으로 모든 문맥에 일괄 적용하기 어려운 높임·띄어쓰기 사례.
