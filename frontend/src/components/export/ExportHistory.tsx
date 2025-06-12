import React, { useEffect, useState } from 'react';
import { Table, Card, Tag, Space, Button, Typography, Tooltip } from 'antd';
import { DownloadOutlined, DeleteOutlined, ReloadOutlined, EyeOutlined } from '@ant-design/icons';
import { useExport } from '../../hooks/useExport';
import dayjs from 'dayjs';

const { Text } = Typography;

interface ExportRecord {
  export_id: string;
  data_version: string;
  export_config: {
    start_date: string;
    end_date: string;
    data_types: string[];
    batch_size: number;
    include_metadata: boolean;
    validation_level: string;
    output_format: string;
    compression: boolean;
  };
  record_count: number;
  file_size: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

interface ExportHistoryProps {
  onExportSelect?: (exportId: string) => void;
}

const ExportHistory: React.FC<ExportHistoryProps> = ({ onExportSelect }) => {
  const { listExports, deleteExport } = useExport();
  const [exports, setExports] = useState<ExportRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });

  const fetchExports = async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const result = await listExports(page, pageSize);
      setExports(result.items);
      setPagination({
        current: page,
        pageSize,
        total: result.total
      });
    } catch (error) {
      console.error('Failed to fetch exports:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExports();
  }, []);

  const handleDelete = async (exportId: string) => {
    try {
      await deleteExport(exportId);
      fetchExports(pagination.current, pagination.pageSize);
    } catch (error) {
      console.error('Failed to delete export:', error);
    }
  };

  const handleViewStatus = (exportId: string) => {
    onExportSelect?.(exportId);
  };

  const columns = [
    {
      title: 'Export ID',
      dataIndex: 'export_id',
      key: 'export_id',
      render: (id: string) => (
        <Tooltip title={id}>
          <Text copyable>{id.substring(0, 8)}...</Text>
        </Tooltip>
      )
    },
    {
      title: 'Date Range',
      key: 'date_range',
      render: (record: ExportRecord) => (
        <Space direction="vertical">
          <Text>From: {dayjs(record.export_config.start_date).format('YYYY-MM-DD HH:mm')}</Text>
          <Text>To: {dayjs(record.export_config.end_date).format('YYYY-MM-DD HH:mm')}</Text>
        </Space>
      )
    },
    {
      title: 'Data Types',
      key: 'data_types',
      render: (record: ExportRecord) => (
        <Space>
          {record.export_config.data_types.map(type => (
            <Tag key={type} color="blue">{type}</Tag>
          ))}
        </Space>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors = {
          pending: 'warning',
          running: 'processing',
          completed: 'success',
          failed: 'error'
        };
        return <Tag color={colors[status as keyof typeof colors]}>{status.toUpperCase()}</Tag>;
      }
    },
    {
      title: 'Records',
      dataIndex: 'record_count',
      key: 'record_count',
      render: (count: number) => count.toLocaleString()
    },
    {
      title: 'Size',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (size: number) => {
        if (size === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(size) / Math.log(k));
        return `${parseFloat((size / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
      }
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss')
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: ExportRecord) => (
        <Space>
          <Tooltip title="View Status">
            <Button
              icon={<EyeOutlined />}
              onClick={() => handleViewStatus(record.export_id)}
            />
          </Tooltip>
          {record.status === 'completed' && (
            <Tooltip title="Download">
              <Button
                icon={<DownloadOutlined />}
                onClick={() => window.open(`/api/export/${record.export_id}/download`)}
              />
            </Tooltip>
          )}
          <Tooltip title="Delete">
            <Button
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record.export_id)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  return (
    <Card
      title="Export History"
      extra={
        <Button
          icon={<ReloadOutlined />}
          onClick={() => fetchExports(pagination.current, pagination.pageSize)}
        >
          Refresh
        </Button>
      }
    >
      <Table
        columns={columns}
        dataSource={exports}
        rowKey="export_id"
        pagination={pagination}
        loading={loading}
        onChange={(pagination) => {
          fetchExports(pagination.current || 1, pagination.pageSize || 10);
        }}
      />
    </Card>
  );
};

export default ExportHistory; 