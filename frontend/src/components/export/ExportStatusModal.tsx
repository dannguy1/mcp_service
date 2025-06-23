import React, { useEffect, useState } from 'react';
import { Modal, Card, Descriptions, Progress, Tag, Space, Typography, Alert, Spin } from 'antd';
import { useExport } from '../../hooks/useExport';
import dayjs from 'dayjs';

const { Text, Title } = Typography;

interface ExportStatusModalProps {
  visible: boolean;
  exportId: string | null;
  onClose: () => void;
}

interface ExportProgress {
  export_id: string;
  status: string;
  progress: any;
  current_batch: number;
  total_batches: number;
  processed_records: number;
  total_records: number;
  start_time: string | null;
  end_time: string | null;
  error_message: string | null;
}

const ExportStatusModal: React.FC<ExportStatusModalProps> = ({
  visible,
  exportId,
  onClose
}) => {
  const { getExportProgress, getExportStatus } = useExport();
  const [progress, setProgress] = useState<ExportProgress | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (visible && exportId) {
      fetchExportData();
    }
  }, [visible, exportId]);

  const fetchExportData = async () => {
    if (!exportId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Fetch both progress and status
      const [progressData, statusData] = await Promise.all([
        getExportProgress(exportId),
        getExportStatus(exportId)
      ]);
      
      setProgress(progressData);
      setStatus(statusData);
    } catch (err) {
      console.error('Failed to fetch export data:', err);
      setError('Failed to load export status');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      pending: 'warning',
      running: 'processing',
      completed: 'success',
      failed: 'error'
    };
    return colors[status as keyof typeof colors] || 'default';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const renderProgressDetails = () => {
    if (!progress) return null;

    const progressValue = typeof progress.progress === 'number' ? progress.progress : 0;
    
    return (
      <Card title="Progress Details" size="small">
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text strong>Overall Progress:</Text>
            <Progress 
              percent={progressValue} 
              status={progress.status === 'failed' ? 'exception' : undefined}
              style={{ marginTop: 8 }}
            />
          </div>
          
          {progress.current_batch && progress.total_batches && (
            <div>
              <Text strong>Batch Progress:</Text>
              <Progress 
                percent={Math.round((progress.current_batch / progress.total_batches) * 100)}
                format={() => `${progress.current_batch}/${progress.total_batches}`}
                style={{ marginTop: 8 }}
              />
            </div>
          )}
          
          <Descriptions size="small" column={2}>
            <Descriptions.Item label="Processed Records">
              {progress.processed_records?.toLocaleString() || '0'}
            </Descriptions.Item>
            <Descriptions.Item label="Total Records">
              {progress.total_records?.toLocaleString() || '0'}
            </Descriptions.Item>
            <Descriptions.Item label="Start Time">
              {progress.start_time ? dayjs(progress.start_time).format('YYYY-MM-DD HH:mm:ss') : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="End Time">
              {progress.end_time ? dayjs(progress.end_time).format('YYYY-MM-DD HH:mm:ss') : 'N/A'}
            </Descriptions.Item>
          </Descriptions>
        </Space>
      </Card>
    );
  };

  const renderStatusDetails = () => {
    if (!status) return null;

    return (
      <Card title="Status Information" size="small">
        <Descriptions size="small" column={1}>
          <Descriptions.Item label="Export ID">
            <Text copyable>{status.export_id}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Status">
            <Tag color={getStatusColor(status.status)}>
              {status.status?.toUpperCase()}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Created">
            {status.created_at ? dayjs(status.created_at).format('YYYY-MM-DD HH:mm:ss') : 'N/A'}
          </Descriptions.Item>
          <Descriptions.Item label="Updated">
            {status.updated_at ? dayjs(status.updated_at).format('YYYY-MM-DD HH:mm:ss') : 'N/A'}
          </Descriptions.Item>
          <Descriptions.Item label="Total Records">
            {status.total_records?.toLocaleString() || '0'}
          </Descriptions.Item>
          <Descriptions.Item label="Total Size">
            {formatFileSize(status.total_size || 0)}
          </Descriptions.Item>
          {status.error_message && (
            <Descriptions.Item label="Error Message">
              <Text type="danger">{status.error_message}</Text>
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>
    );
  };

  return (
    <Modal
      title={
        <Space>
          <Title level={4} style={{ margin: 0 }}>
            Export Status
          </Title>
          {exportId && (
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {exportId.substring(0, 8)}...
            </Text>
          )}
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={800}
      destroyOnClose
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text>Loading export status...</Text>
          </div>
        </div>
      ) : error ? (
        <Alert
          message="Error"
          description={error}
          type="error"
          showIcon
        />
      ) : (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {renderStatusDetails()}
          {renderProgressDetails()}
        </Space>
      )}
    </Modal>
  );
};

export default ExportStatusModal; 