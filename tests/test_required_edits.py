"""필요한 교정이 재조립에서 차단되지 않는지 확인한다. 모델의 교정 누락 평가는 별도다."""
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
from text_guards import protected_values, punctuation_issues


class TestRequiredEdits(unittest.TestCase):
    def assemble(self, source, replacements, options=(), expected=0):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "input.md").write_text(source, encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(seg.main([str(root / "input.md"), *options]), 0)
            data = json.loads((root / "segments.json").read_text(encoding="utf-8"))
            self.assertEqual(seg.reconstruct(data["segments"]), source)
            rows = []
            for s in data["segments"]:
                if s["kind"] == "prose":
                    new = replacements.get(s["core"], s["core"])
                    rule = "G-14" if new != s["core"] else "변경없음"
                    rows.append(f"<!-- SEG {s['idx']} prose -->\n윤문: {new}\n규칙: {rule}\n")
            (root / "worksheet.md").write_text("\n".join(rows), encoding="utf-8")
            (root / "final.md").write_text("previous", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
                result = rea.main([str(root / "segments.json"), str(root / "worksheet.md"), "--check-punctuation"])
            self.assertEqual(result, expected)
            final = (root / "final.md").read_text(encoding="utf-8")
            if expected:
                self.assertEqual(final, "previous")
            return final, output.getvalue()

    def test_short_style_edits_are_not_rejected_by_edit_distance(self):
        for before, after in (("# 되붙이기\n", "# 재조립\n"),
                              ("상기 내용을 숙지하시기 바랍니다", "위 내용을 확인해 주세요")):
            with self.subTest(before=before):
                self.assertEqual(self.assemble(before, {before.lstrip("# ").strip(): after.lstrip("# ").strip()})[0], after)

    def test_numbers_do_not_lock_korean_particles_or_surrounding_prose(self):
        for before, after in (("약 10–20명에게 안내한다.", "약 10–20명을 대상으로 안내한다."),
                              ("가격은 $5이고 배송비는 $2이다.", "가격은 $5이며 배송비는 $2이다.")):
            with self.subTest(before=before):
                self.assertEqual(self.assemble(before, {before: after})[0], after)
        self.assertEqual(protected_values("10–20명에게"), ["10–20명"])
        self.assertEqual(protected_values("$5이고 배송비는 $2이다."), ["$5", "$2"])
        self.assertEqual(protected_values("$2 - 1$와 $x + y$"), ["$2 - 1$", "$x + y$"])
        self.assemble("가격은 $5이다.", {"가격은 $5이다.": "가격은 $6이다."}, expected=4)

    def test_decorative_quotes_can_be_removed_after_source_classification(self):
        source = '그는 "정말" 빨랐다.'
        target = '그는 정말 빨랐다.'
        self.assertEqual(self.assemble(source, {source: target}, ("--editable-quote", '"정말"'))[0], target)
        self.assemble(source, {source: target}, expected=4)
        self.assertEqual(punctuation_issues('"설계·구현"', editable_quotes=['"설계·구현"']), ["·"])
        self.assemble('"`API·v1`"을 쓴다.', {'"`API·v1`"을 쓴다.': '`API v1`을 쓴다.'},
                      ("--editable-quote", '"`API·v1`"'), expected=4)

    def test_quote_period_placement_not_quote_wording_can_change(self):
        source = '그는 "괜찮다".라고 말했다.'
        target = '그는 "괜찮다."라고 말했다.'
        self.assertEqual(self.assemble(source, {source: target})[0], target)
        for changed in ('그는 "좋다."라고 말했다.', '그는 "괜찮다!"라고 말했다.'):
            self.assemble(source, {source: changed}, expected=4)
        self.assemble(source, {source: target}, ("--preserve-text", '"괜찮다"'), expected=4)

    def test_nested_list_and_continuation_prose_are_editable_but_code_is_not(self):
        source = "- 결과\n    - 잘 됬다.\n      메세지를 보낸다.\n\n          코드의 역활\n\n    코드의 역활\n"
        segments = seg.segment(source)
        cores = [s["core"] for s in segments if s["kind"] == "prose"]
        self.assertIn("잘 됬다.", cores)
        self.assertIn("메세지를 보낸다.", cores)
        # 마지막 4칸 줄은 상위 목록의 이어지는 본문이다. 독립된 들여쓴 코드는 그대로 둔다.
        self.assertNotIn("코드의 역활", [s["core"] for s in seg.segment("    코드의 역활\n") if s["kind"] == "prose"])
        result, _ = self.assemble(source, {"잘 됬다.": "잘 됐다.", "메세지를 보낸다.": "메시지를 보낸다."})
        self.assertEqual(result, source.replace("됬다", "됐다").replace("메세지", "메시지"))

    def test_authored_blockquote_can_be_edited_without_touching_fenced_code(self):
        source = "> 이 기능의 역활을 설명할께요.\n> ```txt\n> 메세지·원문\n> ```\n"
        result, status = self.assemble(source, {"이 기능의 역활을 설명할께요.": "이 기능의 역할을 설명할게요."},
                                       ("--edit-blockquotes",))
        self.assertEqual(result, source.replace("역활", "역할").replace("할께요", "할게요"))
        self.assertNotIn("부분 재조립", status)

    def test_unreviewed_html_and_quotes_are_not_reported_as_complete(self):
        for source in ("<p>메세지를 확인하세요.</p>\n", "> 이 기능의 역활을 설명할께요.\n"):
            result, status = self.assemble(source, {})
            self.assertEqual(result, source)
            self.assertIn("부분 재조립", status)
            self.assertNotIn("재조립 완료", status)

    def test_invalid_quote_exemption_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.md"
            source.write_text('"정말" 빠르다.', encoding="utf-8")
            for value in ("정말", '"없는 표현"', ""):
                with self.subTest(value=value), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        seg.main([str(source), "--editable-quote", value])
