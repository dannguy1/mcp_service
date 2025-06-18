import React, { useEffect, useState } from 'react';
import { Table, Card, Tag, Space, Button, Typography, Tooltip } from 'antd';
import { DownloadOutlined, DeleteOutlined, ReloadOutlined, EyeOutlined } from '@ant-design/icons';
import { useExport } from '../../hooks/useExport';
import dayjs from 'dayjs';

const { Text } = Typography;

interface ExportRecord {
  export_id: string;
  created_at: string | null;
  updated_at: string | null;
  status: 'pending' | 'running' | 'completed' | 'failed';
  data_types: string[];
  config: any;
  record_counts: Record<string, number>;
  file_sizes: Record<string, number>;
  error_message: string | null;
  is_compressed: boolean;
  total_records: number;
  total_size: number;
}

interface ExportHistoryProps {
  onExportSelect?: (exportId: string) => void;
}

const ExportHistory: React.FC<ExportHistoryProps> = ({ onExportSelect }) => {
  const { listExports, deleteExport, downloadExport } = useExport();
  const [exports, setExports] = useState<ExportRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);
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

  const handleDownload = async (exportId: string) => {
    setDownloading(exportId);
    try {
      await downloadExport(exportId);
    } catch (error) {
      console.error('Failed to download export:', error);
      // You could add a notification here to show the error to the user
    } finally {
      setDownloading(null);
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
      render: (record: ExportRecord) => {
        const config = record.config || {};
        const startDate = config.start_date;
        const endDate = config.end_date;
        
        if (!startDate && !endDate) {
          return <Text type="secondary">No date range specified</Text>;
        }
        
        return (
          <Space direction="vertical">
            {startDate && <Text>From: {dayjs(startDate).format('YYYY-MM-DD HH:mm')}</Text>}
            {endDate && <Text>To: {dayjs(endDate).format('YYYY-MM-DD HH:mm')}</Text>}
          </Space>
        );
      }
    },
    {
      title: 'Data Types',
      key: 'data_types',
      render: (record: ExportRecord) => {
        const dataTypes = record.data_types || [];
        if (dataTypes.length === 0) {
          return <Text type="secondary">No data types specified</Text>;
        }
        
        return (
          <Space>
            {dataTypes.map(type => (
              <Tag key={type} color="blue">{type}</Tag>
            ))}
          </Space>
        );
      }
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
      dataIndex: 'total_records',
      key: 'total_records',
      render: (count: number) => (count || 0).toLocaleString()
    },
    {
      title: 'Size',
      dataIndex: 'total_size',
      key: 'total_size',
      render: (size: number) => {
        const sizeInBytes = size || 0;
        if (sizeInBytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(sizeInBytes) / Math.log(k));
        return `${parseFloat((sizeInBytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
      }
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string | null) => {
        if (!date) return <Text type="secondary">N/A</Text>;
        return dayjs(date).format('YYYY-MM-DD HH:mm:ss');
      }
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
                loading={downloading === record.export_id}
                disabled={downloading !== null}
                onClick={() => handleDownload(record.export_id)}
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