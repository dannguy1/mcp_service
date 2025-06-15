# AnalyzerMCPServer UI Implementation

## 1. Overview

This document describes the current implementation of the AnalyzerMCPServer User Interface (UI). The UI is a modern, responsive web application that provides real-time monitoring, analysis, and management capabilities for the MCP service.

### 1.1 Architecture

The UI follows a modern three-tier architecture:
1. **React Frontend**: Single Page Application (SPA)
2. **Flask Backend-for-Frontend (BFF)**: API aggregation and security
3. **Nginx Reverse Proxy**: Request routing and static file serving

## 2. Technical Stack

### 2.1 Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **State Management**: React Query
- **UI Components**: 
  - React Bootstrap
  - Ant Design (for specific components)
  - React Icons
- **Development Tools**:
  - TypeScript
  - ESLint
  - Prettier
  - Jest + React Testing Library

### 2.2 Backend (BFF)
- **Framework**: Flask 2.3
- **API Documentation**: OpenAPI/Swagger
- **Authentication**: JWT
- **Caching**: Redis
- **Testing**: pytest

### 2.3 Infrastructure
- **Web Server**: Nginx
- **Containerization**: Docker
- **CI/CD**: GitHub Actions

## 3. Implementation Details

### 3.1 Project Structure
```
/frontend
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── layout/         # Layout components
│   │   ├── dashboard/      # Dashboard components
│   │   ├── logs/          # Log explorer components
│   │   └── models/        # Model management components
│   ├── pages/             # Page components
│   ├── services/          # API clients
│   ├── hooks/             # Custom React hooks
│   ├── styles/            # Global styles
│   └── types/             # TypeScript definitions
├── public/                # Static assets
└── tests/                # Test files
```

### 3.2 Core Components

#### Layout Components
- **MainLayout**: Dark-themed top navigation with hamburger menu
- **Offcanvas Sidebar**: Navigation menu with icons
- **ErrorBoundary**: Global error handling
- **Container**: Fluid layout with consistent padding

#### Page Components
1. **Dashboard**
   - System status overview
   - Recent anomalies feed
   - Performance metrics
   - Real-time updates (30s interval)

2. **Logs**
   - Advanced filtering (date, severity, programs)
   - Pagination controls
   - Export functionality
   - Real-time updates
   - AI processing status indicators

3. **Anomalies**
   - Severity-based categorization
   - Status tracking
   - Detailed view with context
   - Real-time updates

4. **Models**
   - Model statistics
   - Version management
   - Performance metrics
   - Detailed model information
   - Upload/Delete functionality

5. **Server Status**
   - System health overview
   - Component status
   - Resource usage
   - Service status

### 3.3 API Integration

#### Frontend API Service
```typescript
// /frontend/src/services/api.ts
export const endpoints = {
  getDashboardData: () => api.get('/api/ui/dashboard'),
  getLogs: (params) => api.get('/api/ui/logs', { params }),
  getAnomalies: () => api.get('/api/ui/anomalies'),
  getModels: () => api.get('/api/ui/models'),
  getModelInfo: (id) => api.get(`/api/ui/models/${id}`),
  uploadModel: (formData) => api.post('/api/ui/models', formData),
  deleteModel: (id) => api.delete(`/api/ui/models/${id}`),
  getServerStatus: () => api.get('/api/ui/server/status')
};
```

#### Data Types
```typescript
// /frontend/src/services/types.ts
export interface Log {
  id: string;
  timestamp: string;
  device_ip: string;
  log_level: string;
  process_name: string;
  message: string;
  pushed_to_ai: boolean;
}

export interface Anomaly {
  id: string;
  timestamp: string;
  type: string;
  severity: number;
  description: string;
  status: string;
}

export interface Model {
  id: string;
  version: string;
  created_at: string;
  status: string;
  metrics: {
    accuracy: number;
    false_positive_rate: number;
    false_negative_rate: number;
  };
  agent_info?: {
    status: string;
    is_running: boolean;
    last_run?: string;
    description?: string;
    capabilities?: string[];
    programs?: string[];
    model_path?: string;
  };
}
```

### 3.4 Styling

#### Global Styles
- Bootstrap 5 for base components
- Custom CSS for specific components
- Responsive design breakpoints
- Dark theme for navigation
- Consistent spacing and typography

#### Component-Specific Styles
- Card-based layouts
- Status indicators with color coding
- Responsive tables
- Form styling
- Loading states
- Error states

### 3.5 State Management

#### React Query Configuration
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
    mutations: {
      retry: 1,
    },
  },
});
```

#### Data Fetching Patterns
- Real-time updates with refetchInterval
- Optimistic updates for mutations
- Error handling with toast notifications
- Loading states with spinners

### 3.6 Error Handling

#### Global Error Boundary
```typescript
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h1>Something went wrong</h1>
          <p>Please refresh the page or try again later.</p>
          <button onClick={() => window.location.reload()}>
            Refresh Page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
```

## 4. Performance Metrics

### 4.1 Current Performance
- Initial load time: ~2s
- Time to interactive: ~3s
- API response time: <100ms
- Real-time update delay: <1s

### 4.2 Resource Usage
- Frontend bundle size: ~500KB
- Memory usage: ~100MB
- CPU usage: ~30%
- Network I/O: <1MB/min

## 5. Security Implementation

### 5.1 Authentication
- JWT-based authentication
- Token refresh mechanism
- Role-based access control

### 5.2 Data Protection
- HTTPS enforcement
- XSS prevention
- CSRF protection
- Input validation

### 5.3 API Security
- Rate limiting
- Request validation
- Error handling
- Logging and monitoring

## 6. Maintenance

### 6.1 Regular Tasks
- Dependency updates
- Security patches
- Performance monitoring
- Error tracking

### 6.2 Backup Strategy
- Configuration backups
- Database backups
- Log retention
- Disaster recovery

## 7. Documentation

### 7.1 Current Documentation
- API documentation
- Component documentation
- Setup guide
- Troubleshooting guide

### 7.2 Code Standards
- TypeScript strict mode
- ESLint rules
- Prettier configuration
- Git commit conventions 