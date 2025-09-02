#!/usr/bin/env python3
"""
verify_replication.py - Confirm data sync across all nodes
"""

import sys
import os
import uuid
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from elysia.util.client import ClientManager
from elysia.config import settings
import weaviate.classes as wvc
from dotenv import load_dotenv

def write_test_data(client, collection_name):
    """Write test data to a collection"""
    collection = client.collections.get(collection_name)

    test_id = str(uuid.uuid4())
    test_data = {
        "user_id": f"test_user_{test_id}",
        "config_data": f"test_config_data_{test_id}",
        "timestamp": "2024-01-01T00:00:00Z"
    }

    collection.data.insert(test_data)
    print(f"✅ Wrote test data to {collection_name}: {test_id}")
    return test_id

def verify_data_on_node(port, collection_name, test_id):
    """Verify test data exists on a specific node"""
    # Calculate the correct gRPC port for this node
    base_http_port = 18080
    base_grpc_port = 15051
    node_index = port - base_http_port
    grpc_port = base_grpc_port + node_index

    try:
        import weaviate

        client = weaviate.connect_to_local(
            host="localhost",
            port=port,
            grpc_port=grpc_port,
            headers={}
        )
        client.connect()

        collection = client.collections.get(collection_name)

        # Query for the test data
        response = collection.query.fetch_objects(
            filters=wvc.query.Filter.by_property("user_id").equal(f"test_user_{test_id}"),
            limit=1
        )

        found = len(response.objects) > 0
        client.close()

        if found:
            print(f"✅ Data verified on node {port}")
            return True
        else:
            print(f"❌ Data not found on node {port}")
            return False

    except Exception as e:
        print(f"❌ Error checking node {port}: {e}")
        return False

def main():
    """Main function to verify replication"""
    # Load the local .env file
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    # Get configuration values
    wcd_url = os.environ.get("WCD_URL", "")
    wcd_api_key = os.environ.get("WCD_API_KEY", "")
    weaviate_is_local = os.environ.get("WEAVIATE_IS_LOCAL", "False").lower() == "true"

    # Calculate replication factor from cluster ports
    ports_str = os.environ.get("WEAVIATE_CLUSTER_PORTS", "18080,18081,18082")
    cluster_nodes = [int(port.strip()) for port in ports_str.split(",")]
    replication_factor = len(cluster_nodes)

    try:
        nodes = cluster_nodes

        # Write data to first node
        print("=== Writing Test Data ===")
        import weaviate

        client = weaviate.connect_to_local(
            host="localhost",
            port=18080,
            grpc_port=15051,
            headers={}
        )
        client.connect()

        test_id = write_test_data(client, "ELYSIA_CONFIG")
        client.close()

        # Wait for replication
        print("\n=== Waiting for Replication ===")
        time.sleep(5)  # Wait 5 seconds for replication

        # Verify data on all nodes
        print("\n=== Verifying Data on All Nodes ===")
        success_count = 0

        for port in nodes:
            if verify_data_on_node(port, "ELYSIA_CONFIG", test_id):
                success_count += 1

        print(f"\nSummary: Data replicated to {success_count}/{len(nodes)} nodes")

        if success_count == len(nodes):
            print("🎉 Replication verified successfully!")
            return True
        else:
            print("⚠️  Replication verification failed")
            return False

    except Exception as e:
        print(f"❌ Error during replication verification: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)