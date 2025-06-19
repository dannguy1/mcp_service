# UI Design Guide

## Table of Contents
1. [Technology Stack](#technology-stack)
2. [Project Structure](#project-structure)
3. [Layout Structure](#layout-structure)
4. [Navigation](#navigation)
5. [Components](#components)
6. [Styling](#styling)
7. [Responsive Design](#responsive-design)
8. [Implementation Patterns](#implementation-patterns)

## Technology Stack

### Core Dependencies
- **React 18.2.0** with TypeScript
- **React Router DOM 6.22.3** for routing
- **React Bootstrap 2.10.10** for UI components
- **Bootstrap 5.3.6** for styling framework
- **Ant Design 4.24.12** for additional components
- **React Query (@tanstack/react-query 5.80.6)** for data fetching
- **React Hot Toast 2.5.2** for notifications
- **Axios 1.9.0** for HTTP requests

### Icon Libraries
- **Ant Design Icons 4.8.0** for primary icons
- **Heroicons React 2.2.0** for additional icons
- **React Icons 5.5.0** for miscellaneous icons

### Development Tools
- **Vite 6.3.5** for build tooling
- **TypeScript 5.8.3** for type safety
- **ESLint 9.28.0** for code linting

## Project Structure

```
frontend/src/
├── components/          # Reusable UI components
│   ├── common/         # Shared components
│   ├── dashboard/      # Dashboard-specific components
│   ├── export/         # Export functionality components
│   ├── layout/         # Layout components
│   └── models/         # Model management components
├── hooks/              # Custom React hooks
├── pages/              # Page components
├── services/           # API and service layer
├── styles/             # Additional styling
├── App.tsx             # Main app component
├── App.css             # Global app styles
├── index.css           # Base styles and variables
└── main.tsx            # App entry point
```

## Layout Structure

### Main Layout Pattern
```tsx
// App.tsx - Main wrapper
<ErrorBoundary>
  <BrowserRouter>
    <AppRoutes />
  </BrowserRouter>
</ErrorBoundary>

// Layout.tsx - Navigation and content wrapper
<div className="d-flex flex-column min-vh-100">
  <Navbar bg="dark" variant="dark" className="px-3">
    {/* Top navigation */}
  </Navbar>
  <Offcanvas show={show} onHide={handleClose} className="bg-dark text-light">
    {/* Sidebar navigation */}
  </Offcanvas>
  <div className="flex-grow-1">
    <Container fluid className="py-4">
      <Outlet />
    </Container>
  </div>
</div>
```

### Page Structure
- Page title as `h2` element with `mb-4` class
- Content organized in Bootstrap Cards
- Consistent spacing using Bootstrap utility classes
- Loading states with `Spinner` component
- Error states with `Alert` component

## Navigation

### Top Bar Implementation
```tsx
<Navbar bg="dark" variant="dark" className="px-3">
  <Navbar.Brand>
    <button className="btn btn-dark me-3" onClick={handleShow}>
      ☰
    </button>
    MCP Service
  </Navbar.Brand>
</Navbar>
```

**Key Classes:**
- `bg-dark` - Dark background
- `variant="dark"` - Dark theme variant
- `px-3` - Horizontal padding

### Sidebar Implementation
```tsx
<Offcanvas show={show} onHide={handleClose} className="bg-dark text-light">
  <Offcanvas.Header closeButton closeVariant="white">
    <Offcanvas.Title>MCP Service</Offcanvas.Title>
  </Offcanvas.Header>
  <Offcanvas.Body>
    <Nav className="flex-column">
      {menuItems.map((item) => (
        <Nav.Link
          key={item.path}
          as={Link}
          to={item.path}
          className={`text-light mb-2 ${location.pathname === item.path ? "active" : ""}`}
          onClick={handleClose}
        >
          <span className="me-2">{item.icon}</span>
          {item.label}
        </Nav.Link>
      ))}
    </Nav>
  </Offcanvas.Body>
</Offcanvas>
```

**Key Classes:**
- `bg-dark text-light` - Dark background with light text
- `flex-column` - Vertical navigation layout
- `text-light mb-2` - Light text with bottom margin
- `active` - Active state styling

### Navigation Items Structure
```tsx
const menuItems = [
  {
    path: '/',
    label: 'Dashboard',
    icon: <DashboardOutlined />,
  },
  {
    path: '/logs',
    label: 'Logs',
    icon: <FileTextOutlined />,
  },
  // ... additional items
];
```

## Components

### Card Implementation
```tsx
<Card className="mb-4">
  <Card.Header>Card Title</Card.Header>
  <Card.Body>
    {/* Card content */}
  </Card.Body>
</Card>
```

**Key Classes:**
- `mb-4` - Bottom margin for spacing
- `Card.Header` - White background with bottom border
- `Card.Body` - Content padding

### Table Implementation
```tsx
<Card>
  <Card.Body>
    <Table responsive hover>
      <thead>
        <tr>
          <th>Column Header</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Data</td>
        </tr>
      </tbody>
    </Table>
  </Card.Body>
</Card>
```

**Key Classes:**
- `responsive` - Responsive table behavior
- `hover` - Row hover effects
- Wrapped in Card for consistent styling

### Status Badge Implementation
```tsx
<span className={`badge bg-${statusColor}`}>
  {status}
</span>
```

**Status Color Mapping:**
```tsx
const getStatusColor = (status: string) => {
  switch (status.toLowerCase()) {
    case 'connected':
    case 'healthy':
    case 'completed':
      return 'success';
    case 'disconnected':
    case 'failed':
      return 'danger';
    case 'warning':
    case 'pending':
      return 'warning';
    case 'running':
      return 'info';
    default:
      return 'secondary';
  }
};
```

### Form Implementation
```tsx
<Form>
  <Form.Group className="mb-3">
    <Form.Label>Label</Form.Label>
    <Form.Control
      type="text"
      placeholder="Placeholder"
      value={value}
      onChange={handleChange}
    />
  </Form.Group>
  <Button variant="primary" type="submit">
    Submit
  </Button>
</Form>
```

**Key Classes:**
- `mb-3` - Bottom margin for form groups
- `Form.Label` - Consistent label styling
- `Form.Control` - Input styling with focus states

## Styling

### CSS File Organization
1. **index.css** - Base styles, variables, and global overrides
2. **App.css** - Layout-specific styles and component overrides
3. **layout.css** - Layout component specific styles

### Color Palette
```css
/* Primary Colors */
--bs-primary: #0d6efd;    /* Bootstrap blue */
--bs-success: #198754;    /* Green */
--bs-warning: #ffc107;    /* Yellow */
--bs-danger: #dc3545;     /* Red */
--bs-info: #0dcaf0;       /* Blue */
--bs-secondary: #6c757d;  /* Gray */

/* Background Colors */
--bs-light: #f8f9fa;      /* Light background */
--bs-dark: #212529;       /* Dark background */
```

### Typography
```css
:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;
  color-scheme: light dark;
  color: #213547;
  background-color: #f8f9fa;
}
```

### Card Styling
```css
.card {
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.card-header {
  background-color: #fff;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  font-weight: 600;
}
```

### Button Styling
```css
.btn {
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: all 0.2s ease-in-out;
}

.btn:hover {
  transform: translateY(-1px);
}
```

### Form Control Styling
```css
.form-control:focus,
.form-select:focus {
  border-color: #86b7fe;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}
```

## Responsive Design

### Breakpoints
```css
/* Mobile: < 768px */
@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
  }
  
  .sidebar.show {
    transform: translateX(0);
  }
  
  .main-content {
    margin-left: 0;
  }
}

/* Tablet: 768px - 992px */
@media (min-width: 768px) and (max-width: 992px) {
  .sidebar {
    width: 100%;
    max-width: 300px;
  }
}

/* Desktop: > 992px */
@media (min-width: 992px) {
  .sidebar {
    width: 250px;
  }
}
```

### Mobile Adaptations
- Off-canvas sidebar with hamburger menu
- Stacked card layouts
- Adjusted button sizes for touch
- Responsive tables with horizontal scroll

### Tablet Adaptations
- Sidebar becomes off-canvas
- Grid adjustments for medium screens
- Maintained readability with proper spacing

### Desktop Optimizations
- Fixed sidebar (when implemented)
- Multi-column layouts
- Hover effects
- Optimal spacing and typography

## Implementation Patterns

### Data Fetching Pattern
```tsx
import { useQuery } from '@tanstack/react-query';

const Component: React.FC = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['data-key'],
    queryFn: () => apiEndpoint.getData(),
    refetchInterval: 30000, // Optional auto-refresh
  });

  if (isLoading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '200px' }}>
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="danger">
        <FaExclamationTriangle className="me-2" />
        Error loading data: {error instanceof Error ? error.message : 'Unknown error'}
      </Alert>
    );
  }

  return (
    <div>
      <h2 className="mb-4">Page Title</h2>
      {/* Component content */}
    </div>
  );
};
```

### Error Boundary Pattern
```tsx
import React from 'react';

class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong.</h2>
          <pre>{this.state.error?.message}</pre>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### Modal Pattern
```tsx
const [showModal, setShowModal] = useState(false);

<Modal show={showModal} onHide={() => setShowModal(false)}>
  <Modal.Header closeButton>
    <Modal.Title>Modal Title</Modal.Title>
  </Modal.Header>
  <Modal.Body>
    {/* Modal content */}
  </Modal.Body>
  <Modal.Footer>
    <Button variant="secondary" onClick={() => setShowModal(false)}>
      Cancel
    </Button>
    <Button variant="primary" onClick={handleSubmit}>
      Submit
    </Button>
  </Modal.Footer>
</Modal>
```

### Table with Actions Pattern
```tsx
<Table responsive hover>
  <thead>
    <tr>
      <th>Column 1</th>
      <th>Column 2</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody>
    {data.map((item) => (
      <tr key={item.id}>
        <td>{item.field1}</td>
        <td>{item.field2}</td>
        <td>
          <div className="d-flex gap-2">
            <Button variant="info" size="sm" onClick={() => handleInfo(item.id)}>
              <FaInfoCircle />
            </Button>
            <Button variant="danger" size="sm" onClick={() => handleDelete(item.id)}>
              <FaTrash />
            </Button>
          </div>
        </td>
      </tr>
    ))}
  </tbody>
</Table>
```

### Status Panel Pattern
```tsx
<Card className="mb-4">
  <Card.Header>Status Panel</Card.Header>
  <Card.Body>
    <Row>
      <Col md={4}>
        <div className="text-center">
          <h5>Status</h5>
          <span className={`badge bg-${status === "healthy" ? "success" : "danger"}`}>
            {status}
          </span>
        </div>
      </Col>
      {/* Additional status columns */}
    </Row>
  </Card.Body>
</Card>
```

### Loading and Error States
```tsx
// Loading State
<div className="d-flex justify-content-center align-items-center" style={{ minHeight: '200px' }}>
  <Spinner animation="border" role="status">
    <span className="visually-hidden">Loading...</span>
  </Spinner>
</div>

// Error State
<Alert variant="danger">
  <FaExclamationTriangle className="me-2" />
  Error message here
</Alert>

// Empty State
<div className="text-center text-muted py-4">
  <p>No data available</p>
</div>
```

## Best Practices

### Component Organization
1. **Single Responsibility** - Each component should have one clear purpose
2. **Props Interface** - Define clear TypeScript interfaces for component props
3. **Error Handling** - Always handle loading and error states
4. **Accessibility** - Use proper ARIA labels and semantic HTML

### Styling Guidelines
1. **Bootstrap First** - Use Bootstrap classes before custom CSS
2. **Consistent Spacing** - Use Bootstrap spacing utilities (`mb-4`, `p-3`, etc.)
3. **Responsive Design** - Always consider mobile-first approach
4. **Performance** - Minimize custom CSS and leverage Bootstrap utilities

### State Management
1. **React Query** - Use for server state management
2. **Local State** - Use useState for component-specific state
3. **Form State** - Use controlled components with proper validation
4. **Error Boundaries** - Wrap components to catch and handle errors gracefully 