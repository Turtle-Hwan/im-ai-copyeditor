#!/usr/bin/env python3
"""sync_skills.py — 공유 자원을 각 스킬 패키지에 실제 파일로 동기화한다.

저장소는 references/ 와 scripts/ 를 단일 진실 원천(SoT)으로 둔다. 예전에는 각 스킬
패키지가 이 둘을 심볼릭 링크(`../../references`, `../../scripts`)로 가리켰으나,
Windows(core.symlinks=false)에서는 심링크가 "../../references" 같은 글자가 든 깨진
텍스트 파일로 체크아웃돼 스킬이 스크립트·규칙을 찾지 못했다. 그래서 링크 대신 실제
파일을 각 패키지에 복사해 자기완결형으로 만든다.

저작 흐름: references/ · scripts/ 만 고친 뒤 이 스크립트를 돌려 패키지를 갱신한다.
  python3 scripts/sync_skills.py          # 동기화(복사)
  python3 scripts/sync_skills.py --check  # 복사하지 않고 어긋남만 보고(어긋나면 종료 코드 1)

`--check` 는 CI/테스트가 "패키지 사본이 SoT 와 일치하는가"를 확인하는 용도다.
파이썬 표준 기능만 쓴다.
"""
from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(REPO, "skills")
SRC = {
    "references": os.path.join(REPO, "references"),
    "scripts": os.path.join(REPO, "scripts"),
}
# 이 파일은 개발용 도구라 각 패키지에 복사하지 않는다.
SELF = os.path.basename(os.path.abspath(__file__))

# 패키지별로 받을 자원. grill 은 스크립트를 쓰지 않아 references 만 받는다.
PACKAGES = {
    "im-ai-copyeditor": ("references", "scripts"),
    "im-ai-copyeditor-sentence": ("references", "scripts"),
    "im-ai-copyeditor-trans": ("references", "scripts"),
    "im-ai-copyeditor-ai": ("references", "scripts"),
    "im-ai-copyeditor-grammar": ("references", "scripts"),
    "im-ai-copyeditor-grill": ("references",),
}


def _relevant(root, kind):
    """root 아래의 복사 대상 파일을 상대경로로 모은다. __pycache__·*.pyc·자기 자신 제외."""
    out = []
    if not os.path.isdir(root):
        return out
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".pyc"):
                continue
            if kind == "scripts" and f == SELF:
                continue
            out.append(os.path.relpath(os.path.join(base, f), root))
    return sorted(out)


def diff(src, dst, kind):
    """(없거나_다른_파일, 불필요한_파일) 상대경로 목록을 돌려준다."""
    src_files = set(_relevant(src, kind))
    dst_files = set(_relevant(dst, kind))
    changed = [
        rel for rel in sorted(src_files)
        if not os.path.exists(os.path.join(dst, rel))
        or not filecmp.cmp(os.path.join(src, rel), os.path.join(dst, rel), shallow=False)
    ]
    extra = sorted(dst_files - src_files)
    return changed, extra


def apply_sync(src, dst, kind):
    changed, extra = diff(src, dst, kind)
    for rel in changed:
        d = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(d) or ".", exist_ok=True)
        shutil.copy2(os.path.join(src, rel), d)
    for rel in extra:
        os.remove(os.path.join(dst, rel))
    return changed, extra


def main(argv=None):
    ap = argparse.ArgumentParser(description="공유 references/scripts 를 각 스킬 패키지에 동기화")
    ap.add_argument("--check", action="store_true",
                    help="복사하지 않고 어긋남만 보고한다(어긋나면 종료 코드 1)")
    args = ap.parse_args(argv)

    problems = 0
    for pkg, kinds in PACKAGES.items():
        for kind in kinds:
            src, dst = SRC[kind], os.path.join(SKILLS_DIR, pkg, kind)
            if args.check:
                changed, extra = diff(src, dst, kind)
                for rel in changed:
                    print(f"어긋남: skills/{pkg}/{kind}/{rel}")
                for rel in extra:
                    print(f"불필요: skills/{pkg}/{kind}/{rel}")
                problems += len(changed) + len(extra)
            else:
                changed, extra = apply_sync(src, dst, kind)
                for rel in changed:
                    print(f"복사: skills/{pkg}/{kind}/{rel}")
                for rel in extra:
                    print(f"삭제: skills/{pkg}/{kind}/{rel}")

    if args.check:
        if problems:
            print(f"\n동기화 안 됨: {problems}건. `python3 scripts/sync_skills.py` 를 실행하세요.")
            return 1
        print("동기화 상태 정상.")
        return 0
    print("동기화 완료.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
