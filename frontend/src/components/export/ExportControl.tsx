import React from 'react';
import { DatePicker } from 'antd';
import { Button, Card, Form, Select, Switch, InputNumber, Space, message, Input } from 'antd';
import { ExportOutlined } from '@ant-design/icons';
import { useExport } from '../../hooks/useExport';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;

interface ExportConfig {
  dateRange?: [dayjs.Dayjs, dayjs.Dayjs];
  dataTypes: string[];
  batchSize: number;
  includeMetadata: boolean;
  validationLevel: string;
  outputFormat: string;
  compression: boolean;
  processes: string;
}

interface ExportControlProps {
  // Removed onExportCreated prop as it's no longer needed
}

const ExportControl: React.FC<ExportControlProps> = () => {
  const [form] = Form.useForm();
  const { createExport, isExporting } = useExport();
  const [messageApi, contextHolder] = message.useMessage();

  const handleExport = async (values: ExportConfig) => {
    try {
      // Parse comma-separated process names
      const processes = values.processes
        ? values.processes.split(',').map(p => p.trim()).filter(p => p)
        : [];

      // Handle optional date range
      const exportConfig: any = {
        data_types: values.dataTypes,
        batch_size: values.batchSize,
        include_metadata: values.includeMetadata,
        validation_level: values.validationLevel,
        output_format: values.outputFormat,
        compression: values.compression,
        processes
      };

      // Only add date range if specified
      if (values.dateRange && values.dateRange.length === 2) {
        exportConfig.start_date = values.dateRange[0].toISOString();
        exportConfig.end_date = values.dateRange[1].toISOString();
      }

      await createExport(exportConfig);

      messageApi.success('Export started successfully! Check the Export History tab to monitor progress.');
    } catch (error) {
      messageApi.error('Failed to start export');
      console.error('Export error:', error);
    }
  };

  return (
    <Card title="Export Data" extra={<ExportOutlined />}>
      {contextHolder}
      <Form
        form={form}
        layout="vertical"
        onFinish={handleExport}
        initialValues={{
          dataTypes: ['logs'],
          batchSize: 1000,
          includeMetadata: true,
          validationLevel: 'basic',
          outputFormat: 'json',
          compression: false,
          processes: ''
        }}
      >
        <Form.Item
          name="dateRange"
          label="Date Range (Optional)"
          tooltip="Leave empty to export all data. Select a range to export data within specific dates."
        >
          <RangePicker
            showTime
            format="YYYY-MM-DD HH:mm:ss"
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Form.Item
          name="dataTypes"
          label="Data Types"
          rules={[{ required: true, message: 'Please select data types' }]}
        >
          <Select mode="multiple" placeholder="Select data types">
            <Select.Option value="logs">Logs</Select.Option>
            <Select.Option value="anomalies">Anomalies</Select.Option>
            <Select.Option value="ips">IPs</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          label="Processes"
          name="processes"
          tooltip="Enter process names to filter by. Use comma to separate multiple processes (e.g., 'nginx,apache,postgres'). Leave empty to include all processes."
        >
          <Input placeholder="e.g., nginx,apache,postgres" />
        </Form.Item>

        <Form.Item
          name="batchSize"
          label="Batch Size"
          rules={[{ required: true, message: 'Please enter batch size' }]}
        >
          <InputNumber min={100} max={10000} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          name="validationLevel"
          label="Validation Level"
          rules={[{ required: true, message: 'Please select validation level' }]}
        >
          <Select>
            <Select.Option value="basic">Basic</Select.Option>
            <Select.Option value="strict">Strict</Select.Option>
            <Select.Option value="custom">Custom</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="outputFormat"
          label="Output Format"
          rules={[{ required: true, message: 'Please select output format' }]}
        >
          <Select>
            <Select.Option value="json">JSON</Select.Option>
            <Select.Option value="json.gz">Compressed JSON</Select.Option>
          </Select>
        </Form.Item>

        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Form.Item
            name="includeMetadata"
            valuePropName="checked"
          >
            <Switch checkedChildren="Metadata" unCheckedChildren="No Metadata" />
          </Form.Item>

          <Form.Item
            name="compression"
            valuePropName="checked"
          >
            <Switch checkedChildren="Compressed" unCheckedChildren="Uncompressed" />
          </Form.Item>
        </Space>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={isExporting}
            block
          >
            {isExporting ? 'Exporting...' : 'Start Export'}
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default ExportControl; 