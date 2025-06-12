import React, { useEffect, useState } from 'react';
import { Card, Progress, Tag, Space, Typography, Alert } from 'antd';
import { ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined } from '@ant-design/icons';
import { useExport } from '../../hooks/useExport';

const { Text } = Typography;

interface ExportStatusProps {
  exportId: string;
}

interface ExportStatus {
  status: 'pending' | 'running' | 'completed' | 'failed';
  record_counts: Record<string, number>;
  file_sizes: Record<string, number>;
  total_records: number;
  total_size: number;
  error_message?: string;
}

const ExportStatus: React.FC<ExportStatusProps> = ({ exportId }) => {
  const { getExportStatus } = useExport();
  const [status, setStatus] = useState<ExportStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const pollStatus = async () => {
      try {
        const result = await getExportStatus(exportId);
        setStatus(result);
        if (result.status === 'failed') {
          setError(result.error_message || 'Export failed');
        }
      } catch (err) {
        setError('Failed to fetch export status');
        console.error('Status polling error:', err);
      }
    };

    const interval = setInterval(pollStatus, 5000);
    pollStatus(); // Initial poll

    return () => clearInterval(interval);
  }, [exportId, getExportStatus]);

  if (!status) {
    return <Card loading />;
  }

  const getStatusIcon = () => {
    switch (status.status) {
      case 'pending':
        return <ClockCircleOutlined style={{ color: '#faad14' }} />;
      case 'running':
        return <LoadingOutlined style={{ color: '#1890ff' }} />;
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#f5222d' }} />;
      default:
        return null;
    }
  };

  const getStatusColor = () => {
    switch (status.status) {
      case 'pending':
        return 'warning';
      case 'running':
        return 'processing';
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  return (
    <Card title="Export Status">
      <Space direction="vertical" style={{ width: '100%' }}>
        <Space>
          {getStatusIcon()}
          <Tag color={getStatusColor()}>{status.status.toUpperCase()}</Tag>
        </Space>

        {error && (
          <Alert
            message="Export Error"
            description={error}
            type="error"
            showIcon
          />
        )}

        {status.status === 'running' && (
          <Progress
            percent={Math.round((status.total_records / 1000) * 100)}
            status="active"
            format={percent => `${percent}%`}
          />
        )}

        <Space direction="vertical" style={{ width: '100%' }}>
          {Object.entries(status.record_counts).map(([type, count]) => (
            <div key={type}>
              <Text strong>{type}:</Text>
              <Space>
                <Text>{count} records</Text>
                <Text type="secondary">
                  ({formatFileSize(status.file_sizes[type] || 0)})
                </Text>
              </Space>
            </div>
          ))}
        </Space>

        <Space direction="vertical" style={{ width: '100%' }}>
          <Text strong>Total Records:</Text>
          <Text>{status.total_records}</Text>
          <Text strong>Total Size:</Text>
          <Text>{formatFileSize(status.total_size)}</Text>
        </Space>
      </Space>
    </Card>
  );
};

export default ExportStatus; 