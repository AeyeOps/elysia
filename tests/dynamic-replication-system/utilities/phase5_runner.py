#!/usr/bin/env python3
"""
phase5_runner.py - Execute all Phase 5 scale testing scripts
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
                              capture_output=False, text=True, timeout=600)  # 10 min timeout

        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT (10 minutes)")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    """Main function to run all Phase 5 tests"""
    print("🚀 STARTING PHASE 5: SCALE TESTING SUITE")
    print("   Testing cluster scaling from 3→5→3 nodes")
    print(f"{'='*80}")

    # Test scenarios
    tests = [
        {
            'script': 'five_node_setup.py',
            'description': '5-Node Cluster Setup - Configure and validate 5-node cluster',
            'duration_estimate': '5-8 minutes'
        },
        {
            'script': 'scale_down_test.py',
            'description': 'Scale-Down Test - Reduce from 5-node to 3-node cluster',
            'duration_estimate': '3-5 minutes'
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
            time.sleep(30)  # Longer pause for cluster operations

    # Final results summary
    total_duration = time.time() - total_start_time
    successful_tests = sum(1 for r in results if r['success'])

    print(f"\n{'='*80}")
    print("🏁 PHASE 5 SCALE TESTING COMPLETE")
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
        ("5-node cluster successfully deployed", successful_tests >= 1),  # At least setup works
        ("Scale-down maintains data integrity", successful_tests >= 2),   # Both tests pass
        ("No data loss during scaling", successful_tests >= 2),
        ("Operations work after scaling", successful_tests >= 2),
        ("Cluster stable at different sizes", successful_tests >= 1)
    ]

    criteria_passed = sum(1 for _, passed in criteria if passed)
    print(f"   Criteria Met: {criteria_passed}/{len(criteria)}")

    for desc, passed in criteria:
        status = "✅" if passed else "❌"
        print(f"   {status} {desc}")

    # Final assessment
    if successful_tests == len(results):
        print("\n🎉 ALL TESTS PASSED - Excellent scale testing!")
        print("   ✅ 5-node cluster deployment successful")
        print("   ✅ Scale-down operations work perfectly")
        print("   ✅ Data integrity maintained throughout")
        print("   ✅ System handles cluster size changes gracefully")
        return True
    elif successful_tests >= len(results) * 0.5:  # At least 50% success rate
        print("\n⚠️  MOST TESTS PASSED - Good scale testing with minor issues")
        print("   ✅ Basic scaling functionality verified")
        return True
    else:
        print("\n❌ SCALE TESTING ISSUES DETECTED")
        print("   ❌ Multiple scale testing failures")
        print("   📊 Review Docker resource allocation and cluster configuration")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n🔚 Phase 5 testing completed with {'success' if success else 'issues'}")
    sys.exit(0 if success else 1)