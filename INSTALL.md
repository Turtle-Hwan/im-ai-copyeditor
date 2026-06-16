# 설치 안내

여러 AI 도구에서 같은 스킬을 씁니다. 도구별 방법을 아래에 정리했습니다.

먼저 저장소를 받습니다.

```bash
git clone https://github.com/Turtle-Hwan/paraphrasing-korean
cd paraphrasing-korean
```

`./install.sh` 는 설치돼 있는 도구를 스스로 찾아 설치합니다. 기본은 심링크입니다. `git pull` 만 하면
최신으로 갱신됩니다. 저장소를 지워도 유지하려면 `--copy` 를 붙입니다.

## Claude Code

한 줄 설치를 권합니다. 클론하지 않아도 됩니다.

```
/plugin marketplace add Turtle-Hwan/paraphrasing-korean
/plugin install paraphrasing-korean@paraphrasing-korean
```

클론해서 설치하려면 이렇게 합니다.

```bash
./install.sh --claude-only        # → ~/.claude/skills/
```

새 세션에서 `/paraphrasing-korean` 으로 부릅니다.

## Codex

```bash
./install.sh --codex-only         # → ~/.codex/skills/ 와 ~/.agents/skills/
```

## OpenClaw

```bash
./install.sh --openclaw-only      # → ~/.openclaw/skills/ 와 ~/.agents/skills/
```

## Hermes

```bash
./install.sh --hermes-only        # → ~/.hermes/skills/writing/
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
