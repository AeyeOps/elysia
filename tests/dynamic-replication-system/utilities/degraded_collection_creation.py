#!/usr/bin/env python3
"""
degraded_collection_creation.py - Test creating collections when cluster is degraded
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

def create_test_collection(client, collection_name):
    """Create a test collection with replication"""
    try:
        # Delete if exists
        if client.collections.exists(collection_name):
            client.collections.delete(collection_name)
            print(f"🗑️  Deleted existing collection: {collection_name}")

        # Create new collection
        properties = [
            Property(name="test_id", data_type=DataType.TEXT),
            Property(name="test_data", data_type=DataType.TEXT),
            Property(name="created_at", data_type=DataType.DATE),
            Property(name="degraded_test", data_type=DataType.BOOL),
        ]

        collection = client.collections.create(
            name=collection_name,
            properties=properties
        )

        print(f"✅ Created collection: {collection_name}")
        return True

    except Exception as e:
        print(f"❌ Failed to create collection {collection_name}: {e}")
        return False

def write_test_data(client, collection_name, test_id):
    """Write test data to verify collection functionality"""
    try:
        collection = client.collections.get(collection_name)

        test_data = {
            "test_id": f"degraded_test_{test_id}",
            "test_data": f"Data written during degraded state {test_id}",
            "created_at": "2024-01-01T00:00:00Z",
            "degraded_test": True
        }

        collection.data.insert(test_data)
        print(f"✅ Wrote test data to {collection_name}")
        return True

    except Exception as e:
        print(f"❌ Failed to write data to {collection_name}: {e}")
        return False

def verify_collection_replication(ports, collection_name, test_id):
    """Verify collection exists and data is replicated across available nodes"""
    success_count = 0
    total_healthy = 0

    for port in ports:
        if not check_node_health(port):
            print(f"⚠️  Node {port} is down, skipping")
            continue

        total_healthy += 1

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

            # Check if collection exists
            if not client.collections.exists(collection_name):
                print(f"❌ Collection {collection_name} not found on node {port}")
                client.close()
                continue

            # Try to read the test data
            collection = client.collections.get(collection_name)
            response = collection.query.fetch_objects(
                filters=wvc.query.Filter.by_property("test_id").equal(f"degraded_test_{test_id}"),
                limit=1
            )

            if len(response.objects) > 0:
                print(f"✅ Collection and data verified on node {port}")
                success_count += 1
            else:
                print(f"❌ Data not found in collection on node {port}")

            client.close()

        except Exception as e:
            print(f"❌ Error checking node {port}: {e}")

    return success_count, total_healthy

def main():
    """Main function for degraded collection creation testing"""
    # Load configuration
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    # Cluster configuration
    ports = [18080, 18081, 18082]
    container_names = ["phase4-test-node1-1", "phase4-test-node2-1", "phase4-test-node3-1"]
    container_map = dict(zip(ports, container_names))

    # Test scenarios with different numbers of nodes down
    scenarios = [
        ([18082], "Single node down (2/3 operational)"),
        ([18081, 18082], "Two nodes down (1/3 operational)")
    ]

    for failed_ports, scenario_desc in scenarios:
        print(f"\n{'='*70}")
        print(f"🧪 TESTING DEGRADED COLLECTION CREATION")
        print(f"   Scenario: {scenario_desc}")
        print(f"   Failing nodes: {failed_ports}")
        print(f"{'='*70}")

        # Step 1: Stop the target nodes
        print(f"\n🛑 Step 1: Stopping nodes {failed_ports}")
        stopped_containers = []

        for port in failed_ports:
            container_name = container_map[port]
            if stop_docker_container(container_name):
                stopped_containers.append(container_name)
            else:
                print(f"❌ Failed to stop {container_name}")

        if not stopped_containers:
            print("❌ No containers stopped, skipping test")
            continue

        # Wait for nodes to go down
        time.sleep(5)
        remaining_ports = [p for p in ports if p not in failed_ports]

        # Step 2: Verify cluster health
        print(f"\n🔍 Step 2: Checking remaining nodes")
        healthy_ports = []
        for port in remaining_ports:
            if check_node_health(port):
                healthy_ports.append(port)
                print(f"✅ Node {port} is healthy")
            else:
                print(f"❌ Node {port} is not responding")

        if not healthy_ports:
            print("❌ No healthy nodes remaining, cannot proceed with test")
            # Restart stopped containers before continuing
            for container in stopped_containers:
                start_docker_container(container)
            continue

        # Step 3: Create collection in degraded state
        print(f"\n📝 Step 3: Creating collection in degraded state")
        test_collection_name = f"DEGRADED_TEST_{str(uuid.uuid4())[:8]}"
        test_id = str(uuid.uuid4())

        collection_created = False
        data_written = False

        try:
            import weaviate
            # Connect to first healthy node
            primary_port = healthy_ports[0]
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

            # Create collection
            if create_test_collection(client, test_collection_name):
                collection_created = True

                # Write test data
                if write_test_data(client, test_collection_name, test_id):
                    data_written = True

            client.close()

        except Exception as e:
            print(f"❌ Error during collection operations: {e}")

        # Step 4: Verify collection across available nodes
        print(f"\n🔍 Step 4: Verifying collection replication on available nodes")
        success_count, total_healthy = verify_collection_replication(healthy_ports, test_collection_name, test_id)

        # Step 5: Restart stopped nodes
        print(f"\n🚀 Step 5: Restarting stopped nodes")
        restarted_count = 0
        for container in stopped_containers:
            if start_docker_container(container):
                restarted_count += 1

        # Step 6: Wait for nodes to recover
        print(f"\n⏳ Step 6: Waiting for nodes to recover")
        recovered_ports = []
        for port in failed_ports:
            if wait_for_node_health(port, timeout=60):
                recovered_ports.append(port)
                print(f"✅ Node {port} recovered")
            else:
                print(f"❌ Node {port} failed to recover")

        # Step 7: Verify collection after recovery
        if recovered_ports:
            print(f"\n🔍 Step 7: Verifying collection on recovered nodes")
            all_ports = healthy_ports + recovered_ports
            final_success, final_total = verify_collection_replication(all_ports, test_collection_name, test_id)

            if final_success == final_total:
                print(f"🎉 SUCCESS: Collection replicated to all {final_total} nodes after recovery")
            else:
                print(f"⚠️  PARTIAL: Collection only available on {final_success}/{final_total} nodes")
        else:
            print("⚠️  No nodes recovered, cannot verify final replication")

        # Test Results Summary
        print(f"\n📊 Test Results for {scenario_desc}:")
        print(f"   Collection Created: {'✅' if collection_created else '❌'}")
        print(f"   Data Written: {'✅' if data_written else '❌'}")
        print(f"   Available During Degradation: {success_count}/{total_healthy} nodes")
        print(f"   Nodes Restarted: {restarted_count}/{len(stopped_containers)}")

        # Brief pause before next scenario
        print("\n⏸️  Pausing before next scenario...")
        time.sleep(10)

    print(f"\n{'='*70}")
    print("🏁 DEGRADED COLLECTION CREATION TESTING COMPLETE")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()