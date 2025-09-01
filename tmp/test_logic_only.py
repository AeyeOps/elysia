#!/usr/bin/env python3
"""
Logic-only test for Weaviate local mode fixes.
Tests the implementation logic without making actual connections.
"""

import sys
sys.path.insert(0, '/opt/elysia')

from elysia.util.client import ClientManager

def test_all_phases():
    """Test all three phases of the implementation"""
    
    print("=" * 60)
    print("WEAVIATE LOCAL MODE LOGIC TEST")
    print("=" * 60)
    
    # Phase 1: Test is_client logic for local without API key
    print("\n=== Phase 1: Local connection without API key ===")
    
    # Local with no API key should be valid
    cm1 = ClientManager(
        wcd_url="http://localhost:8080",
        weaviate_is_local=True,
        wcd_api_key=""
    )
    assert cm1.is_client == True, "Local should work without API key"
    print("✅ Local mode allows empty API key")
    
    # Cloud with no API key should be invalid
    cm2 = ClientManager(
        wcd_url="https://cluster.weaviate.cloud",
        weaviate_is_local=False,
        wcd_api_key=""
    )
    assert cm2.is_client == False, "Cloud should require API key"
    print("✅ Cloud mode requires API key")
    
    # Phase 2: Test port extraction
    print("\n=== Phase 2: Custom port configuration ===")
    
    cm3 = ClientManager(
        wcd_url="http://localhost:9090",
        weaviate_is_local=True,
        local_weaviate_port=9090,
        local_weaviate_grpc_port=60051
    )
    host, port = cm3._get_local_host_and_port()
    assert host == "localhost", f"Expected localhost, got {host}"
    assert port == 9090, f"Expected 9090, got {port}"
    print(f"✅ Custom HTTP port extracted: {port}")
    
    # Phase 3: Test gRPC port calculation
    print("\n=== Phase 3: Multi-node gRPC port detection ===")
    
    # Node 1 (default)
    cm4 = ClientManager(
        wcd_url="http://localhost:8080",
        weaviate_is_local=True,
        local_weaviate_port=8080,
        local_weaviate_grpc_port=50051
    )
    cm4._get_local_host_and_port()
    assert cm4._calculated_grpc_port == 50051, f"Expected 50051, got {cm4._calculated_grpc_port}"
    print(f"✅ Node 1 (8080): gRPC={cm4._calculated_grpc_port}")
    
    # Node 2 (offset +1)
    cm5 = ClientManager(
        wcd_url="http://localhost:8081",
        weaviate_is_local=True,
        local_weaviate_port=8080,
        local_weaviate_grpc_port=50051
    )
    cm5._get_local_host_and_port()
    assert cm5._calculated_grpc_port == 50052, f"Expected 50052, got {cm5._calculated_grpc_port}"
    print(f"✅ Node 2 (8081): gRPC={cm5._calculated_grpc_port}")
    
    # Node 3 (offset +2)
    cm6 = ClientManager(
        wcd_url="http://localhost:8082",
        weaviate_is_local=True,
        local_weaviate_port=8080,
        local_weaviate_grpc_port=50051
    )
    cm6._get_local_host_and_port()
    assert cm6._calculated_grpc_port == 50053, f"Expected 50053, got {cm6._calculated_grpc_port}"
    print(f"✅ Node 3 (8082): gRPC={cm6._calculated_grpc_port}")
    
    # Custom base with offset
    cm7 = ClientManager(
        wcd_url="http://localhost:9091",
        weaviate_is_local=True,
        local_weaviate_port=9090,
        local_weaviate_grpc_port=60051
    )
    cm7._get_local_host_and_port()
    assert cm7._calculated_grpc_port == 60052, f"Expected 60052, got {cm7._calculated_grpc_port}"
    print(f"✅ Custom base (9091): gRPC={cm7._calculated_grpc_port}")
    
    # Edge case: Port overflow
    print("\n=== Edge Cases ===")
    cm8 = ClientManager(
        wcd_url="http://localhost:65530",
        weaviate_is_local=True,
        local_weaviate_port=8080,
        local_weaviate_grpc_port=50051
    )
    cm8._get_local_host_and_port()
    # Should fallback since 50051 + (65530-8080) > 65535
    assert cm8._calculated_grpc_port == 50051, f"Should fallback on overflow"
    print(f"✅ Port overflow handled: fallback to {cm8._calculated_grpc_port}")
    
    # Test various URL formats
    print("\n=== URL Format Parsing ===")
    
    test_cases = [
        ("http://localhost:8081", "localhost", 8081),
        ("https://localhost:8081", "localhost", 8081),
        ("localhost:8081", "localhost", 8081),
        ("http://127.0.0.1:8081", "127.0.0.1", 8081),
    ]
    
    for url, expected_host, expected_port in test_cases:
        cm = ClientManager(
            wcd_url=url,
            weaviate_is_local=True,
            local_weaviate_port=8080,
            local_weaviate_grpc_port=50051
        )
        host, port = cm._get_local_host_and_port()
        assert host == expected_host, f"URL {url}: Expected host {expected_host}, got {host}"
        assert port == expected_port, f"URL {url}: Expected port {expected_port}, got {port}"
        print(f"✅ {url} → {host}:{port}")
    
    print("\n" + "=" * 60)
    print("✅ ALL LOGIC TESTS PASSED!")
    print("All three phases are working correctly:")
    print("  • Phase 1: Local connections work without API key")
    print("  • Phase 2: Custom ports are properly handled")
    print("  • Phase 3: Multi-node gRPC ports are calculated correctly")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_all_phases()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)