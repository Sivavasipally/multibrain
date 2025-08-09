# Comprehensive Error Boundary System Documentation

## Overview

The Error Boundary System provides robust error handling for React components in the RAG Chatbot PWA. This system catches JavaScript errors anywhere in the component tree, provides user-friendly error messages, and includes comprehensive error reporting and recovery mechanisms.

## Architecture

### Error Boundary Components

#### 1. GlobalErrorBoundary
**Purpose**: Catches application-wide errors
**Usage**: Wraps the entire application
**Behavior**: 
- Shows full-page error screen
- Provides application reload option
- Reports critical errors
- Shows technical details in development mode

```tsx
<GlobalErrorBoundary>
  <App />
</GlobalErrorBoundary>
```

#### 2. PageErrorBoundary
**Purpose**: Isolates errors to specific routes/pages
**Usage**: Wraps individual page components
**Behavior**:
- Shows page-level error message
- Provides retry and navigation options
- Maintains application functionality for other pages

```tsx
<PageErrorBoundary pageName="Dashboard">
  <Dashboard />
</PageErrorBoundary>
```

#### 3. ComponentErrorBoundary
**Purpose**: Granular error handling for specific components
**Usage**: Wraps individual components that might fail
**Behavior**:
- Shows compact error message in place of component
- Provides retry mechanism
- Allows custom fallback UI

```tsx
<ComponentErrorBoundary 
  componentName="ChatMessage"
  fallback={<ErrorFallback />}
>
  <ChatMessage message={message} />
</ComponentErrorBoundary>
```

### Error Reporting Service

#### Features
- **Automatic Error Collection**: Catches all JavaScript errors and unhandled promise rejections
- **Error Deduplication**: Prevents duplicate error reports using fingerprinting
- **Rate Limiting**: Prevents spam from repeated errors
- **Offline Storage**: Stores errors locally when offline, syncs when online
- **Breadcrumb Tracking**: Records user actions leading to errors
- **Privacy Protection**: Sanitizes sensitive data from error reports

#### Usage
```tsx
import { errorService } from '../services/errorService';

// Initialize (done automatically in App.tsx)
errorService.initialize();

// Report custom errors
errorService.reportError(error, { component: 'MyComponent' }, 'high');

// Add breadcrumbs
errorService.addBreadcrumb('user', 'Button clicked', { buttonId: 'submit' });
```

### Error Handler Hook

#### Features
- **Automatic Error Classification**: Categorizes errors by type
- **User-Friendly Messages**: Converts technical errors to readable messages
- **API Error Handling**: Specialized handling for HTTP errors
- **Function Wrapping**: Wraps async functions with automatic error handling
- **Context Tracking**: Associates errors with specific components and actions

#### Usage
```tsx
import useErrorHandler from '../hooks/useErrorHandler';

function MyComponent() {
  const errorHandler = useErrorHandler({ component: 'MyComponent' });
  
  // Wrap async functions
  const loadData = errorHandler.withErrorHandler(
    async () => {
      const data = await api.getData();
      setData(data);
    },
    'Failed to load data',
    'loadData'
  );
  
  // Handle errors directly
  const handleSubmit = async () => {
    try {
      await api.submit(formData);
    } catch (error) {
      errorHandler.handleApiError(error, 'Failed to submit form', 'submit');
    }
  };
}
```

## Implementation Guide

### 1. Application Setup

```tsx
// App.tsx
import { GlobalErrorBoundary } from './components/ErrorBoundary/ErrorBoundary';
import { errorService } from './services/errorService';

function App() {
  useEffect(() => {
    errorService.initialize();
  }, []);

  return (
    <GlobalErrorBoundary>
      {/* Your app content */}
    </GlobalErrorBoundary>
  );
}
```

### 2. Page-Level Protection

```tsx
// Route setup
<Route path="/dashboard" element={
  <PageErrorBoundary pageName="Dashboard">
    <Dashboard />
  </PageErrorBoundary>
} />
```

### 3. Component-Level Protection

```tsx
// For critical components
<ComponentErrorBoundary componentName="DataTable">
  <DataTable data={data} />
</ComponentErrorBoundary>

// With custom fallback
<ComponentErrorBoundary 
  componentName="Chart"
  fallback={<ChartPlaceholder />}
>
  <Chart data={chartData} />
</ComponentErrorBoundary>
```

### 4. Hook Integration

```tsx
function DataComponent() {
  const { handleApiError, withErrorHandler } = useErrorHandler();
  
  // Method 1: Wrap function
  const fetchData = withErrorHandler(
    async () => {
      const response = await api.fetchData();
      setData(response.data);
    },
    'Failed to fetch data'
  );
  
  // Method 2: Try-catch with handler
  const saveData = async () => {
    try {
      await api.saveData(data);
      showSuccess('Data saved');
    } catch (error) {
      handleApiError(error, 'Failed to save data');
    }
  };
}
```

## Error Types and Classification

### Network Errors
- **Detection**: Connection issues, fetch failures, timeouts
- **User Message**: "Network connection issue. Please check your internet connection."
- **Automatic Retry**: Yes (with exponential backoff)

### Authentication Errors
- **Detection**: 401/403 status codes, token-related errors
- **User Message**: "Authentication failed. Please log in again."
- **Automatic Action**: Redirect to login (configurable)

### Validation Errors
- **Detection**: 400 status codes, validation patterns
- **User Message**: "Please check your input and try again."
- **User Action**: Form field highlighting (when integrated)

### Server Errors
- **Detection**: 5xx status codes, server error patterns
- **User Message**: "Server error occurred. Please try again later."
- **Reporting**: High priority, always reported

## Error Reporting Backend Integration

### API Endpoint
```typescript
POST /api/errors/report
Content-Type: application/json

{
  "errors": [{
    "id": "error_123456789_abc123",
    "message": "Cannot read property 'foo' of undefined",
    "stack": "TypeError: Cannot read property...",
    "url": "https://app.example.com/dashboard",
    "userAgent": "Mozilla/5.0...",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "context": {
      "component": "Dashboard",
      "action": "loadData",
      "userId": "user123",
      "sessionId": "session_456"
    },
    "errorType": "runtime",
    "severity": "medium",
    "fingerprint": "abc123def456",
    "breadcrumbs": [
      {
        "timestamp": "2024-01-15T10:29:30.000Z",
        "type": "navigation",
        "message": "Navigation to /dashboard"
      },
      {
        "timestamp": "2024-01-15T10:29:58.000Z",
        "type": "user",
        "message": "Button clicked",
        "data": { "buttonId": "refresh" }
      }
    ]
  }]
}
```

### Backend Route (Flask)
```python
@app.route('/api/errors/report', methods=['POST'])
def report_errors():
    data = request.get_json()
    errors = data.get('errors', [])
    
    for error_data in errors:
        # Store in database
        error = ErrorReport(
            error_id=error_data['id'],
            message=error_data['message'],
            stack_trace=error_data.get('stack'),
            url=error_data['url'],
            user_agent=error_data['userAgent'],
            timestamp=error_data['timestamp'],
            context=json.dumps(error_data.get('context', {})),
            error_type=error_data['errorType'],
            severity=error_data['severity'],
            fingerprint=error_data['fingerprint']
        )
        db.session.add(error)
    
    db.session.commit()
    return {'status': 'success'}, 200
```

## Configuration

### Error Service Configuration
```typescript
const errorService = new ErrorService({
  maxBreadcrumbs: 50,           // Maximum breadcrumbs to keep
  maxBatchSize: 10,             // Maximum errors per batch
  batchTimeout: 5000,           // Batch timeout in ms
  maxRetries: 3,                // Maximum retry attempts
  enableAutoReporting: true,    // Automatic error reporting
  enableBreadcrumbs: true,      // Breadcrumb tracking
  apiEndpoint: '/api/errors/report',
  rateLimitWindow: 60000,       // Rate limit window (1 minute)
  maxErrorsPerWindow: 10,       // Maximum errors per window
});
```

### Environment-Based Behavior
```typescript
// Development
- Show detailed error information
- Log errors to console
- Enable debug features

// Production  
- Show user-friendly messages only
- Report all errors to backend
- Hide technical details
```

## Best Practices

### 1. Strategic Error Boundary Placement
```tsx
// ✅ Good: Granular boundaries for specific functionality
<ComponentErrorBoundary componentName="UserProfile">
  <UserProfile user={user} />
</ComponentErrorBoundary>

// ❌ Avoid: Too many nested boundaries
<ErrorBoundary>
  <ErrorBoundary>
    <ErrorBoundary>
      <Component />
    </ErrorBoundary>
  </ErrorBoundary>
</ErrorBoundary>
```

### 2. Meaningful Error Messages
```tsx
// ✅ Good: User-friendly, actionable
errorHandler.handleError(error, 'Unable to save your changes. Please try again.');

// ❌ Avoid: Technical jargon
errorHandler.handleError(error, 'HTTP 500 Internal Server Error');
```

### 3. Error Context
```tsx
// ✅ Good: Rich context
const errorHandler = useErrorHandler({
  component: 'UserDashboard',
  userId: user.id,
  metadata: { feature: 'profile-edit' }
});

// ❌ Avoid: No context
const errorHandler = useErrorHandler();
```

### 4. Fallback UI Design
```tsx
// ✅ Good: Maintains layout and provides recovery
const fallback = (
  <Box sx={{ p: 2, textAlign: 'center', bgcolor: 'grey.100' }}>
    <Typography variant="body2" color="text.secondary">
      Unable to load this section
    </Typography>
    <Button size="small" onClick={retry}>Try Again</Button>
  </Box>
);

// ❌ Avoid: Breaks layout
const fallback = <div>Error</div>;
```

## Testing Error Boundaries

### Test Utils
```tsx
// test-utils.tsx
export function triggerError(wrapper: ReactWrapper) {
  const errorComponent = wrapper.find('ThrowError');
  errorComponent.prop('onError')();
  wrapper.update();
}

// Test component that throws errors
export function ThrowError({ shouldThrow, onError }: { shouldThrow: boolean, onError: () => void }) {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div onClick={onError}>Trigger Error</div>;
}
```

### Example Tests
```tsx
describe('ErrorBoundary', () => {
  it('should catch and display error', () => {
    const onError = jest.fn();
    const wrapper = mount(
      <ErrorBoundary onError={onError}>
        <ThrowError shouldThrow={true} onError={() => {}} />
      </ErrorBoundary>
    );

    expect(wrapper.text()).toContain('Something went wrong');
    expect(onError).toHaveBeenCalled();
  });

  it('should provide retry functionality', () => {
    const wrapper = mount(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} onError={() => {}} />
      </ErrorBoundary>
    );

    const retryButton = wrapper.find('button').filterWhere(n => 
      n.text().includes('Try Again')
    );
    
    expect(retryButton).toHaveLength(1);
  });
});
```

## Monitoring and Analytics

### Error Metrics
- **Error Rate**: Percentage of sessions with errors
- **Error Types**: Distribution of error categories
- **Component Reliability**: Error rates per component
- **User Impact**: Users affected by errors
- **Recovery Rate**: Successful error recoveries

### Alerting
- **Critical Errors**: Immediate notification
- **High Error Rates**: Threshold-based alerts
- **New Error Types**: First occurrence notifications
- **Performance Impact**: Error-related performance degradation

## Conclusion

The comprehensive error boundary system provides multiple layers of error protection, from application-wide error catching to granular component-level error handling. By combining error boundaries with intelligent error reporting and user-friendly recovery mechanisms, the system ensures a robust and resilient user experience even when unexpected errors occur.

The system is designed to be:
- **Non-intrusive**: Doesn't interfere with normal application flow
- **Informative**: Provides useful error information for debugging
- **User-friendly**: Shows helpful messages and recovery options
- **Maintainable**: Easy to configure and extend
- **Performance-conscious**: Minimal overhead in normal operation