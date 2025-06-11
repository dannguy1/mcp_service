import React from "react";
import { Container, Nav, Offcanvas } from "react-bootstrap";
import { Link, Outlet, useLocation } from "react-router-dom";

const MainLayout: React.FC = () => {
  const [show, setShow] = React.useState(false);
  const location = useLocation();

  const handleClose = () => setShow(false);
  const handleShow = () => setShow(true);

  const navItems = [
    { path: "/", label: "Dashboard", icon: "📊" },
    { path: "/logs", label: "Logs", icon: "📝" },
    { path: "/anomalies", label: "Anomalies", icon: "⚠️" },
    { path: "/models", label: "Models", icon: "🤖" },
    { path: "/server", label: "Server Status", icon: "🖥️" },
    { path: "/settings", label: "Settings", icon: "⚙️" },
  ];

  return (
    <div className="d-flex">
      {/* Sidebar */}
      <div className="sidebar bg-dark text-light" style={{ width: "250px", minHeight: "100vh" }}>
        <div className="p-3">
          <h4 className="text-light mb-4">MCP Service</h4>
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
        </div>
      </div>

      {/* Mobile Menu Button */}
      <button
        className="btn btn-dark d-md-none position-fixed"
        style={{ top: "10px", left: "10px", zIndex: 1000 }}
        onClick={handleShow}
      >
        ☰
      </button>

      {/* Mobile Menu */}
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

      {/* Main Content */}
      <div className="flex-grow-1">
        <Container fluid className="py-4">
          <Outlet />
        </Container>
      </div>
    </div>
  );
};

export default MainLayout;
