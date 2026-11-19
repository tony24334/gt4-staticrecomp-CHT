import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("cht_crash_trace", ROOT / "scripts/prepare_cht_crash_trace.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ChtCrashTraceTests(unittest.TestCase):
    def test_unique_anchors_and_reversal(self):
        for name in ("kernel.cpp", "dispatch.cpp", "unit_00A1.cpp"):
            source = "\n".join(before for before, _ in module.patches(name))
            self.assertEqual(module.reverse(name, module.derive(name, source)), source)
            with self.assertRaises(ValueError):
                module.derive(name, source + source)
            with self.assertRaises(ValueError):
                module.derive(name, "unexpected donor")

    def test_unpinned_input_refused_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "runtime/src"
            source.mkdir(parents=True)
            (source / "kernel.cpp").write_text("wrong donor")
            with self.assertRaisesRegex(ValueError, "Pinned donor mismatch"):
                module.prepare(root, root, root / "capsule")
            self.assertFalse((root / "capsule").exists())


if __name__ == "__main__":
    unittest.main()
