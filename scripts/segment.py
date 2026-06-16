#!/usr/bin/env python3
"""segment.py — 한국어 텍스트를 문장 부호 단위로 분절해 윤문 워크시트를 만든다.

paraphrasing-korean 스킬의 강제 장치 1단계.
grep/정규식 "탐지" 대신, 텍스트를 문장 단위 행으로 잘라 에이전트가 한 행씩
in/out 윤문하도록 만든다. 표준 라이브러리만 사용한다(외부 의존 없음).

산출물:
  - segments.json : 원본 구조 정보 (되붙일 때 쓰는 기준, 수정하지 않는다)
  - worksheet.md  : 에이전트가 문장마다 '윤문/규칙'을 채우는 작업 파일

손실 없음 규칙:
  잘라 낸 조각을 순서대로 도로 이으면 원문과 글자 하나까지 똑같아진다. tests/ 가 이를 검사한다.

사용법:
  python3 segment.py <input.txt> [--outdir DIR]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

# 구조(structure) 행 = 윤문 대상이 아니라 그대로 통과시키는 줄.
# 마크다운 헤딩 · 리스트 · 인용 · 표 · 코드펜스 · 수평선 등.
STRUCTURE_RE = re.compile(
    r"""^\s*(
        \#{1,6}\s        |   # 헤딩
        [-*+]\s          |   # 불릿
        \d+[.)]\s        |   # 번호 목록
        >\s?             |   # 인용
        \|               |   # 표
        (-{3,}|\*{3,}|_{3,})\s*$  |  # 수평선
        ```              |   # 코드펜스
        ~~~                  # 코드펜스
    )""",
    re.VERBOSE,
)
FENCE_RE = re.compile(r"^\s*(```|~~~)")

# 문장 종결: . ? ! … 。 (닫는 따옴표/괄호가 뒤따를 수 있음) + 뒤에 공백/끝.
SENT_END_RE = re.compile(r'([.?!…。]+["\'”’」』)\]]*)(\s+|$)', re.UNICODE)


def split_sentences(block: str):
    """프로즈 블록(여러 줄 가능)을 문장 단위로 자른다.

    각 문장을 (prefix, core, suffix) 로 반환한다.
      prefix : 직전 공백(첫 문장의 들여쓰기 포함)
      core   : 종결 부호까지의 문장 본문(윤문 대상)
      suffix : 문장 뒤 공백/개행(다음 문장 전까지)
    이으면 block 과 정확히 일치한다.
    """
    out = []
    pos = 0
    n = len(block)
    # 선두 공백은 첫 문장의 prefix 로.
    lead_m = re.match(r"\s*", block)
    lead = lead_m.group(0) if lead_m else ""
    pos = len(lead)
    pending_prefix = lead

    last = pos
    for m in SENT_END_RE.finditer(block, pos):
        core = block[last:m.start(1)] + m.group(1)
        suffix = m.group(2)
        out.append((pending_prefix, core, suffix))
        pending_prefix = ""  # 다음 문장의 prefix 는 이전 suffix 가 흡수.
        last = m.end()
    # 종결 부호 없이 남은 꼬리(예: 마지막 줄에 마침표 없음).
    if last < n:
        tail = block[last:]
        m2 = re.search(r"\s*$", tail)
        trail = m2.group(0) if m2 else ""
        core = tail[: len(tail) - len(trail)]
        if core:
            out.append((pending_prefix, core, trail))
        elif out:
            # 꼬리가 공백뿐이면 직전 문장 suffix 에 붙인다.
            p, c, s = out[-1]
            out[-1] = (p, c, s + tail)
        else:
            out.append((pending_prefix, "", tail))
    return out


def segment(text: str):
    segments = []
    idx = 0
    lines = text.splitlines(keepends=True)
    in_fence = False
    prose_buf = []  # 연속 프로즈 줄 모음

    def flush_prose():
        nonlocal idx
        if not prose_buf:
            return
        block = "".join(prose_buf)
        prose_buf.clear()
        for prefix, core, suffix in split_sentences(block):
            idx += 1
            segments.append(
                {"idx": idx, "kind": "prose", "prefix": prefix, "core": core, "suffix": suffix}
            )

    for line in lines:
        is_fence = bool(FENCE_RE.match(line))
        stripped = line.strip()
        is_structure = (
            in_fence
            or is_fence
            or stripped == ""
            or bool(STRUCTURE_RE.match(line))
        )
        if is_structure:
            flush_prose()
            idx += 1
            segments.append({"idx": idx, "kind": "structure", "raw": line})
            if is_fence:
                in_fence = not in_fence
        else:
            prose_buf.append(line)
    flush_prose()
    return segments


def reconstruct(segments) -> str:
    parts = []
    for s in segments:
        if s["kind"] == "prose":
            parts.append(s["prefix"] + s["core"] + s["suffix"])
        else:
            parts.append(s["raw"])
    return "".join(parts)


def build_worksheet(segments) -> str:
    lines = [
        "# 윤문 워크시트",
        "",
        "> 각 문장 칸의 **윤문:** 줄에 다듬은 문장을, **규칙:** 줄에 적용한 규칙 번호를 적습니다.",
        "> · 고칠 게 없으면 윤문에 원문을 그대로 옮기고 규칙에 `변경없음`.",
        "> · 문장을 합치거나 나누거나 순서를 바꾸지 마세요. '그대로 둘 줄'은 손대지 않습니다.",
        "> · 수치·고유명사·직접 인용·영어 약어·법령 조문은 그대로 둡니다.",
        "",
        "---",
        "",
    ]
    for s in segments:
        if s["kind"] == "structure":
            shown = s["raw"].rstrip("\n")
            lines.append(f"<!-- SEG {s['idx']} structure (수정 금지): {shown} -->")
            lines.append("")
        else:
            lines.append(f"<!-- SEG {s['idx']} prose -->")
            lines.append(f"원문: {s['core']}")
            lines.append("윤문: ")
            lines.append("규칙: ")
            lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="문장 부호 단위 분절 → 윤문 워크시트")
    ap.add_argument("input", help="입력 텍스트 파일")
    ap.add_argument("--outdir", default=None, help="출력 디렉토리(기본: 입력 파일과 같은 폴더)")
    args = ap.parse_args(argv)

    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()

    segments = segment(text)
    rebuilt = reconstruct(segments)
    if rebuilt != text:
        print("오류: 자른 조각을 도로 이었더니 원문과 달라졌습니다 — 되붙일 때 원문이 손상될 수 있어 멈춥니다.",
              file=sys.stderr)
        return 2

    outdir = args.outdir or os.path.dirname(os.path.abspath(args.input))
    os.makedirs(outdir, exist_ok=True)
    n_prose = sum(1 for s in segments if s["kind"] == "prose")

    seg_path = os.path.join(outdir, "segments.json")
    with open(seg_path, "w", encoding="utf-8") as f:
        json.dump(
            {"source": os.path.abspath(args.input), "n_prose": n_prose,
             "n_total": len(segments), "segments": segments},
            f, ensure_ascii=False, indent=2,
        )
    ws_path = os.path.join(outdir, "worksheet.md")
    with open(ws_path, "w", encoding="utf-8") as f:
        f.write(build_worksheet(segments))

    print(f"문장 {n_prose}개로 나눔 (전체 조각 {len(segments)}개)")
    print(f"  segments.json → {seg_path}")
    print(f"  worksheet.md  → {ws_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
