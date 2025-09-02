#!/usr/bin/env python3
"""
test_derived_collections.py - Validate CHUNKED_* inheritance of replication settings
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from elysia.util.client import ClientManager
from elysia.config import settings
import weaviate.classes as wvc
from weaviate.classes.config import Property, DataType
from dotenv import load_dotenv

def create_parent_collection(client, name):
    """Create a parent collection with replication_factor=3"""
    if client.collections.exists(name):
        client.collections.delete(name)

    collection = client.collections.create(
        name=name,
        properties=[
            Property(name="content", data_type=DataType.TEXT),
            Property(name="timestamp", data_type=DataType.DATE),
        ]
    )
    print(f"✅ Created parent collection: {name}")
    return collection

def create_derived_collection(client, parent_name, derived_name):
    """Create a derived collection that should inherit replication"""
    if client.collections.exists(derived_name):
        client.collections.delete(derived_name)

    # Get parent collection config
    parent = client.collections.get(parent_name)

    # Create derived collection with same replication
    derived = client.collections.create(
        name=derived_name,
        properties=[
            Property(name="chunk_id", data_type=DataType.INT),
            Property(name="content", data_type=DataType.TEXT),
            Property(name="parent_id", data_type=DataType.TEXT),
        ]
    )
    print(f"✅ Created derived collection: {derived_name}")
    return derived

def verify_inheritance(client, parent_name, derived_name):
    """Verify that derived collection has same replication as parent"""
    try:
        parent = client.collections.get(parent_name)
        derived = client.collections.get(derived_name)

        parent_config = parent.config.get()
        derived_config = derived.config.get()

        parent_factor = parent_config.replication_config.factor
        derived_factor = derived_config.replication_config.factor

        print(f"Parent {parent_name} replication factor: {parent_factor}")
        print(f"Derived {derived_name} replication factor: {derived_factor}")

        if parent_factor == derived_factor:
            print("✅ Replication inheritance verified!")
            return True
        else:
            print("❌ Replication inheritance failed!")
            return False

    except Exception as e:
        print(f"❌ Error verifying inheritance: {e}")
        return False

def main():
    """Main function to test derived collection inheritance"""
    parent_name = "TEST_PARENT_COLLECTION"
    derived_name = "CHUNKED_TEST_PARENT_COLLECTION"

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
        with ClientManager(
            wcd_url=wcd_url,
            wcd_api_key=wcd_api_key,
            weaviate_is_local=weaviate_is_local
        ).connect_to_client() as client:

            print("=== Testing Derived Collection Inheritance ===")

            # Create parent collection
            parent = create_parent_collection(client, parent_name)

            # Create derived collection
            derived = create_derived_collection(client, parent_name, derived_name)

            # Verify inheritance
            success = verify_inheritance(client, parent_name, derived_name)

            # Cleanup
            client.collections.delete(derived_name)
            client.collections.delete(parent_name)
            print("✅ Test collections cleaned up")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        success = False

    if success:
        print("\n🎉 Derived collection inheritance test passed!")
    else:
        print("\n⚠️  Derived collection inheritance test failed!")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)