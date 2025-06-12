import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Progress, Typography } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { useExport } from '../../hooks/useExport';

const { Title } = Typography;

interface ExportMetrics {
  total_exports: number;
  successful_exports: number;
  failed_exports: number;
  total_records: number;
  total_size: number;
  average_duration: number;
  success_rate: number;
  data_type_distribution: Record<string, number>;
  export_trend: {
    date: string;
    count: number;
    success_rate: number;
  }[];
}

const ExportMetrics: React.FC = () => {
  const { getExportMetrics } = useExport();
  const [metrics, setMetrics] = useState<ExportMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const data = await getExportMetrics();
        setMetrics(data);
      } catch (error) {
        console.error('Failed to fetch export metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 60000); // Refresh every minute

    return () => clearInterval(interval);
  }, [getExportMetrics]);

  if (!metrics) {
    return <Card loading />;
  }

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  return (
    <Card title="Export Metrics" loading={loading}>
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Exports"
              value={metrics.total_exports}
              valueStyle={{ color: '#3f8600' }}
              prefix={<ArrowUpOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Success Rate"
              value={metrics.success_rate}
              precision={1}
              suffix="%"
              valueStyle={{ color: metrics.success_rate >= 90 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Records"
              value={metrics.total_records}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Size"
              value={formatFileSize(metrics.total_size)}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="Export Status Distribution">
            <Progress
              percent={metrics.success_rate}
              success={{ percent: metrics.success_rate }}
              format={percent => `${percent}% Success`}
            />
            <Progress
              percent={100 - metrics.success_rate}
              status="exception"
              format={percent => `${percent}% Failed`}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Data Type Distribution">
            {Object.entries(metrics.data_type_distribution).map(([type, count]) => (
              <div key={type} style={{ marginBottom: 8 }}>
                <Title level={5}>{type}</Title>
                <Progress
                  percent={Math.round((count / metrics.total_records) * 100)}
                  format={percent => `${percent}% (${count.toLocaleString()} records)`}
                />
              </div>
            ))}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="Export Performance">
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="Average Duration"
                  value={formatDuration(metrics.average_duration)}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Successful Exports"
                  value={metrics.successful_exports}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Failed Exports"
                  value={metrics.failed_exports}
                  valueStyle={{ color: '#cf1322' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </Card>
  );
};

export default ExportMetrics; 