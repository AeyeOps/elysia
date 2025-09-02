#!/usr/bin/env python3
"""
Integration test to verify namespace protection actually works via HTTP API.
This test should be run with a live API server to verify HTTP 400 responses.
"""

import asyncio
import json
import aiohttp
from typing import List, Dict, Any

# Test cases for reserved prefixes
RESERVED_PREFIX_TEST_CASES = [
    "ELYSIA_test_collection",
    "elysia_test_collection", 
    "Elysia_Test_Collection",
    "ELYSIA_TEST_COLLECTION",
    "ElYsIa_test",
    "SYSTEM_test_collection",
    "system_test_collection",
    "System_Test_Collection",
    "SYSTEM_TEST_COLLECTION",
    "SyStEm_test"
]

# Valid collection names that should be accepted
VALID_TEST_CASES = [
    "MyCollection",
    "user_data", 
    "PRODUCTS",
    "elysia",  # Just "elysia" without underscore is OK
    "my_elysia_collection",  # ELYSIA in middle is OK
    "collection_ELYSIA",  # ELYSIA at end is OK
    "normal_collection_name"
]

async def test_preprocessing_endpoint(base_url: str = "http://localhost:8000"):
    """Test the /preprocess endpoint rejects reserved prefixes with HTTP 400."""
    
    async with aiohttp.ClientSession() as session:
        print(f"Testing namespace protection at {base_url}/preprocess")
        print("=" * 60)
        
        # Test reserved prefixes - should all return HTTP 400
        print("\n🛡️  Testing RESERVED prefixes (should return HTTP 400):")
        for collection_name in RESERVED_PREFIX_TEST_CASES:
            payload = {
                "user_id": "test_user",
                "collection_name": collection_name
            }
            
            try:
                async with session.post(
                    f"{base_url}/preprocess", 
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 400:
                        error_detail = await response.text()
                        print(f"  ✅ {collection_name:<25} → HTTP 400 (correctly rejected)")
                        if "reserved for system use" in error_detail:
                            print(f"     └─ Error message: {json.loads(error_detail).get('detail', 'N/A')}")
                        else:
                            print(f"     ⚠️  Unexpected error message: {error_detail}")
                    else:
                        print(f"  ❌ {collection_name:<25} → HTTP {response.status} (SHOULD BE 400!)")
                        response_text = await response.text()
                        print(f"     └─ Response: {response_text}")
                        
            except Exception as e:
                print(f"  🔥 {collection_name:<25} → Exception: {e}")
        
        # Test valid names - should not return HTTP 400 (though might fail for other reasons)
        print(f"\n✅ Testing VALID prefixes (should NOT return HTTP 400 for namespace reasons):")
        for collection_name in VALID_TEST_CASES:
            payload = {
                "user_id": "test_user", 
                "collection_name": collection_name
            }
            
            try:
                async with session.post(
                    f"{base_url}/preprocess",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 400:
                        error_detail = await response.text()
                        error_msg = json.loads(error_detail).get('detail', 'N/A')
                        if "reserved for system use" in error_msg:
                            print(f"  ❌ {collection_name:<25} → HTTP 400 (WRONGLY REJECTED!)")
                            print(f"     └─ Error: {error_msg}")
                        else:
                            print(f"  ⚠️  {collection_name:<25} → HTTP 400 (different reason: {error_msg})")
                    else:
                        print(f"  ✅ {collection_name:<25} → HTTP {response.status} (namespace validation passed)")
                        
            except Exception as e:
                print(f"  🔥 {collection_name:<25} → Exception: {e}")

async def test_validation_function_directly():
    """Test the validation function directly to ensure it works as expected."""
    from elysia.api.utils.validation import validate_collection_name
    from fastapi import HTTPException
    
    print(f"\n🧪 Testing validation function directly:")
    print("=" * 60)
    
    # Test reserved prefixes
    print("\n🛡️  Testing RESERVED prefixes (should raise HTTPException):")
    for collection_name in RESERVED_PREFIX_TEST_CASES:
        try:
            validate_collection_name(collection_name)
            print(f"  ❌ {collection_name:<25} → No exception raised (SHOULD HAVE FAILED!)")
        except HTTPException as e:
            if e.status_code == 400 and "reserved for system use" in e.detail:
                print(f"  ✅ {collection_name:<25} → HTTP 400 with correct message")
            else:
                print(f"  ⚠️  {collection_name:<25} → HTTP {e.status_code}, message: {e.detail}")
        except Exception as e:
            print(f"  🔥 {collection_name:<25} → Unexpected exception: {e}")
    
    # Test valid names
    print(f"\n✅ Testing VALID prefixes (should NOT raise HTTPException):")
    for collection_name in VALID_TEST_CASES:
        try:
            validate_collection_name(collection_name)
            print(f"  ✅ {collection_name:<25} → Validation passed")
        except HTTPException as e:
            print(f"  ❌ {collection_name:<25} → HTTP {e.status_code}: {e.detail} (SHOULD NOT FAIL!)")
        except Exception as e:
            print(f"  🔥 {collection_name:<25} → Unexpected exception: {e}")

async def main():
    """Run all namespace protection tests."""
    import sys
    
    print("🔒 NAMESPACE PROTECTION INTEGRATION TEST")
    print("=" * 60)
    print("This test verifies that ELYSIA_ and SYSTEM_ prefixes are properly")
    print("protected and return HTTP 400 when attempted via API endpoints.")
    print()
    
    # Test the validation function directly first
    await test_validation_function_directly()
    
    # Test via HTTP API if server is available
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print(f"\n🌐 Testing via HTTP API at {base_url}")
    print("Note: If the server is not running, this will show connection errors.")
    print()
    
    try:
        await test_preprocessing_endpoint(base_url)
    except Exception as e:
        print(f"❌ Could not test HTTP API: {e}")
        print("   Make sure the server is running with: elysia start")
    
    print("\n" + "=" * 60)
    print("✅ Namespace protection test completed!")

if __name__ == "__main__":
    asyncio.run(main())