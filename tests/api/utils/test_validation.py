import pytest
from fastapi import HTTPException
from elysia.api.utils.validation import validate_collection_name

def test_validate_collection_name_rejects_elysia_prefix():
    """Test that ELYSIA_ prefix is rejected."""
    with pytest.raises(HTTPException) as exc:
        validate_collection_name("ELYSIA_test")
    assert exc.value.status_code == 400
    assert "reserved for system use" in exc.value.detail

def test_validate_collection_name_case_insensitive():
    """Test that validation is case-insensitive."""
    test_cases = ["elysia_test", "Elysia_Test", "ELYSIA_TEST", "ElYsIa_test"]
    for name in test_cases:
        with pytest.raises(HTTPException) as exc:
            validate_collection_name(name)
        assert exc.value.status_code == 400

def test_validate_collection_name_rejects_system_prefix():
    """Test that SYSTEM_ prefix is rejected."""
    with pytest.raises(HTTPException) as exc:
        validate_collection_name("SYSTEM_test")
    assert exc.value.status_code == 400
    assert "reserved for system use" in exc.value.detail

def test_validate_collection_name_accepts_valid_names():
    """Test that valid names are accepted."""
    valid_names = [
        "MyCollection",
        "user_data",
        "PRODUCTS",
        "elysia",  # Just "elysia" without underscore is OK
        "my_elysia_collection",  # ELYSIA in middle is OK
        "collection_ELYSIA"  # ELYSIA at end is OK
    ]
    for name in valid_names:
        validate_collection_name(name)  # Should not raise

def test_validate_collection_name_empty():
    """Test that empty names are rejected."""
    with pytest.raises(HTTPException) as exc:
        validate_collection_name("")
    assert exc.value.status_code == 400
    assert "cannot be empty" in exc.value.detail

def test_validate_collection_name_too_long():
    """Test that overly long names are rejected."""
    long_name = "a" * 101
    with pytest.raises(HTTPException) as exc:
        validate_collection_name(long_name)
    assert exc.value.status_code == 400
    assert "100 characters or less" in exc.value.detail