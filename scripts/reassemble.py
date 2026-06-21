#!/usr/bin/env python3
"""reassemble.py — 채운 작업표를 원문 구조에 맞춰 한 편의 윤문본으로 되붙인다.

문장 단위 다듬기의 2단계다. 원본 구조 정보 segments.json 과 채운 윤문 worksheet.md 를
합쳐 final.md 를 만든다.

핵심 안전장치:
  - 문장 수 검사: 작업표의 문장 칸 수가 원본 문장 수와 같아야 한다.
    다르면 멈춘다. 문장이 사라지거나 합쳐지면 뜻 보존이 깨진 것으로 본다.
  - 변경량 검사: 전체 변경량이 30% 를 넘으면 경고하고 50% 를 넘으면 멈춘다.
  - '그대로 둘 줄'인 헤딩·목록·코드 따위는 원문 그대로 지나간다.

사용법:
  python3 reassemble.py <segments.json> <worksheet.md> [--out final.md] [--max-change 0.5]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

SEG_HEADER_RE = re.compile(r"<!--\s*SEG\s+(\d+)\s+(prose|structure)")


def parse_worksheet(text: str):
    """워크시트에서 prose 세그먼트별 윤문/규칙을 추출한다 → {idx: (윤문, 규칙)}."""
    result = {}
    cur_idx = None
    cur_kind = None
    field = None  # '윤문' | '규칙' | None
    buf_yun = []
    buf_rule = []

    def commit():
        if cur_idx is not None and cur_kind == "prose":
            result[cur_idx] = ("\n".join(buf_yun).strip(), "\n".join(buf_rule).strip())

    for line in text.splitlines():
        m = SEG_HEADER_RE.search(line)
        if m:
            commit()
            cur_idx = int(m.group(1))
            cur_kind = m.group(2)
            field = None
            buf_yun, buf_rule = [], []
            continue
        if cur_kind != "prose":
            continue
        if line.startswith("원문:"):
            field = None
            continue
        if line.startswith("윤문:"):
            field = "yun"
            buf_yun.append(line[len("윤문:"):].lstrip())
            continue
        if line.startswith("규칙:"):
            field = "rule"
            buf_rule.append(line[len("규칙:"):].lstrip())
            continue
        if field == "yun":
            buf_yun.append(line)
        elif field == "rule":
            buf_rule.append(line)
    commit()
    return result


def levenshtein(a: str, b: str) -> int:
    """두 문자열의 편집 거리. 표준 두 줄 DP, O(len(a)·len(b))."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def main(argv=None):
    ap = argparse.ArgumentParser(description="워크시트 → 최종 윤문본 재조립")
    ap.add_argument("segments", help="segment.py 가 만든 segments.json")
    ap.add_argument("worksheet", help="에이전트가 채운 worksheet.md")
    ap.add_argument("--out", default=None, help="최종본 출력 경로(기본: segments.json 옆 final.md)")
    ap.add_argument("--max-change", type=float, default=0.5, help="허용 최대 변경률(기본 0.5)")
    args = ap.parse_args(argv)

    with open(args.segments, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(args.worksheet, "r", encoding="utf-8") as f:
        ws = f.read()

    segments = data["segments"]
    prose_ids = [s["idx"] for s in segments if s["kind"] == "prose"]
    rewrites = parse_worksheet(ws)

    # --- 문장 수 검사 (다르면 멈춤) ---
    missing = [i for i in prose_ids if i not in rewrites]
    extra = [i for i in rewrites if i not in set(prose_ids)]
    if missing or extra:
        print("오류: 작업표의 문장 수가 원본과 다릅니다.", file=sys.stderr)
        if missing:
            print(f"  누락된 세그먼트: {missing}", file=sys.stderr)
        if extra:
            print(f"  알 수 없는 세그먼트: {extra}", file=sys.stderr)
        return 2

    # --- 재조립 + 변경률 ---
    parts = []
    tot_core = 0
    tot_dist = 0
    diffs = []
    for s in segments:
        if s["kind"] == "structure":
            parts.append(s["raw"])
            continue
        yun, rule = rewrites[s["idx"]]
        new_core = yun or s["core"]
        parts.append(s["prefix"] + new_core + s["suffix"])
        d = levenshtein(s["core"], new_core)
        tot_core += len(s["core"])
        tot_dist += d
        if new_core != s["core"]:
            diffs.append((s["idx"], s["core"], new_core, rule))

    final = "".join(parts)
    change = (tot_dist / tot_core) if tot_core else 0.0

    out_path = args.out
    if not out_path:
        out_path = os.path.join(os.path.dirname(os.path.abspath(args.segments)), "final.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(final)

    print(f"재조립 완료: {len(prose_ids)}문장, 변경 {len(diffs)}건, 변경률 {change:.1%}")
    print(f"  final.md → {out_path}")
    if change > args.max_change:
        print(f"ABORT: 변경률 {change:.1%} > 한계 {args.max_change:.0%} — 과윤문. 롤백 권장.",
              file=sys.stderr)
        return 3
    if change > 0.30:
        print(f"경고: 변경률 {change:.1%} > 30% — 의미 보존을 다시 점검하세요.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
