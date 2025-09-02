#!/usr/bin/env python3
"""
test_replication_simple.py - Simple replication verification test
"""

import os
import sys
import uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from dotenv import load_dotenv
import weaviate

def test_replication():
    """Test basic replication functionality"""
    # Load environment
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    # Configuration
    nodes = [18080, 18081, 18082]
    test_id = str(uuid.uuid4())
    collection_name = "ELYSIA_CONFIG"

    print("=== Testing Replication ===")
    print(f"Test ID: {test_id}")

    # Step 1: Insert data on first node
    print("\n1. Inserting data on node 18080...")
    try:
        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        collection = client.collections.get(collection_name)
        test_data = {
            "user_id": f"replication_test_{test_id}",
            "config_data": f"test_data_{test_id}",
            "timestamp": "2024-01-01T00:00:00Z"
        }

        collection.data.insert(test_data)
        print(f"✅ Data inserted on node 18080: {test_data['user_id']}")

        client.close()

    except Exception as e:
        print(f"❌ Failed to insert data: {e}")
        return False

    # Step 2: Wait for replication
    print("\n2. Waiting for replication...")
    import time
    time.sleep(10)

    # Step 3: Check data on all nodes
    print("\n3. Checking data on all nodes...")
    success_count = 0

    for i, port in enumerate(nodes):
        grpc_port = 15051 + i
        print(f"   Checking node {port} (gRPC: {grpc_port})...")

        try:
            client = weaviate.connect_to_local(
                host="localhost",
                port=port,
                grpc_port=grpc_port,
                headers={}
            )
            client.connect()

            collection = client.collections.get(collection_name)

            # Simple query without filters first
            response = collection.query.fetch_objects(limit=10)

            # Look for our test data
            found = False
            for obj in response.objects:
                if obj.properties.get("user_id") == f"replication_test_{test_id}":
                    found = True
                    break

            client.close()

            if found:
                print(f"   ✅ Data found on node {port}")
                success_count += 1
            else:
                print(f"   ❌ Data NOT found on node {port}")

        except Exception as e:
            print(f"   ❌ Error checking node {port}: {e}")

    # Step 4: Summary
    print("\n=== Replication Test Summary ===")
    print(f"Data replicated to {success_count}/{len(nodes)} nodes")

    if success_count == len(nodes):
        print("🎉 REPLICATION TEST PASSED!")
        return True
    else:
        print("⚠️  REPLICATION TEST FAILED")
        return False

if __name__ == "__main__":
    success = test_replication()
    sys.exit(0 if success else 1)