#!/usr/bin/env python3
"""scan.py — 작업표의 각 문장에 정규식으로 '후보 힌트'를 단다. 선택 단계다.

segment.py 와 에이전트 윤문 사이에 끼우는 선택 단계 Phase 2.5 다. 정규식은 의심 가는
규칙 번호를 `힌트:` 줄로 표시할 뿐 윤문을 대신하지 않는다. 에이전트는 여전히 모든
문장을 직접 읽고 다듬는다. 힌트는 주의를 끌어 줄 뿐이고 틀릴 수도 있다.

힌트 패턴(regex-patterns.json)은 '고정밀 맞춤법·표기 오류'만 담는다 — 정규식이 룰북
예시(ICL)보다 확실히 잘 잡는, 문맥 안 타는 고정 오타류. 문체·번역투·AI 티는 룰북의
before→after 예시로 에이전트가 직접 판단하므로 여기서 힌트로 달지 않는다(맞춤법 외
명령에선 힌트가 거의 안 붙을 수 있다 — 정상이다).

`힌트:` 줄은 `원문:` 바로 다음에 들어가며 reassemble.py 는 이를 읽지 않는다.

파이썬 표준 기능만 쓴다. 사용법:
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
