import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, Table, Badge, Tag } from 'antd';
import { endpoints } from '../services/api';
import type { Anomaly } from '../services/types';

const Anomalies: React.FC = () => {
  const { data: anomalies, isLoading, error } = useQuery<Anomaly[]>({
    queryKey: ['anomalies'],
    queryFn: () => endpoints.getAnomalies(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const columns = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (text: string) => new Date(text).toLocaleString(),
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => <Tag color="blue">{type}</Tag>,
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity: number) => (
        <Badge
          color={
            severity >= 8 ? 'red' :
            severity >= 5 ? 'orange' :
            severity >= 3 ? 'yellow' : 'green'
          }
          text={`${severity}/10`}
        />
      ),
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'resolved' ? 'green' : 'orange'}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
  ];

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <p>Loading anomalies...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <div style={{ color: 'red' }}>
          Error loading anomalies: {error instanceof Error ? error.message : 'Unknown error'}
        </div>
      </Card>
    );
  }

  return (
    <div>
      <h2 className="mb-4">Detected Anomalies</h2>
      <Card>
        <Table
          dataSource={anomalies}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
};

export default Anomalies; 