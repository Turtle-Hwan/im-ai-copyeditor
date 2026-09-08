"""설명문의 콜론이 YAML mapping으로 해석되던 회귀를 방지한다."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestSkillMetadata(unittest.TestCase):
    def test_descriptions_with_colons_use_block_scalars(self):
        for path in (ROOT / "skills").glob("*/SKILL.md"):
            frontmatter = path.read_text(encoding="utf-8").split("---", 2)[1].splitlines()
            for index, line in enumerate(frontmatter):
                if line.startswith("description:"):
                    value = line.partition(":")[2].strip()
                    self.assertNotIn(": ", value, path.parent.name)
                    if value == ">-":
                        self.assertTrue(frontmatter[index + 1].startswith("  "), path.parent.name)
