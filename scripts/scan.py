#!/usr/bin/env python3
"""scan.py — 워크시트의 각 문장에 정규식 기반 '후보 힌트'를 단다 (선택 단계).

위치: segment.py 와 에이전트 윤문(Phase 4) 사이의 **선택적** Phase 2.5.
정규식은 의심 가는 규칙 ID를 `힌트:` 줄로 표시할 뿐, 윤문을 대신 하지 않는다.
에이전트는 여전히 모든 prose 문장을 직접 읽고 다듬는다(힌트는 주의 환기용, 오탐 가능).

`힌트:` 줄은 `원문:` 바로 다음에 삽입되며 reassemble.py 가 무시한다(윤문/규칙만 읽음).

표준 라이브러리만 사용. 사용법:
  python3 scan.py <worksheet.md> [--patterns references/regex-patterns.json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

SEG_HEADER_RE = re.compile(r"<!--\s*SEG\s+(\d+)\s+(prose|structure)")


def load_patterns(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    compiled = []
    for p in data.get("patterns", []):
        try:
            rx = re.compile(p["regex"])
        except re.error as e:
            print(f"경고: 패턴 {p.get('id')} 정규식 오류 — {e}", file=sys.stderr)
            continue
        compiled.append((p.get("id", "?"), p.get("name", ""), rx))
    return compiled


def annotate(text: str, patterns) -> tuple[str, int]:
    lines = text.splitlines()
    out = []
    i = 0
    n_hint = 0
    cur_kind = None
    while i < len(lines):
        line = lines[i]
        m = SEG_HEADER_RE.search(line)
        if m:
            cur_kind = m.group(2)
        out.append(line)
        # 원문 줄 다음에만 힌트 삽입 (prose 한정, 중복 방지).
        if cur_kind == "prose" and line.startswith("원문:"):
            sentence = line[len("원문:"):].strip()
            already = (i + 1 < len(lines) and lines[i + 1].startswith("힌트:"))
            hits = []
            for pid, _name, rx in patterns:
                if rx.search(sentence) and pid not in hits:
                    hits.append(pid)
            if hits and not already:
                out.append("힌트: " + ", ".join(hits))
                n_hint += 1
        i += 1
    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), n_hint


def main(argv=None):
    ap = argparse.ArgumentParser(description="워크시트에 정규식 후보 힌트 달기(선택)")
    ap.add_argument("worksheet")
    default_patterns = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "references", "regex-patterns.json",
    )
    ap.add_argument("--patterns", default=default_patterns)
    args = ap.parse_args(argv)

    patterns = load_patterns(args.patterns)
    with open(args.worksheet, "r", encoding="utf-8") as f:
        text = f.read()
    annotated, n_hint = annotate(text, patterns)
    with open(args.worksheet, "w", encoding="utf-8") as f:
        f.write(annotated)
    print(f"힌트 표시: {n_hint}개 문장 (패턴 {len(patterns)}종). 윤문은 에이전트가 수행.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
