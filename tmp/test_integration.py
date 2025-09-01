#!/usr/bin/env python3
"""
Integration test for all three phases of Weaviate local mode fixes.
Tests the complete flow from connection to multi-node support.
"""

from elysia.util.client import ClientManager
import logging

# Set up logging to see debug messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_phase1_local_without_api_key():
    """Phase 1: Test local connection works without API key"""
    print("\n=== Testing Phase 1: Local connection without API key ===")
    
    cm = ClientManager(
        logger=None,  # Reduce noise
        wcd_url="http://localhost:8080",
        weaviate_is_local=True,
        wcd_api_key=""  # Empty API key should work
    )
    
    assert cm.is_client == True, "Local connection should be valid without API key"
    print("✅ Phase 1 PASSED: Local connection works without API key")
    return True

def test_phase2_custom_ports():
    """Phase 2: Test custom port configuration"""
    print("\n=== Testing Phase 2: Custom port configuration ===")
    
    # Test with custom ports (logic test only, no actual connection)
    cm = ClientManager(
        logger=None,  # Reduce noise
        wcd_url="http://localhost:9090",
        weaviate_is_local=True,
        wcd_api_key="",
        local_weaviate_port=9090,
        local_weaviate_grpc_port=60051
    )
    
    host, port = cm._get_local_host_and_port()
    assert host == "localhost", f"Expected localhost, got {host}"
    assert port == 9090, f"Expected port 9090, got {port}"
    assert cm._calculated_grpc_port == 60051, f"Expected gRPC 60051, got {cm._calculated_grpc_port}"
    
    print("✅ Phase 2 PASSED: Custom ports are properly handled")
    return True

def test_phase3_multinode_grpc():
    """Phase 3: Test multi-node gRPC port detection"""
    print("\n=== Testing Phase 3: Multi-node gRPC port detection ===")
    
    # Test node 1 (default)
    cm1 = ClientManager(
        logger=None,
        wcd_url="http://localhost:8080",
        weaviate_is_local=True,
        wcd_api_key="",
        local_weaviate_port=8080,
        local_weaviate_grpc_port=50051
    )
    cm1._get_local_host_and_port()
    assert cm1._calculated_grpc_port == 50051, f"Node 1: Expected gRPC 50051, got {cm1._calculated_grpc_port}"
    print(f"✅ Node 1 (8080): gRPC port correctly calculated as {cm1._calculated_grpc_port}")
    
    # Test node 2
    cm2 = ClientManager(
        logger=None,
        wcd_url="http://localhost:8081",
        weaviate_is_local=True,
        wcd_api_key="",
        local_weaviate_port=8080,
        local_weaviate_grpc_port=50051
    )
    cm2._get_local_host_and_port()
    assert cm2._calculated_grpc_port == 50052, f"Node 2: Expected gRPC 50052, got {cm2._calculated_grpc_port}"
    print(f"✅ Node 2 (8081): gRPC port correctly calculated as {cm2._calculated_grpc_port}")
    
    # Test node 3
    cm3 = ClientManager(
        logger=None,
        wcd_url="http://localhost:8082",
        weaviate_is_local=True,
        wcd_api_key="",
        local_weaviate_port=8080,
        local_weaviate_grpc_port=50051
    )
    cm3._get_local_host_and_port()
    assert cm3._calculated_grpc_port == 50053, f"Node 3: Expected gRPC 50053, got {cm3._calculated_grpc_port}"
    print(f"✅ Node 3 (8082): gRPC port correctly calculated as {cm3._calculated_grpc_port}")
    
    print("✅ Phase 3 PASSED: Multi-node gRPC port detection works correctly")
    return True

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n=== Testing Edge Cases ===")
    
    # Test cloud connection still requires API key
    cm_cloud = ClientManager(
        logger=None,
        wcd_url="https://my-cluster.weaviate.cloud",
        weaviate_is_local=False,
        wcd_api_key=""
    )
    assert cm_cloud.is_client == False, "Cloud connection should require API key"
    print("✅ Cloud connections still require API key")
    
    # Test port overflow handling
    cm_overflow = ClientManager(
        logger=None,
        wcd_url="http://localhost:65530",
        weaviate_is_local=True,
        wcd_api_key="",
        local_weaviate_port=8080,
        local_weaviate_grpc_port=50051
    )
    cm_overflow._get_local_host_and_port()
    # Should fallback to default since 50051 + (65530-8080) > 65535
    assert cm_overflow._calculated_grpc_port == 50051, "Should fallback to default on overflow"
    print("✅ Port overflow handled gracefully")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("WEAVIATE LOCAL MODE INTEGRATION TEST")
    print("=" * 60)
    
    all_passed = True
    
    try:
        all_passed &= test_phase1_local_without_api_key()
        all_passed &= test_phase2_custom_ports()
        all_passed &= test_phase3_multinode_grpc()
        all_passed &= test_edge_cases()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("The Weaviate local mode implementation is complete and working.")
    else:
        print("❌ Some tests failed. Please review the output above.")
    print("=" * 60)