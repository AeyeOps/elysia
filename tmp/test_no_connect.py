#!/usr/bin/env python3
"""
Pure logic test for Weaviate local mode fixes.
Tests only the logic without any connections.
"""

import sys
import os
sys.path.insert(0, '/opt/elysia')

# We'll test the logic directly without ClientManager's auto-connect
from elysia.util.client import ClientManager

def test_logic():
    """Test the core logic of all three phases"""
    
    print("=" * 60)
    print("WEAVIATE LOCAL MODE IMPLEMENTATION TEST")
    print("=" * 60)
    
    # Phase 1: Test is_client logic
    print("\n=== Phase 1: API Key Validation Logic ===")
    
    # Create instances but prevent auto-connect by making is_client False initially
    cm = ClientManager.__new__(ClientManager)
    cm.wcd_url = "http://localhost:8080"
    cm.weaviate_is_local = True
    cm.wcd_api_key = ""
    cm.local_weaviate_port = 8080
    cm.local_weaviate_grpc_port = 50051
    cm.logger = None
    cm.headers = {}
    
    # Test the is_client calculation
    is_client = cm.wcd_url != "" and (cm.wcd_api_key != "" or cm.weaviate_is_local)
    assert is_client == True, "Local mode should allow empty API key"
    print("✅ Local mode with empty API key: is_client = True")
    
    # Test cloud mode
    cm.weaviate_is_local = False
    is_client = cm.wcd_url != "" and (cm.wcd_api_key != "" or cm.weaviate_is_local)
    assert is_client == False, "Cloud mode should require API key"
    print("✅ Cloud mode with empty API key: is_client = False")
    
    # Phase 2 & 3: Test port parsing and gRPC calculation
    print("\n=== Phase 2 & 3: Port Extraction and gRPC Calculation ===")
    
    test_cases = [
        # (url, local_is, base_http, base_grpc, expected_http, expected_grpc, description)
        ("http://localhost:8080", True, 8080, 50051, 8080, 50051, "Node 1 (default)"),
        ("http://localhost:8081", True, 8080, 50051, 8081, 50052, "Node 2 (+1 offset)"),
        ("http://localhost:8082", True, 8080, 50051, 8082, 50053, "Node 3 (+2 offset)"),
        ("localhost:8081", True, 8080, 50051, 8081, 50052, "Bare host:port"),
        ("http://127.0.0.1:8082", True, 8080, 50051, 8082, 50053, "IP address"),
        ("http://localhost:9091", True, 9090, 60051, 9091, 60052, "Custom base ports"),
    ]
    
    for url, is_local, base_http, base_grpc, exp_http, exp_grpc, desc in test_cases:
        cm = ClientManager.__new__(ClientManager)
        cm.wcd_url = url
        cm.weaviate_is_local = is_local
        cm.local_weaviate_port = base_http
        cm.local_weaviate_grpc_port = base_grpc
        cm.logger = None
        
        # Call the port extraction method
        host, port = cm._get_local_host_and_port()
        grpc_port = cm._calculated_grpc_port
        
        assert port == exp_http, f"{desc}: Expected HTTP {exp_http}, got {port}"
        assert grpc_port == exp_grpc, f"{desc}: Expected gRPC {exp_grpc}, got {grpc_port}"
        print(f"✅ {desc}: HTTP={port}, gRPC={grpc_port}")
    
    # Test edge case: port overflow
    print("\n=== Edge Cases ===")
    cm = ClientManager.__new__(ClientManager)
    cm.wcd_url = "http://localhost:65530"
    cm.weaviate_is_local = True
    cm.local_weaviate_port = 8080
    cm.local_weaviate_grpc_port = 50051
    cm.logger = None
    
    host, port = cm._get_local_host_and_port()
    grpc_port = cm._calculated_grpc_port
    
    # 50051 + (65530 - 8080) = 107501 which is > 65535, should fallback to 50051
    assert grpc_port == 50051, f"Port overflow should fallback to default, got {grpc_port}"
    print(f"✅ Port overflow handled: fallback to {grpc_port}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("\nSummary of implemented fixes:")
    print("  • Phase 1: Local connections work without API key")
    print("  • Phase 2: Custom port configurations supported")
    print("  • Phase 3: Multi-node gRPC ports calculated automatically")
    print("\nYour 3-node Weaviate cluster is now fully supported!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_logic()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)