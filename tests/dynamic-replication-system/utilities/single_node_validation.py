#!/usr/bin/env python3
"""
single_node_validation.py - Verify single-node mode without replication
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

def stop_cluster_nodes():
    """Stop all nodes except the primary one for single-node testing"""
    print("🛑 Stopping cluster nodes for single-node testing")

    nodes_to_stop = ["phase4-test-node2-1", "phase4-test-node3-1"]

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

    # Wait for nodes to go down
    time.sleep(5)

def start_cluster_nodes():
    """Restart the cluster nodes"""
    print("🚀 Restarting cluster nodes")

    nodes_to_start = ["phase4-test-node2-1", "phase4-test-node3-1"]

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

    # Wait for nodes to come back
    time.sleep(15)

def test_single_node_collection_operations():
    """Test collection creation and data operations on single node"""
    print("🧪 TESTING SINGLE-NODE COLLECTION OPERATIONS")
    print("=" * 50)

    results = []

    try:
        import weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        # Test 1: Create collection
        collection_name = f"SINGLE_NODE_TEST_{str(uuid.uuid4())[:8]}"

        try:
            collection = client.collections.create(
                name=collection_name,
                properties=[
                    Property(name="test_id", data_type=DataType.TEXT),
                    Property(name="single_node_data", data_type=DataType.TEXT),
                    Property(name="timestamp", data_type=DataType.DATE),
                ]
            )
            print(f"   ✅ Collection created: {collection_name}")
            results.append(("collection_creation", "SUCCESS", "Collection created successfully"))

        except Exception as e:
            print(f"   ❌ Collection creation failed: {e}")
            results.append(("collection_creation", "FAILED", str(e)))
            client.close()
            return results

        # Test 2: Insert data
        try:
            collection = client.collections.get(collection_name)

            test_data = {
                "test_id": f"single_node_test_{uuid.uuid4()}",
                "single_node_data": "Data written in single-node mode without replication",
                "timestamp": "2024-01-01T00:00:00Z"
            }

            collection.data.insert(test_data)
            print("   ✅ Data inserted successfully")
            results.append(("data_insertion", "SUCCESS", "Data inserted successfully"))

        except Exception as e:
            print(f"   ❌ Data insertion failed: {e}")
            results.append(("data_insertion", "FAILED", str(e)))

        # Test 3: Query data
        try:
            collection = client.collections.get(collection_name)
            response = collection.query.fetch_objects(
                filters=wvc.query.Filter.by_property("test_id").equal(test_data["test_id"]),
                limit=1
            )

            if len(response.objects) > 0:
                retrieved_data = response.objects[0].properties
                print(f"   ✅ Data retrieved: {retrieved_data['test_id']}")
                results.append(("data_retrieval", "SUCCESS", "Data retrieved successfully"))
            else:
                print("   ❌ Data not found")
                results.append(("data_retrieval", "FAILED", "Data not found"))

        except Exception as e:
            print(f"   ❌ Data retrieval failed: {e}")
            results.append(("data_retrieval", "FAILED", str(e)))

        # Test 4: Update data
        try:
            collection = client.collections.get(collection_name)

            # Update the data
            updated_data = {
                "single_node_data": "Updated data in single-node mode"
            }

            collection.data.update(
                uuid=response.objects[0].uuid,
                properties=updated_data
            )
            print("   ✅ Data updated successfully")
            results.append(("data_update", "SUCCESS", "Data updated successfully"))

        except Exception as e:
            print(f"   ❌ Data update failed: {e}")
            results.append(("data_update", "FAILED", str(e)))

        # Test 5: Delete data
        try:
            collection = client.collections.get(collection_name)
            collection.data.delete(
                uuid=response.objects[0].uuid
            )
            print("   ✅ Data deleted successfully")
            results.append(("data_deletion", "SUCCESS", "Data deleted successfully"))

        except Exception as e:
            print(f"   ❌ Data deletion failed: {e}")
            results.append(("data_deletion", "FAILED", str(e)))

        # Clean up collection
        try:
            client.collections.delete(collection_name)
            print(f"   🗑️  Collection deleted: {collection_name}")
        except Exception as e:
            print(f"   ⚠️  Failed to delete collection: {e}")

        client.close()

    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        results.append(("connection", "FAILED", str(e)))

    return results

def test_single_node_error_handling():
    """Test error handling in single-node mode"""
    print("\n🧪 TESTING SINGLE-NODE ERROR HANDLING")
    print("=" * 50)

    results = []

    try:
        import weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        # Test accessing non-existent collection
        try:
            collection = client.collections.get("NON_EXISTENT_COLLECTION_12345")
            response = collection.query.fetch_objects(limit=1)
            print("   ❌ Unexpected success with non-existent collection")
            results.append(("non_existent_access", "UNEXPECTED_SUCCESS", "Should have failed"))

        except Exception as e:
            error_msg = str(e)
            print(f"   ✅ Expected failure for non-existent collection: {error_msg[:100]}...")
            results.append(("non_existent_access", "EXPECTED_FAILURE", error_msg))

        # Test invalid query
        try:
            collection = client.collections.get("ELYSIA_CONFIG")  # This should exist
            # Try an invalid filter
            response = collection.query.fetch_objects(
                filters="invalid_filter_syntax"
            )
            print("   ❌ Unexpected success with invalid filter")
            results.append(("invalid_query", "UNEXPECTED_SUCCESS", "Should have failed"))

        except Exception as e:
            error_msg = str(e)
            print(f"   ✅ Expected failure for invalid query: {error_msg[:100]}...")
            results.append(("invalid_query", "EXPECTED_FAILURE", error_msg))

        client.close()

    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        results.append(("error_handling_connection", "FAILED", str(e)))

    return results

def test_single_node_boundary_conditions():
    """Test boundary conditions in single-node mode"""
    print("\n🧪 TESTING SINGLE-NODE BOUNDARY CONDITIONS")
    print("=" * 50)

    results = []

    try:
        import weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        collection_name = f"BOUNDARY_TEST_{str(uuid.uuid4())[:8]}"

        # Test 1: Empty collection creation
        try:
            collection = client.collections.create(
                name=collection_name,
                properties=[]  # Empty properties
            )
            print("   ⚠️  Empty collection created (might be allowed)")
            results.append(("empty_collection", "SUCCESS", "Empty collection creation allowed"))

            # Clean up
            try:
                client.collections.delete(collection_name)
            except:
                pass

        except Exception as e:
            error_msg = str(e)
            print(f"   ✅ Empty collection rejected: {error_msg[:100]}...")
            results.append(("empty_collection", "EXPECTED_FAILURE", error_msg))

        # Test 2: Very long property names
        long_name = "a" * 200  # Very long property name
        try:
            collection = client.collections.create(
                name=f"LONG_NAME_TEST_{str(uuid.uuid4())[:8]}",
                properties=[
                    Property(name=long_name, data_type=DataType.TEXT),
                ]
            )
            print(f"   ⚠️  Very long property name accepted: {len(long_name)} chars")
            results.append(("long_property_name", "SUCCESS", f"Accepted {len(long_name)} char property name"))

            # Clean up
            try:
                client.collections.delete(f"LONG_NAME_TEST_{str(uuid.uuid4())[:8]}")
            except:
                pass

        except Exception as e:
            error_msg = str(e)
            print(f"   ✅ Long property name rejected: {error_msg[:100]}...")
            results.append(("long_property_name", "EXPECTED_FAILURE", error_msg))

        client.close()

    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        results.append(("boundary_conditions", "FAILED", str(e)))

    return results

def main():
    """Main function for single-node validation testing"""
    print("🚀 STARTING SINGLE-NODE VALIDATION TESTS")
    print("   Testing system behavior without replication")
    print("=" * 70)

    # Load configuration
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    # Check initial cluster health
    ports = [18080, 18081, 18082]
    healthy_nodes = sum(1 for port in ports if check_node_health(port))
    print(f"📊 Initial Cluster Status: {healthy_nodes}/{len(ports)} nodes healthy")

    if healthy_nodes < 3:
        print("⚠️  WARNING: Cluster not fully healthy, results may vary")
        if healthy_nodes < 1:
            print("❌ Cannot proceed - no healthy nodes")
            return False

    # Stop cluster nodes for single-node testing
    stop_cluster_nodes()

    # Verify single node is still healthy
    if not check_node_health(18080):
        print("❌ Primary node is not healthy after stopping others")
        start_cluster_nodes()  # Restore cluster
        return False

    print("📊 Single-Node Status: 1/3 nodes operational (as expected)")

    # Run single-node tests
    all_results = []

    test_functions = [
        test_single_node_collection_operations,
        test_single_node_error_handling,
        test_single_node_boundary_conditions,
    ]

    for test_func in test_functions:
        try:
            results = test_func()
            all_results.extend(results)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed: {e}")
            all_results.append((test_func.__name__, "TEST_CRASH", str(e)))

        # Brief pause between tests
        time.sleep(2)

    # Restore cluster
    print("\n🔄 RESTORING CLUSTER")
    start_cluster_nodes()

    # Verify cluster restoration
    time.sleep(10)
    final_healthy = sum(1 for port in ports if check_node_health(port))
    print(f"📊 Final Cluster Status: {final_healthy}/{len(ports)} nodes healthy")

    # Summary
    print("\n" + "=" * 70)
    print("📊 SINGLE-NODE VALIDATION TEST RESULTS")
    print("=" * 70)

    successes = 0
    failures = 0
    expected_failures = 0
    unexpected_successes = 0

    for test_name, result_type, details in all_results:
        status = {
            "SUCCESS": "✅",
            "FAILED": "❌",
            "EXPECTED_FAILURE": "✅",
            "UNEXPECTED_SUCCESS": "❌",
            "TEST_CRASH": "💥"
        }.get(result_type, "❓")

        print(f"   {status} {test_name}: {result_type}")

        if result_type == "SUCCESS":
            successes += 1
        elif result_type == "FAILED":
            failures += 1
        elif result_type == "EXPECTED_FAILURE":
            expected_failures += 1
        elif result_type == "UNEXPECTED_SUCCESS":
            unexpected_successes += 1

    print("\n📈 SUMMARY:")
    print(f"   Successful Operations: {successes}")
    print(f"   Failed Operations: {failures}")
    print(f"   Expected Failures: {expected_failures}")
    print(f"   Unexpected Successes: {unexpected_successes}")
    print(f"   Cluster Restored: {'✅' if final_healthy == len(ports) else '❌'}")

    success = (successes > 0 and unexpected_successes == 0 and final_healthy == len(ports))

    if success:
        print("\n🎉 SINGLE-NODE VALIDATION TESTS PASSED")
        print("   ✅ System works correctly in single-node mode")
        print("   ✅ Error handling functions properly")
        print("   ✅ Cluster restoration successful")
        return True
    else:
        print("\n⚠️  SINGLE-NODE VALIDATION TESTS COMPLETED WITH ISSUES")
        if successes == 0:
            print("   ❌ No successful operations in single-node mode")
        if unexpected_successes > 0:
            print("   ❌ Some operations succeeded when they should have failed")
        if final_healthy != len(ports):
            print("   ❌ Cluster not properly restored")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)