#!/usr/bin/env python3
"""
wave1_runner.py - Execute all Wave 1 tests in sequence
"""

import sys
import os
import subprocess
import time

def run_script(script_name, description):
    """Run a test script and return success status"""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"{'='*50}")

    try:
        result = subprocess.run([sys.executable, script_name],
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Failed to run {script_name}: {e}")
        return False

def main():
    """Main function to run all Wave 1 tests"""
    print("🚀 Starting Wave 1: Positive Path Validation Tests")
    print("This will test dynamic replication in a 3-node Weaviate cluster")

    tests = [
        ("cluster_check.py", "Cluster Health Check - Verify 3 healthy nodes"),
        ("create_system_collections.py", "System Collections Creation - ELYSIA_* with replication_factor=3"),
        ("verify_replication.py", "Replication Verification - Data sync across all nodes"),
        ("test_derived_collections.py", "Derived Collections Test - CHUNKED_* inheritance")
    ]

    results = []

    for script, description in tests:
        success = run_script(script, description)
        results.append((script, success))

        if not success:
            print(f"⚠️  {script} failed, but continuing with other tests...")

    # Summary
    print(f"\n{'='*50}")
    print("WAVE 1 TEST SUMMARY")
    print(f"{'='*50}")

    passed = 0
    total = len(results)

    for script, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{script}: {status}")
        if success:
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 WAVE 1 COMPLETE: All positive path validation tests passed!")
        print("✅ Cluster shows 3 healthy nodes")
        print("✅ System collections created with factor=3")
        print("✅ Data written to node 1 readable from nodes 2 & 3")
        print("✅ Derived collections inherit parent replication")
        return True
    else:
        print("⚠️  WAVE 1 INCOMPLETE: Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)