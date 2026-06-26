# 설치 안내

여러 AI 도구에서 같은 스킬을 씁니다. 도구별 방법을 아래에 정리했습니다.

먼저 저장소를 받습니다.

```bash
git clone https://github.com/Turtle-Hwan/im-ai-copyeditor
cd im-ai-copyeditor
```

`./install.sh` 는 설치돼 있는 도구를 스스로 찾아 설치합니다.

> [!NOTE]
> 기본은 심링크입니다. `git pull` 만 하면 최신으로 갱신됩니다. 저장소를 지워도 유지하려면 `--copy` 를 붙입니다.

> [!NOTE]
> **Windows** 에서도 별도 설정 없이 그대로 동작합니다. 스킬 패키지는 심링크가 아니라 실제 파일이라
> `git clone`·`/plugin marketplace`·`./install.sh` 가 모두 정상입니다. `./install.sh` 는 Windows 를 감지해
> 자동으로 복사 모드로 설치합니다. 파이썬은 `python3` 가 없으면 `python` 또는 `py -3` 로 실행하세요.

## Claude Code

> [!TIP]
> 한 줄 설치를 권합니다. 클론하지 않아도 됩니다.

```
/plugin marketplace add Turtle-Hwan/im-ai-copyeditor
/plugin install im-ai-copyeditor@im-ai-copyeditor
```

클론해서 설치하려면 이렇게 합니다.

```bash
./install.sh --claude-only        # → ~/.claude/skills/
```

새 세션에서 `/im-ai-copyeditor:all` 으로 부릅니다.

## Codex

```bash
./install.sh --codex-only         # → ~/.codex/skills/ 와 ~/.agents/skills/
```

## OpenClaw

```bash
./install.sh --openclaw-only      # → ~/.openclaw/skills/ 와 ~/.agents/skills/
```

설치한 스킬은 자동 발견되고, `user-invocable` 기본값이라 슬래시 명령으로도 노출됩니다. 파이썬 의존은 각 스킬의 `metadata.openclaw.requires.anyBins` 로 게이팅합니다. 플러그인으로 배포하려면 루트의 `openclaw.plugin.json` 매니페스트를 씁니다.

## Hermes

```bash
./install.sh --hermes-only        # → ~/.hermes/skills/
```

저장소가 `skills/` 레이아웃이라 [agentskills.io](https://agentskills.io/specification) 표준 tap 으로도 받습니다.

```bash
hermes skills tap add Turtle-Hwan/im-ai-copyeditor
hermes skills install Turtle-Hwan/im-ai-copyeditor/im-ai-copyeditor
```

## Gemini CLI

```bash
./install.sh --gemini-only        # gemini extensions link 로 등록
```

직접 등록해도 됩니다.

```bash
gemini extensions link "$(pwd)"
```

## 한 번에 모두

```bash
./install.sh                      # 설치돼 있는 도구 전부
./install.sh --copy               # 심링크 대신 복사
./install.sh --dry-run            # 실제로 바꾸지 않고 할 일만 출력
```

## 갱신과 제거

```bash
./update.sh                       # 새 버전 확인하고 적용
./update.sh --check               # 확인만
./uninstall.sh                    # 우리가 만든 심링크만 제거
```

## 경로 바꾸기

도구의 홈 경로가 다르면 환경변수로 덮어씁니다.

```bash
CLAUDE_HOME=~/myclaude ./install.sh --claude-only
```

`CODEX_HOME` · `OPENCLAW_HOME` · `HERMES_HOME` · `AGENTS_HOME` 도 같은 방식입니다.
