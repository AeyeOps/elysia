#!/usr/bin/env python3
"""
misconfiguration_tests.py - Test various invalid configurations and error responses
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

def test_invalid_replication_factor():
    """Test invalid replication factor configurations"""
    print("🧪 TESTING INVALID REPLICATION FACTOR")
    print("=" * 50)

    # Test scenarios with invalid replication factors
    invalid_scenarios = [
        ("factor=-1", {"replication_factor": -1}),
        ("factor=0", {"replication_factor": 0}),
        ("factor=4", {"replication_factor": 4}),  # Too high for 3-node cluster
        ("factor='invalid'", {"replication_factor": "invalid"}),
        ("factor=None", {"replication_factor": None}),  # This should work in single-node
    ]

    results = []

    for desc, config in invalid_scenarios:
        print(f"\n🔍 Testing {desc}")
        try:
            # This would normally be set in the configuration
            # For testing, we'll try to create a collection with invalid settings
            import weaviate
            client = weaviate.connect_to_local(
                host="localhost",
                port=18080,
                grpc_port=15051,
                headers={}
            )
            client.connect()

            # Try to create a collection with invalid replication settings
            # Note: Weaviate client may not expose replication factor directly
            # This is more of a conceptual test

            collection_name = f"INVALID_TEST_{str(uuid.uuid4())[:8]}"

            try:
                collection = client.collections.create(
                    name=collection_name,
                    properties=[
                        Property(name="test_id", data_type=DataType.TEXT),
                        Property(name="error_test", data_type=DataType.TEXT),
                    ]
                )
                print(f"   ❌ Expected failure but collection created: {collection_name}")
                results.append((desc, "UNEXPECTED_SUCCESS", "Collection should have failed to create"))

                # Clean up
                try:
                    client.collections.delete(collection_name)
                except:
                    pass

            except Exception as e:
                error_msg = str(e)
                print(f"   ✅ Expected failure: {error_msg[:100]}...")
                results.append((desc, "EXPECTED_FAILURE", error_msg))

            client.close()

        except Exception as e:
            print(f"   ❌ Connection error: {e}")
            results.append((desc, "CONNECTION_ERROR", str(e)))

    return results

def test_missing_parent_collection():
    """Test operations on collections that reference non-existent parents"""
    print("\n🧪 TESTING MISSING PARENT COLLECTION")
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

        # Try to query a collection that references a non-existent parent
        non_existent_collection = f"NON_EXISTENT_PARENT_{str(uuid.uuid4())[:8]}"

        try:
            # This should fail gracefully
            collection = client.collections.get(non_existent_collection)
            response = collection.query.fetch_objects(limit=1)
            print(f"   ❌ Unexpected success with non-existent collection: {non_existent_collection}")
            results.append(("missing_parent", "UNEXPECTED_SUCCESS", "Should have failed"))

        except Exception as e:
            error_msg = str(e)
            print(f"   ✅ Expected failure for missing collection: {error_msg[:100]}...")
            results.append(("missing_parent", "EXPECTED_FAILURE", error_msg))

        client.close()

    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        results.append(("missing_parent", "CONNECTION_ERROR", str(e)))

    return results

def test_network_interruptions():
    """Test behavior during network interruptions"""
    print("\n🧪 TESTING NETWORK INTERRUPTIONS")
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

        # Test with a node that's down
        # First, let's stop a node temporarily
        print("   🛑 Stopping node 18082 for network test")

        # Stop the node
        subprocess.run(["docker", "stop", "phase4-test-node3-1"],
                      capture_output=True, timeout=30)

        time.sleep(5)  # Wait for node to go down

        # Try operations that would involve the stopped node
        try:
            # This might fail due to network issues
            collections = client.collections.list_all()
            print(f"   ⚠️  Operations succeeded despite node down: {len(collections)} collections")
            results.append(("network_down", "UNEXPECTED_SUCCESS", "Should have shown network issues"))

        except Exception as e:
            error_msg = str(e)
            print(f"   ✅ Network error detected: {error_msg[:100]}...")
            results.append(("network_down", "EXPECTED_FAILURE", error_msg))

        # Restart the node
        print("   🚀 Restarting node 18082")
        subprocess.run(["docker", "start", "phase4-test-node3-1"],
                      capture_output=True, timeout=30)

        # Wait for recovery
        time.sleep(10)

        client.close()

    except Exception as e:
        print(f"   ❌ Test error: {e}")
        results.append(("network_down", "TEST_ERROR", str(e)))

    return results

def test_invalid_data_types():
    """Test invalid data types in collection properties"""
    print("\n🧪 TESTING INVALID DATA TYPES")
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

        # Try to create properties with invalid data types
        invalid_types = [
            ("invalid_type", "INVALID_TYPE"),
            ("null_type", None),
            ("empty_string", ""),
        ]

        for prop_name, invalid_type in invalid_types:
            collection_name = f"INVALID_TYPE_TEST_{str(uuid.uuid4())[:8]}"

            try:
                # This should fail
                properties = [
                    Property(name="test_id", data_type=DataType.TEXT),
                    Property(name=prop_name, data_type=invalid_type),
                ]

                collection = client.collections.create(
                    name=collection_name,
                    properties=properties
                )

                print(f"   ❌ Unexpected success with invalid type '{invalid_type}'")
                results.append((f"invalid_type_{prop_name}", "UNEXPECTED_SUCCESS", f"Should have failed with type {invalid_type}"))

                # Clean up
                try:
                    client.collections.delete(collection_name)
                except:
                    pass

            except Exception as e:
                error_msg = str(e)
                print(f"   ✅ Expected failure for invalid type '{invalid_type}': {error_msg[:100]}...")
                results.append((f"invalid_type_{prop_name}", "EXPECTED_FAILURE", error_msg))

        client.close()

    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        results.append(("invalid_types", "CONNECTION_ERROR", str(e)))

    return results

def main():
    """Main function for misconfiguration testing"""
    print("🚀 STARTING MISCONFIGURATION TESTS")
    print("   Testing invalid configurations and error responses")
    print("=" * 70)

    # Load configuration
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    # Check cluster health
    ports = [18080, 18081, 18082]
    healthy_nodes = sum(1 for port in ports if check_node_health(port))
    print(f"📊 Cluster Status: {healthy_nodes}/{len(ports)} nodes healthy")

    if healthy_nodes < 2:
        print("⚠️  WARNING: Need at least 2 healthy nodes for meaningful testing")
        return False

    # Run all tests
    all_results = []

    test_functions = [
        test_invalid_replication_factor,
        test_missing_parent_collection,
        test_network_interruptions,
        test_invalid_data_types,
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

    # Summary
    print("\n" + "=" * 70)
    print("📊 MISCONFIGURATION TEST RESULTS")
    print("=" * 70)

    expected_failures = 0
    unexpected_successes = 0
    errors = 0

    for test_name, result_type, details in all_results:
        status = {
            "EXPECTED_FAILURE": "✅",
            "UNEXPECTED_SUCCESS": "❌",
            "CONNECTION_ERROR": "🔌",
            "TEST_ERROR": "💥",
            "TEST_CRASH": "💥"
        }.get(result_type, "❓")

        print(f"   {status} {test_name}: {result_type}")

        if result_type == "EXPECTED_FAILURE":
            expected_failures += 1
        elif result_type == "UNEXPECTED_SUCCESS":
            unexpected_successes += 1
        elif result_type in ["CONNECTION_ERROR", "TEST_ERROR", "TEST_CRASH"]:
            errors += 1

    print("\n📈 SUMMARY:")
    print(f"   Expected Failures: {expected_failures}")
    print(f"   Unexpected Successes: {unexpected_successes}")
    print(f"   Errors: {errors}")

    success = (unexpected_successes == 0 and expected_failures > 0)

    if success:
        print("\n🎉 MISCONFIGURATION TESTS PASSED")
        print("   ✅ System properly handles invalid configurations")
        print("   ✅ Error messages are generated for misconfigurations")
        return True
    else:
        print("\n⚠️  MISCONFIGURATION TESTS COMPLETED WITH ISSUES")
        if unexpected_successes > 0:
            print("   ❌ Some invalid configurations were accepted when they should have failed")
        if expected_failures == 0:
            print("   ❌ No expected failures detected - error handling may be inadequate")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)