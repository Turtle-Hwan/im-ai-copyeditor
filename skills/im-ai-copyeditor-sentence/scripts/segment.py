#!/usr/bin/env python3
"""segment.py — 한국어 글을 문장 부호 단위로 잘라 윤문 작업표를 만든다.

문장 단위 다듬기의 1단계다. 정규식으로 한꺼번에 바꾸지 않는다. 문장 부호로 자르되,
종결부호가 없는 줄바꿈 글은 줄 단위로 쪼개 한 줄을 한 문장으로 본다. 약어(A.I.·e.g.)나
숫자(1980.)의 마침표는 문장 끝으로 오인하지 않는다. 에이전트가 한 문장씩 읽고 다듬게 한다.
파이썬 표준 기능만 쓴다.

산출물:
  - segments.json : 원본 구조 정보. 되붙일 때 기준이 되니 고치지 않는다.
  - worksheet.md  : 에이전트가 문장마다 '윤문/규칙'을 채우는 작업 파일.

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

from text_guards import QUOTE_RE, protected_spans, table_pipes

FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
PREFIX_RE = re.compile(r"^( *)(#{1,6}[ \t]+|[-*+][ \t]+(?:\[[ xX]\][ \t]+)?|\d{1,2}[.)][ \t]+)")
DIVIDER_RE = re.compile(r"^[ \t]*(?:(?:-[ \t]*){3,}|(?:\*[ \t]*){3,}|(?:_[ \t]*){3,}|=+)[ \t]*$")
TABLE_DIVIDER_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?\s*$")


def is_table_divider(line):
    return "|" in line and bool(TABLE_DIVIDER_RE.fullmatch(line))

# 문장 종결: . ? ! … 。 (닫는 따옴표/괄호가 뒤따를 수 있음) + 뒤에 공백/끝.
SENT_END_RE = re.compile(r'([.?!…。]+["\'”’」』)\]*_]*)(\s+|$)')

# 약어의 마침표는 문장 끝이 아니다 — 단일 '.' 매치일 때만 검사해 분절을 건너뛴다.
#   이니셜리즘: A.I.  U.S.A.  e.g.  i.e.  Ph.D.  (한두 글자+마침표가 둘 이상 '연달아')
ABBREV_RUN_RE = re.compile(r"(?:[A-Za-z]{1,2}\.){2,}$")
#   단일 토큰 약어(끝 마침표 하나): vs. etc. cf. Dr. No. Fig. et al. …
ABBREV_WORD_RE = re.compile(
    r"(?:^|[\s(\"'\[])(vs|etc|cf|al|et|Dr|Mr|Mrs|Ms|St|No|Fig|Vol|pp|eq)\.$",
    re.IGNORECASE,
)


def _is_abbrev_dot(upto: str) -> bool:
    """'upto'(이번 종결 직전까지의 본문, 끝이 '.')가 약어 마침표면 True.

    ABBREV_RUN_RE 는 '$' 로 끝을 잡으므로 마지막 40자만 봐도 충분하다. 긴 입력에서
    반복 토큰을 정규식이 거듭 되짚는 비용(ReDoS류)을 막으려고 꼬리만 검사한다.
    """
    return bool(ABBREV_RUN_RE.search(upto[-40:]) or ABBREV_WORD_RE.search(upto))


def _split_lines(prefix: str, core: str, trail: str):
    """종결부호 없이 줄바꿈으로 나뉜 core 를 줄 단위 세그먼트로 쪼갠다(무손실).

    각 물리 줄이 한 문장이 된다(문장 단위 의도). 마지막 줄 뒤에 원래 꼬리 공백을 복원한다.
    """
    pieces = core.splitlines(keepends=True)
    out = []
    for i, piece in enumerate(pieces):
        if piece.endswith("\n"):
            c, suf = piece[:-1], "\n"
        else:
            c, suf = piece, ""
        if i == len(pieces) - 1:
            suf += trail
        out.append((prefix if i == 0 else "", c, suf))
    return out


def split_sentences(block: str, preserve=()):
    """프로즈 블록(여러 줄 가능)을 문장 단위로 자른다.

    각 문장을 (prefix, core, suffix) 로 반환한다.
      prefix : 직전 공백(첫 문장의 들여쓰기 포함)
      core   : 종결 부호까지의 문장 본문(윤문 대상)
      suffix : 문장 뒤 공백/개행(다음 문장 전까지)
    이으면 block 과 정확히 일치한다.
    """
    out = []
    n = len(block)
    # 선두 공백은 첫 문장의 prefix 로. (re.match(r"\s*") 는 항상 매치하니 group(0)을 그대로 쓴다.)
    lead = re.match(r"\s*", block).group(0)
    pending_prefix = lead

    last = len(lead)
    protected = protected_spans(block, preserve)
    for m in SENT_END_RE.finditer(block, last):
        if any(start <= m.start() < end for start, end in protected):
            continue
        # 단일 '.' 가 약어(A.I.·e.g.·etc.)나 숫자(1980.·3.14.) 뒤면 문장 끝이 아니다 —
        # 건너뛰어 다음 종결까지 이어 붙인다(과대분절 방지; 한국어 문장은 거의 '다/요'로 끝남).
        if m.group(1) == "." and (
            block[m.start(1) - 1: m.start(1)].isdigit()
            or _is_abbrev_dot(block[last:m.start(2)])
        ):
            continue
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
        if core and "\n" in core and not any("\n" in block[start:end] for start, end in protected if end > last):
            # 무종결 + 줄바꿈: 한 덩어리로 두지 않고 줄 단위로 쪼갠다(문장 단위 의도).
            out.extend(_split_lines(pending_prefix, core, trail))
        elif core:
            out.append((pending_prefix, core, trail))
        elif out:
            # 꼬리가 공백뿐이면 직전 문장 suffix 에 붙인다.
            p, c, s = out[-1]
            out[-1] = (p, c, s + tail)
        else:
            out.append((pending_prefix, "", tail))
    return out


def segment(text: str, preserve=(), *, edit_blockquotes=False):
    segments = []
    idx = 0
    lines = text.splitlines(keepends=True)
    fence = None
    in_table = False
    prose_buf = []  # 연속 프로즈 줄 모음
    list_indents = []  # 활성 목록의 본문 들여쓰기

    def flush_prose():
        nonlocal idx
        if not prose_buf:
            return
        block = "".join(prose_buf)
        prose_buf.clear()
        for prefix, core, suffix in split_sentences(block, preserve):
            idx += 1
            segments.append(
                {"idx": idx, "kind": "prose", "prefix": prefix, "core": core, "suffix": suffix}
            )

    def raw(value, review_required=False):
        nonlocal idx
        if value:
            idx += 1
            segments.append({"idx": idx, "kind": "structure", "raw": value})
            if review_required:
                segments[-1]["review_required"] = True

    def editable(value, prefix="", suffix="", role="text"):
        nonlocal idx
        # 제목, 목록 행, 표 셀은 구조를 유지하는 하나의 작업 칸으로 다룬다.
        lead = value[:len(value) - len(value.lstrip())]
        core = value.strip()
        trail = value[len(value.rstrip()):]
        if not core:
            raw(prefix + value + suffix)
            return
        idx += 1
        segments.append({"idx": idx, "kind": "prose", "prefix": prefix + lead,
                         "core": core, "suffix": trail + suffix, "role": role})

    for number, line in enumerate(lines):
        original_line = line
        quote = re.match(r"^ {0,3}(?:>[ \t]?)+", line)
        outer_prefix = ""
        if quote and edit_blockquotes:
            flush_prose()
            outer_prefix, line = quote[0], line[quote.end():]
        indent = len(line) - len(line.lstrip(" "))
        if line.strip():
            while list_indents and indent < list_indents[-1]:
                list_indents.pop()
        code_indent = (list_indents[-1] if list_indents else 0) + 4
        indented_code = line.startswith("\t") or indent >= code_indent
        marker = FENCE_RE.match(line)
        list_prefix = PREFIX_RE.match(line)
        if not fence and not marker and list_prefix and not list_prefix[2].startswith("#"):
            marker = FENCE_RE.match(line[list_prefix.end():])
        if fence or marker:
            flush_prose()
            raw(original_line)
            if fence:
                if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                    fence = None
            else:
                fence = marker[1]
            in_table = False
            continue
        # 직접 인용과 HTML은 자동 편집 범위에서 제외하되 검토 누락을 숨기지 않는다.
        excluded_text = bool(re.match(r"^ {0,3}(>|<)", line))
        if not line.strip() or indented_code or excluded_text or re.match(r"^ {0,3}\[[^\]]+\]:", line):
            flush_prose()
            raw(original_line, review_required=excluded_text and not indented_code)
            in_table = False
            continue
        table_header = number + 1 < len(lines) and is_table_divider(lines[number + 1])
        if is_table_divider(line):
            flush_prose()
            raw(original_line)
            continue
        pipes = table_pipes(line)
        if pipes and (table_header or in_table):
            flush_prose()
            raw(outer_prefix)
            start = 0
            for end in pipes:
                editable(line[start:end], role="table-cell")
                raw("|")
                start = end + 1
            editable(line[start:], role="table-cell")
            in_table = True
            continue
        in_table = False
        if DIVIDER_RE.fullmatch(line):
            flush_prose()
            raw(original_line)
            continue
        prefix = PREFIX_RE.match(line)
        if prefix:
            flush_prose()
            value, suffix = line[prefix.end():], ""
            if prefix[2].startswith("#"):
                closing = re.search(r"[ \t]+#+[ \t]*(?:\r?\n)?$", value)
                if closing:
                    value, suffix = value[:closing.start()], value[closing.start():]
            is_heading = prefix[2].startswith("#")
            if not is_heading:
                list_indents.append(prefix.end())
            editable(value, outer_prefix + prefix[0], suffix, role="heading" if is_heading else "list")
            continue
        if outer_prefix:
            editable(line, outer_prefix, role="blockquote")
            continue
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
        "> 각 텍스트 칸의 **윤문:** 줄에 다듬은 내용을, **규칙:** 줄에 적용한 규칙 번호를 적습니다.",
        "> 제목·목록 행·표 셀도 작업 칸입니다. 줄바꿈이나 표 열을 추가하지 마세요.",
        "> · 고칠 게 없으면 윤문에 원문을 그대로 옮기고 규칙에 `변경없음`.",
        "> · 한 칸 안의 긴 문장은 나눠도 됩니다. 칸 병합과 정보 순서 변경은 하지 마세요.",
        "> · 변경없음 칸도 맞춤법, 번역투, 군더더기와 요청한 문장부호 정리를 다시 확인하세요.",
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
            # 소프트랩으로 core 안에 줄바꿈이 있어도 표시는 한 줄로 접는다(원문 한 줄 = 한 문장).
            # 실제 재조립은 segments.json 의 core 를 쓰므로 표시 접기는 무손실에 영향 없음.
            shown_core = re.sub(r"\s*\n\s*", " ", s["core"])
            lines.append(f"원문: {shown_core}")
            lines.append("윤문: ")
            lines.append("규칙: ")
            lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="문장 부호 단위 분절 → 윤문 워크시트")
    ap.add_argument("input", help="입력 텍스트 파일")
    ap.add_argument("--outdir", default=None, help="출력 디렉토리(기본: 입력 파일과 같은 폴더)")
    ap.add_argument("--preserve-text", action="append", default=[],
                    help="정확히 보존할 고유명사/기술 표현. 필요하면 반복 지정")
    ap.add_argument("--editable-quote", action="append", default=[],
                    help="직접 인용이 아닌 장식용 따옴표 표현(따옴표 포함). 필요하면 반복 지정")
    ap.add_argument("--edit-blockquotes", action="store_true",
                    help="직접 인용이 아닌 작성자의 Markdown 인용 블록을 편집 대상으로 포함")
    args = ap.parse_args(argv)

    with open(args.input, "r", encoding="utf-8", newline="") as f:
        text = f.read()

    if any(not value.strip() or value not in text for value in args.preserve_text):
        ap.error("--preserve-text 는 원문에 있는 비어 있지 않은 표현이어야 합니다.")
    if any(not QUOTE_RE.fullmatch(value) or value not in text for value in args.editable_quote):
        ap.error("--editable-quote 는 원문에 있는 따옴표로 감싼 표현이어야 합니다.")
    segments = segment(text, args.preserve_text, edit_blockquotes=args.edit_blockquotes)
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
            {"source": os.path.abspath(args.input), "n_prose": n_prose, "preserve_text": args.preserve_text,
             "editable_quotes": args.editable_quote,
             "n_total": len(segments), "segments": segments},
            f, ensure_ascii=False, indent=2,
        )
    ws_path = os.path.join(outdir, "worksheet.md")
    with open(ws_path, "w", encoding="utf-8") as f:
        f.write(build_worksheet(segments))

    print(f"텍스트 작업 칸 {n_prose}개로 나눔 (전체 조각 {len(segments)}개)")
    if any(s.get("review_required") for s in segments):
        print("  인용/HTML 제외 구간은 별도 검토 필요. 직접 인용이 아닌 블록은 --edit-blockquotes 사용.")
    print(f"  segments.json → {seg_path}")
    print(f"  worksheet.md  → {ws_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
