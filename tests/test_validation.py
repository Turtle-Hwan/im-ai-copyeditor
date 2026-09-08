"""실패한 검증은 기존 결과를 바꾸거나 성공으로 보고하지 않는다."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import reassemble as rea
import segment as seg


class TestValidation(unittest.TestCase):
    def run_case(self, worksheet, expected, source="원래 문장입니다.\n", existing=True, options=()):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "segments.json").write_text(json.dumps({"segments": seg.segment(source)}), encoding="utf-8")
            (root / "worksheet.md").write_text(worksheet, encoding="utf-8")
            out = root / "final.md"
            if existing:
                out.write_bytes(b"previous verified output\r\n")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
                result = rea.main([str(root / "segments.json"), str(root / "worksheet.md"), "--out", str(out), *options])
            self.assertEqual(result, expected)
            if expected:
                self.assertNotIn("재조립 완료", stdout.getvalue())
                if existing:
                    self.assertEqual(out.read_bytes(), b"previous verified output\r\n")
                else:
                    self.assertFalse(out.exists())
            else:
                self.assertEqual(out.read_text(encoding="utf-8"), source)

    def test_incomplete_rows_rejected(self):
        for fields in ("윤문: \n규칙: S-1", "윤문: 원래 문장입니다.\n규칙: ", "원문: 원래 문장입니다."):
            with self.subTest(fields=fields):
                self.run_case("<!-- SEG 1 prose -->\n" + fields, 2)

    def test_duplicate_id_rejected(self):
        row = "<!-- SEG 1 prose -->\n윤문: 원래 문장입니다.\n규칙: 변경없음\n"
        self.run_case(row + row, 2)

    def test_duplicate_field_rejected(self):
        self.run_case("<!-- SEG 1 prose -->\n윤문: 원래 문장입니다.\n윤문: 추가\n규칙: S-1", 2)

    def test_missing_and_unknown_id_rejected(self):
        for worksheet in ("", "<!-- SEG 2 prose -->\n윤문: 원래 문장입니다.\n규칙: 변경없음"):
            self.run_case(worksheet, 2)

    def test_false_unchanged_rejected(self):
        self.run_case("<!-- SEG 1 prose -->\n윤문: 원래 문장입니다!\n규칙: 변경없음", 2)

    def test_overedit_preserves_previous_output(self):
        for options in ((), ("--max-change", "0.5")):
            with self.subTest(options=options):
                self.run_case("<!-- SEG 1 prose -->\n윤문: 다른 내용으로 전부 새로 쓴 아주 긴 문장입니다.\n규칙: S-1", 3,
                              options=options)

    def test_rule_without_actual_edit_rejected(self):
        self.run_case("<!-- SEG 1 prose -->\n윤문: 원래 문장입니다.\n규칙: S-1", 2)

    def test_failure_does_not_create_output(self):
        self.run_case("<!-- SEG 1 prose -->\n윤문: \n규칙: ", 2, existing=False)

    def test_explicit_unchanged_and_folded_softwrap(self):
        self.run_case("<!-- SEG 1 prose -->\n윤문: 원래 문장입니다.\n규칙: 변경없음", 0)
        self.run_case("<!-- SEG 1 prose -->\n윤문: 원래 문장입니다.\n규칙: 변경없음", 0,
                      source="원래\n문장입니다.\n")

    def test_invalid_max_change_rejected(self):
        for value in ("nan", "inf", "-0.1", "1.1"):
            with self.subTest(value=value), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    rea.main(["unused.json", "unused.md", "--max-change", value])
                self.assertEqual(error.exception.code, 2)

    def test_atomic_replace_failure_cleans_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "final.md"
            out.write_text("previous", encoding="utf-8")
            with patch.object(rea.os, "replace", side_effect=OSError("test failure")):
                with self.assertRaises(OSError):
                    rea.atomic_write(str(out), "next")
            self.assertEqual(out.read_text(encoding="utf-8"), "previous")
            self.assertEqual(list(Path(directory).iterdir()), [out])
