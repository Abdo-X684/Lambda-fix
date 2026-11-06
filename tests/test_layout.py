import unittest
from pathlib import Path

from merge.layout import is_safe_relative, rewrite_includes, to_bhl, to_classic

ROOT = Path(__file__).resolve().parents[1]


class LayoutTests(unittest.TestCase):
    def test_bhl_to_classic(self):
        cases = {
            "src/game/client/hud/timer.cpp": "cl_dll/hud/timer.cpp",
            "src/game/server/player.cpp": "dlls/player.cpp",
            "src/game/shared/bitvec.h": "game_shared/bitvec.h",
            "src/common/convar.h": "common/convar.h",
            "src/pm_shared/pm_shared.cpp": "pm_shared/pm_shared.cpp",
            "src/public/steamtypes.h": "public/steamtypes.h",
            "src/engine/eiface.h": "engine/eiface.h",
            "dlls/world.cpp": "dlls/world.cpp",  # already classic
        }
        for src, expected in cases.items():
            with self.subTest(src=src):
                self.assertEqual(to_classic(src), expected)

    def test_round_trip(self):
        for path in ["src/game/client/hud.cpp", "src/game/server/client.cpp", "src/common/cvardef.h"]:
            self.assertEqual(to_bhl(to_classic(path)), path)

    def test_normalises_backslashes(self):
        self.assertEqual(to_classic("src\\game\\client\\hud.cpp"), "cl_dll/hud.cpp")

    def test_rewrite_includes_explicit_rule_wins(self):
        text = '#include "src/common/convar.h"\n#include "hud/timer.h"\n#include <stdio.h>\n'
        new, count = rewrite_includes(text, [("src/", "")])
        self.assertEqual(count, 1)
        self.assertIn('#include "common/convar.h"', new)
        self.assertIn('#include "hud/timer.h"', new)
        self.assertIn("#include <stdio.h>", new)

    def test_rewrite_includes_default_layout(self):
        new, count = rewrite_includes('#include "src/game/client/hud.h"\n')
        self.assertEqual(count, 1)
        self.assertIn('#include "cl_dll/hud.h"', new)

    def test_safe_relative(self):
        self.assertTrue(is_safe_relative("cl_dll/hud.cpp"))
        self.assertFalse(is_safe_relative("../etc/passwd"))
        self.assertFalse(is_safe_relative("/etc/passwd"))
        self.assertFalse(is_safe_relative(""))


if __name__ == "__main__":
    unittest.main()
