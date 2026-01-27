#!/usr/bin/env python3
"""Run tests with coverage."""

import subprocess
import sys

def run_tests():
    """Run all tests with coverage."""
    try:
        # Install coverage if not present
        subprocess.check_call([sys.executable, "-m", "pip", "install", "coverage"])
        
        # Run tests with coverage
        subprocess.check_call([
            sys.executable, "-m", "coverage", "run", 
            "-m", "pytest", "tests/", "-v"
        ])
        
        # Generate coverage report
        subprocess.check_call([
            sys.executable, "-m", "coverage", "report", 
            "--include=core/*", "--show-missing"
        ])
        
        print("\n✅ All tests passed!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()