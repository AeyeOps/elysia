# Frontend Error Handling Guide

## Overview
The Elysia API now implements standardized error responses through the `@recoverable_endpoint` decorator pattern (ADR-001). This guide helps frontend developers handle these responses appropriately.

## Error Response Format

All errors follow the FastAPI/OpenAPI standard:

```json
{
    "detail": "Human-readable error message"
}
```

## HTTP Status Codes and Their Meanings

### 401 Unauthorized - Session Not Initialized
**When:** User session doesn't exist or has expired
**Message:** `"Session not initialized"`
**Frontend Action:**
- Redirect to login/initialization flow
- Clear any cached user data
- Show "Please log in" or "Session expired" message

```javascript
if (response.status === 401) {
    // Clear local session
    localStorage.removeItem('userId');
    localStorage.removeItem('sessionToken');
    
    // Redirect to login
    window.location.href = '/login';
}
```

### 404 Not Found - Resource Missing
**When:** Requested collection or resource doesn't exist
**Messages:** 
- `"Collection {name} not found"` (for user collections)
- `"Collection not found"` (for system collections)
**Frontend Action:**
- Show user-friendly "not found" message
- Offer to refresh collection list
- Don't retry automatically

```javascript
if (response.status === 404) {
    const error = await response.json();
    if (error.detail.includes('Collection')) {
        showNotification('Collection not available. Please refresh.', 'warning');
        refreshCollectionList();
    }
}
```

### 400 Bad Request - Invalid Input
**When:** Request data is invalid or malformed
**Message:** Original validation error message
**Frontend Action:**
- Display the error message to user
- Highlight invalid form fields
- Don't auto-retry

```javascript
if (response.status === 400) {
    const error = await response.json();
    showValidationError(error.detail);
    highlightInvalidFields();
}
```

### 422 Unprocessable Entity - Missing Required Field
**When:** Required field is missing from request
**Message:** `"Missing required field: {fieldname}"`
**Frontend Action:**
- Highlight the missing field
- Show inline validation message
- Focus on the empty field

```javascript
if (response.status === 422) {
    const error = await response.json();
    const match = error.detail.match(/Missing required field: (.*)/);
    if (match) {
        const fieldName = match[1];
        highlightField(fieldName);
        showFieldError(fieldName, 'This field is required');
    }
}
```

### 503 Service Unavailable - Temporary Outage
**When:** Database or service temporarily unavailable
**Messages:**
- `"Database temporarily unavailable"` (Weaviate issues)
- `"Service temporarily unavailable"` (other services)
**Frontend Action:**
- Show "temporary issue" message
- Implement exponential backoff retry
- Offer manual retry button

```javascript
if (response.status === 503) {
    showNotification('Service temporarily unavailable. Retrying...', 'info');
    
    // Exponential backoff retry
    const retryWithBackoff = async (retriesLeft = 3, delay = 1000) => {
        if (retriesLeft === 0) {
            showNotification('Service unavailable. Please try again later.', 'error');
            return;
        }
        
        setTimeout(async () => {
            const retryResponse = await fetch(url, options);
            if (!retryResponse.ok && retryResponse.status === 503) {
                retryWithBackoff(retriesLeft - 1, delay * 2);
            }
        }, delay);
    };
    
    retryWithBackoff();
}
```

### 500 Internal Server Error
**When:** Unexpected server error
**Message:** `"Internal server error"`
**Frontend Action:**
- Show generic error message
- Log to error tracking service
- Don't expose technical details
- Offer to report issue

```javascript
if (response.status === 500) {
    // Log to error tracking
    console.error('Server error:', {
        url: response.url,
        timestamp: new Date().toISOString(),
        userId: getCurrentUserId()
    });
    
    showNotification('Something went wrong. Please try again.', 'error');
    showReportIssueButton();
}
```

## Complete Error Handler Example

```javascript
class ElysiaAPIClient {
    async handleResponse(response) {
        if (response.ok) {
            return await response.json();
        }
        
        const error = await response.json();
        
        switch (response.status) {
            case 401:
                this.handleSessionExpired();
                break;
                
            case 404:
                this.handleNotFound(error.detail);
                break;
                
            case 400:
                this.handleValidationError(error.detail);
                break;
                
            case 422:
                this.handleMissingField(error.detail);
                break;
                
            case 503:
                await this.handleServiceUnavailable();
                break;
                
            case 500:
                this.handleServerError();
                break;
                
            default:
                console.error('Unexpected error:', error);
                throw new Error(error.detail || 'An error occurred');
        }
        
        throw new Error(error.detail);
    }
    
    handleSessionExpired() {
        // Clear session and redirect to login
        this.clearSession();
        window.location.href = '/login';
    }
    
    handleNotFound(message) {
        // Show not found notification
        if (message.includes('Collection')) {
            this.showNotification('Collection not found', 'warning');
            this.refreshCollections();
        }
    }
    
    handleValidationError(message) {
        // Display validation errors
        this.showNotification(message, 'error');
    }
    
    handleMissingField(message) {
        // Extract field name and highlight it
        const match = message.match(/Missing required field: (.*)/);
        if (match) {
            const fieldName = match[1];
            this.highlightRequiredField(fieldName);
        }
    }
    
    async handleServiceUnavailable() {
        // Implement retry with exponential backoff
        this.showNotification('Service temporarily unavailable', 'info');
        // ... retry logic
    }
    
    handleServerError() {
        // Generic server error handling
        this.showNotification('An error occurred. Please try again.', 'error');
        this.logError('Server error occurred');
    }
}
```

## User Experience Best Practices

### 1. Session Management
- Detect 401 errors globally
- Implement auto-refresh for expiring sessions
- Clear local state on session errors
- Provide clear re-authentication flow

### 2. Error Messages
- Show user-friendly messages, not raw error details
- Use toast notifications for transient errors
- Inline validation for form errors
- Avoid technical jargon

### 3. Retry Logic
- Automatic retry only for 503 errors
- Exponential backoff to prevent server overload
- Manual retry button for user control
- Maximum retry limit to prevent infinite loops

### 4. Loading States
- Show loading indicators during requests
- Disable buttons during submission
- Optimistic updates with rollback on error
- Skeleton screens for better perceived performance

## What NOT to Do

### ❌ Don't Expose Internal Details
```javascript
// BAD - Exposes internal collection names
if (error.detail.includes('ELYSIACTL_CONFIG')) {
    alert('System collection error: ' + error.detail);
}

// GOOD - Generic message for system errors
if (response.status === 404) {
    showNotification('Resource not available');
}
```

### ❌ Don't Retry Everything
```javascript
// BAD - Retrying 400/422 errors won't help
if (!response.ok) {
    retry();
}

// GOOD - Only retry temporary failures
if (response.status === 503) {
    retryWithBackoff();
}
```

### ❌ Don't Ignore Error Patterns
```javascript
// BAD - Generic handling for all errors
catch (error) {
    alert('Error occurred');
}

// GOOD - Specific handling per error type
catch (error) {
    if (error.status === 401) {
        handleSessionExpired();
    } else if (error.status === 503) {
        handleTemporaryFailure();
    }
}
```

## Testing Error Scenarios

### Manual Testing Checklist
- [ ] Test with expired session (401)
- [ ] Request non-existent collection (404)
- [ ] Submit invalid data (400)
- [ ] Submit with missing required fields (422)
- [ ] Test during maintenance window (503)
- [ ] Simulate server errors (500)

### Automated Testing
```javascript
describe('Error Handling', () => {
    it('should redirect on 401', async () => {
        mockFetch.mockResponseOnce('', { status: 401 });
        await apiClient.getCollections();
        expect(window.location.href).toBe('/login');
    });
    
    it('should show notification on 404', async () => {
        mockFetch.mockResponseOnce(
            JSON.stringify({ detail: 'Collection not found' }), 
            { status: 404 }
        );
        await apiClient.getCollection('missing');
        expect(mockNotification).toHaveBeenCalledWith(
            'Collection not found', 
            'warning'
        );
    });
});
```

## Migration Guide

### Before (Raw Error Handling)
```javascript
try {
    const response = await fetch('/api/user/config/123');
    const data = await response.json();
} catch (error) {
    // Raw error exposed
    alert(error.message); 
    // "User with ID '123' not found in collection 'ELYSIACTL_CONFIG_xyz'"
}
```

### After (Standardized Handling)
```javascript
try {
    const response = await fetch('/api/user/config/123');
    if (!response.ok) {
        const error = await response.json();
        if (response.status === 401) {
            // Clean, actionable message
            redirectToLogin(); // "Session not initialized"
        }
    }
    const data = await response.json();
} catch (error) {
    handleError(error);
}
```

## Summary

The new error handling provides:
1. **Consistent** error format across all endpoints
2. **Secure** responses without internal details
3. **Actionable** status codes for different scenarios
4. **User-friendly** messages suitable for display

Frontend teams should:
1. Update error handlers to use status codes
2. Remove any parsing of internal error details
3. Implement proper retry logic for 503 errors
4. Add session management for 401 responses
5. Test all error scenarios thoroughly