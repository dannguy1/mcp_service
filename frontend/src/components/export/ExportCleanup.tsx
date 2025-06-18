import React, { useState, useEffect } from 'react';
import { Card, Button, Space, Typography, Alert, Statistic, Row, Col, message } from 'antd';
import { DeleteOutlined, ReloadOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { useExport } from '../../hooks/useExport';

const { Text, Title } = Typography;

interface ExportStats {
  total_files: number;
  total_size_mb: number;
  total_metadata: number;
  old_files: number;
  exports_dir: string;
  max_age_days: number;
}

const ExportCleanup: React.FC = () => {
  const { cleanupExports, getExportStats } = useExport();
  const [stats, setStats] = useState<ExportStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [cleanupLoading, setCleanupLoading] = useState(false);
  const [messageApi, contextHolder] = message.useMessage();

  const fetchStats = async () => {
    setLoading(true);
    try {
      const statsData = await getExportStats();
      setStats(statsData);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      messageApi.error('Failed to fetch export statistics');
    } finally {
      setLoading(false);
    }
  };

  const handleCleanup = async () => {
    setCleanupLoading(true);
    try {
      const result = await cleanupExports();
      messageApi.success(`Cleanup completed: ${result.details.deleted_files} files, ${result.details.deleted_metadata} metadata entries deleted`);
      fetchStats(); // Refresh stats after cleanup
    } catch (error) {
      console.error('Cleanup failed:', error);
      messageApi.error('Failed to perform cleanup');
    } finally {
      setCleanupLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <Card title="Export Management" extra={<InfoCircleOutlined />}>
      {contextHolder}
      
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* Statistics */}
        <Card title="Export Statistics" size="small">
          {stats ? (
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="Total Files"
                  value={stats.total_files}
                  loading={loading}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Total Size"
                  value={stats.total_size_mb}
                  suffix="MB"
                  loading={loading}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Metadata Entries"
                  value={stats.total_metadata}
                  loading={loading}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Old Files"
                  value={stats.old_files}
                  loading={loading}
                  valueStyle={{ color: stats.old_files > 0 ? '#cf1322' : '#3f8600' }}
                />
              </Col>
            </Row>
          ) : (
            <Text type="secondary">Loading statistics...</Text>
          )}
          
          {stats && (
            <div style={{ marginTop: 16 }}>
              <Text type="secondary">
                Exports directory: {stats.exports_dir} | Max age: {stats.max_age_days} days
              </Text>
            </div>
          )}
        </Card>

        {/* Cleanup Actions */}
        <Card title="Cleanup Actions" size="small">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Alert
              message="Automatic Cleanup"
              description="Export files older than 7 days are automatically cleaned up. You can also manually trigger cleanup below."
              type="info"
              showIcon
            />
            
            <Space>
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchStats}
                loading={loading}
              >
                Refresh Stats
              </Button>
              
              <Button
                type="primary"
                danger
                icon={<DeleteOutlined />}
                onClick={handleCleanup}
                loading={cleanupLoading}
                disabled={!stats || stats.old_files === 0}
              >
                Clean Up Old Exports
              </Button>
            </Space>
            
            {stats && stats.old_files > 0 && (
              <Alert
                message={`${stats.old_files} old export files found`}
                description="These files are older than 7 days and can be safely deleted."
                type="warning"
                showIcon
              />
            )}
          </Space>
        </Card>
      </Space>
    </Card>
  );
};

export default ExportCleanup; 