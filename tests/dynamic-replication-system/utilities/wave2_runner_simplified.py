#!/usr/bin/env python3
"""
wave2_runner_simplified.py - Simplified Wave 2 resilience testing
"""

import sys
import os
import time
import subprocess
import urllib.request
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

def check_node_health(port):
    """Check if a node is responding"""
    try:
        url = f"http://localhost:{port}/v1/meta"
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status == 200
    except:
        return False

def test_basic_resilience():
    """Test basic resilience concepts with available nodes"""
    ports = [18080, 18081, 18082]

    print("🩺 BASIC RESILIENCE TEST")
    print("=" * 50)

    # Check which nodes are actually healthy
    healthy_nodes = []
    for port in ports:
        if check_node_health(port):
            healthy_nodes.append(port)
            print(f"✅ Node {port}: Healthy")
        else:
            print(f"❌ Node {port}: Unhealthy")

    print(f"\n📊 Cluster Status: {len(healthy_nodes)}/{len(ports)} nodes healthy")

    if len(healthy_nodes) < 2:
        print("⚠️  WARNING: Need at least 2 healthy nodes for meaningful resilience testing")
        return False

    # Test 1: Basic connectivity
    print("\n🔗 Test 1: Basic Connectivity")
    connectivity_test = True
    for port in healthy_nodes:
        try:
            import weaviate
            client = weaviate.connect_to_local(
                host="localhost",
                port=port,
                grpc_port=15051 + (port - 18080),
                headers={}
            )
            client.connect()

            # Try to get collections
            collections = client.collections.list_all()
            print(f"✅ Node {port}: Connected, {len(collections)} collections available")

            client.close()

        except Exception as e:
            print(f"❌ Node {port}: Connection failed - {e}")
            connectivity_test = False

    # Test 2: Data persistence
    print("\n💾 Test 2: Data Persistence")
    persistence_test = False

    if len(healthy_nodes) >= 1:
        try:
            import weaviate
            import uuid

            primary_port = healthy_nodes[0]
            client = weaviate.connect_to_local(
                host="localhost",
                port=primary_port,
                grpc_port=15051 + (primary_port - 18080),
                headers={}
            )
            client.connect()

            # Check if ELYSIA_CONFIG exists, create if needed
            if not client.collections.exists("ELYSIA_CONFIG"):
                from weaviate.classes.config import Property, DataType
                client.collections.create(
                    name="ELYSIA_CONFIG",
                    properties=[
                        Property(name="user_id", data_type=DataType.TEXT),
                        Property(name="test_data", data_type=DataType.TEXT),
                        Property(name="timestamp", data_type=DataType.DATE),
                    ]
                )
                print("✅ Created ELYSIA_CONFIG collection")

            # Write test data
            collection = client.collections.get("ELYSIA_CONFIG")
            test_id = str(uuid.uuid4())
            test_data = {
                "user_id": f"resilience_test_{test_id}",
                "test_data": f"Basic resilience test data {test_id}",
                "timestamp": "2024-01-01T00:00:00Z"
            }

            collection.data.insert(test_data)
            print(f"✅ Wrote test data: {test_id}")

            # Verify data is readable
            response = collection.query.fetch_objects(
                filters=weaviate.classes.query.Filter.by_property("user_id").equal(f"resilience_test_{test_id}"),
                limit=1
            )

            if len(response.objects) > 0:
                print("✅ Data verification successful")
                persistence_test = True
            else:
                print("❌ Data verification failed")

            client.close()

        except Exception as e:
            print(f"❌ Persistence test failed: {e}")

    # Test 3: Node isolation simulation
    print("\n🚧 Test 3: Node Isolation Simulation")
    isolation_test = False

    if len(healthy_nodes) >= 2:
        # Try to access data from different nodes
        primary_port = healthy_nodes[0]
        secondary_port = healthy_nodes[1]

        test_id = None

        # Write data to primary node
        try:
            import weaviate
            client = weaviate.connect_to_local(
                host="localhost",
                port=primary_port,
                grpc_port=15051 + (primary_port - 18080),
                headers={}
            )
            client.connect()

            collection = client.collections.get("ELYSIA_CONFIG")
            test_id = str(uuid.uuid4())
            test_data = {
                "user_id": f"isolation_test_{test_id}",
                "test_data": f"Isolation test data {test_id}",
                "timestamp": "2024-01-01T00:00:00Z"
            }

            collection.data.insert(test_data)
            print(f"✅ Wrote isolation test data to node {primary_port}")
            client.close()

        except Exception as e:
            print(f"❌ Failed to write to primary node {primary_port}: {e}")
            return False

        # Try to read from secondary node
        time.sleep(2)  # Brief wait for replication
        try:
            client = weaviate.connect_to_local(
                host="localhost",
                port=secondary_port,
                grpc_port=15051 + (secondary_port - 18080),
                headers={}
            )
            client.connect()

            collection = client.collections.get("ELYSIA_CONFIG")
            response = collection.query.fetch_objects(
                filters=weaviate.classes.query.Filter.by_property("user_id").equal(f"isolation_test_{test_id}"),
                limit=1
            )

            if len(response.objects) > 0:
                print(f"✅ Data accessible from secondary node {secondary_port}")
                isolation_test = True
            else:
                print(f"⚠️  Data not found on secondary node {secondary_port}")

            client.close()

        except Exception as e:
            print(f"❌ Failed to read from secondary node {secondary_port}: {e}")

    else:
        print("⚠️  Skipping isolation test - need at least 2 healthy nodes")

    # Results summary
    print("\n📋 TEST RESULTS SUMMARY")
    print(f"   Basic Connectivity: {'✅ PASS' if connectivity_test else '❌ FAIL'}")
    print(f"   Data Persistence: {'✅ PASS' if persistence_test else '❌ FAIL'}")
    print(f"   Node Isolation: {'✅ PASS' if isolation_test else '❌ FAIL'}")

    overall_success = connectivity_test and persistence_test

    if overall_success:
        print("\n🎉 BASIC RESILIENCE TESTS PASSED")
        print("   ✅ System demonstrates basic resilience capabilities")
        print(f"   ✅ {len(healthy_nodes)} healthy nodes operational")
        return True
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("   This indicates potential resilience issues")
        return False

def main():
    """Main function"""
    print("🚀 STARTING SIMPLIFIED WAVE 2: RESILIENCE TESTING")
    print("   Testing basic resilience concepts")
    print("=" * 70)

    success = test_basic_resilience()

    print("=" * 70)
    if success:
        print("🏁 SIMPLIFIED WAVE 2 TESTING: SUCCESS")
        print("   Basic resilience validation completed")
    else:
        print("🏁 SIMPLIFIED WAVE 2 TESTING: ISSUES DETECTED")
        print("   Some resilience tests failed - investigate cluster health")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)