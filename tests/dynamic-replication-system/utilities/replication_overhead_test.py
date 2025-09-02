#!/usr/bin/env python3
"""
replication_overhead_test.py - Compare single vs multi-node performance
"""

import sys
import os
import uuid
import time
import statistics
import json
import subprocess
import urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from elysia.util.client import ClientManager
from elysia.config import settings
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
    print("🛑 Stopping cluster nodes for single-node comparison")
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
        if healthy_count == len(ports):
            print("   ✅ All nodes healthy and stable")
            return True
        time.sleep(5)

    healthy_count = sum(1 for port in ports if check_node_health(port))
    print(f"   ⚠️ Cluster stabilization incomplete: {healthy_count}/{len(ports)} nodes healthy")
    return healthy_count >= 2  # At least 2 nodes for meaningful testing

def create_test_collection(client, collection_name, num_properties=5):
    """Create a collection with specified number of properties"""
    properties = [
        Property(name="test_id", data_type=DataType.TEXT),
        Property(name="timestamp", data_type=DataType.DATE),
    ]

    # Add additional properties
    for i in range(num_properties - 2):
        properties.append(Property(name=f"property_{i}", data_type=DataType.TEXT))

    collection = client.collections.create(
        name=collection_name,
        properties=properties
    )

    return collection

def generate_test_data(num_properties=5):
    """Generate test data for operations"""
    data = {
        "test_id": str(uuid.uuid4()),
        "timestamp": "2024-01-01T00:00:00Z",
    }

    # Add additional properties
    for i in range(num_properties - 2):
        data[f"property_{i}"] = f"Test data for property {i}"

    return data

def run_write_benchmark(client, collection_name, num_operations=200):
    """Run write benchmark and return timing results"""
    write_times = []

    collection = client.collections.get(collection_name)

    for i in range(num_operations):
        test_data = generate_test_data()
        start_time = time.perf_counter()

        try:
            collection.data.insert(test_data)
            end_time = time.perf_counter()
            write_times.append(end_time - start_time)

        except Exception as e:
            print(f"   ❌ Write {i} failed: {e}")
            return None

        # Progress indicator
        if (i + 1) % 50 == 0:
            print(f"     Progress: {i + 1}/{num_operations} writes")

    return write_times

def run_read_benchmark(client, collection_name, num_operations=100):
    """Run read benchmark and return timing results"""
    read_times = []

    collection = client.collections.get(collection_name)

    # First, get objects to read
    all_objects = collection.query.fetch_objects(limit=num_operations * 2)
    if len(all_objects.objects) == 0:
        print("   ❌ No objects found to read")
        return None

    objects_to_read = all_objects.objects

    for i in range(min(num_operations, len(objects_to_read))):
        start_time = time.perf_counter()

        try:
            obj_uuid = objects_to_read[i].uuid
            obj = collection.query.fetch_object_by_id(obj_uuid)
            end_time = time.perf_counter()
            read_times.append(end_time - start_time)

        except Exception as e:
            print(f"   ❌ Read {i} failed: {e}")
            return None

        # Progress indicator
        if (i + 1) % 25 == 0:
            print(f"     Progress: {i + 1}/{num_operations} reads")

    return read_times

def run_query_benchmark(client, collection_name, num_operations=50):
    """Run query benchmark and return timing results"""
    query_times = []

    collection = client.collections.get(collection_name)

    for i in range(num_operations):
        start_time = time.perf_counter()

        try:
            response = collection.query.fetch_objects(limit=10)
            end_time = time.perf_counter()
            query_times.append(end_time - start_time)

        except Exception as e:
            print(f"   ❌ Query {i} failed: {e}")
            return None

        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"     Progress: {i + 1}/{num_operations} queries")

    return query_times

def perform_configuration_test(config_name, node_config, num_iterations=2):
    """Perform performance test for a specific configuration"""
    print(f"\n🧪 TESTING CONFIGURATION: {config_name}")
    print("=" * 60)

    results = {
        'config_name': config_name,
        'node_config': node_config,
        'iterations': []
    }

    # Configure cluster state
    if node_config == 'single-node':
        stop_cluster_nodes()
        if not check_node_health(18080):
            print("   ❌ Single-node setup failed")
            return None
    elif node_config == 'three-node':
        start_cluster_nodes()
        if not wait_for_cluster_stability():
            print("   ❌ Three-node cluster stabilization failed")
            return None

    # Verify configuration
    ports = [18080, 18081, 18082]
    healthy_nodes = sum(1 for port in ports if check_node_health(port))
    print(f"   📊 Node Status: {healthy_nodes}/{len(ports)} nodes healthy")

    if node_config == 'single-node' and healthy_nodes != 1:
        print("   ❌ Single-node configuration not achieved")
        return None
    elif node_config == 'three-node' and healthy_nodes < 2:
        print("   ❌ Multi-node configuration not achieved")
        return None

    # Run iterations
    for iteration in range(num_iterations):
        print(f"\n🔄 ITERATION {iteration + 1}/{num_iterations}")
        print("-" * 40)

        iteration_results = {
            'iteration': iteration + 1,
            'write_times': [],
            'read_times': [],
            'query_times': []
        }

        try:
            # Connect to primary node
            import weaviate
            import urllib.request

            client = weaviate.connect_to_local(
                host="localhost",
                port=18080,
                grpc_port=15051,
                headers={}
            )
            client.connect()

            # Create test collection
            collection_name = f"Overhead_Test_{config_name.replace(' ', '_')}_{iteration}_{str(uuid.uuid4())[:6]}"
            print(f"   📋 Creating collection: {collection_name}")
            create_test_collection(client, collection_name)
            time.sleep(2)  # Allow collection to stabilize

            # Run write benchmark
            print("   📝 Running write benchmark...")
            write_times = run_write_benchmark(client, collection_name, num_operations=200)
            if write_times:
                iteration_results['write_times'] = write_times

            # Run read benchmark
            print("   📖 Running read benchmark...")
            read_times = run_read_benchmark(client, collection_name, num_operations=100)
            if read_times:
                iteration_results['read_times'] = read_times

            # Run query benchmark
            print("   🔍 Running query benchmark...")
            query_times = run_query_benchmark(client, collection_name, num_operations=50)
            if query_times:
                iteration_results['query_times'] = query_times

            # Clean up
            try:
                client.collections.delete(collection_name)
                print("   🗑️ Test collection cleaned up")
            except Exception as e:
                print(f"   ⚠️ Cleanup failed: {e}")

            client.close()

        except Exception as e:
            print(f"   ❌ Iteration {iteration + 1} failed: {e}")
            continue

        results['iterations'].append(iteration_results)

    return results

def analyze_overhead(single_results, cluster_results):
    """Analyze performance overhead of replication"""
    print("\n" + "=" * 70)
    print("📊 REPLICATION OVERHEAD ANALYSIS")
    print("=" * 70)

    analysis = {
        'single_node': {},
        'three_node': {},
        'overhead': {}
    }

    # Analyze single-node results
    if single_results and single_results['iterations']:
        single_write_times = []
        single_read_times = []
        single_query_times = []

        for iteration in single_results['iterations']:
            single_write_times.extend(iteration['write_times'])
            single_read_times.extend(iteration['read_times'])
            single_query_times.extend(iteration['query_times'])

        if single_write_times:
            analysis['single_node']['write'] = {
                'avg_time': statistics.mean(single_write_times),
                'throughput': len(single_write_times) / sum(single_write_times),
                'count': len(single_write_times)
            }

        if single_read_times:
            analysis['single_node']['read'] = {
                'avg_time': statistics.mean(single_read_times),
                'throughput': len(single_read_times) / sum(single_read_times),
                'count': len(single_read_times)
            }

        if single_query_times:
            analysis['single_node']['query'] = {
                'avg_time': statistics.mean(single_query_times),
                'throughput': len(single_query_times) / sum(single_query_times),
                'count': len(single_query_times)
            }

    # Analyze cluster results
    if cluster_results and cluster_results['iterations']:
        cluster_write_times = []
        cluster_read_times = []
        cluster_query_times = []

        for iteration in cluster_results['iterations']:
            cluster_write_times.extend(iteration['write_times'])
            cluster_read_times.extend(iteration['read_times'])
            cluster_query_times.extend(iteration['query_times'])

        if cluster_write_times:
            analysis['three_node']['write'] = {
                'avg_time': statistics.mean(cluster_write_times),
                'throughput': len(cluster_write_times) / sum(cluster_write_times),
                'count': len(cluster_write_times)
            }

        if cluster_read_times:
            analysis['three_node']['read'] = {
                'avg_time': statistics.mean(cluster_read_times),
                'throughput': len(cluster_read_times) / sum(cluster_read_times),
                'count': len(cluster_read_times)
            }

        if cluster_query_times:
            analysis['three_node']['query'] = {
                'avg_time': statistics.mean(cluster_query_times),
                'throughput': len(cluster_query_times) / sum(cluster_query_times),
                'count': len(cluster_query_times)
            }

    # Calculate overhead
    for operation in ['write', 'read', 'query']:
        if (operation in analysis['single_node'] and
            operation in analysis['three_node']):

            single_avg = analysis['single_node'][operation]['avg_time']
            cluster_avg = analysis['three_node'][operation]['avg_time']

            overhead_percent = ((cluster_avg - single_avg) / single_avg) * 100
            overhead_ratio = cluster_avg / single_avg

            analysis['overhead'][operation] = {
                'overhead_percent': overhead_percent,
                'overhead_ratio': overhead_ratio,
                'single_avg': single_avg,
                'cluster_avg': cluster_avg,
                'acceptable': abs(overhead_percent) <= 20  # Success criteria: < 20% overhead
            }

    # Display results
    for operation in ['write', 'read', 'query']:
        if operation in analysis['overhead']:
            oh = analysis['overhead'][operation]
            status = "✅" if oh['acceptable'] else "❌"

            print(f"\n🔹 {operation.upper()} PERFORMANCE:")
            print(f"   Single-node avg: {oh['single_avg']:.6f}s")
            print(f"   Cluster avg: {oh['cluster_avg']:.6f}s")
            print(f"   Overhead: {oh['overhead_percent']:.2f}%")
            print(f"   Ratio: {oh['overhead_ratio']:.2f}x")
            print(f"   Status: {status} {'ACCEPTABLE' if oh['acceptable'] else 'TOO HIGH'}")

    return analysis

def main():
    """Main function for replication overhead testing"""
    print("🚀 STARTING REPLICATION OVERHEAD TESTS")
    print("   Comparing single vs multi-node performance")
    print("=" * 70)

    # Load configuration
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    # Check initial cluster health
    ports = [18080, 18081, 18082]
    healthy_nodes = sum(1 for port in ports if check_node_health(port))
    print(f"📊 Initial Cluster Status: {healthy_nodes}/{len(ports)} nodes healthy")

    if healthy_nodes < 3:
        print("⚠️  WARNING: Full cluster not healthy - results may be affected")
        if healthy_nodes < 1:
            print("❌ Cannot proceed - no healthy nodes")
            return False

    # Test single-node performance
    print("\n🔹 PHASE 1: SINGLE-NODE BASELINE")
    single_results = perform_configuration_test("Single Node Baseline", "single-node", num_iterations=2)

    # Test three-node cluster performance
    print("\n🔹 PHASE 2: THREE-NODE CLUSTER PERFORMANCE")
    cluster_results = perform_configuration_test("Three Node Cluster", "three-node", num_iterations=2)

    # Restore cluster to original state
    print("\n🔄 RESTORING CLUSTER TO ORIGINAL STATE")
    start_cluster_nodes()
    wait_for_cluster_stability()

    # Analyze overhead
    if single_results and cluster_results:
        analysis = analyze_overhead(single_results, cluster_results)

        # Save results
        results_data = {
            'timestamp': time.time(),
            'single_node_results': single_results,
            'cluster_results': cluster_results,
            'analysis': analysis
        }

        results_file = os.path.join(os.path.dirname(__file__), 'overhead_analysis.json')
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)

        print(f"\n💾 Analysis saved to: overhead_analysis.json")
        # Check success criteria
        success_criteria = {
            'write_overhead_acceptable': False,
            'read_performance_improved': False,
            'query_performance_acceptable': False
        }

        if 'write' in analysis['overhead']:
            oh = analysis['overhead']['write']
            success_criteria['write_overhead_acceptable'] = abs(oh['overhead_percent']) <= 20

        if 'read' in analysis['overhead']:
            oh = analysis['overhead']['read']
            success_criteria['read_performance_improved'] = oh['overhead_percent'] <= 0  # Neutral or improved

        if 'query' in analysis['overhead']:
            oh = analysis['overhead']['query']
            success_criteria['query_performance_acceptable'] = abs(oh['overhead_percent']) <= 50  # Allow more overhead for queries

        # Overall assessment
        criteria_met = sum(success_criteria.values())
        total_criteria = len(success_criteria)

        print(f"\n🎯 SUCCESS CRITERIA EVALUATION:")
        print(f"   Write overhead < 20%: {'✅' if success_criteria['write_overhead_acceptable'] else '❌'}")
        print(f"   Read performance improved/neutral: {'✅' if success_criteria['read_performance_improved'] else '❌'}")
        print(f"   Query performance acceptable: {'✅' if success_criteria['query_performance_acceptable'] else '❌'}")
        print(f"   Overall: {criteria_met}/{total_criteria} criteria met")

        if criteria_met >= total_criteria - 1:  # Allow 1 failure
            print("\n🎉 REPLICATION OVERHEAD ANALYSIS COMPLETE")
            print("   ✅ Performance overhead is within acceptable limits")
            return True
        else:
            print("\n⚠️  REPLICATION OVERHEAD ANALYSIS COMPLETE WITH ISSUES")
            print("   ❌ Performance overhead exceeds acceptable limits")
            return False

    else:
        print("\n❌ OVERHEAD ANALYSIS FAILED")
        print("   ❌ Could not collect both single-node and cluster performance data")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
