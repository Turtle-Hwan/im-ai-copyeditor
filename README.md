<div align="center">

# ai-copyeditor

**진짜 교정·교열가처럼 문장 하나하나 꼼꼼히 첨삭해서 사람이 읽기 좋은 글로 다듬는 스킬**

[설치](#설치) · [명령어](#명령어) · [동작 방식](#동작-방식) · [규칙](#규칙) · [기여](#기여)

![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-0.3.0-blue)
![Tools](https://img.shields.io/badge/tools-Claude_Code_·_Codex_·_Gemini_CLI-black)
![Stars](https://img.shields.io/github/stars/Turtle-Hwan/im-ai-copyeditor)

</div>

> [!IMPORTANT]
> 다양한 어휘와 수려한 문체로 우아하게 표현할 수 있는 한글을 AI가 너무 못 쓰는 것이 답답했어요.

AI가 쓴 글이든 사람이 쓴 글이든, 진짜 교정·교열가처럼 한 문장 한 문장 꼼꼼히 첨삭해요.

영어 번역체와 AI 챗봇 같은 말투에서 군더더기와 어색함을 덜어내어 사람이 읽기 좋은 문장으로 바꾸어줘요.

## 교정 예시

![교정 예시 — 맞춤법·경어법(커피 나오셨습니다 → 나왔습니다), 번역 문체(가지고 있다 → 강하다), AI 문체(단순한 ~가 아니라 → 단언), 문장 간소화(적·의·것·들: 환경적 요인의 → 환경 요인 · 덮여 있는 → 덮인), 문체(종결 통일)를 before→after로 보여 주는 예시](docs/what-we-fix.png)

## 차별점

- **한 줄 한 줄 읽는 LLM**

  grep 이나 정규식으로 대충 훑지 않아요. 문장 부호 단위로 잘라 작업표를 만들고, 모든 문장을 빠짐없이 읽고 다듬어요.

- **번역체·AI체를 걷어낸 자연스러운 문장**

  내용은 그대로 두고 사람이 읽기 좋은 어휘와 문체로 고쳐요.

- **책에서 영감받은 문장 교정**

  문장 교정 규칙은 책 [『내 문장이 그렇게 이상한가요?』](https://product.kyobobook.co.kr/detail/S000001863138)에서 영감을 받아 더했어요.

- **한국어 특화 스킬**

  규칙은 국립국어원 어문 규범과 번역학·문체 논문에 근거해요.

## 명령어

| 명령어 | 기능 |
|---|---|
| `/im-ai-copyeditor:all` | **통합**. 맞춤법 → 번역 문체 → AI 문체 → 문장 간소화 → 문체를 한 문장씩 차례로 적용 |
| `/im-ai-copyeditor:grammar` | 맞춤법·문체 교정. 예요/되/안, 띄어쓰기, 문장 부호, 외래어 표기, 종결문체 통일, 사물존칭 |
| `/im-ai-copyeditor:sentence` | 문장 간소화. 적·의·것·들, 군더더기 "있다", 군더더기 피동, 조사 다듬기 |
| `/im-ai-copyeditor:trans` | 번역 문체 제거. 피동→능동, 가지다·통해·대해, 무생물 주어, 대명사 남용 |
| `/im-ai-copyeditor:ai` | AI 문체 제거. 첫째·둘째 나열, 결말 공식, 과장 어휘, 괄호·쉼표, 클리셰 |
| `/im-ai-copyeditor:grill` | **대화형 공동 교정**. 전체 맥락·표현이 맞는지 한 번에 하나씩 되묻고, 합의되면 압축·재집필까지 |

> [!TIP]
> `grill`은 사용자에게 전체 맥락까지 되물으며 함께 고치고, 동의하면 문장을 합치거나 줄여 주는 스킬이에요.

> [!NOTE]
> 스킬로 설치한 이후엔 `im-ai-copyeditor` 처럼 이름으로 부르거나, 그냥 **"이 글 문장 다듬어줘"** 라고 하면 알아서 교정해줘요.

## 설치

### 한 줄 설치

```bash
curl -fsSL https://raw.githubusercontent.com/Turtle-Hwan/im-ai-copyeditor/main/install.sh | bash
```

가장 간편한 방법이에요. **Claude Code · Codex · OpenClaw · Hermes · Gemini CLI** 중 깔린 도구를 스스로 찾아 **스킬**로 연결해요. 설치 뒤 그냥 **"이 글 문장 다듬어줘"** 라고 하거나 스킬을 이름으로 불러요. 특정 도구만 깔려면 끝에 `-s -- --claude-only` 처럼 붙여요.

### Claude Code 플러그인

```
/plugin marketplace add Turtle-Hwan/im-ai-copyeditor
/plugin install im-ai-copyeditor@im-ai-copyeditor
```

플러그인으로 깔면 `/im-ai-copyeditor:all`·`:grammar`·`:sentence`·`:trans`·`:ai` 슬래시 명령이 생겨요. 위 한 줄 설치는 **스킬**만 깔아 이름이나 자연어로 부르고요. 부르는 방식만 다를 뿐 규칙은 똑같아요.

### 도구별 설치 위치

| 도구 | 설치 위치 | 사용법 |
|---|---|---|
| **Claude Code** | 스킬 `~/.claude/skills/` · 플러그인 마켓플레이스 | `im-ai-copyeditor` 스킬 · `/im-ai-copyeditor:all` · "이 글 다듬어줘" |
| **Codex** | `~/.codex/skills/` · `~/.agents/skills/` | "이 글 문장 다듬어줘" |
| **OpenClaw** | `~/.openclaw/skills/` · `~/.agents/skills/` | "이 글 문장 다듬어줘" |
| **Hermes** | `~/.hermes/skills/writing/` | "이 글 문장 다듬어줘" |
| **Gemini CLI** | 확장 `gemini extensions link` | `/im-ai-copyeditor` |

### 직접 클론

```bash
git clone https://github.com/Turtle-Hwan/im-ai-copyeditor
cd im-ai-copyeditor
./install.sh            # 깔린 도구를 자동 감지해 연결
```

코드를 고치거나 개발할 때 써요. 심링크가 기본이라 `git pull` 로 갱신돼요. 특정 도구만 깔려면 `--claude-only`, 복사로 깔려면 `--copy`, 미리 보려면 `--dry-run` 을 붙여요.

```bash
./update.sh    # 새 버전 확인·적용
./uninstall.sh # 제거
```

### Windows

별도 설정 없이 그대로 깔려요. 스킬 패키지가 실제 파일이라(심링크를 쓰지 않아요) `git clone`·`/plugin marketplace`·`./install.sh` 가 모두 정상 동작해요. `./install.sh` 는 Windows 를 감지해 자동으로 복사(`--copy`) 모드로 설치하고요. 파이썬은 `python3` 가 없으면 `python` 또는 `py -3` 로 실행돼요.

## 동작 방식

핵심은 **LLM이 모든 문장을 한 줄씩 읽고 다듬는다는 데** 있어요. 정규식으로 한꺼번에 바꾸지 않아요.
한 문장이라도 빠뜨리지 않으려고 작은 도구 두 개로 흐름을 묶었어요.

1. **분할.** `scripts/segment.py` 가 글을 문장 부호 기준으로 잘라 작업표를 만들어요.
   제목·목록·코드 블록은 손대지 않아요.
2. **윤문.** 에이전트가 작업표의 문장을 위에서 아래로 하나씩 읽고 고쳐요. 고칠 게 없으면 그대로 둬요.
3. **재조립.** `scripts/reassemble.py` 가 다듬은 문장을 원래 구조에 맞춰 다시 한 편으로 이어요.

문장을 되붙일 때 두 가지를 자동으로 지켜요. 들어간 문장 수와 나온 문장 수가 다르면 멈춰요. 너무 많이
바뀌어도 멈춰요. 둘 다 원문을 망치지 않으려는 장치예요.

## 규칙

규칙은 모두 `references/` 폴더에 글로 정리했어요. 국립국어원 어문 규범과 번역학·문체 논문에 근거해요.

- `grammar-rules.md`: 맞춤법·문장 부호·외래어 표기. 국립국어원 어문 규범 기준.
- `translationese-rules.md`: 번역 문체. 영어 직역, 일본어투, 어려운 공공언어를 실용 규칙으로 옮겼어요.
- `ai-tell-rules.md`: AI 문체. AI 글과 사람 글을 비교한 논문에 근거해요.
- `sentence-rules.md`: 문장 간소화. 책 [『내 문장이 그렇게 이상한가요?』](https://product.kyobobook.co.kr/detail/S000001863138)에서
  영감을 받았어요. 김정선 지음, 유유, 2016.
- `style-guide.md`: 문체·경어법. 종결문체 일관성, 사물존칭·간접높임, 쉬운 공공언어.
- `prime-directives.md`: 모든 명령이 함께 지키는 약속.
- `sources.md`: 국립국어원 어문 규범, 사전, 공공언어 자료를 룰북별로 연결한 근거 지도.

각 규칙은 "무엇을 찾고 어떻게 고치고 예를 들면 이렇게" 형식이에요. 예시만 읽어도 이해가 쉽도록 했어요.

## 기여

번역 문체와 AI 문체, 맞춤법 예시는 모을수록 좋아져요. 새 예시와 새 규칙은 누구나 추가할 수 있어요.
방법은 [CONTRIBUTING.md](CONTRIBUTING.md) 에 있어요.

## 개발

```bash
python3 -m unittest discover -s tests
```

별다른 라이브러리 설치 없이 파이썬 표준 기능만 써요. `python3` 가 없으면 `python`(Windows 는 `py -3`)으로 실행해요.

`references/` 나 `scripts/` 를 고쳤다면 각 스킬 패키지에 반영하도록 동기화를 한 번 돌려요.

```bash
python3 scripts/sync_skills.py          # 공유 자원을 스킬 패키지에 복사
python3 scripts/sync_skills.py --check  # 어긋남만 확인(검사가 이걸로 막아요)
```

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Turtle-Hwan/im-ai-copyeditor&type=Date)](https://star-history.com/#Turtle-Hwan/im-ai-copyeditor&Date)

## LICENSE

[MIT](LICENSE)

책 내용의 저작권은 원저작자에게 있으며, 본 스킬에서 책 내용을 그대로 옮겨 싣지 않았음을 미리 밝힙니다.
