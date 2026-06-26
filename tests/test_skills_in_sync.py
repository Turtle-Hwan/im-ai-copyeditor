#!/usr/bin/env python3
"""각 스킬 패키지의 references/scripts 가 SoT 와 일치하는지 검증한다.

심볼릭 링크를 제거하고 실제 파일을 복사하는 구조라(Windows 호환), 최상위
references/ · scripts/ 를 고친 뒤 `python3 scripts/sync_skills.py` 를 돌리지 않으면
패키지 사본이 어긋난다. 이 테스트가 그 어긋남을 잡는다.

실행: python3 -m unittest discover -s tests -v   (repo 루트에서)
고치는 법: python3 scripts/sync_skills.py
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)

import sync_skills as sync  # noqa: E402


class TestSkillsInSync(unittest.TestCase):
    def test_no_committed_symlinks_under_skills(self):
        found = []
        for base, dirs, files in os.walk(os.path.join(ROOT, "skills")):
            for name in list(dirs) + files:
                p = os.path.join(base, name)
                if os.path.islink(p):
                    found.append(os.path.relpath(p, ROOT))
        self.assertEqual(found, [], f"심링크가 남아 있습니다(Windows에서 깨짐): {found}")

    def test_packages_match_source_of_truth(self):
        problems = []
        for pkg, kinds in sync.PACKAGES.items():
            for kind in kinds:
                src = sync.SRC[kind]
                dst = os.path.join(sync.SKILLS_DIR, pkg, kind)
                changed, extra = sync.diff(src, dst, kind)
                problems += [f"어긋남 skills/{pkg}/{kind}/{r}" for r in changed]
                problems += [f"불필요 skills/{pkg}/{kind}/{r}" for r in extra]
        self.assertEqual(
            problems, [],
            "패키지 사본이 SoT와 다릅니다. `python3 scripts/sync_skills.py` 실행:\n"
            + "\n".join(problems),
        )


if __name__ == "__main__":
    unittest.main()
