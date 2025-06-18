import React from 'react';
import { Tabs, Space, Typography } from 'antd';
import ExportControl from '../components/export/ExportControl';
import ExportHistory from '../components/export/ExportHistory';
import ExportCleanup from '../components/export/ExportCleanup';

const { Title } = Typography;

const ExportPage: React.FC = () => {
  const items = [
    {
      key: 'control',
      label: 'New Export',
      children: (
        <Space direction="vertical" style={{ width: '100%' }}>
          <Title level={2}>Create New Export</Title>
          <ExportControl />
        </Space>
      )
    },
    {
      key: 'history',
      label: 'Export History',
      children: (
        <Space direction="vertical" style={{ width: '100%' }}>
          <Title level={2}>Export History</Title>
          <ExportHistory />
        </Space>
      )
    },
    {
      key: 'cleanup',
      label: 'Management',
      children: (
        <Space direction="vertical" style={{ width: '100%' }}>
          <Title level={2}>Export Management</Title>
          <ExportCleanup />
        </Space>
      )
    }
  ];

  return (
    <Tabs
      defaultActiveKey="control"
      items={items}
      style={{ background: '#fff', padding: '24px', borderRadius: '8px' }}
    />
  );
};

export default ExportPage; 