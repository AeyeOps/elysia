#!/usr/bin/env python3
"""
create_system_collections.py - Initialize ELYSIA_* collections with replication_factor=3
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from elysia.util.client import ClientManager
from elysia.config import settings
import weaviate.classes as wvc
from weaviate.classes.config import Property, DataType
from dotenv import load_dotenv

def create_system_collection(client, name, properties=None):
    """Create a system collection with replication_factor=3"""
    try:
        # Delete if exists
        if client.collections.exists(name):
            client.collections.delete(name)
            print(f"Deleted existing collection: {name}")

        # Create new collection
        collection = client.collections.create(
            name=name,
            properties=properties or []
        )

        print(f"✅ Created collection: {name} with replication_factor=3")
        return True

    except Exception as e:
        print(f"❌ Failed to create collection {name}: {e}")
        return False

def main():
    """Main function to create system collections"""
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

            print("=== Creating System Collections ===")

            # Define system collections and their properties
            collections = {
                "ELYSIA_CONFIG": [
                    Property(name="user_id", data_type=DataType.TEXT),
                    Property(name="config_data", data_type=DataType.TEXT),
                    Property(name="timestamp", data_type=DataType.DATE),
                ],
                "ELYSIA_FEEDBACK": [
                    Property(name="user_id", data_type=DataType.TEXT),
                    Property(name="session_id", data_type=DataType.TEXT),
                    Property(name="feedback_type", data_type=DataType.TEXT),
                    Property(name="content", data_type=DataType.TEXT),
                    Property(name="timestamp", data_type=DataType.DATE),
                ],
                "ELYSIA_METADATA": [
                    Property(name="collection_name", data_type=DataType.TEXT),
                    Property(name="metadata_type", data_type=DataType.TEXT),
                    Property(name="data", data_type=DataType.TEXT),
                    Property(name="timestamp", data_type=DataType.DATE),
                ]
            }

            success_count = 0
            total_count = len(collections)

            for name, properties in collections.items():
                if create_system_collection(client, name, properties):
                    success_count += 1

            print(f"\nSummary: {success_count}/{total_count} collections created successfully")

            if success_count == total_count:
                print("🎉 All system collections created!")
                return True
            else:
                print("⚠️  Some collections failed to create")
                return False

    except Exception as e:
        print(f"❌ Error during collection creation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)