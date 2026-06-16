#!/usr/bin/env bash
# paraphrasing-korean — 설치 제거.
# install.sh 가 만든 "이 저장소를 가리키는 심링크"만 지운다. 사용자가 직접 둔 파일,
# 다른 곳을 가리키는 링크, .bak.* 백업, --copy 로 복사한 것은 건드리지 않는다.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$REPO/skills"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
OPENCLAW_HOME="${OPENCLAW_HOME:-$HOME/.openclaw}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
AGENTS_HOME="${AGENTS_HOME:-$HOME/.agents}"
DRYRUN=0

case "${1:-}" in
  --dry-run) DRYRUN=1 ;;
  -h|--help) echo "사용법: ./uninstall.sh [--dry-run]"; exit 0 ;;
  "") ;;
  *) echo "모르는 인자: $1" >&2; exit 2 ;;
esac

SKILLS=(paraphrasing-korean paraphrasing-korean-센텐스 paraphrasing-korean-sentence paraphrasing-korean-trans paraphrasing-korean-ai)

remove_if_ours() {  # $1=dest, $2=src
  local dest="$1" src="$2"
  if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
    echo "+ rm $dest"; [ "$DRYRUN" = 1 ] || rm "$dest"
  elif [ -e "$dest" ]; then
    echo "그대로 둠(우리 것 아님): $dest"
  fi
}

remove_from() {  # $1=대상 skills 디렉토리
  for s in "${SKILLS[@]}"; do remove_if_ours "$1/$s" "$SKILLS_SRC/$s"; done
}

remove_from "$CLAUDE_HOME/skills"
remove_from "$CODEX_HOME/skills"
remove_from "$OPENCLAW_HOME/skills"
remove_from "$HERMES_HOME/skills/writing"
remove_from "$AGENTS_HOME/skills"

if command -v gemini >/dev/null 2>&1; then
  echo "Gemini extension 제거 시도..."
  if [ "$DRYRUN" = 1 ]; then echo "+ gemini extensions uninstall paraphrasing-korean (dry-run)"; else
    gemini extensions uninstall paraphrasing-korean 2>/dev/null && echo "제거됨: Gemini extension" \
      || echo "  (Gemini extension 미설치 또는 이미 제거됨)"
  fi
fi

echo "제거 완료. (.bak.* 백업·--copy 복사본은 그대로 둠)"
