import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from cht_elf import CORE_SIZE, reconstruct


class TraditionalChineseElfTests(unittest.TestCase):
    def test_rejects_truncated_core(self):
        with self.assertRaisesRegex(ValueError, "CORE.GT4 identity"):
            reconstruct(b"")

    def test_rejects_unrecognized_core_of_the_correct_size(self):
        with self.assertRaisesRegex(ValueError, "CORE.GT4 identity"):
            reconstruct(bytes(CORE_SIZE))
