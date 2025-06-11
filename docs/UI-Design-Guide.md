# UI Design Guide

## Table of Contents
1. [Layout Structure](#layout-structure)
2. [Typography](#typography)
3. [Colors](#colors)
4. [Components](#components)
5. [Spacing](#spacing)
6. [Responsive Design](#responsive-design)
7. [Loading States](#loading-states)
8. [Error Handling](#error-handling)
9. [Navigation](#navigation)
10. [Forms](#forms)
11. [Tables](#tables)
12. [Cards](#cards)

## Layout Structure

### Page Layout
- Use a consistent layout structure across all pages
- Main content should be wrapped in a `Container fluid` with `py-4` padding
- Page title should be an `h2` element
- Content sections should be organized in cards with proper spacing

```jsx
<div className="d-flex flex-column min-vh-100">
    {/* Top Bar */}
    <Navbar bg="dark" variant="dark" className="px-3">
        <Navbar.Brand>
            <button className="btn btn-dark me-3" style={{ border: 'none' }}>
                ☰
            </button>
            MCP Service
        </Navbar.Brand>
    </Navbar>

    {/* Main Content */}
    <div className="flex-grow-1">
        <Container fluid className="py-4">
            <h2>Page Title</h2>
            <Card className="mt-4">
                <Card.Header className="bg-white text-dark">
                    <h5 className="mb-0">Section Title</h5>
                </Card.Header>
                <Card.Body>
                    {/* Content */}
                </Card.Body>
            </Card>
        </Container>
    </div>
</div>
```

### Container Usage
- Use `Container fluid` for full-width pages
- Apply consistent padding with `py-4` class
- Maintain consistent spacing between sections
- Ensure proper flex layout with `d-flex flex-column min-vh-100`

## Typography

### Headings
- Page titles: `h2`
- Section headers: `h5` with `mb-0`
- Card headers: `h5` with `mb-0`
- Subsection headers: `h6`

### Text Styles
- Regular text: Default body text
- Muted text: Use `text-muted` class
- Bold text: Use `fw-bold` class
- Small text: Use `small` tag or `text-sm` class

## Colors

### Theme Colors
- Primary: Bootstrap primary blue
- Secondary: Bootstrap secondary gray
- Success: Bootstrap success green
- Danger: Bootstrap danger red
- Warning: Bootstrap warning yellow
- Info: Bootstrap info cyan
- Dark: Bootstrap dark (for top bar and sidebar)

### Severity Colors
- High Severity: `danger`
- Medium Severity: `warning`
- Low Severity: `info`
- Unknown/Default: `secondary`

## Components

### Cards
- Use white background for headers: `bg-white text-dark`
- Consistent padding in body: `Card.Body`
- Proper spacing between cards: `mt-4`
- Card headers should use `h5` with `mb-0`

### Buttons
- Primary actions: `variant="primary"`
- Secondary actions: `variant="outline-primary"`
- Danger actions: `variant="danger"` or `variant="outline-danger"`
- Include icons where appropriate
- Use consistent button sizes

### Badges
- Use for status indicators
- Match severity colors
- Include appropriate spacing: `ms-2`

## Spacing

### Margins
- Between sections: `mt-4`
- Between cards: `mb-4`
- Between form elements: `mb-3`
- Between buttons: `gap-2`

### Padding
- Card body: Default Bootstrap padding
- Container: `py-4`
- Form groups: `mb-3`

## Responsive Design

### Grid System
- Use Bootstrap's grid system
- Default column sizes:
  - Full width: `Col`
  - Half width: `Col md={6}`
  - Third width: `Col md={4}`
  - Quarter width: `Col md={3}`

### Responsive Tables
- Use `Table responsive` for scrollable tables
- Ensure proper column sizing
- Maintain readability on mobile devices

## Loading States

### Loading Spinners
- Center loading spinners: `d-flex justify-content-center align-items-center`
- Use consistent spinner size
- Include loading text where appropriate

```jsx
<div className="d-flex justify-content-center align-items-center" style={{ minHeight: '200px' }}>
    <Spinner animation="border" role="status">
        <span className="visually-hidden">Loading...</span>
    </Spinner>
</div>
```

## Error Handling

### Error Messages
- Use `Alert` component with `variant="danger"`
- Include clear error messages
- Provide retry options where appropriate

```jsx
<Alert variant="danger" className="mt-3">
    <Alert.Heading>Error</Alert.Heading>
    <p>{error}</p>
</Alert>
```

## Navigation

### Top Bar
- Dark theme with light text
- Fixed at the top of the page
- Contains hamburger menu and app title
- Consistent padding with `px-3`

### Sidebar
- Implemented using React Bootstrap's `Offcanvas`
- Dark theme with light text
- Slides in from the left when hamburger is clicked
- Contains navigation items with icons
- Closes on menu item selection or manual close

```jsx
<Offcanvas show={show} onHide={handleClose} className="bg-dark text-light">
    <Offcanvas.Header closeButton closeVariant="white">
        <Offcanvas.Title>MCP Service</Offcanvas.Title>
    </Offcanvas.Header>
    <Offcanvas.Body>
        <Nav className="flex-column">
            {navItems.map((item) => (
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

### Navigation Items
- Include icons for visual hierarchy
- Use consistent spacing with `mb-2`
- Show active state for current route
- Close sidebar on selection

## Forms

### Form Layout
- Use `Form.Group` for form elements
- Consistent spacing between elements
- Clear labels and placeholders

### Form Controls
- Use appropriate input types
- Include validation feedback
- Maintain consistent styling

## Tables

### Table Structure
- Use `Table striped bordered hover responsive`
- Include proper column headers
- Maintain consistent cell padding

### Table Actions
- Align action buttons to the right
- Use appropriate button variants
- Include tooltips where helpful

## Cards

### Card Structure
- White background headers
- Consistent padding
- Clear section separation

### Card Headers
- Use `bg-white text-dark` class
- Include `h5` with `mb-0`
- Maintain consistent spacing

## Best Practices

1. **Consistency**
   - Maintain consistent spacing
   - Use consistent component styling
   - Follow established patterns

2. **Accessibility**
   - Include proper ARIA labels
   - Maintain proper heading hierarchy
   - Ensure sufficient color contrast

3. **Performance**
   - Optimize component rendering
   - Use appropriate loading states
   - Implement proper error boundaries

4. **User Experience**
   - Provide clear feedback
   - Include helpful tooltips
   - Maintain intuitive navigation

5. **Code Organization**
   - Keep components focused
   - Maintain consistent file structure
   - Use proper component composition 