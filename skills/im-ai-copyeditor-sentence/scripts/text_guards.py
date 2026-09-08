"""윤문 대상의 보호 구간과 문장부호 잔존을 검사한다. 자동 치환은 하지 않는다.

완전한 Markdown 파서나 고유명사 판별기는 아니다. 코드, 인용, URL, 숫자 범위,
인라인 수식을 보수적으로 보호하고 그 밖의 고유명사는 --preserve-text로 지정한다.
"""
from __future__ import annotations

import re

INLINE_CODE_RE = re.compile(r"(?<!`)(`+)(?!`)([\s\S]*?)(?<!`)\1(?!`)")
QUOTE_RE = re.compile(r'''"(?:\\.|[^"\\])*"|“[^”]*”|‘[^’]*’|「[^」]*」|『[^』]*』|(?<!\w)'(?:\\.|[^'\\])*'(?!\w)''')
# 한국어 조사는 단위가 아니다. 모르는 단위라도 범위 숫자 자체는 보호한다.
UNIT = r"(?:개월|시간|달러|명|개|년|월|일|분|초|건|회|점|원|%|[a-zA-Z]+)?"
NUMBER = r"[+-]?\d+(?:[.,]\d+)*"
PROTECTED_RE = re.compile(
    r'(?:https?://|www\.)(?:[^\s<>"`|()]|\([^\s<>"`|()]*\))+'
    r'|' + QUOTE_RE.pattern +
    r'|(?<!\d)' + NUMBER + UNIT + r'[ \t]*[-–—][ \t]*' + NUMBER + UNIT +
    r'|(?<![\\$])\$(?!\$)[^$\n]+\$(?![\d$])'
    r'|[$€₩]' + NUMBER
)
PUNCTUATION_RE = re.compile(r"[·‧・･–—]|(?<=[ \t])-{1,2}(?=[ \t])")
TOKEN_RE = re.compile(INLINE_CODE_RE.pattern + "|" + PROTECTED_RE.pattern)


def protected_spans(text: str, preserve=(), editable_quotes=()):
    """겹치는 구간을 합쳐 원문 위치 순서로 반환한다."""
    # 왼쪽부터 한 토큰씩 소비한다. 코드 안 따옴표가 바깥 문장을 삼키지 않게 한다.
    spans = []
    for match in TOKEN_RE.finditer(text):
        if match.group() in editable_quotes and QUOTE_RE.fullmatch(match.group()):
            # 장식용 따옴표 안의 코드, URL, 수치 보호는 유지한다.
            spans.extend((match.start() + 1 + start, match.start() + 1 + end)
                         for start, end in protected_spans(match.group()[1:-1], preserve))
        else:
            spans.append(match.span())
    for literal in preserve:
        spans.extend(m.span() for m in re.finditer(re.escape(literal), text))
    merged = []
    for start, end in sorted(spans):
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def protected_values(text: str, preserve=(), editable_quotes=()):
    values = []
    for start, end in protected_spans(text, preserve, editable_quotes):
        value = text[start:end]
        # G-21: 끝 마침표 위치 교정은 허용하되 인용 어휘와 ?/!는 보존한다.
        if QUOTE_RE.fullmatch(value):
            normalized = value[0] + value[1:-1].removesuffix(".") + value[-1]
            if not any(literal in value or literal in normalized for literal in preserve):
                value = normalized
        values.append(value)
    return values


def punctuation_issues(text: str, preserve=(), editable_quotes=()):
    spans = protected_spans(text, preserve, editable_quotes)
    return [m.group() for m in PUNCTUATION_RE.finditer(text)
            if not any(start <= m.start() < end for start, end in spans)]


def table_pipes(text: str):
    """이스케이프 또는 인라인 코드 안의 | 는 열 구분자가 아니다."""
    code = [m.span() for m in INLINE_CODE_RE.finditer(text)]
    positions = []
    for match in re.finditer(r"\|", text):
        index = match.start()
        backslashes = len(text[:index]) - len(text[:index].rstrip("\\"))
        if backslashes % 2 == 0 and not any(start <= index < end for start, end in code):
            positions.append(index)
    return positions
