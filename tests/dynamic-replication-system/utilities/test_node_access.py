#!/usr/bin/env python3
"""
test_node_access.py - Test if individual nodes are accessible
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from dotenv import load_dotenv
from elysia.util.client import ClientManager

def test_node_access(port):
    """Test access to a specific node"""
    print(f"\n=== Testing Node {port} ===")

    # Load environment
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

    # Calculate gRPC port
    base_http_port = 18080
    base_grpc_port = 15051
    node_index = port - base_http_port
    grpc_port = base_grpc_port + node_index

    print(f"HTTP Port: {port}")
    print(f"gRPC Port: {grpc_port}")

    try:
        with ClientManager(
            wcd_url=f"http://localhost:{port}",
            wcd_api_key=os.environ.get("WCD_API_KEY", ""),
            weaviate_is_local=True,
            local_weaviate_grpc_port=grpc_port
        ).connect_to_client() as client:
            # Simple test - get collections
            collections = client.collections.list_all()
            print(f"✅ Successfully connected to node {port}")
            print(f"   Collections: {list(collections.keys())}")
            return True

    except Exception as e:
        print(f"❌ Failed to connect to node {port}: {e}")
        return False

def main():
    """Test all nodes"""
    nodes = [18080, 18081, 18082]
    success_count = 0

    print("Testing individual node access...")

    for port in nodes:
        if test_node_access(port):
            success_count += 1

    print(f"\nSummary: {success_count}/{len(nodes)} nodes accessible")

if __name__ == "__main__":
    main()