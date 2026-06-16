#!/usr/bin/env python3
"""segment ↔ reassemble 라운드트립 & 가드 검증. 표준 라이브러리(unittest)만 사용.

실행: python3 -m unittest discover -s tests -v   (repo 루트에서)
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)

import segment as seg  # noqa: E402
import reassemble as rea  # noqa: E402

SAMPLES = [
    "오늘은 날씨가 좋다. 내일은 비가 온다고 한다.\n",
    "한 문장만 있고 개행 없음.",
    "질문인가요? 그렇다! 줄임표도… 끝.\n\n다음 문단입니다.\n",
    "# 제목\n\n본문 첫 문장이다. 두 번째 문장.\n\n- 항목 하나\n- 항목 둘\n\n마지막 문단.\n",
    "따옴표 문장입니다. 그는 \"안녕\"이라고 말했다. 끝났다.\n",
    "```\n코드 블록은 그대로 통과한다.\n여기 마침표. 도 건드리지 않는다.\n```\n바깥 문장.\n",
    "",
    "공백만   있는   줄\n\n   \n다음.\n",
    # 무종결 + 줄바꿈(줄 단위 분절 경로).
    "오늘 날씨 좋다\n내일은 비\n모레는 맑음",
    # 약어(연달아 마침표) — 한 문장 유지.
    "A.I. 기술은 좋다. U.S.A. 시장도 크다. 예를 들어 e.g. 같은 표현.\n",
    # 숫자+마침표 — 문장 끝으로 오인하지 않음.
    "1980. 그해 여름은 더웠다. 끝.\n",
    # 소프트랩 멀티라인 문장(워크시트 한 줄화 경로).
    "이것은 긴 문장인데\n줄바꿈으로 나뉘어 있다. 둘째 문장.\n",
]


class TestRoundtrip(unittest.TestCase):
    def test_lossless_reconstruct(self):
        for i, text in enumerate(SAMPLES):
            segments = seg.segment(text)
            rebuilt = seg.reconstruct(segments)
            self.assertEqual(rebuilt, text, f"샘플 {i} 손실 발생")

    def test_unmodified_worksheet_reproduces_input(self):
        """윤문을 비워 둔(=변경 없음) 워크시트는 입력을 그대로 복원한다."""
        for i, text in enumerate(SAMPLES):
            if not text:
                continue
            with tempfile.TemporaryDirectory() as d:
                inp = os.path.join(d, "in.txt")
                with open(inp, "w", encoding="utf-8") as f:
                    f.write(text)
                self.assertEqual(seg.main([inp, "--outdir", d]), 0)
                rc = rea.main([
                    os.path.join(d, "segments.json"),
                    os.path.join(d, "worksheet.md"),
                    "--out", os.path.join(d, "final.md"),
                ])
                self.assertEqual(rc, 0, f"샘플 {i} 재조립 실패")
                with open(os.path.join(d, "final.md"), encoding="utf-8") as f:
                    self.assertEqual(f.read(), text, f"샘플 {i} 복원 불일치")

    def test_prose_count_matches_worksheet(self):
        text = "문장 하나. 문장 둘. 문장 셋.\n"
        segments = seg.segment(text)
        n_prose = sum(1 for s in segments if s["kind"] == "prose")
        self.assertEqual(n_prose, 3)

    def _n_prose(self, text):
        return sum(1 for s in seg.segment(text) if s["kind"] == "prose")

    def test_no_terminal_punct_splits_by_line(self):
        """마침표 없는 줄바꿈 글은 줄(=문장) 단위로 쪼갠다 — 한 덩어리로 두지 않는다."""
        self.assertEqual(self._n_prose("오늘 날씨 좋다\n내일은 비\n모레는 맑음"), 3)

    def test_abbreviation_not_oversplit(self):
        """약어의 마침표가 연달아 와도 문장이 쪼개지지 않는다(A.I.·U.S.A.·e.g.)."""
        text = "A.I. 기술은 좋다. U.S.A. 시장도 크다. 예를 들어 e.g. 같은 표현.\n"
        cores = [s["core"] for s in seg.segment(text) if s["kind"] == "prose"]
        self.assertEqual(len(cores), 3, cores)
        self.assertTrue(cores[0].startswith("A.I.") and cores[0].endswith("좋다."))

    def test_number_dot_not_oversplit(self):
        """숫자+마침표(연도 등)는 문장 끝으로 오인하지 않는다 — 다음 문장과 붙여 둔다."""
        cores = [s["core"] for s in seg.segment("1980. 그해 여름은 더웠다. 끝.\n")
                 if s["kind"] == "prose"]
        self.assertEqual(cores, ["1980. 그해 여름은 더웠다.", "끝."])

    def test_year_line_is_prose_not_structure(self):
        """3자리 이상 숫자로 시작하는 줄은 번호목록(structure)으로 오판하지 않는다."""
        kinds = [s["kind"] for s in seg.segment("1980. 그해 여름은 더웠다.\n")]
        self.assertNotIn("structure", kinds)

    def test_softwrapped_core_shows_one_line(self):
        """소프트랩으로 core 에 줄바꿈이 있어도 워크시트 원문은 한 물리 줄로 접힌다."""
        text = "이것은 긴 문장인데\n줄바꿈으로 나뉘어 있다. 둘째 문장.\n"
        ws = seg.build_worksheet(seg.segment(text))
        won = [ln for ln in ws.splitlines() if ln.startswith("원문:")]
        self.assertEqual(won[0], "원문: 이것은 긴 문장인데 줄바꿈으로 나뉘어 있다.")
        # 접힌 원문 줄에는 줄바꿈이 없어야 한다(scan.py 가 문장 전체를 보게).
        self.assertNotIn("\n", won[0])

    def test_count_mismatch_hard_fails(self):
        text = "문장 하나. 문장 둘.\n"
        with tempfile.TemporaryDirectory() as d:
            inp = os.path.join(d, "in.txt")
            with open(inp, "w", encoding="utf-8") as f:
                f.write(text)
            seg.main([inp, "--outdir", d])
            # 워크시트에서 마지막 prose 블록을 통째로 지워 카운트 깨뜨리기.
            wp = os.path.join(d, "worksheet.md")
            with open(wp, encoding="utf-8") as f:
                lines = f.read().splitlines()
            prose_starts = [i for i, ln in enumerate(lines)
                            if ln.startswith("<!-- SEG") and " prose " in ln]
            self.assertTrue(prose_starts, "prose 블록이 있어야 함")
            start = prose_starts[-1]
            end = len(lines)
            for j in range(start + 1, len(lines)):
                if lines[j].startswith("<!-- SEG"):
                    end = j
                    break
            kept = lines[:start] + lines[end:]
            with open(wp, "w", encoding="utf-8") as f:
                f.write("\n".join(kept) + "\n")
            rc = rea.main([os.path.join(d, "segments.json"), wp, "--out", os.path.join(d, "final.md")])
            self.assertEqual(rc, 2, "카운트 불일치는 hard fail(2) 이어야 함")

    def test_overedit_aborts(self):
        text = "짧다.\n"
        with tempfile.TemporaryDirectory() as d:
            inp = os.path.join(d, "in.txt")
            with open(inp, "w", encoding="utf-8") as f:
                f.write(text)
            seg.main([inp, "--outdir", d])
            wp = os.path.join(d, "worksheet.md")
            with open(wp, encoding="utf-8") as f:
                content = f.read()
            content = content.replace("윤문: ", "윤문: 완전히 다른 매우 긴 문장으로 통째로 바꿔버린다 정말로.", 1)
            with open(wp, "w", encoding="utf-8") as f:
                f.write(content)
            rc = rea.main([os.path.join(d, "segments.json"), wp, "--out", os.path.join(d, "final.md")])
            self.assertEqual(rc, 3, "과윤문(>50%)은 abort(3) 이어야 함")

    def test_cli_segment_runs(self):
        inp = os.path.join(ROOT, "tests", "sample_in.txt")
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run(
                [sys.executable, os.path.join(SCRIPTS, "segment.py"), inp, "--outdir", d],
                capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(os.path.exists(os.path.join(d, "segments.json")))
            self.assertTrue(os.path.exists(os.path.join(d, "worksheet.md")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
