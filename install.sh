#!/usr/bin/env bash
# paraphrasing-korean — 여러 AI 도구에 한 번에 설치하는 스크립트.
# 저장소를 클론한 뒤 `./install.sh` 한 번이면 깔려 있는 도구(claude/codex/openclaw/hermes/gemini)를
# 스스로 찾아 스킬을 연결한다. 기본은 심링크(저장소를 고치면 바로 반영, `git pull` 로 갱신).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$REPO/skills"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
OPENCLAW_HOME="${OPENCLAW_HOME:-$HOME/.openclaw}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
AGENTS_HOME="${AGENTS_HOME:-$HOME/.agents}"   # agentskills.io 공용 경로(Codex·OpenClaw가 함께 읽음)

MODE=symlink         # symlink | copy
ONLY=""              # "" | claude | codex | openclaw | hermes | gemini
DO_GEMINI=auto       # auto | yes | no
FORCE=0
DRYRUN=0
TS="$(date +%Y%m%d-%H%M%S)"

# 설치할 스킬 폴더(영문 별칭 -sentence 포함).
SKILLS=(paraphrasing-korean paraphrasing-korean-센텐스 paraphrasing-korean-sentence paraphrasing-korean-trans paraphrasing-korean-ai)

print_help() {
  cat <<'H'
사용법: ./install.sh [옵션]

  깔려 있는 AI 도구를 스스로 찾아 paraphrasing-korean 스킬을 설치한다.
  Claude  : ~/.claude/skills/
  Codex   : ~/.codex/skills/   + ~/.agents/skills/
  OpenClaw: ~/.openclaw/skills/ + ~/.agents/skills/
  Hermes  : ~/.hermes/skills/writing/
  Gemini  : gemini extensions link (gemini-extension.json + GEMINI.md + commands/)

옵션:
  --copy           심링크 대신 복사(저장소를 지워도 유지). 복사본은 uninstall.sh가 지우지 않음.
  --claude-only    Claude 에만 설치
  --codex-only     Codex 에만 설치
  --openclaw-only  OpenClaw 에만 설치
  --hermes-only    Hermes 에만 설치
  --gemini-only    Gemini 에만 설치
  --no-gemini      Gemini 는 건너뜀
  --force          대상에 일반 파일/폴더가 있어도 .bak.<시각> 으로 백업 후 덮어씀
  --dry-run        실제로 바꾸지 않고 할 일만 출력
  -h, --help       이 도움말

환경변수: CLAUDE_HOME · CODEX_HOME · OPENCLAW_HOME · HERMES_HOME · AGENTS_HOME 로 경로 덮어쓰기
H
}

while [ $# -gt 0 ]; do
  case "$1" in
    --copy) MODE=copy ;;
    --claude-only) ONLY=claude; DO_GEMINI=no ;;
    --codex-only) ONLY=codex; DO_GEMINI=no ;;
    --openclaw-only) ONLY=openclaw; DO_GEMINI=no ;;
    --hermes-only) ONLY=hermes; DO_GEMINI=no ;;
    --gemini-only) ONLY=gemini; DO_GEMINI=yes ;;
    --no-gemini) DO_GEMINI=no ;;
    --force) FORCE=1 ;;
    --dry-run) DRYRUN=1 ;;
    -h|--help) print_help; exit 0 ;;
    *) echo "모르는 인자: $1" >&2; print_help; exit 2 ;;
  esac
  shift
done

run() { echo "+ $*"; [ "$DRYRUN" = 1 ] || "$@"; }

# 도구가 깔렸는지: PATH 에 있거나, 홈 폴더가 있으면 "있음".
present() {  # $1=cli명, $2=홈경로
  command -v "$1" >/dev/null 2>&1 && return 0
  [ -d "$2" ] && return 0
  return 1
}
want() {  # $1=대상명. ONLY 가 비었으면 전부, 아니면 해당만.
  [ -z "$ONLY" ] || [ "$ONLY" = "$1" ]
}

# rc: 0=대상 비었음(진행) / 1=이미 우리 심링크(스킵) / 2=충돌(거부)
prepare_target() {
  local dest="$1" src="$2"
  if [ -L "$dest" ]; then
    [ "$(readlink "$dest")" = "$src" ] && { echo "그대로 둠(이미 연결): $dest"; return 1; }
    run mv "$dest" "$dest.bak.$TS"
  elif [ -e "$dest" ]; then
    [ "$FORCE" = 1 ] || { echo "거부: $dest 가 이미 있음 (--force 로 백업 후 덮어쓰기 또는 --copy)"; return 2; }
    run mv "$dest" "$dest.bak.$TS"
  fi
  return 0
}

install_one() {  # $1=src, $2=dest
  local src="$1" dest="$2" rc=0
  run mkdir -p "$(dirname "$dest")"
  prepare_target "$dest" "$src" || rc=$?
  [ "$rc" = 1 ] && return 0
  [ "$rc" = 2 ] && return 1
  case "$MODE" in
    symlink) run ln -s "$src" "$dest" ;;
    copy)    run cp -RL "$src" "$dest" ;;
  esac
  echo "설치됨: $dest"
}

install_skills_into() {  # $1=대상 skills 디렉토리
  local dir="$1"
  for s in "${SKILLS[@]}"; do
    [ -e "$SKILLS_SRC/$s" ] && install_one "$SKILLS_SRC/$s" "$dir/$s"
  done
}

DID=0

if want claude && present claude "$CLAUDE_HOME"; then
  echo "== Claude Code =="; install_skills_into "$CLAUDE_HOME/skills"; DID=1
fi
if want codex && present codex "$CODEX_HOME"; then
  echo "== Codex =="; install_skills_into "$CODEX_HOME/skills"; install_skills_into "$AGENTS_HOME/skills"; DID=1
fi
if want openclaw && present openclaw "$OPENCLAW_HOME"; then
  echo "== OpenClaw =="; install_skills_into "$OPENCLAW_HOME/skills"; install_skills_into "$AGENTS_HOME/skills"; DID=1
fi
if want hermes && present hermes "$HERMES_HOME"; then
  echo "== Hermes =="; install_skills_into "$HERMES_HOME/skills/writing"; DID=1
fi
if { [ "$ONLY" = gemini ] || { [ -z "$ONLY" ] && [ "$DO_GEMINI" != no ]; }; } && command -v gemini >/dev/null 2>&1; then
  echo "== Gemini CLI =="
  if [ "$DRYRUN" = 1 ]; then echo "+ gemini extensions link $REPO (dry-run)"; else
    echo "Y" | gemini extensions link "$REPO" 2>/dev/null && echo "설치됨: Gemini extension" \
      || echo "  (이미 등록됨 또는 수동 등록 필요: gemini extensions link $REPO)"
  fi
  DID=1
fi

[ "$DID" = 0 ] && echo "설치한 도구가 없습니다. (도구가 안 깔렸거나 --xxx-only 가 맞지 않음)"
echo ""
echo "완료 (방식=$MODE)."
echo "  새 세션에서 /paraphrasing-korean (또는 \"이 글 문장 다듬어줘\")."
echo "  업데이트: ./update.sh   ·   제거: ./uninstall.sh"
exit 0
