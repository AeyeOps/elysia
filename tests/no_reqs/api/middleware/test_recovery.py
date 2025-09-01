import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from elysia.api.middleware.recovery import recoverable_endpoint, extract_resource_name

@pytest.mark.asyncio
async def test_recoverable_endpoint_user_not_found():
    """Test that user not found returns 401."""
    @recoverable_endpoint
    async def test_func():
        raise ValueError("User 'abc123' not found in collection ELYSIA_CONFIG_xyz")
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func()
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Session not initialized"

@pytest.mark.asyncio
async def test_recoverable_endpoint_collection_not_found():
    """Test that collection not found returns 404."""
    @recoverable_endpoint
    async def test_func():
        raise ValueError("Collection 'MyCollection' not found")
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func()
    
    assert exc_info.value.status_code == 404
    assert "MyCollection" in exc_info.value.detail

@pytest.mark.asyncio
async def test_recoverable_endpoint_collection_not_found_without_quotes():
    """Test that collection not found without quotes still returns 404."""
    @recoverable_endpoint
    async def test_func():
        raise ValueError("Collection TestCollection not found")
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func()
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Collection not found"

@pytest.mark.asyncio
async def test_recoverable_endpoint_internal_collection_filtered():
    """Test that internal ELYSIA_ collection names are filtered out."""
    @recoverable_endpoint
    async def test_func():
        raise ValueError("Collection 'ELYSIA_CONFIG_metadata' not found")
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func()
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Collection not found"
    # Ensure the internal name is NOT in the error message
    assert "ELYSIA_CONFIG" not in exc_info.value.detail
    assert "metadata" not in exc_info.value.detail

@pytest.mark.asyncio
async def test_recoverable_endpoint_key_error():
    """Test that KeyError returns 422."""
    @recoverable_endpoint
    async def test_func():
        d = {}
        return d["missing_key"]
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func()
    
    assert exc_info.value.status_code == 422
    assert "Missing required field: missing_key" in exc_info.value.detail

@pytest.mark.asyncio
async def test_recoverable_endpoint_key_error_with_quotes():
    """Test that KeyError with quoted key returns 422 with clean key name."""
    @recoverable_endpoint
    async def test_func():
        raise KeyError('"quoted_key"')
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func()
    
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "Missing required field: quoted_key"

@pytest.mark.asyncio
async def test_recoverable_endpoint_connection_error_weaviate():
    """Test that Weaviate ConnectionError returns 503."""
    @recoverable_endpoint
    async def test_func():
        raise ConnectionError("Cannot connect to Weaviate cluster")
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func()
    
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Database temporarily unavailable"

@pytest.mark.asyncio
async def test_recoverable_endpoint_connection_error_generic():
    """Test that generic ConnectionError returns 503."""
    @recoverable_endpoint
    async def test_func():
        raise ConnectionError("Network connection failed")
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func()
    
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Service temporarily unavailable"

@pytest.mark.asyncio
async def test_recoverable_endpoint_generic_error():
    """Test that generic exceptions return 500."""
    @recoverable_endpoint
    async def test_func():
        raise RuntimeError("Something went wrong")
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func()
    
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Internal server error"

@pytest.mark.asyncio
async def test_recoverable_endpoint_logs_exception():
    """Test that exceptions are logged."""
    with patch('elysia.api.middleware.recovery.logger') as mock_logger:
        @recoverable_endpoint
        async def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(HTTPException):
            await test_func()
        
        mock_logger.exception.assert_called_once()
        call_args = mock_logger.exception.call_args[0][0]
        assert "ValueError" in call_args
        assert "test_func" in call_args

def test_extract_resource_name():
    """Test resource name extraction."""
    assert extract_resource_name("Collection 'TestCollection' not found") == "TestCollection"
    assert extract_resource_name('User "user123" not found') == "user123"
    assert extract_resource_name("No quotes here") == ""
    assert extract_resource_name("Collection \"MyData\" does not exist") == "MyData"

@pytest.mark.asyncio
async def test_recoverable_endpoint_preserves_success():
    """Test that successful functions work normally."""
    @recoverable_endpoint
    async def test_func():
        return {"status": "success"}
    
    result = await test_func()
    assert result == {"status": "success"}

@pytest.mark.asyncio
async def test_recoverable_endpoint_other_valueerror():
    """Test that other ValueErrors return 400."""
    @recoverable_endpoint
    async def test_func():
        raise ValueError("Invalid input data")
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func()
    
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid input data"

@pytest.mark.asyncio
async def test_recoverable_endpoint_preserves_function_metadata():
    """Test that decorator preserves function metadata."""
    @recoverable_endpoint
    async def test_func_with_docs():
        """This function has documentation."""
        return "success"
    
    assert test_func_with_docs.__name__ == "test_func_with_docs"
    assert test_func_with_docs.__doc__ == "This function has documentation."

@pytest.mark.asyncio
async def test_recoverable_endpoint_user_not_found_variations():
    """Test various user not found message patterns."""
    test_cases = [
        "User 'test123' not found",
        "user 'abc' not found in collection",
        "User not found: test456",
        "The user 'xyz' was not found"
    ]
    
    for message in test_cases:
        @recoverable_endpoint
        async def test_func():
            raise ValueError(message)
        
        with pytest.raises(HTTPException) as exc_info:
            await test_func()
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Session not initialized"

@pytest.mark.asyncio
async def test_recoverable_endpoint_collection_not_found_variations():
    """Test various collection not found message patterns."""
    test_cases = [
        "Collection 'TestData' not found",
        "collection 'MyCollection' not found in database",
        "Collection not found: TestCollection",
        "The collection 'DataSet' was not found"
    ]
    
    for message in test_cases:
        @recoverable_endpoint
        async def test_func():
            raise ValueError(message)
        
        with pytest.raises(HTTPException) as exc_info:
            await test_func()
        
        assert exc_info.value.status_code == 404
        # Test that we get appropriate message
        if "'" in message or '"' in message:
            assert "not found" in exc_info.value.detail
        else:
            assert exc_info.value.detail == "Collection not found"