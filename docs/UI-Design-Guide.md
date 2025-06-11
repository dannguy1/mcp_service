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
- Main content should be wrapped in a `div` with appropriate padding
- Page title should be an `h2` element
- Content sections should be organized in cards with proper spacing

```jsx
<div>
    <h2>Page Title</h2>
    <Card className="mt-4">
        <Card.Header className="bg-white text-dark">
            <h5 className="mb-0">Section Title</h5>
        </Card.Header>
        <Card.Body>
            {/* Content */}
        </Card.Body>
    </Card>
</div>
```

### Container Usage
- Use `Container fluid` for full-width pages
- Apply consistent padding with `py-4` class
- Maintain consistent spacing between sections

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

### Sidebar
- Use consistent navigation structure
- Include icons for visual hierarchy
- Maintain active state indicators

### Back Navigation
- Use "Back to List" buttons where appropriate
- Position in top-right corner
- Use `variant="outline-secondary"`

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