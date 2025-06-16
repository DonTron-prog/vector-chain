#!/usr/bin/env python3
"""
Simple test runner for the pydantic-ai investment research system.
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent, check=False)
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
        return result.returncode
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return 1


def main():
    """Main test runner."""
    print("🧪 Pydantic-AI Investment Research Test Suite")
    print(f"Python: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    # Test categories to run
    test_suites = [
        (["pytest", "tests/unit/", "-v"], "Unit Tests"),
        (["pytest", "tests/unit/", "--cov=tools", "--cov=models", "--cov-report=term-missing"], "Unit Tests with Coverage"),
        (["pytest", "tests/integration/", "-v", "-m", "integration"], "Integration Tests"),
        (["pytest", "tests/", "-m", "not slow and not network"], "Fast Tests Only"),
    ]
    
    failed_suites = []
    
    for cmd, description in test_suites:
        exit_code = run_command(cmd, description)
        if exit_code != 0:
            failed_suites.append(description)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    if failed_suites:
        print(f"❌ Failed test suites: {len(failed_suites)}")
        for suite in failed_suites:
            print(f"   - {suite}")
        print(f"✅ Passed test suites: {len(test_suites) - len(failed_suites)}")
        return 1
    else:
        print(f"✅ All {len(test_suites)} test suites passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())