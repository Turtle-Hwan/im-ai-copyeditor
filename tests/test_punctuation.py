"""Markdown 텍스트 편집과 보호 구간 검사를 실제 재조립 경로로 검증한다."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import reassemble as rea
import segment as seg
from text_guards import punctuation_issues, protected_values


DOCUMENT = """# 상태·수명 ##

- [x] 경로 — 준비 대기
  1. 완료·재실행

| 항목·범위 | 설명 |
| :--- | ---: |
| 엔진 | 타깃·툴팁 |
| 코드 | `a | b`와 \\| |

````markdown
```js
const a = '키·값 — 보존';
```
~~~~
````
> 인용·원문 — 유지

`--safe-mode`를 사용한다. “표현·인용”과 https://example.com/a-b?q=x·y 를 보존한다.
10–25%와 $a - b$도 보존한다.
"""


class TestPunctuation(unittest.TestCase):
    def assemble(self, source, rewrite, expected_code=0, preserve=(), strict=True):
        segments = seg.segment(source, preserve)
        worksheet = []
        for s in segments:
            if s["kind"] != "prose":
                continue
            new = rewrite(s["core"])
            worksheet.append(f"<!-- SEG {s['idx']} prose -->\n윤문: {new}\n규칙: " +
                             ("변경없음" if new == s["core"] else "AI-6") + "\n")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "segments.json").write_text(json.dumps({"segments": segments, "preserve_text": preserve}), encoding="utf-8")
            (root / "worksheet.md").write_text("\n".join(worksheet), encoding="utf-8")
            (root / "final.md").write_text("previous", encoding="utf-8")
            args = [str(root / "segments.json"), str(root / "worksheet.md")]
            if strict:
                args.append("--check-punctuation")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                rc = rea.main(args)
            self.assertEqual(rc, expected_code)
            output = (root / "final.md").read_text(encoding="utf-8")
            if expected_code:
                self.assertEqual(output, "previous")
            return output

    def test_markdown_roundtrip(self):
        for source in (DOCUMENT, "A·B | C\n--- | ---\n텍스트 | A·B\n", "# 제목 ##\r\n- 목록\r\n",
                       "~~~py\n```\n보존·대상\n~~~\n", "````\n```\n끝나지 않은·코드\n",
                       "    코드·유지\n\n---\n", "# 제목\n\n- [ ] 목록\n"):
            with self.subTest(source=source):
                self.assertEqual(seg.reconstruct(seg.segment(source)), source)

    def test_edit_heading_list_and_table_without_touching_syntax(self):
        replacements = {"상태·수명": "상태와 수명", "경로 — 준비 대기": "경로: 준비 대기",
                        "완료·재실행": "완료와 재실행", "항목·범위": "항목과 범위", "타깃·툴팁": "타깃과 툴팁"}
        def rewrite(text):
            for before, after in replacements.items():
                text = text.replace(before, after)
            return text
        self.assertEqual(self.assemble(DOCUMENT, rewrite), rewrite(DOCUMENT))

    def test_residue_in_each_editable_container_fails(self):
        for source in ("본문·내용입니다.\n", "# 제목·내용\n", "- 목록·내용\n",
                       "| 제목 |\n| --- |\n| 값·내용 |\n"):
            with self.subTest(source=source):
                self.assemble(source, lambda text: text, 4)

    def test_protected_content_cannot_change_or_be_added_to_bypass_guard(self):
        for before, after in (("`A·B`", "`A와 B`"), ("“A·B”", "“A와 B”"),
                              ("https://example.com/a-b", "https://example.com/ab"),
                              ("10–25%", "10–30%"), ("A·B", "“A·B”")):
            with self.subTest(before=before):
                self.assemble(f"기존 표현 {before}를 그대로 보존한다.\n", lambda text: text.replace(before, after), 4)

    def test_inline_code_fence_length_and_quote_boundaries(self):
        text = '``x = `a. b.` ``와 “안녕. 반가워.”를 보존한다. **다음 문장.** 마지막 문장.\n'
        pieces = seg.segment(text)
        self.assertEqual(seg.reconstruct(pieces), text)
        cores = [s["core"] for s in pieces if s["kind"] == "prose"]
        self.assertEqual(len(cores), 3, cores)
        self.assertEqual(cores[1], "**다음 문장.**")

    def test_numeric_ranges_code_urls_quotes_and_technical_hyphens_exempt(self):
        text = '`a - b`와 "A·B"와 10–25%와 10 - 20과 react-joyride와 https://x.test/a-b 그리고 $a - b$'
        self.assertEqual(punctuation_issues(text), [])
        self.assertEqual(len(protected_values(text)), 6)

    def test_middle_dot_and_separator_variants_detected(self):
        for text in ("타깃·툴팁", "타깃‧툴팁", "타깃・툴팁", "타깃･툴팁", "엔진—상태", "엔진–상태",
                     "엔진 - 상태", "엔진 -- 상태"):
            self.assertTrue(punctuation_issues(text), text)
        self.assertEqual(punctuation_issues("첫 줄\n- 목록"), [])

    def test_named_protected_literal_preserved(self):
        source = "AI·SW마에스트로가 진행하는 프로그램이다.\n"
        self.assertEqual(self.assemble(source, lambda text: text, preserve=["AI·SW마에스트로"]), source)
        self.assemble(source, lambda text: text.replace("AI·SW", "AI SW"), 4, preserve=["AI·SW마에스트로"])

    def test_table_cannot_gain_column_or_newline(self):
        source = "| 제목 |\n| --- |\n| 긴 설명을 담은 내용 |\n"
        for replacement in ("긴 설명을 담은 | 내용", "긴 설명을 담은\n내용"):
            self.assemble(source, lambda text: text.replace("긴 설명을 담은 내용", replacement), 4)

    def test_punctuation_policy_is_opt_in_for_grammar_only_cli(self):
        source = "검사·정리는 필요하다.\n"
        self.assertEqual(self.assemble(source, lambda text: text, strict=False), source)

    def test_link_destination_does_not_hide_following_punctuation(self):
        text = "[안내](https://example.com)·세부 내용을 정리한다."
        self.assertEqual(punctuation_issues(text), ["·"])
        self.assemble(text, lambda value: value, 4)

    def test_multiline_quote_and_inline_code_remain_protected(self):
        for protected in ('"인용·앞\n인용·뒤"', '`코드·앞\n코드·뒤`'):
            source = f"다음 표현 {protected}"
            pieces = seg.segment(source)
            self.assertEqual(len(pieces), 1)
            self.assertEqual(self.assemble(source, lambda value: value), source)
            self.assemble(source, lambda value: value.replace("·", ", "), 4)

    def test_quote_inside_code_does_not_mask_surrounding_prose(self):
        source = '`"` 기획·개발 "설명"'
        self.assertEqual(punctuation_issues(source), ["·"])
        self.assertEqual(self.assemble(source, lambda value: value.replace("·", "과 ")),
                         '`"` 기획과 개발 "설명"')

    def test_list_nested_fence_is_not_editable(self):
        source = "- ```js\n  const x = '코드·원문';\n  ```\n\n본문.\n"
        self.assertEqual(seg.reconstruct(seg.segment(source)), source)
        cores = [s["core"] for s in seg.segment(source) if s["kind"] == "prose"]
        self.assertEqual(cores, ["본문."])
