#!/usr/bin/env python3
"""
replication_lag_measurement.py - Time data sync across nodes
"""

import sys
import os
import uuid
import time
import threading
import concurrent.futures
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

def create_replication_test_collection(client, collection_name):
    """Create a collection for replication lag testing"""
    properties = [
        Property(name="test_id", data_type=DataType.TEXT),
        Property(name="write_timestamp", data_type=DataType.DATE),
        Property(name="node_written", data_type=DataType.TEXT),
        Property(name="sequence_number", data_type=DataType.INT),
    ]

    collection = client.collections.create(
        name=collection_name,
        properties=properties
    )

    return collection

def measure_replication_lag_single_write(collection_name, test_data, write_node_port):
    """Measure replication lag for a single write operation"""
    write_client = None
    read_clients = []

    try:
        # Connect to write node
        import weaviate
        import urllib.request

        base_grpc_port = 15051
        node_index = write_node_port - 18080
        grpc_port = base_grpc_port + node_index

        write_client = weaviate.connect_to_local(
            host="localhost",
            port=write_node_port,
            grpc_port=grpc_port,
            headers={}
        )
        write_client.connect()

        # Write the data and record write time
        collection = write_client.collections.get(collection_name)
        write_start_time = time.perf_counter()
        collection.data.insert(test_data)
        write_end_time = time.perf_counter()

        write_time = write_end_time - write_start_time
        write_timestamp = time.time()

        # Prepare read clients for other nodes
        ports = [18080, 18081, 18082]
        read_ports = [p for p in ports if p != write_node_port]

        for port in read_ports:
            node_index = port - 18080
            grpc_port = base_grpc_port + node_index

            try:
                client = weaviate.connect_to_local(
                    host="localhost",
                    port=port,
                    grpc_port=grpc_port,
                    headers={}
                )
                client.connect()
                read_clients.append((port, client))
            except Exception as e:
                print(f"   ⚠️  Failed to connect to read node {port}: {e}")

        # Measure replication lag to each node
        replication_lags = {}

        for read_port, read_client in read_clients:
            try:
                collection = read_client.collections.get(collection_name)

                # Poll for data appearance
                start_poll_time = time.time()
                max_poll_time = 30  # Maximum time to wait for replication

                while time.time() - start_poll_time < max_poll_time:
                    response = collection.query.fetch_objects(
                        filters=wvc.query.Filter.by_property("test_id").equal(test_data["test_id"]),
                        limit=1
                    )

                    if len(response.objects) > 0:
                        replication_time = time.time() - write_timestamp
                        replication_lags[read_port] = {
                            'lag_seconds': replication_time,
                            'found': True,
                            'poll_duration': time.time() - start_poll_time
                        }
                        break

                    time.sleep(0.1)  # Poll every 100ms

                if read_port not in replication_lags:
                    replication_lags[read_port] = {
                        'lag_seconds': None,
                        'found': False,
                        'poll_duration': max_poll_time
                    }

            except Exception as e:
                print(f"   ❌ Error checking replication on node {read_port}: {e}")
                replication_lags[read_port] = {
                    'lag_seconds': None,
                    'found': False,
                    'error': str(e)
                }

        # Clean up clients
        write_client.close()
        for _, client in read_clients:
            try:
                client.close()
            except:
                pass

        return {
            'write_node': write_node_port,
            'write_time_seconds': write_time,
            'write_timestamp': write_timestamp,
            'test_id': test_data['test_id'],
            'replication_lags': replication_lags
        }

    except Exception as e:
        print(f"   ❌ Replication lag measurement failed: {e}")

        # Clean up clients
        if write_client:
            try:
                write_client.close()
            except:
                pass
        for _, client in read_clients:
            try:
                client.close()
            except:
                pass

        return None

def run_replication_lag_test(num_tests=10):
    """Run replication lag tests across different nodes"""
    print("🧪 MEASURING REPLICATION LAG")
    print("=" * 50)

    # Check cluster health
    ports = [18080, 18081, 18082]
    healthy_nodes = sum(1 for port in ports if check_node_health(port))
    print(f"📊 Cluster Status: {healthy_nodes}/{len(ports)} nodes healthy")

    if healthy_nodes < 3:
        print("⚠️  WARNING: Need all nodes healthy for accurate replication lag measurement")
        if healthy_nodes < 2:
            print("❌ Cannot proceed - insufficient healthy nodes")
            return None

    # Create test collection on primary node
    collection_name = f"Replication_Lag_Test_{str(uuid.uuid4())[:8]}"

    try:
        import weaviate
        import urllib.request

        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        print(f"   📋 Creating test collection: {collection_name}")
        create_replication_test_collection(client, collection_name)
        client.close()

        time.sleep(2)  # Allow collection to propagate

    except Exception as e:
        print(f"   ❌ Failed to create test collection: {e}")
        return None

    # Run replication lag tests
    test_results = []
    write_nodes = [18080, 18081, 18082]  # Test writing to each node

    for test_num in range(num_tests):
        print(f"\n🔄 Test {test_num + 1}/{num_tests}")

        # Choose write node (rotate through available nodes)
        write_node = write_nodes[test_num % len(write_nodes)]
        print(f"   📝 Writing to node: {write_node}")

        # Generate test data
        test_data = {
            "test_id": f"replication_test_{test_num}_{str(uuid.uuid4())[:8]}",
            "write_timestamp": "2024-01-01T00:00:00Z",
            "node_written": str(write_node),
            "sequence_number": test_num
        }

        # Measure replication lag
        result = measure_replication_lag_single_write(collection_name, test_data, write_node)

        if result:
            test_results.append(result)

            # Show immediate results
            print(f"      - Write time: {result['write_time_seconds']:.3f}s")
            for node_port, lag_data in result['replication_lags'].items():
                if lag_data['found'] and lag_data['lag_seconds'] is not None:
                    print(f"      - Lag to node {node_port}: {lag_data['lag_seconds']:.3f}s")
                else:
                    print(f"      ❌ Node {node_port}: Data not found within timeout")
        else:
            print("   ❌ Test failed")

        # Brief pause between tests
        time.sleep(1)

    # Clean up test collection
    try:
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()
        client.collections.delete(collection_name)
        client.close()
        print("   🗑️ Test collection cleaned up")

    except Exception as e:
        print(f"   ⚠️ Failed to clean up test collection: {e}")

    return test_results

def analyze_replication_lag_results(test_results):
    """Analyze replication lag results and generate statistics"""
    if not test_results:
        return None

    print("\n" + "=" * 70)
    print("📊 REPLICATION LAG ANALYSIS")
    print("=" * 70)

    analysis = {
        'total_tests': len(test_results),
        'successful_tests': 0,
        'node_analysis': {},
        'overall_stats': {}
    }

    # Collect lag times by target node
    all_lags = []
    node_lags = {}

    for result in test_results:
        write_node = result['write_node']
        lags = result['replication_lags']

        success_count = 0
        for target_node, lag_data in lags.items():
            if lag_data['found'] and lag_data['lag_seconds'] is not None:
                lag_time = lag_data['lag_seconds']
                all_lags.append(lag_time)

                if target_node not in node_lags:
                    node_lags[target_node] = []
                node_lags[target_node].append(lag_time)

                success_count += 1

        if success_count == len(lags):  # All replications successful
            analysis['successful_tests'] += 1

    # Calculate overall statistics
    if all_lags:
        import statistics

        analysis['overall_stats'] = {
            'total_measurements': len(all_lags),
            'avg_lag': statistics.mean(all_lags),
            'min_lag': min(all_lags),
            'max_lag': max(all_lags),
            'p95_lag': statistics.quantiles(all_lags, n=20)[18] if len(all_lags) >= 20 else max(all_lags),
            'success_rate': len(all_lags) / (len(test_results) * 2)  # 2 target nodes per test
        }

        print(f"\n🎯 OVERALL REPLICATION LAG:")
        print(f"   Average lag: {analysis['overall_stats']['avg_lag']:.3f}s")
        print(f"   Min lag: {analysis['overall_stats']['min_lag']:.3f}s")
        print(f"   Max lag: {analysis['overall_stats']['max_lag']:.3f}s")
        print(f"   95th percentile: {analysis['overall_stats']['p95_lag']:.3f}s")
        print(f"   Success rate: {analysis['overall_stats']['success_rate']:.1f}")

        # Success criteria check
        success_criteria = {
            'avg_lag_under_1s': analysis['overall_stats']['avg_lag'] < 1.0,
            'p95_lag_under_2s': analysis['overall_stats']['p95_lag'] < 2.0,
            'high_success_rate': analysis['overall_stats']['success_rate'] > 0.9
        }

        print(f"\n🎯 SUCCESS CRITERIA EVALUATION:")
        print(f"   Average lag < 1 second: {'✅' if success_criteria['avg_lag_under_1s'] else '❌'}")
        print(f"   95th percentile < 2 seconds: {'✅' if success_criteria['p95_lag_under_2s'] else '❌'}")
        print(f"   Success rate > 90%: {'✅' if success_criteria['high_success_rate'] else '❌'}")

        criteria_met = sum(success_criteria.values())
        print(f"   Overall: {criteria_met}/3 criteria met")

    # Analyze by node
    print(f"\n📋 PER-NODE ANALYSIS:")
    for node_port, lags in node_lags.items():
        if lags:
            avg_lag = statistics.mean(lags)
            success_rate = len(lags) / analysis['total_tests']

            print(f"   Node {node_port}:")
            print(f"      Average lag: {avg_lag:.3f}s")
            print(f"      Success rate: {success_rate:.1f}")
            print(f"      Samples: {len(lags)}")

            analysis['node_analysis'][node_port] = {
                'avg_lag': avg_lag,
                'success_rate': success_rate,
                'samples': len(lags)
            }

    return analysis

def main():
    """Main function for replication lag measurement"""
    print("🚀 STARTING REPLICATION LAG MEASUREMENT")
    print("   Measuring data sync timing across nodes")
    print("=" * 60)

    # Load configuration
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    # Run replication lag tests
    test_results = run_replication_lag_test(num_tests=10)

    if test_results:
        # Analyze results
        analysis = analyze_replication_lag_results(test_results)

        if analysis:
            # Save results
            import json
            results_data = {
                'timestamp': time.time(),
                'test_results': test_results,
                'analysis': analysis
            }

            results_file = os.path.join(os.path.dirname(__file__), 'replication_lag_results.json')
            with open(results_file, 'w') as f:
                json.dump(results_data, f, indent=2, default=str)

            print(f"\n💾 Results saved to: replication_lag_results.json")
            # Determine success
            if 'overall_stats' in analysis and analysis['overall_stats']['avg_lag'] < 1.0:
                print("\n🎉 REPLICATION LAG MEASUREMENT COMPLETE")
                print("   ✅ Replication lag is within acceptable limits (< 1 second)")
                print("   📊 Data synchronizes quickly across the cluster")
                return True
            else:
                print("\n⚠️  REPLICATION LAG MEASUREMENT COMPLETE WITH ISSUES")
                if 'overall_stats' in analysis:
                    print(f"   Average lag: {analysis['overall_stats']['avg_lag']:.3f}s")
                print("   ❌ Replication lag exceeds recommended limits")
                return False

    else:
        print("\n❌ REPLICATION LAG MEASUREMENT FAILED")
        print("   ❌ Could not collect replication lag data")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)