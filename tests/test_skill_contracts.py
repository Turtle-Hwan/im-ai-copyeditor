"""로딩과 안전 지침의 알려진 회귀를 막는 제한된 정적 검사.

이 검사는 YAML 파서나 문체 품질/의미 보존 평가를 대체하지 않는다.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestSkillContracts(unittest.TestCase):
    def test_integrated_and_ai_commands_require_punctuation_guard(self):
        for name in ("im-ai-copyeditor", "im-ai-copyeditor-ai"):
            text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("final.md --check-punctuation", text)

    def test_change_ratio_is_not_an_output_grade(self):
        prime = (ROOT / "references" / "prime-directives.md").read_text(encoding="utf-8")
        skill = (ROOT / "skills" / "im-ai-copyeditor" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("등급 {A~D}", skill)
        self.assertNotIn("변경량 10~25%", prime)
        self.assertIn("변경률 0%도 정상", prime)
        self.assertIn("다른 항목이 좋아도 상쇄할 수 없다", prime)

    def test_known_fact_invention_instructions_do_not_return(self):
        ai = (ROOT / "references" / "ai-tell-rules.md").read_text(encoding="utf-8")
        for instruction in ("→ 처리 시간을 절반으로 줄였습니다", "→ 미루면 비용이 두 배로 듭니다",
                            "→ 재구매가 60%였습니다", "출처가 없으면 빼고, 체감상", "→ 이 기술로 효율이 오른다"):
            self.assertNotIn(instruction, ai)
