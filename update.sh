#!/usr/bin/env bash
# paraphrasing-korean — 업데이트 확인 + 적용.
# 원격(git)을 확인해 새 커밋이 있으면 fast-forward 로 받고 install.sh 를 다시 돌린다.
# 심링크 설치는 pull 만으로도 반영되지만, 새 스킬·구조 변경까지 확실히 연결하려고 다시 설치한다.
#
# 사용:
#   ./update.sh           업데이트 있으면 자동 적용
#   ./update.sh --check   확인만(적용 안 함). 최신=exit 0, 업데이트 있음=exit 10
#   그 외 인자는 install.sh 로 전달 (예: ./update.sh --copy, ./update.sh --claude-only)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
g() { git -C "$REPO" "$@"; }

CHECK_ONLY=0
ARGS=()
for a in "$@"; do
  case "$a" in
    --check) CHECK_ONLY=1 ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) ARGS+=("$a") ;;
  esac
done

g rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "git 저장소가 아닙니다: $REPO"; exit 2; }

UPSTREAM="$(g rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo origin/main)"
UP_REMOTE="${UPSTREAM%%/*}"
echo "업데이트 확인 중… (원격: $UPSTREAM)"
g fetch --quiet "$UP_REMOTE" || { echo "fetch 실패 — 네트워크/원격을 확인하세요."; exit 2; }

LOCAL="$(g rev-parse HEAD)"
REMOTE="$(g rev-parse "$UPSTREAM" 2>/dev/null || true)"
[ -z "$REMOTE" ] && { echo "원격($UPSTREAM)을 찾을 수 없습니다."; exit 2; }
BASE="$(g merge-base HEAD "$UPSTREAM" 2>/dev/null || echo "")"

if [ "$LOCAL" = "$REMOTE" ]; then
  echo "이미 최신입니다 ($(g rev-parse --short HEAD))."; exit 0
elif [ "$BASE" = "$REMOTE" ]; then
  echo "로컬이 원격보다 앞서 있습니다 — 적용할 업데이트 없음."; exit 0
elif [ "$BASE" != "$LOCAL" ]; then
  echo "로컬이 원격과 갈라져 있어 자동 업데이트를 멈춥니다(수동 병합 필요)."; exit 1
fi

BEHIND="$(g rev-list --count "HEAD..$UPSTREAM")"
echo "업데이트 있음: $BEHIND개 커밋"
g --no-pager log --oneline "HEAD..$UPSTREAM" 2>/dev/null | head -10 | sed 's/^/    /'

if [ "$CHECK_ONLY" = 1 ]; then echo "(--check: 적용하지 않음. 적용하려면 ./update.sh)"; exit 10; fi

echo "받는 중(fast-forward)…"
g pull --ff-only
echo "다시 설치(install.sh)…"
"$REPO/install.sh" ${ARGS[@]+"${ARGS[@]}"}
echo "업데이트 완료."
