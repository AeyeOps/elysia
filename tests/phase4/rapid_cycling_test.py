#!/usr/bin/env python3
"""
rapid_cycling_test.py - Automated node stop/start sequences with data validation
"""

import sys
import os
import uuid
import time
import subprocess
import urllib.request
import json
import random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from elysia.util.client import ClientManager
from elysia.config import settings
import weaviate.classes as wvc
from dotenv import load_dotenv

def check_node_health(port):
    """Check if a node is responding"""
    try:
        url = f"http://localhost:{port}/v1/meta"
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status == 200
    except:
        return False

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

def wait_for_node_health(port, timeout=30):
    """Wait for a node to become healthy"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if check_node_health(port):
            return True
        time.sleep(1)
    return False

def write_cycle_data(client, collection_name, cycle_num, test_id):
    """Write test data for a specific cycle"""
    collection = client.collections.get(collection_name)

    test_data = {
        "test_id": f"cycle_{cycle_num}_{test_id}",
        "cycle_number": cycle_num,
        "cycle_data": f"Data written during cycle {cycle_num}",
        "timestamp": "2024-01-01T00:00:00Z",
        "rapid_test": True
    }

    collection.data.insert(test_data)
    return f"cycle_{cycle_num}_{test_id}"

def verify_cycle_data(ports, collection_name, cycle_ids):
    """Verify data from all cycles is accessible"""
    total_checks = 0
    successful_checks = 0

    for port in ports:
        if not check_node_health(port):
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

            for cycle_id in cycle_ids:
                total_checks += 1
                response = collection.query.fetch_objects(
                    filters=wvc.query.Filter.by_property("test_id").equal(cycle_id),
                    limit=1
                )

                if len(response.objects) > 0:
                    successful_checks += 1

            client.close()

        except Exception as e:
            print(f"❌ Error checking node {port}: {e}")

    return successful_checks, total_checks

def perform_rapid_cycle(ports, container_map, cycle_num, test_id):
    """Perform one rapid cycling iteration"""
    print(f"\n🔄 Cycle {cycle_num}: Starting rapid node cycling")

    # Randomly select nodes to cycle (1-2 nodes)
    nodes_to_cycle = random.sample(ports, random.randint(1, 2))
    print(f"   Cycling nodes: {nodes_to_cycle}")

    # Write data before cycling
    cycle_data_id = None
    try:
        import weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        cycle_data_id = write_cycle_data(client, "ELYSIA_CONFIG", cycle_num, test_id)
        print(f"   📝 Wrote cycle data: {cycle_data_id}")

        client.close()

    except Exception as e:
        print(f"   ❌ Failed to write cycle data: {e}")
        return False

    # Stop selected nodes
    stopped_containers = []
    for port in nodes_to_cycle:
        container_name = container_map[port]
        print(f"   🛑 Stopping {container_name}")
        if stop_docker_container(container_name):
            stopped_containers.append(container_name)
        else:
            print(f"   ❌ Failed to stop {container_name}")

    # Brief wait for nodes to go down
    time.sleep(3)

    # Verify data accessibility during outage
    remaining_ports = [p for p in ports if p not in nodes_to_cycle]
    healthy_remaining = [p for p in remaining_ports if check_node_health(p)]

    if healthy_remaining:
        # Write additional data during outage
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

            outage_data_id = write_cycle_data(client, "ELYSIA_CONFIG", f"{cycle_num}_outage", test_id)
            print(f"   📝 Wrote outage data: {outage_data_id}")

            client.close()

        except Exception as e:
            print(f"   ❌ Failed to write outage data: {e}")

    # Restart nodes immediately
    restarted_count = 0
    for container in stopped_containers:
        print(f"   🚀 Restarting {container}")
        if start_docker_container(container):
            restarted_count += 1
        else:
            print(f"   ❌ Failed to restart {container}")

    # Wait for nodes to recover
    recovered_count = 0
    for port in nodes_to_cycle:
        if wait_for_node_health(port, timeout=30):
            recovered_count += 1
            print(f"   ✅ Node {port} recovered")
        else:
            print(f"   ❌ Node {port} failed to recover")

    print(f"   📊 Cycle {cycle_num} results: {restarted_count}/{len(stopped_containers)} restarted, {recovered_count}/{len(nodes_to_cycle)} recovered")

    return recovered_count == len(nodes_to_cycle)

def main():
    """Main function for rapid cycling testing"""
    # Load configuration
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    # Cluster configuration
    ports = [18080, 18081, 18082]
    container_names = ["phase4-test-node1-1", "phase4-test-node2-1", "phase4-test-node3-1"]
    container_map = dict(zip(ports, container_names))

    # Test configuration
    num_cycles = 10  # Number of rapid cycles to perform
    cycle_delay = 5  # Seconds between cycles

    test_id = str(uuid.uuid4())
    cycle_ids = []

    print(f"🚀 STARTING RAPID CYCLING TEST")
    print(f"   Test ID: {test_id}")
    print(f"   Cycles: {num_cycles}")
    print(f"   Delay between cycles: {cycle_delay}s")
    print(f"{'='*60}")

    # Pre-cycle: Ensure all nodes are healthy
    print("\n🏥 Pre-test: Checking cluster health")
    healthy_count = sum(1 for port in ports if check_node_health(port))
    if healthy_count < len(ports):
        print(f"⚠️  Only {healthy_count}/{len(ports)} nodes healthy. Starting anyway...")
    else:
        print("✅ All nodes healthy, starting test")

    # Perform rapid cycling
    successful_cycles = 0

    for cycle in range(1, num_cycles + 1):
        if perform_rapid_cycle(ports, container_map, cycle, test_id):
            successful_cycles += 1

        # Brief pause between cycles
        if cycle < num_cycles:
            print(f"⏳ Waiting {cycle_delay}s before next cycle...")
            time.sleep(cycle_delay)

    # Post-test: Verify all data is accessible
    print(f"\n🔍 Post-test: Verifying data integrity")
    print(f"   Successful cycles: {successful_cycles}/{num_cycles}")

    # Final health check
    final_healthy = sum(1 for port in ports if check_node_health(port))
    print(f"   Final cluster health: {final_healthy}/{len(ports)} nodes healthy")

    # Verify data accessibility across all nodes
    print(f"\n📊 Final Data Verification:")

    # Check data written before each cycle
    successful_verifications = 0
    total_verifications = 0

    for cycle in range(1, num_cycles + 1):
        cycle_ids.extend([
            f"cycle_{cycle}_{test_id}",
            f"cycle_{cycle}_outage_{test_id}"
        ])

    # Remove duplicates and filter valid IDs
    cycle_ids = list(set(cycle_ids))

    if cycle_ids:
        successful_checks, total_checks = verify_cycle_data(ports, "ELYSIA_CONFIG", cycle_ids)
        print(f"   Data accessibility: {successful_checks}/{total_checks} checks passed")

        if successful_checks == total_checks:
            print("✅ All cycle data verified across cluster")
        else:
            print("⚠️  Some cycle data not accessible on all nodes")
    else:
        print("⚠️  No cycle data IDs to verify")

    # Test Results Summary
    print(f"\n{'='*60}")
    print("🏁 RAPID CYCLING TEST RESULTS")
    print(f"{'='*60}")
    print(f"Test ID: {test_id}")
    print(f"Cycles Completed: {successful_cycles}/{num_cycles}")
    print(f"Final Cluster Health: {final_healthy}/{len(ports)} nodes")
    print(f"Data Verification: {'✅ PASS' if successful_checks == total_checks else '⚠️  PARTIAL'}")

    if successful_cycles == num_cycles and final_healthy == len(ports):
        print("🎉 RAPID CYCLING TEST PASSED")
        return True
    else:
        print("⚠️  RAPID CYCLING TEST COMPLETED WITH ISSUES")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)