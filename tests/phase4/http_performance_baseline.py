#!/usr/bin/env python3
"""
http_performance_baseline.py - Performance baseline using HTTP API
"""

import sys
import os
import uuid
import time
import statistics
import subprocess
import urllib.request
import urllib.parse
import json
import threading

def check_node_health(port):
    """Check if a node is responding"""
    try:
        url = f"http://localhost:{port}/v1/meta"
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status == 200
    except:
        return False

def stop_cluster_nodes():
    """Stop cluster nodes for single-node testing"""
    print("🛑 Stopping cluster nodes for single-node baseline testing")
    nodes_to_stop = ["test-node2", "test-node3"]

    for container in nodes_to_stop:
        try:
            result = subprocess.run(["docker", "stop", container],
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"   ✅ Stopped {container}")
            else:
                print(f"   ❌ Failed to stop {container}")
        except Exception as e:
            print(f"   ❌ Error stopping {container}: {e}")

def start_cluster_nodes():
    """Restart the cluster nodes"""
    print("🚀 Restarting cluster nodes")
    nodes_to_start = ["test-node2", "test-node3"]

    for container in nodes_to_start:
        try:
            result = subprocess.run(["docker", "start", container],
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"   ✅ Started {container}")
            else:
                print(f"   ❌ Failed to start {container}")
        except Exception as e:
            print(f"   ❌ Error starting {container}: {e}")

def wait_for_cluster_stability(timeout=60):
    """Wait for cluster to become stable after node changes"""
    print(f"⏳ Waiting up to {timeout}s for cluster stabilization...")

    start_time = time.time()
    ports = [18080, 18081, 18082]

    while time.time() - start_time < timeout:
        healthy_count = sum(1 for port in ports if check_node_health(port))
        if healthy_count >= 1:  # At least 1 node for single-node testing
            print("   ✅ Primary node healthy")
            return True
        time.sleep(5)

    healthy_count = sum(1 for port in ports if check_node_health(port))
    print(f"   ⚠️ Cluster stabilization incomplete: {healthy_count}/3 nodes healthy")
    return healthy_count >= 1

def create_collection_http(collection_name, port=18080):
    """Create a collection using HTTP API"""
    url = f"http://localhost:{port}/v1/schema"

    schema = {
        "class": collection_name,
        "properties": [
            {
                "name": "test_id",
                "dataType": ["string"]
            },
            {
                "name": "timestamp",
                "dataType": ["date"]
            },
            {
                "name": "data",
                "dataType": ["string"]
            }
        ]
    }

    data = json.dumps(schema).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except Exception as e:
        print(f"   ❌ Failed to create collection: {e}")
        return False

def delete_collection_http(collection_name, port=18080):
    """Delete a collection using HTTP API"""
    url = f"http://localhost:{port}/v1/schema/{collection_name}"

    req = urllib.request.Request(url, method='DELETE')

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status in [200, 204]
    except Exception as e:
        print(f"   ⚠️ Failed to delete collection: {e}")
        return False

def insert_object_http(collection_name, obj_data, port=18080):
    """Insert an object using HTTP API"""
    url = f"http://localhost:{port}/v1/objects"

    data = json.dumps({
        "class": collection_name,
        **obj_data
    }).encode('utf-8')

    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')

    start_time = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            end_time = time.perf_counter()
            if response.status == 200:
                return end_time - start_time
            else:
                return None
    except Exception as e:
        return None

def query_objects_http(collection_name, limit=10, port=18080):
    """Query objects using HTTP API"""
    url = f"http://localhost:{port}/v1/graphql"

    query = f"""
    {{
        Get {{
            {collection_name}(limit: {limit}) {{
                test_id
                timestamp
                data
            }}
        }}
    }}
    """

    data = json.dumps({"query": query}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')

    start_time = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            end_time = time.perf_counter()
            if response.status == 200:
                return end_time - start_time
            else:
                return None
    except Exception as e:
        return None

def run_write_benchmark_http(collection_name, num_operations=100, port=18080):
    """Run write benchmark using HTTP API"""
    print("📝 RUNNING WRITE BENCHMARK (HTTP)")
    print("=" * 35)

    write_times = []

    for i in range(num_operations):
        test_data = {
            "test_id": f"http_baseline_test_{i}_{str(uuid.uuid4())[:8]}",
            "timestamp": "2024-01-01T00:00:00Z",
            "data": f"HTTP Performance baseline test data {i}"
        }

        write_time = insert_object_http(collection_name, test_data, port)
        if write_time is not None:
            write_times.append(write_time)
        else:
            print(f"   ❌ Write {i} failed")

        if (i + 1) % 20 == 0:
            print(f"   Progress: {i + 1}/{num_operations} writes")

    if write_times:
        avg_time = statistics.mean(write_times)
        throughput = len(write_times) / sum(write_times)
        print("   ✅ Write benchmark complete")
        print(f"   📊 Average write time: {avg_time:.6f}s")
        print(f"   📊 Throughput: {throughput:.2f} ops/sec")
        return {
            'avg_time': avg_time,
            'throughput': throughput,
            'count': len(write_times),
            'success_rate': len(write_times) / num_operations
        }
    return None

def run_read_benchmark_http(collection_name, num_operations=50, port=18080):
    """Run read benchmark using HTTP API"""
    print("\n📖 RUNNING READ BENCHMARK (HTTP)")
    print("=" * 35)

    read_times = []

    for i in range(num_operations):
        read_time = query_objects_http(collection_name, limit=10, port=port)
        if read_time is not None:
            read_times.append(read_time)
        else:
            print(f"   ❌ Read {i} failed")

        if (i + 1) % 10 == 0:
            print(f"   Progress: {i + 1}/{num_operations} reads")

    if read_times:
        avg_time = statistics.mean(read_times)
        throughput = len(read_times) / sum(read_times)
        print("   ✅ Read benchmark complete")
        print(f"   📊 Average read time: {avg_time:.6f}s")
        print(f"   📊 Throughput: {throughput:.2f} ops/sec")
        return {
            'avg_time': avg_time,
            'throughput': throughput,
            'count': len(read_times),
            'success_rate': len(read_times) / num_operations
        }
    return None

def main():
    """Main function for HTTP-based performance baseline testing"""
    print("🚀 STARTING HTTP-BASED PERFORMANCE BASELINE")
    print("   Testing single-node performance via HTTP API")
    print("=" * 55)

    # Check initial cluster health
    ports = [18080, 18081, 18082]
    healthy_nodes = sum(1 for port in ports if check_node_health(port))
    print(f"📊 Initial cluster status: {healthy_nodes}/3 nodes healthy")

    if healthy_nodes < 1:
        print("❌ No healthy nodes - cannot proceed")
        return False

    # Configure for single-node testing
    print("\n🔹 PHASE 1: CONFIGURING FOR SINGLE-NODE")
    stop_cluster_nodes()

    if not wait_for_cluster_stability():
        print("❌ Single-node configuration failed")
        return False

    # Run performance tests
    print("\n🔹 PHASE 2: RUNNING HTTP PERFORMANCE TESTS")
    results = {}

    # Create test collection
    collection_name = f"HTTP_Baseline_Test_{str(uuid.uuid4())[:8]}"
    print(f"   📋 Creating collection: {collection_name}")

    if not create_collection_http(collection_name):
        print("❌ Failed to create collection")
        return False

    time.sleep(2)  # Allow collection to stabilize

    # Run write benchmark
    write_results = run_write_benchmark_http(collection_name, num_operations=50)  # Reduced for HTTP testing
    if write_results:
        results['write'] = write_results

    # Run read benchmark
    read_results = run_read_benchmark_http(collection_name, num_operations=25)  # Reduced for HTTP testing
    if read_results:
        results['read'] = read_results

    # Clean up
    delete_collection_http(collection_name)
    print("   🗑️ Test collection cleaned up")

    # Restore cluster
    print("\n🔹 PHASE 3: RESTORING CLUSTER")
    start_cluster_nodes()
    wait_for_cluster_stability()

    # Analyze results
    if results:
        print("\n" + "=" * 55)
        print("📊 HTTP PERFORMANCE BASELINE RESULTS")
        print("=" * 55)

        success = True

        if 'write' in results:
            write = results['write']
            print("📝 Write Performance:")
            print(f"   Average time: {write['avg_time']:.6f}s")
            print(f"   Throughput: {write['throughput']:.2f} ops/sec")
            print(f"   Success rate: {write['success_rate']:.2f}")

            # Check if performance is reasonable (should be < 0.5s per write for HTTP)
            if write['avg_time'] > 0.5:
                print("   ⚠️  Write performance slower than expected")
                success = False
            else:
                print("   ✅ Write performance acceptable")

        if 'read' in results:
            read = results['read']
            print(f"\n📖 Read Performance:")
            print(f"   Average time: {read['avg_time']:.6f}s")
            print(f"   Throughput: {read['throughput']:.2f} ops/sec")
            print(f"   Success rate: {read['success_rate']:.2f}")

            # Check if performance is reasonable (should be < 0.2s per read for HTTP)
            if read['avg_time'] > 0.2:
                print("   ⚠️  Read performance slower than expected")
                success = False
            else:
                print("   ✅ Read performance acceptable")

        # Save results
        results_data = {
            'timestamp': time.time(),
            'test_type': 'http_baseline',
            'results': results,
            'success': success
        }

        results_file = os.path.join(os.path.dirname(__file__), 'http_baseline_results.json')
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)

        print(f"\n💾 Results saved to: http_baseline_results.json")

        if success:
            print("\n🎉 HTTP PERFORMANCE BASELINE TEST PASSED")
            print("   ✅ HTTP API performance is within acceptable limits")
            return True
        else:
            print("\n⚠️  HTTP PERFORMANCE BASELINE TEST COMPLETED WITH ISSUES")
            print("   ❌ Performance metrics outside expected ranges")
            return False

    else:
        print("\n❌ NO RESULTS COLLECTED")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)