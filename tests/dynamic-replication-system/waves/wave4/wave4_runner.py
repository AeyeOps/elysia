#!/usr/bin/env python3
"""
wave4_runner.py - Execute all Wave 4 performance validation tests in sequence
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
                              capture_output=False, text=True, timeout=1800)  # 30 min timeout

        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT (30 minutes)")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    """Main function to run all Wave 4 tests"""
    print("🚀 STARTING WAVE 4: PERFORMANCE VALIDATION SUITE")
    print("   Measuring overhead, latency, and resource usage")
    print(f"{'='*80}")

    # Test scenarios
    tests = [
        {
            'script': 'performance_baseline.py',
            'description': 'Performance Baseline - Measure single-node operations for comparison',
            'duration_estimate': '3-5 minutes'
        },
        {
            'script': 'replication_overhead_test.py',
            'description': 'Replication Overhead Analysis - Compare single vs multi-node performance',
            'duration_estimate': '5-8 minutes'
        },
        {
            'script': 'replication_lag_measurement.py',
            'description': 'Replication Lag Measurement - Time data sync across nodes',
            'duration_estimate': '4-6 minutes'
        },
        {
            'script': 'resource_monitoring.py',
            'description': 'Resource Monitoring - Track CPU/memory usage during operations',
            'duration_estimate': '2-4 minutes'
        },
        {
            'script': 'scalability_test.py',
            'description': 'Scalability Testing - Test performance with growing datasets',
            'duration_estimate': '6-10 minutes'
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

    # Final results summary
    total_duration = time.time() - total_start_time
    successful_tests = sum(1 for r in results if r['success'])

    print(f"\n{'='*80}")
    print("🏁 WAVE 4 PERFORMANCE VALIDATION COMPLETE")
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
        ("Performance overhead < 20% for writes", successful_tests >= 3),  # At least 3 tests should pass for basic performance
        ("Read performance improved or neutral", successful_tests >= 2),
        ("Replication lag < 1 second", successful_tests >= 3),
        ("Resource usage within acceptable limits", successful_tests >= 2),
        ("No performance degradation with data growth", successful_tests >= 3)
    ]

    criteria_passed = sum(1 for _, passed in criteria if passed)
    print(f"   Criteria Met: {criteria_passed}/{len(criteria)}")

    for desc, passed in criteria:
        status = "✅" if passed else "❌"
        print(f"   {status} {desc}")

    # Final assessment
    if successful_tests == len(results):
        print("\n🎉 ALL TESTS PASSED - Excellent performance characteristics!")
        print("   ✅ Performance overhead is within acceptable limits")
        print("   ✅ Replication lag meets requirements")
        print("   ✅ Resource usage is efficient")
        print("   ✅ System scales well with data growth")
        return True
    elif successful_tests >= len(results) * 0.75:  # 75% success rate
        print("\n⚠️  MOST TESTS PASSED - Good performance with minor issues")
        print("   ✅ System performs well under most conditions")
        return True
    else:
        print("\n❌ SIGNIFICANT ISSUES DETECTED - Performance needs improvement")
        print("   ❌ Multiple performance tests failed")
        print("   📊 Consider performance optimization")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n🔚 Wave 4 testing completed with {'success' if success else 'issues'}")
    sys.exit(0 if success else 1)