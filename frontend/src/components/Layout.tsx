import React, { useState } from 'react';
import { Container, Nav, Offcanvas, Navbar } from 'react-bootstrap';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import {
  DashboardOutlined,
  SettingOutlined,
  ExportOutlined,
  FileTextOutlined,
  AlertOutlined,
  RobotOutlined,
  DesktopOutlined,
  LockOutlined,
  TeamOutlined,
  BarChartOutlined,
} from '@ant-design/icons';
import { FaCog } from 'react-icons/fa';

const Layout: React.FC = () => {
  const [show, setShow] = useState(false);
  const location = useLocation();

  const handleClose = () => setShow(false);
  const handleShow = () => setShow(true);

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
    {
      path: '/anomalies',
      label: 'Anomalies',
      icon: <AlertOutlined />,
    },
    {
      path: '/models',
      label: 'Models',
      icon: <RobotOutlined />,
    },
    {
      path: '/agents',
      label: 'Agents',
      icon: <TeamOutlined />,
    },
    {
      path: '/analysis-stats',
      label: 'Analysis Stats',
      icon: <BarChartOutlined />,
    },
    {
      path: '/server',
      label: 'Server Status',
      icon: <DesktopOutlined />,
    },
    {
      path: '/settings',
      label: 'Settings',
      icon: <SettingOutlined />,
    },
    {
      path: '/export',
      label: 'Export',
      icon: <ExportOutlined />,
    },
    {
      path: '/change-password',
      label: 'Change Password',
      icon: <LockOutlined />,
    },
  ];

  return (
    <div className="d-flex flex-column min-vh-100">
      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#4ade80',
              secondary: '#fff',
            },
          },
          error: {
            duration: 5000,
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
      
      {/* Top Bar */}
      <Navbar bg="dark" variant="dark" className="px-3">
        <Navbar.Brand>
          <button
            className="btn btn-dark me-3"
            onClick={handleShow}
            style={{ border: 'none' }}
          >
            ☰
          </button>
          MCP Service
        </Navbar.Brand>
      </Navbar>

      {/* Sidebar */}
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

      {/* Main Content */}
      <div className="flex-grow-1">
        <Container fluid className="py-4">
          <Outlet />
        </Container>
      </div>
    </div>
  );
};

export default Layout; 