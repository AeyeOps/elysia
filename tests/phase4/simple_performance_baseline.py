#!/usr/bin/env python3
"""
simple_performance_baseline.py - Simplified performance baseline test
"""

import sys
import os
import uuid
import time
import statistics
import subprocess
import urllib.request
import json
import weaviate
import weaviate.classes as wvc
from weaviate.classes.config import Property, DataType
from dotenv import load_dotenv

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

def create_test_collection(client, collection_name):
    """Create a test collection"""
    properties = [
        Property(name="test_id", data_type=DataType.TEXT),
        Property(name="timestamp", data_type=DataType.DATE),
        Property(name="data", data_type=DataType.TEXT),
    ]

    collection = client.collections.create(
        name=collection_name,
        properties=properties
    )
    return collection

def run_write_benchmark(client, collection_name, num_operations=100):
    """Run write benchmark"""
    print("📝 RUNNING WRITE BENCHMARK")
    print("=" * 30)

    write_times = []
    collection = client.collections.get(collection_name)

    for i in range(num_operations):
        test_data = {
            "test_id": f"baseline_test_{i}_{str(uuid.uuid4())[:8]}",
            "timestamp": "2024-01-01T00:00:00Z",
            "data": f"Performance baseline test data {i}"
        }

        start_time = time.perf_counter()
        collection.data.insert(test_data)
        end_time = time.perf_counter()
        write_times.append(end_time - start_time)

        if (i + 1) % 20 == 0:
            print(f"   Progress: {i + 1}/{num_operations} writes")

    if write_times:
        avg_time = statistics.mean(write_times)
        throughput = len(write_times) / sum(write_times)
        print(f"   ✅ Write benchmark complete")
        print(f"   📊 Average write time: {avg_time:.6f}s")
        print(f"   📊 Throughput: {throughput:.2f} ops/sec")
        return {
            'avg_time': avg_time,
            'throughput': throughput,
            'count': len(write_times)
        }
    return None

def run_read_benchmark(client, collection_name, num_operations=50):
    """Run read benchmark"""
    print("\n📖 RUNNING READ BENCHMARK")
    print("=" * 30)

    read_times = []
    collection = client.collections.get(collection_name)

    # Get some objects to read
    all_objects = collection.query.fetch_objects(limit=num_operations * 2)
    if len(all_objects.objects) == 0:
        print("   ❌ No objects found to read")
        return None

    objects_to_read = all_objects.objects[:num_operations]

    for i, obj in enumerate(objects_to_read):
        start_time = time.perf_counter()
        obj_uuid = obj.uuid
        result = collection.query.fetch_object_by_id(obj_uuid)
        end_time = time.perf_counter()
        read_times.append(end_time - start_time)

        if (i + 1) % 10 == 0:
            print(f"   Progress: {i + 1}/{len(objects_to_read)} reads")

    if read_times:
        avg_time = statistics.mean(read_times)
        throughput = len(read_times) / sum(read_times)
        print(f"   ✅ Read benchmark complete")
        print(f"   📊 Average read time: {avg_time:.6f}s")
        print(f"   📊 Throughput: {throughput:.2f} ops/sec")
        return {
            'avg_time': avg_time,
            'throughput': throughput,
            'count': len(read_times)
        }
    return None

def main():
    """Main function for simplified performance baseline testing"""
    print("🚀 STARTING SIMPLIFIED PERFORMANCE BASELINE")
    print("   Testing single-node performance")
    print("=" * 50)

    # Load configuration
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

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
    print("\n🔹 PHASE 2: RUNNING PERFORMANCE TESTS")
    results = {}

    try:
        # Connect to primary node
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        # Create test collection
        collection_name = f"Baseline_Test_{str(uuid.uuid4())[:8]}"
        print(f"   📋 Creating collection: {collection_name}")
        create_test_collection(client, collection_name)
        time.sleep(2)

        # Run write benchmark
        write_results = run_write_benchmark(client, collection_name, num_operations=100)
        if write_results:
            results['write'] = write_results

        # Run read benchmark
        read_results = run_read_benchmark(client, collection_name, num_operations=50)
        if read_results:
            results['read'] = read_results

        # Clean up
        try:
            client.collections.delete(collection_name)
            print("   🗑️ Test collection cleaned up")
        except Exception as e:
            print(f"   ⚠️ Cleanup failed: {e}")

        client.close()

    except Exception as e:
        print(f"❌ Performance testing failed: {e}")
        return False

    # Restore cluster
    print("\n🔹 PHASE 3: RESTORING CLUSTER")
    start_cluster_nodes()
    wait_for_cluster_stability()

    # Analyze results
    if results:
        print("\n" + "=" * 50)
        print("📊 PERFORMANCE BASELINE RESULTS")
        print("=" * 50)

        success = True

        if 'write' in results:
            write = results['write']
            print(f"📝 Write Performance:")
            print(f"   Average time: {write['avg_time']:.6f}s")
            print(f"   Throughput: {write['throughput']:.2f} ops/sec")

            # Check if performance is reasonable (should be < 0.1s per write)
            if write['avg_time'] > 0.1:
                print("   ⚠️  Write performance slower than expected")
                success = False
            else:
                print("   ✅ Write performance acceptable")

        if 'read' in results:
            read = results['read']
            print(f"\n📖 Read Performance:")
            print(f"   Average time: {read['avg_time']:.6f}s")
            print(f"   Throughput: {read['throughput']:.2f} ops/sec")

            # Check if performance is reasonable (should be < 0.05s per read)
            if read['avg_time'] > 0.05:
                print("   ⚠️  Read performance slower than expected")
                success = False
            else:
                print("   ✅ Read performance acceptable")

        # Save results
        results_data = {
            'timestamp': time.time(),
            'results': results,
            'success': success
        }

        results_file = os.path.join(os.path.dirname(__file__), 'baseline_results_simple.json')
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)

        print(f"\n💾 Results saved to: baseline_results_simple.json")

        if success:
            print("\n🎉 PERFORMANCE BASELINE TEST PASSED")
            print("   ✅ Single-node performance is within acceptable limits")
            return True
        else:
            print("\n⚠️  PERFORMANCE BASELINE TEST COMPLETED WITH ISSUES")
            print("   ❌ Performance metrics outside expected ranges")
            return False

    else:
        print("\n❌ NO RESULTS COLLECTED")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)