import React, { useState } from 'react';
import { Tabs, Space, Typography } from 'antd';
import ExportControl from '../components/export/ExportControl';
import ExportStatus from '../components/export/ExportStatus';
import ExportHistory from '../components/export/ExportHistory';

const { Title } = Typography;

const ExportPage: React.FC = () => {
  const [activeExportId, setActiveExportId] = useState<string | null>(null);

  const handleExportCreated = (exportId: string) => {
    setActiveExportId(exportId);
  };

  const items = [
    {
      key: 'control',
      label: 'New Export',
      children: (
        <Space direction="vertical" style={{ width: '100%' }}>
          <Title level={2}>Create New Export</Title>
          <ExportControl onExportCreated={handleExportCreated} />
        </Space>
      )
    },
    {
      key: 'status',
      label: 'Export Status',
      children: activeExportId ? (
        <Space direction="vertical" style={{ width: '100%' }}>
          <Title level={2}>Export Status</Title>
          <ExportStatus exportId={activeExportId} />
        </Space>
      ) : (
        <Typography.Text type="secondary">
          No active export. Create a new export to view status.
        </Typography.Text>
      )
    },
    {
      key: 'history',
      label: 'Export History',
      children: (
        <Space direction="vertical" style={{ width: '100%' }}>
          <Title level={2}>Export History</Title>
          <ExportHistory onExportSelect={setActiveExportId} />
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