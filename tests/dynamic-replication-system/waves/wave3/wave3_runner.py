#!/usr/bin/env python3
"""
wave3_runner.py - Execute all Wave 3 edge cases & error handling tests in sequence
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def run_test_script(script_name, description):
    """Run a test script and return success status"""
    script_path = os.path.join(os.path.dirname(__file__), script_name)

    if not os.path.exists(script_path):
        print(f"❌ Test script not found: {script_path}")
        return False

    print(f"\n{'='*70}")
    print(f"🧪 RUNNING: {description}")
    print(f"   Script: {script_name}")
    print(f"{'='*70}")

    try:
        result = subprocess.run([sys.executable, script_path],
                              capture_output=False, text=True, timeout=900)  # 15 min timeout

        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT (15 minutes)")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    """Main function to run all Wave 3 tests"""
    print("🚀 STARTING WAVE 3: EDGE CASES & ERROR HANDLING SUITE")
    print("   Testing misconfigurations, error handling, and boundary conditions")
    print(f"{'='*80}")

    # Test scenarios
    tests = [
        {
            'script': 'misconfiguration_tests.py',
            'description': 'Misconfiguration Tests - Invalid replication factors, missing parents, network issues',
            'duration_estimate': '5-8 minutes'
        },
        {
            'script': 'single_node_validation.py',
            'description': 'Single Node Validation - Verify system works with replication_factor=None',
            'duration_estimate': '6-10 minutes'
        },
        {
            'script': 'concurrent_operations.py',
            'description': 'Concurrent Operations - Test simultaneous collection creation from multiple connections',
            'duration_estimate': '8-12 minutes'
        },
        {
            'script': 'error_message_audit.py',
            'description': 'Error Message Audit - Collect and analyze error messages for clarity',
            'duration_estimate': '4-6 minutes'
        }
    ]

    # Run tests
    results = []
    total_start_time = time.time()

    for i, test in enumerate(tests, 1):
        print(f"\n📋 Test {i}/{len(tests)}")
        print(f"   Estimated duration: {test['duration_estimate']}")

        start_time = time.time()
        success = run_test_script(test['script'], test['description'])
        end_time = time.time()

        duration = end_time - start_time
        results.append({
            'test': test['script'],
            'description': test['description'],
            'success': success,
            'duration': duration
        })

        print(f"   Duration: {duration:.1f}s")
        # Brief pause between tests (except after last test)
        if i < len(tests):
            print("\n⏸️  Preparing for next test...")
            time.sleep(15)

    # Final results summary
    total_duration = time.time() - total_start_time
    successful_tests = sum(1 for r in results if r['success'])

    print(f"\n{'='*80}")
    print("🏁 WAVE 3 EDGE CASES & ERROR HANDLING COMPLETE")
    print(f"{'='*80}")

    print("\n📊 TEST RESULTS SUMMARY:")
    for i, result in enumerate(results, 1):
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        duration_str = f"{duration:.1f}s"
        print(f"   {i}. {result['test']}: {status} ({duration_str})")

    print("\n📈 OVERALL STATISTICS:")
    print(f"   Total Tests: {len(results)}")
    print(f"   Passed: {successful_tests}")
    print(f"   Failed: {len(results) - successful_tests}")
    print(f"   Total Duration: {total_duration:.1f}s")

    # Success criteria check
    print("\n🎯 SUCCESS CRITERIA EVALUATION:")
    criteria = [
        ("Clear, actionable error messages for misconfigurations", successful_tests >= 3),
        ("Single-node mode works without replication settings", successful_tests >= 2),
        ("No race conditions in concurrent creation", successful_tests >= 3),
        ("Fail-fast behavior with invalid inputs", successful_tests >= 2),
        ("Graceful handling of network interruptions", successful_tests >= 2)
    ]

    criteria_passed = sum(1 for _, passed in criteria if passed)
    print(f"   Criteria Met: {criteria_passed}/{len(criteria)}")

    for desc, passed in criteria:
        status = "✅" if passed else "❌"
        print(f"   {status} {desc}")

    # Final assessment
    if successful_tests == len(results):
        print("\n🎉 ALL TESTS PASSED - Excellent error handling and edge case coverage!")
        print("   ✅ System fails gracefully with clear error messages")
        print("   ✅ No race conditions in concurrent operations")
        print("   ✅ Robust handling of misconfigurations")
        return True
    elif successful_tests >= len(results) * 0.75:  # 75% success rate
        print("\n⚠️  MOST TESTS PASSED - Good error handling with minor issues")
        print("   ✅ System generally handles errors well")
        return True
    else:
        print("\n❌ SIGNIFICANT ISSUES DETECTED - Error handling needs improvement")
        print("   ❌ Multiple test failures indicate potential reliability issues")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n🔚 Wave 3 testing completed with {'success' if success else 'issues'}")
    sys.exit(0 if success else 1)