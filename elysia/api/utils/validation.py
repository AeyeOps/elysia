"""Validation utilities for API operations."""
from typing import List
from fastapi import HTTPException

# Reserved prefixes that users cannot use for collection names
RESERVED_PREFIXES: List[str] = ["ELYSIA_", "SYSTEM_"]

def validate_collection_name(name: str) -> None:
    """
    Validate that a collection name doesn't use reserved namespaces.
    
    Args:
        name: The proposed collection name
        
    Raises:
        HTTPException: If the name uses a reserved prefix
    """
    if not name:
        raise HTTPException(400, "Collection name cannot be empty")
    
    name_upper = name.upper()
    
    for prefix in RESERVED_PREFIXES:
        if name_upper.startswith(prefix.upper()):
            raise HTTPException(
                400,
                f"Collection names starting with '{prefix}' are reserved for system use. "
                "Please choose a different name for your collection."
            )
    
    # Additional validation could go here (e.g., length, special characters)
    if len(name) > 100:
        raise HTTPException(400, "Collection name must be 100 characters or less")