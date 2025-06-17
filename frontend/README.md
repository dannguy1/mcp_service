# MCP Service Frontend

React + TypeScript + Vite frontend for the MCP Service application.

## Quick Start

### Prerequisites
- Node.js 16+ and npm
- Backend service running on port 5000

### Installation
```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:3000

## Environment Configuration

Create a `.env` file in the frontend directory with the following variables:

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:5000/api/v1

# Feature Flags
VITE_ENABLE_WEBSOCKETS=true
VITE_ENABLE_ANALYTICS=true
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:5000/api/v1` |
| `VITE_ENABLE_WEBSOCKETS` | Enable WebSocket connections | `true` |
| `VITE_ENABLE_ANALYTICS` | Enable analytics tracking | `true` |

## Development

### Available Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm test

# Lint code
npm run lint
```

### Project Structure

```
src/
├── components/          # React components
│   ├── common/         # Shared components
│   ├── dashboard/      # Dashboard components
│   ├── export/         # Export functionality
│   ├── layout/         # Layout components
│   └── models/         # Model management
├── hooks/              # Custom React hooks
├── pages/              # Page components
├── services/           # API services
├── styles/             # CSS styles
└── types.ts            # TypeScript type definitions
```

## API Integration

The frontend communicates with the backend API through the `services/api.ts` module. The API base URL is configured via the `VITE_API_BASE_URL` environment variable.

### CORS Configuration

The backend is configured to allow CORS requests from the frontend. If you encounter CORS issues:

1. Ensure the frontend URL is in the backend's CORS allowlist
2. Check that `VITE_API_BASE_URL` is correctly set
3. Verify the backend is running on the expected port

## Building for Production

```bash
# Build the application
npm run build

# The built files will be in the dist/ directory
```

## Troubleshooting

### CORS Issues
- Check that the backend CORS configuration includes your frontend URL
- Verify the API base URL in your `.env` file
- Ensure the backend is running and accessible

### Build Issues
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version compatibility
- Verify all environment variables are set correctly

## Contributing

1. Follow the existing code style and structure
2. Add TypeScript types for new components and functions
3. Test your changes thoroughly
4. Update documentation as needed
