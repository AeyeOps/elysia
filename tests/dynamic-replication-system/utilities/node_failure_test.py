#!/usr/bin/env python3
"""
node_failure_test.py - Test node failure scenarios and data accessibility
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
        print(f"🛑 Stopping container: {container_name}")
        result = subprocess.run(["docker", "stop", container_name],
                              capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to stop container {container_name}: {e}")
        return False

def start_docker_container(container_name):
    """Start a Docker container"""
    try:
        print(f"🚀 Starting container: {container_name}")
        result = subprocess.run(["docker", "start", container_name],
                              capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to start container {container_name}: {e}")
        return False

def wait_for_node_health(port, timeout=60):
    """Wait for a node to become healthy"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if check_node_health(port):
            return True
        time.sleep(2)
    return False

def write_test_data(client, collection_name, test_id):
    """Write test data to a collection"""
    collection = client.collections.get(collection_name)

    test_data = {
        "user_id": f"resilience_test_{test_id}",
        "test_data": f"failure_test_data_{test_id}",
        "timestamp": "2024-01-01T00:00:00Z",
        "test_type": "node_failure"
    }

    collection.data.insert(test_data)
    print(f"✅ Wrote test data: {test_id}")
    return test_id

def verify_data_access(ports, collection_name, test_id):
    """Verify data is accessible from available nodes"""
    accessible_count = 0
    total_ports = len(ports)

    for port in ports:
        if not check_node_health(port):
            print(f"⚠️  Node {port} is down, skipping")
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
            response = collection.query.fetch_objects(
                filters=wvc.query.Filter.by_property("user_id").equal(f"resilience_test_{test_id}"),
                limit=1
            )

            if len(response.objects) > 0:
                print(f"✅ Data accessible from node {port}")
                accessible_count += 1
            else:
                print(f"❌ Data not found on node {port}")

            client.close()

        except Exception as e:
            print(f"❌ Error accessing node {port}: {e}")

    return accessible_count, total_ports

def main():
    """Main function for node failure testing"""
    # Load configuration
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    # Cluster configuration
    ports = [18080, 18081, 18082]
    container_names = ["phase4-test-node1-1", "phase4-test-node2-1", "phase4-test-node3-1"]
    container_map = dict(zip(ports, container_names))

    # Test each node failure scenario
    for fail_port in ports:
        print(f"\n{'='*60}")
        print(f"🧪 TESTING NODE FAILURE: {fail_port}")
        print(f"{'='*60}")

        # Step 1: Write test data before failure
        print("\n📝 Step 1: Writing test data")
        test_id = str(uuid.uuid4())

        try:
            import weaviate
            client = weaviate.connect_to_local(
                host="localhost",
                port=18080,
                grpc_port=15051,
                headers={}
            )
            client.connect()

            write_test_data(client, "ELYSIA_CONFIG", test_id)
            client.close()

        except Exception as e:
            print(f"❌ Failed to write test data: {e}")
            continue

        # Step 2: Stop the target node
        print(f"\n🛑 Step 2: Stopping node {fail_port}")
        container_name = container_map[fail_port]

        if not stop_docker_container(container_name):
            print(f"❌ Failed to stop {container_name}, skipping test")
            continue

        # Wait for node to go down
        time.sleep(5)
        if check_node_health(fail_port):
            print(f"⚠️  Node {fail_port} still responding, continuing anyway")

        # Step 3: Verify data accessibility from remaining nodes
        print(f"\n🔍 Step 3: Verifying data access from remaining nodes")
        remaining_ports = [p for p in ports if p != fail_port]
        accessible_count, total_remaining = verify_data_access(remaining_ports, "ELYSIA_CONFIG", test_id)

        if accessible_count == total_remaining:
            print(f"✅ Data accessible from all {total_remaining} remaining nodes")
        else:
            print(f"⚠️  Data only accessible from {accessible_count}/{total_remaining} nodes")

        # Step 4: Restart the node
        print(f"\n🚀 Step 4: Restarting node {fail_port}")
        if start_docker_container(container_name):
            print(f"✅ Container {container_name} started successfully")
        else:
            print(f"❌ Failed to start {container_name}")

        # Step 5: Wait for node to come back online
        print(f"\n⏳ Step 5: Waiting for node {fail_port} to become healthy")
        if wait_for_node_health(fail_port, timeout=60):
            print(f"✅ Node {fail_port} is back online")

            # Step 6: Verify data is now accessible from all nodes
            print(f"\n🔍 Step 6: Verifying data access from all nodes after recovery")
            all_accessible, total_all = verify_data_access(ports, "ELYSIA_CONFIG", test_id)

            if all_accessible == total_all:
                print(f"🎉 SUCCESS: Data accessible from all {total_all} nodes after recovery")
            else:
                print(f"⚠️  PARTIAL: Data only accessible from {all_accessible}/{total_all} nodes after recovery")
        else:
            print(f"❌ Node {fail_port} failed to recover within timeout")

        # Brief pause before next test
        print("\n⏸️  Pausing before next test...")
        time.sleep(10)

    print(f"\n{'='*60}")
    print("🏁 NODE FAILURE TESTING COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()