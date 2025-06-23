import React from 'react';
import { Card, Nav, Tab } from 'react-bootstrap';
import type { TabItem } from './types';

interface TabbedLayoutProps {
  title: string;
  tabs: TabItem[];
  activeTab?: string;
  onTabChange?: (key: string) => void;
  className?: string;
}

const TabbedLayout: React.FC<TabbedLayoutProps> = ({
  title,
  tabs,
  activeTab,
  onTabChange,
  className = ''
}) => {
  const defaultActiveTab = activeTab || tabs[0]?.key || '';

  return (
    <div className={`tabbed-layout ${className}`}>
      <h2 className="mb-4">{title}</h2>

      <Card>
        <Card.Body>
          <Tab.Container 
            activeKey={defaultActiveTab} 
            onSelect={(k) => onTabChange?.(k || defaultActiveTab)}
          >
            <div>
              <Nav variant="tabs" className="mb-3">
                {tabs.map((tab) => (
                  <Nav.Item key={tab.key}>
                    <Nav.Link eventKey={tab.key}>
                      {tab.icon && <span className="me-2">{tab.icon}</span>}
                      {tab.title}
                    </Nav.Link>
                  </Nav.Item>
                ))}
              </Nav>
              <Tab.Content>
                {tabs.map((tab) => (
                  <Tab.Pane key={tab.key} eventKey={tab.key}>
                    {tab.content}
                  </Tab.Pane>
                ))}
              </Tab.Content>
            </div>
          </Tab.Container>
        </Card.Body>
      </Card>
    </div>
  );
};

// Export both the component and the interface
export default TabbedLayout;
export type { TabItem }; 