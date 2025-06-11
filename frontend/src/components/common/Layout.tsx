import React from 'react';
import { Container, Navbar, Nav } from 'react-bootstrap';
import { Link, Outlet } from 'react-router-dom';

const Layout: React.FC = () => {
  return (
    <>
      <Navbar bg="dark" variant="dark" expand="lg">
        <Container>
          <Navbar.Brand as={Link} to="/">MCP Service</Navbar.Brand>
          <Navbar.Toggle aria-controls="basic-navbar-nav" />
          <Navbar.Collapse id="basic-navbar-nav">
            <Nav className="me-auto">
              <Nav.Link as={Link} to="/">Dashboard</Nav.Link>
              <Nav.Link as={Link} to="/logs">Logs</Nav.Link>
              <Nav.Link as={Link} to="/models">Models</Nav.Link>
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      <Container className="mt-4">
        <Outlet />
      </Container>
    </>
  );
};

export default Layout; 