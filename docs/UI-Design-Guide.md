# UI Design Guide

## Table of Contents
1. [Layout Structure](#layout-structure)
2. [Navigation](#navigation)
3. [Components](#components)
4. [Styling](#styling)
5. [Responsive Design](#responsive-design)

## Layout Structure

### Main Layout
- Dark-themed top navigation bar with hamburger menu
- Off-canvas sidebar for navigation
- Fluid container for main content with consistent padding
- Error boundary wrapper for graceful error handling

### Page Structure
- Page title as `h2` element
- Content organized in cards with white headers
- Consistent spacing between sections
- Loading and error states handled uniformly

## Navigation

### Top Bar
- Dark theme (`bg-dark`)
- Hamburger menu toggle
- App title
- Fixed position with proper z-index

### Sidebar
- Off-canvas component
- Dark theme with light text
- Navigation items with icons
- Active state highlighting
- Closes on selection or manual close

### Navigation Items
- Dashboard
- Logs
- Anomalies
- Models
- Server Status
- Settings
- Export
- Change Password

## Components

### Cards
- White background
- Subtle shadow
- White headers with bottom border
- Consistent padding
- Hover effect with slight elevation

### Tables
- Responsive design
- Striped rows
- Hover effect
- Vertical alignment for content
- Action buttons in last column

### Forms
- Consistent spacing between elements
- Clear labels
- Proper validation states
- Responsive layout
- Submit buttons with loading states

### Status Indicators
- Badges for status display
- Color coding:
  - Success: Green
  - Warning: Yellow
  - Error: Red
  - Info: Blue
  - Secondary: Gray

## Styling

### Colors
- Primary: Bootstrap blue
- Success: Green
- Warning: Yellow
- Danger: Red
- Info: Blue
- Dark: For navigation
- Light: For backgrounds

### Typography
- System font stack
- Consistent heading hierarchy
- Proper line heights
- Muted text for secondary information

### Spacing
- Consistent padding in containers
- Proper margins between sections
- Gap between buttons
- Responsive spacing adjustments

## Responsive Design

### Breakpoints
- Mobile: < 768px
- Tablet: 768px - 992px
- Desktop: > 992px

### Mobile Adaptations
- Collapsible sidebar
- Stacked layouts
- Adjusted spacing
- Touch-friendly targets

### Tablet Adaptations
- Sidebar becomes fixed
- Grid adjustments
- Maintained readability

### Desktop Optimizations
- Fixed sidebar
- Multi-column layouts
- Hover effects
- Optimal spacing 