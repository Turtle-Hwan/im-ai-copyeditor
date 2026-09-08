#!/usr/bin/env python3
"""reassemble.py — 채운 작업표를 원문 구조에 맞춰 한 편의 윤문본으로 되붙인다.

문장 단위 다듬기의 2단계다. 원본 구조 정보 segments.json 과 채운 윤문 worksheet.md 를
합쳐 final.md 를 만든다.

핵심 안전장치:
  - 작업표 검사: ID 중복·누락·추가와 미작성 칸을 거부한다.
    칸 안의 문장 병합·분할과 의미 보존은 별도 검토가 필요하다.
  - 변경량 검사: 전체 변경량이 30% 를 넘으면 경고하고, 기본 상한 50% 를 넘으면 중단한다.
  - 구조 기호와 코드 블록은 그대로 두며 인라인 보호 표현 변경을 거부한다.
  - --check-punctuation 으로 중간점/구분용 대시 잔존 검사를 켤 수 있다.

사용법:
  python3 reassemble.py <segments.json> <worksheet.md> [--out final.md] [--max-change 0.5]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import tempfile

from text_guards import protected_values, punctuation_issues, table_pipes

SEG_HEADER_RE = re.compile(r"^<!--\s*SEG\s+(\d+)\s+(prose|structure)\b")


def parse_worksheet(text: str):
    """워크시트에서 prose 세그먼트별 윤문/규칙을 추출한다 → {idx: (윤문, 규칙)}."""
    result = {}
    cur_idx = None
    cur_kind = None
    field = None  # '윤문' | '규칙' | None
    buf_yun = []
    buf_rule = []
    seen = set()
    fields = set()

    def commit():
        if cur_idx is not None and cur_kind == "prose":
            yun, rule = "\n".join(buf_yun).strip(), "\n".join(buf_rule).strip()
            if not yun or not rule:
                raise ValueError(f"세그먼트 {cur_idx}: 윤문과 규칙을 모두 작성해야 합니다.")
            result[cur_idx] = (yun, rule)

    for line in text.splitlines():
        m = SEG_HEADER_RE.match(line)
        if m:
            commit()
            cur_idx = int(m.group(1))
            if cur_idx in seen:
                raise ValueError(f"중복된 세그먼트: {cur_idx}")
            seen.add(cur_idx)
            cur_kind = m.group(2)
            field = None
            fields = set()
            buf_yun, buf_rule = [], []
            continue
        if cur_kind != "prose":
            continue
        if line.startswith("원문:"):
            field = None
            continue
        if line.startswith("윤문:"):
            if "yun" in fields:
                raise ValueError(f"세그먼트 {cur_idx}: 윤문 칸이 중복되었습니다.")
            fields.add("yun")
            field = "yun"
            buf_yun.append(line[len("윤문:"):].lstrip())
            continue
        if line.startswith("규칙:"):
            if "rule" in fields:
                raise ValueError(f"세그먼트 {cur_idx}: 규칙 칸이 중복되었습니다.")
            fields.add("rule")
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


def atomic_write(path: str, text: str):
    """검증을 마친 결과만 같은 디렉토리의 임시 파일에서 교체한다."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                         dir=os.path.dirname(os.path.abspath(path)),
                                         prefix=".copyeditor-", delete=False) as f:
            temporary = f.name
            f.write(text)
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def main(argv=None):
    ap = argparse.ArgumentParser(description="워크시트 → 최종 윤문본 재조립")
    ap.add_argument("segments", help="segment.py 가 만든 segments.json")
    ap.add_argument("worksheet", help="에이전트가 채운 worksheet.md")
    ap.add_argument("--out", default=None, help="최종본 출력 경로(기본: segments.json 옆 final.md)")
    ap.add_argument("--max-change", type=float, default=0.5, help="변경률 상한(기본: 0.5)")
    ap.add_argument("--check-punctuation", action="store_true",
                    help="보호 구간 밖 중간점과 구분용 대시가 남으면 저장하지 않고 종료 코드 4")
    args = ap.parse_args(argv)
    if not math.isfinite(args.max_change) or not 0 <= args.max_change <= 1:
        ap.error("--max-change 는 0 이상 1 이하의 유한한 값이어야 합니다.")

    with open(args.segments, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(args.worksheet, "r", encoding="utf-8") as f:
        ws = f.read()

    segments = data["segments"]
    prose_ids = [s["idx"] for s in segments if s["kind"] == "prose"]
    if len({s["idx"] for s in segments}) != len(segments):
        print("오류: 원본 세그먼트 ID가 중복되었습니다.", file=sys.stderr)
        return 2
    try:
        rewrites = parse_worksheet(ws)
    except ValueError as error:
        print(f"오류: {error}", file=sys.stderr)
        return 2

    # ID 대조는 작업표 완결성 검사이며, 문장 경계나 의미 보존의 증명이 아니다.
    missing = [i for i in prose_ids if i not in rewrites]
    extra = [i for i in rewrites if i not in set(prose_ids)]
    if missing or extra:
        print("오류: 작업표의 세그먼트 ID가 원본과 다릅니다.", file=sys.stderr)
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
        # 작업표에서 한 줄로 표시된 원문도 명시적인 변경없음 검토 후에는 원래 줄바꿈을 복원한다.
        shown_core = re.sub(r"\s*\n\s*", " ", s["core"])
        if rule == "변경없음" and yun not in (s["core"], shown_core):
            print(f"오류: 세그먼트 {s['idx']}의 변경없음 표기와 윤문이 다릅니다.", file=sys.stderr)
            return 2
        new_core = s["core"] if rule == "변경없음" else yun
        if rule != "변경없음" and new_core == s["core"]:
            print(f"오류: 세그먼트 {s['idx']}에 교정 규칙을 적었지만 실제 변경이 없습니다.", file=sys.stderr)
            return 2
        preserve = data.get("preserve_text", [])
        editable_quotes = data.get("editable_quotes", [])
        if protected_values(s["core"], preserve, editable_quotes) != protected_values(new_core, preserve, editable_quotes):
            print(f"오류: 세그먼트 {s['idx']}의 코드/인용/URL/보호 표현이 변경되었습니다.", file=sys.stderr)
            return 4
        if s.get("role") and ("\n" in new_core or "\r" in new_core or
                              (s["role"] == "table-cell" and table_pipes(new_core))):
            print(f"오류: 세그먼트 {s['idx']}의 Markdown 행/열 구조가 변경되었습니다.", file=sys.stderr)
            return 4
        if args.check_punctuation and punctuation_issues(new_core, preserve, editable_quotes):
            print(f"오류: 세그먼트 {s['idx']}에 중간점 또는 구분용 대시가 남아 있습니다.", file=sys.stderr)
            return 4
        parts.append(s["prefix"] + new_core + s["suffix"])
        d = levenshtein(s["core"], new_core)
        tot_core += len(s["core"])
        tot_dist += d
        if new_core != s["core"]:
            diffs.append((s["idx"], s["core"], new_core, rule))

    final = "".join(parts)
    change = (tot_dist / tot_core) if tot_core else 0.0

    if change > args.max_change:
        print(f"ABORT: 변경률 {change:.1%} > 한계 {args.max_change:.0%} — 결과를 저장하지 않았습니다.",
              file=sys.stderr)
        return 3
    if change > 0.30:
        print(f"경고: 변경률 {change:.1%} > 30% — 의미 보존을 다시 점검하세요.", file=sys.stderr)
    out_path = args.out or os.path.join(os.path.dirname(os.path.abspath(args.segments)), "final.md")
    atomic_write(out_path, final)
    excluded = [s['idx'] for s in segments if s.get('review_required')]
    if excluded:
        print(f"부분 재조립: 별도 검토가 필요한 인용/HTML 칸 {excluded}. 전체 윤문 완료로 보고하지 마세요.")
    else:
        print("재조립 완료 (작업표 검사 통과, 교정 누락과 의미는 별도 검토)")
    print(f"  {len(prose_ids)}개 텍스트 칸, 변경 {len(diffs)}건, 변경률 {change:.1%}")
    print(f"  final.md → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
