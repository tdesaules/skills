"""Run both validator suites with the same interpreter/dependencies used by CI."""

from pathlib import Path
import sys
import unittest


root = Path(__file__).resolve().parents[1]
suite = unittest.TestSuite()
for relative in ("skill/scripts", "tests/unit"):
    path = str(root / relative)
    tests = unittest.TestLoader().discover(path, top_level_dir=path)
    if not tests.countTestCases():
        raise SystemExit(f"No tests found in {relative}")
    suite.addTests(tests)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
