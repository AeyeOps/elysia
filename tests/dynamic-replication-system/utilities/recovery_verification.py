#!/usr/bin/env python3
"""
recovery_verification.py - Comprehensive recovery validation after node failures
"""

import sys
import os
import uuid
import time
import subprocess
import urllib.request
import json
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
            if response.status == 200:
                data = json.loads(response.read().decode())
                return {
                    'healthy': True,
                    'hostname': data.get('hostname', 'unknown'),
                    'version': data.get('version', 'unknown')
                }
        return {'healthy': False, 'error': f'HTTP {response.status}'}
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

def stop_docker_container(container_name):
    """Stop a Docker container"""
    try:
        result = subprocess.run(["docker", "stop", container_name],
                              capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to stop container {container_name}: {e}")
        return False

def start_docker_container(container_name):
    """Start a Docker container"""
    try:
        result = subprocess.run(["docker", "start", container_name],
                              capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to start container {container_name}: {e}")
        return False

def wait_for_node_health(port, timeout=120):
    """Wait for a node to become healthy with detailed logging"""
    print(f"⏳ Waiting for node {port} to become healthy (timeout: {timeout}s)")
    start_time = time.time()
    last_status = None

    while time.time() - start_time < timeout:
        status = check_node_health(port)
        if status['healthy']:
            elapsed = time.time() - start_time
            print(f"   ✅ Node {port} recovered in {elapsed:.1f}s")
            return True

        # Log status changes
        current_status = f"Node {port}: {'Healthy' if status['healthy'] else 'Unhealthy'}"
        if current_status != last_status:
            print(f"   {current_status}")
            if not status['healthy'] and 'error' in status:
                print(f"   Error: {status['error']}")
            last_status = current_status

        time.sleep(2)

    print(f"❌ Node {port} failed to recover within {timeout}s timeout")
    return False

def create_recovery_test_collection(client, collection_name):
    """Create a test collection for recovery testing"""
    try:
        if client.collections.exists(collection_name):
            client.collections.delete(collection_name)

        properties = [
            Property(name="recovery_test_id", data_type=DataType.TEXT),
            Property(name="test_phase", data_type=DataType.TEXT),
            Property(name="node_id", data_type=DataType.TEXT),
            Property(name="timestamp", data_type=DataType.DATE),
            Property(name="recovery_data", data_type=DataType.TEXT),
        ]

        collection = client.collections.create(
            name=collection_name,
            properties=properties
        )

        print(f"✅ Created recovery test collection: {collection_name}")
        return True

    except Exception as e:
        print(f"❌ Failed to create collection {collection_name}: {e}")
        return False

def write_recovery_data(client, collection_name, test_id, phase, node_info):
    """Write recovery test data"""
    try:
        collection = client.collections.get(collection_name)

        test_data = {
            "recovery_test_id": f"{test_id}_{phase}",
            "test_phase": phase,
            "node_id": node_info.get('hostname', 'unknown'),
            "timestamp": "2024-01-01T00:00:00Z",
            "recovery_data": f"Data written during {phase} phase on {node_info.get('hostname', 'unknown')}"
        }

        collection.data.insert(test_data)
        print(f"✅ Wrote recovery data for phase: {phase}")
        return True

    except Exception as e:
        print(f"❌ Failed to write recovery data: {e}")
        return False

def verify_recovery_data(ports, collection_name, test_id, phases):
    """Verify recovery data is accessible across all nodes"""
    results = {}

    for port in ports:
        status = check_node_health(port)
        if not status['healthy']:
            results[port] = {'accessible': False, 'error': 'Node unhealthy'}
            continue

        try:
            # Calculate gRPC port
            base_http_port = 18080
            base_grpc_port = 15051
            node_index = port - base_http_port
            grpc_port = base_grpc_port + node_index

            import weaviate
            client = weaviate.connect_to_local(
                host="localhost",
                port=port,
                grpc_port=grpc_port,
                headers={}
            )
            client.connect()

            collection = client.collections.get(collection_name)
            node_results = {}

            for phase in phases:
                response = collection.query.fetch_objects(
                    filters=wvc.query.Filter.by_property("recovery_test_id").equal(f"{test_id}_{phase}"),
                    limit=1
                )
                node_results[phase] = len(response.objects) > 0

            results[port] = {
                'accessible': True,
                'phases_found': node_results,
                'all_phases': all(node_results.values())
            }

            client.close()

        except Exception as e:
            results[port] = {'accessible': False, 'error': str(e)}

    return results

def perform_recovery_test(ports, container_map, test_scenario):
    """Perform a comprehensive recovery test"""
    print(f"\n🧪 RECOVERY TEST: {test_scenario['name']}")
    print(f"   Description: {test_scenario['description']}")

    test_id = str(uuid.uuid4())
    collection_name = f"RECOVERY_TEST_{str(uuid.uuid4())[:8]}"
    phases = ["pre_failure", "during_outage", "post_recovery", "final_verification"]

    # Phase 1: Pre-failure setup
    print("\n📝 Phase 1: Pre-failure setup")
    try:
        import weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        # Create test collection
        if not create_recovery_test_collection(client, collection_name):
            print("❌ Failed to create test collection")
            return False

        # Write pre-failure data
        node_info = check_node_health(18080)
        write_recovery_data(client, collection_name, test_id, "pre_failure", node_info)

        client.close()

    except Exception as e:
        print(f"❌ Pre-failure setup failed: {e}")
        return False

    # Phase 2: Simulate failure
    print(f"\n🛑 Phase 2: Simulating failure - {test_scenario['failure_desc']}")
    failed_ports = test_scenario['failed_ports']
    stopped_containers = []

    for port in failed_ports:
        container_name = container_map[port]
        if stop_docker_container(container_name):
            stopped_containers.append(container_name)
            print(f"   ✅ Stopped {container_name}")
        else:
            print(f"   ❌ Failed to stop {container_name}")

    # Wait for nodes to go down
    time.sleep(5)
    remaining_ports = [p for p in ports if p not in failed_ports]

    # Phase 3: During outage operations
    print("\n📝 Phase 3: During outage operations")
    healthy_remaining = [p for p in remaining_ports if check_node_health(p)['healthy']]

    if healthy_remaining:
        try:
            import weaviate
            primary_port = healthy_remaining[0]
            base_grpc_port = 15051
            node_index = primary_port - 18080
            grpc_port = base_grpc_port + node_index

            client = weaviate.connect_to_local(
                host="localhost",
                port=primary_port,
                grpc_port=grpc_port,
                headers={}
            )
            client.connect()

            # Write data during outage
            node_info = check_node_health(primary_port)
            write_recovery_data(client, collection_name, test_id, "during_outage", node_info)

            client.close()

        except Exception as e:
            print(f"❌ During outage operations failed: {e}")
    else:
        print("⚠️  No healthy nodes remaining during outage")

    # Phase 4: Recovery
    print("\n🚀 Phase 4: Node recovery")
    restarted_count = 0
    recovered_count = 0

    for container in stopped_containers:
        print(f"   Starting {container}...")
        if start_docker_container(container):
            restarted_count += 1
            print(f"   ✅ {container} started")
        else:
            print(f"   ❌ Failed to start {container}")

    # Wait for recovery
    for port in failed_ports:
        if wait_for_node_health(port, timeout=120):
            recovered_count += 1

    print(f"   Recovery results: {recovered_count}/{len(failed_ports)} nodes recovered")

    # Phase 5: Post-recovery verification
    print("\n🔍 Phase 5: Post-recovery verification")
    # Write post-recovery data
    try:
        import weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        node_info = check_node_health(18080)
        write_recovery_data(client, collection_name, test_id, "post_recovery", node_info)

        client.close()

    except Exception as e:
        print(f"❌ Post-recovery data write failed: {e}")

    # Phase 6: Final verification across all nodes
    print("\n📊 Phase 6: Final verification across all nodes")
    time.sleep(10)  # Allow time for final replication

    verification_results = verify_recovery_data(ports, collection_name, test_id, phases)

    # Analyze results
    print("\n📋 VERIFICATION RESULTS:")
    all_nodes_accessible = True
    all_data_replicated = True

    for port in ports:
        result = verification_results[port]
        status = "✅ Accessible" if result['accessible'] else "❌ Inaccessible"
        print(f"   Node {port}: {status}")

        if not result['accessible']:
            all_nodes_accessible = False
        elif not result.get('all_phases', False):
            all_data_replicated = False
            found_phases = [p for p, found in result.get('phases_found', {}).items() if found]
            missing_phases = [p for p, found in result.get('phases_found', {}).items() if not found]
            print(f"      Found phases: {found_phases}")
            print(f"      Missing phases: {missing_phases}")

    # Test summary
    print("\n🏁 TEST SUMMARY:")
    print(f"   Scenario: {test_scenario['name']}")
    print(f"   Nodes Restarted: {restarted_count}/{len(stopped_containers)}")
    print(f"   Nodes Recovered: {recovered_count}/{len(failed_ports)}")
    print(f"   All Nodes Accessible: {'✅' if all_nodes_accessible else '❌'}")
    print(f"   All Data Replicated: {'✅' if all_data_replicated else '❌'}")

    success = (restarted_count == len(stopped_containers) and
               recovered_count == len(failed_ports) and
               all_nodes_accessible and
               all_data_replicated)

    if success:
        print("🎉 RECOVERY TEST PASSED")
    else:
        print("⚠️  RECOVERY TEST COMPLETED WITH ISSUES")

    return success

def main():
    """Main function for recovery verification testing"""
    # Load configuration
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    # Cluster configuration
    ports = [18080, 18081, 18082]
    container_names = ["phase4-test-node1-1", "phase4-test-node2-1", "phase4-test-node3-1"]
    container_map = dict(zip(ports, container_names))

    # Test scenarios
    test_scenarios = [
        {
            'name': 'Single Node Failure',
            'description': 'Test recovery when one node fails and rejoins',
            'failed_ports': [18082],
            'failure_desc': 'Stopping node 18082'
        },
        {
            'name': 'Dual Node Failure',
            'description': 'Test recovery when two nodes fail and rejoin',
            'failed_ports': [18081, 18082],
            'failure_desc': 'Stopping nodes 18081 and 18082'
        },
        {
            'name': 'Sequential Failures',
            'description': 'Test recovery with nodes failing and recovering sequentially',
            'failed_ports': [18080, 18081, 18082],
            'failure_desc': 'Stopping all nodes sequentially'
        }
    ]

    print("🚀 STARTING COMPREHENSIVE RECOVERY VERIFICATION")
    print(f"{'='*70}")

    # Pre-test cluster health check
    print("\n🏥 Pre-test cluster health check:")
    healthy_count = 0
    for port in ports:
        status = check_node_health(port)
        if status['healthy']:
            healthy_count += 1
            print(f"✅ Node {port}: {status['hostname']} (v{status['version']})")
        else:
            print(f"❌ Node {port}: Unhealthy")

    if healthy_count < len(ports):
        print(f"⚠️  WARNING: Only {healthy_count}/{len(ports)} nodes healthy at start")
    else:
        print("✅ All nodes healthy, proceeding with tests")

    # Execute test scenarios
    successful_tests = 0
    total_tests = len(test_scenarios)

    for scenario in test_scenarios:
        if perform_recovery_test(ports, container_map, scenario):
            successful_tests += 1

        # Pause between tests
        print("\n⏸️  Preparing for next test scenario...")
        time.sleep(15)

    # Final cluster status
    print(f"\n{'='*70}")
    print("🏁 FINAL CLUSTER STATUS")
    print(f"{'='*70}")

    final_healthy = 0
    for port in ports:
        status = check_node_health(port)
        if status['healthy']:
            final_healthy += 1
            print(f"✅ Node {port}: {status['hostname']} (v{status['version']})")
        else:
            print(f"❌ Node {port}: Unhealthy - {status.get('error', 'Unknown error')}")

    # Overall results
    print(f"\n{'='*70}")
    print("📊 COMPREHENSIVE RECOVERY TEST RESULTS")
    print(f"{'='*70}")
    print(f"Test Scenarios Passed: {successful_tests}/{total_tests}")
    print(f"Final Cluster Health: {final_healthy}/{len(ports)} nodes")
    print(f"Overall Status: {'🎉 ALL TESTS PASSED' if successful_tests == total_tests and final_healthy == len(ports) else '⚠️  ISSUES DETECTED'}")

    return successful_tests == total_tests and final_healthy == len(ports)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)