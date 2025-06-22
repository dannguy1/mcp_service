# Frontend - Environment Configuration Guide

## Overview
The frontend is a React application built with Vite that provides a modern web interface for the MCP service. It uses environment variables for configuration and integrates seamlessly with the backend API through Vite's proxy configuration.

## Architecture
- **React 18** with TypeScript for the UI framework
- **Vite** for build tooling and development server
- **Ant Design** for UI components
- **Axios** for API communication
- **React Query** for data fetching and caching

## Environment Variable Configuration

### How It Works
1. **Vite Environment Variables**: All frontend configuration uses `VITE_` prefixed environment variables
2. **Automatic Loading**: Environment variables are loaded from `.env` files by Vite
3. **Build-time Injection**: Variables are embedded at build time for security
4. **Proxy Integration**: API calls are proxied to the backend through Vite's dev server

### Key Environment Variables

#### API Configuration
```bash
VITE_API_BASE_URL=/api/v1          # API base URL (uses Vite proxy)
```

#### Development Settings
```bash
VITE_DEV_MODE=true                  # Enable development features
VITE_MOCK_API=false                 # Use mock API responses
VITE_ENABLE_DEBUG_LOGGING=true      # Enable debug logging
```

#### Feature Flags
```bash
VITE_ENABLE_WEBSOCKETS=true         # Enable WebSocket connections
VITE_ENABLE_ANALYTICS=true          # Enable analytics tracking
VITE_ENABLE_AUTH=true               # Enable authentication
```

#### Performance Settings
```bash
VITE_CACHE_TTL=300                  # Cache time-to-live (seconds)
VITE_REQUEST_TIMEOUT=10000          # API request timeout (ms)
VITE_MAX_RETRIES=3                  # Maximum API retry attempts
```

#### UI Configuration
```bash
VITE_THEME=light                    # UI theme (light/dark)
VITE_LANGUAGE=en                    # Interface language
VITE_TIMEZONE=UTC                   # Timezone for date display
```

#### Security Settings
```bash
VITE_SESSION_TIMEOUT=3600           # Session timeout (seconds)
VITE_REFRESH_TOKEN_INTERVAL=300     # Token refresh interval (seconds)
```

## How to Use

### Starting the Frontend
```bash
# Start development server
./scripts/start_frontend.sh

# Or manually
cd frontend
npm run dev
```

### Environment Setup
1. **Copy the template**:
   ```bash
   cp frontend/example.env frontend/.env
   ```

2. **Edit configuration**:
   ```bash
   # Edit frontend/.env to customize settings
   nano frontend/.env
   ```

3. **Start the frontend**:
   ```bash
   ./scripts/start_frontend.sh
   ```

### Development Commands
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## API Integration

### Proxy Configuration
The frontend uses Vite's proxy to forward API calls to the backend:

```typescript
// vite.config.ts
proxy: {
  "/api": {
    target: "http://127.0.0.1:5000",
    changeOrigin: true,
    secure: false,
  }
}
```

### API Usage
```typescript
// Using environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// Making API calls
const response = await axios.get(`${API_BASE_URL}/dashboard`);
```

## Configuration Migration

### From Hardcoded URLs to Environment Variables
The frontend previously used hardcoded API URLs. These have been replaced with environment variables:

| Old Hardcoded Value | New Environment Variable |
|---------------------|--------------------------|
| `'http://192.168.10.12:5000/api/v1'` | `VITE_API_BASE_URL=/api/v1` |
| `'/api/v1'` | `VITE_API_BASE_URL=/api/v1` |

### Benefits of Environment Variables
- **Environment-specific configuration**: Different settings for dev/staging/prod
- **Security**: No hardcoded URLs in source code
- **Flexibility**: Easy to change without rebuilding
- **Consistency**: Same approach as backend and MCP service

## Troubleshooting

### Common Issues
1. **API calls failing**: Check that backend is running and proxy is configured
2. **Environment variables not loading**: Ensure `.env` file exists and has correct format
3. **CORS errors**: Verify Vite proxy configuration in `vite.config.ts`
4. **Build errors**: Check that all `VITE_` prefixed variables are properly set

### Debug Mode
```bash
# Start with debug logging enabled
VITE_ENABLE_DEBUG_LOGGING=true npm run dev
```

### Checking Configuration
```bash
# View current environment variables
cd frontend
cat .env

# Check if Vite is loading variables correctly
npm run dev
# Look for console.log output showing API_BASE_URL
```

## Integration with Backend

The frontend integrates seamlessly with the backend:

- **Shared Configuration**: Both use `.env` files for configuration
- **API Communication**: Frontend proxies requests to backend API
- **CORS Handling**: Vite proxy handles CORS automatically
- **Environment Consistency**: Same environment variables across all services

## Security Considerations

- **Client-side variables**: Only `VITE_` prefixed variables are available in the browser
- **Sensitive data**: Never put secrets in frontend environment variables
- **Build security**: Environment variables are embedded at build time
- **HTTPS**: Use HTTPS in production for secure communication

## Development Workflow

1. **Environment setup**: Copy and configure `.env` file
2. **Start backend**: Ensure backend API is running
3. **Start frontend**: Run `./scripts/start_frontend.sh`
4. **Development**: Make changes and see live updates
5. **Testing**: Use browser dev tools to debug API calls

## Production Deployment

### Build Process
```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables
- Set production environment variables in your deployment platform
- Ensure `VITE_API_BASE_URL` points to your production backend
- Configure any production-specific feature flags

---

For more details, see the main project README and the backend documentation. 