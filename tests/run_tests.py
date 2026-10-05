#!/usr/bin/env python3
"""
Test Runner for HTTP-in-Binary Test Suite
"""

import unittest
import sys
import os

if __name__ == "__main__":
    start_dir = os.path.dirname(__file__)
    suite = unittest.TestLoader().discover(start_dir, pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
