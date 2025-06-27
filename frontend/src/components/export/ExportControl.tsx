import React, { useState } from 'react';
import { DatePicker } from 'antd';
import { Button, Card, Form, Select, Switch, InputNumber, Space, message, Input, Alert } from 'antd';
import { ExportOutlined } from '@ant-design/icons';
import { useExport } from '../../hooks/useExport';
import { useAgents } from '../../hooks/useAgents';
import dayjs from 'dayjs';
import type { Agent } from '../../services/types';

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
  selectedAgent?: string;
}

interface ExportControlProps {
  // Removed onExportCreated prop as it's no longer needed
}

const ExportControl: React.FC<ExportControlProps> = () => {
  const [form] = Form.useForm();
  const { createExport, isExporting } = useExport();
  const { agents, isLoadingAgents } = useAgents();
  const [messageApi, contextHolder] = message.useMessage();
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  // Handle agent selection change
  const handleAgentChange = (agentId: string) => {
    const agent = agents.find(a => a.id === agentId);
    setSelectedAgent(agent || null);
    
    if (agent && agent.process_filters && agent.process_filters.length > 0) {
      // Auto-populate process filters from agent configuration
      form.setFieldsValue({
        processes: agent.process_filters.join(', '),
        selectedAgent: agentId
      });
    } else {
      // Clear process filters if agent has none
      form.setFieldsValue({
        processes: '',
        selectedAgent: agentId
      });
    }
  };

  // Handle manual process filter change
  const handleProcessChange = () => {
    // Clear agent selection if user manually edits process filters
    form.setFieldsValue({ selectedAgent: undefined });
    setSelectedAgent(null);
  };

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
          processes: '',
          selectedAgent: undefined
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
          name="selectedAgent"
          label="Target Agent (Optional)"
          tooltip="Select an agent to automatically filter data based on its process configuration. This is useful for training data generation."
        >
          <Select
            placeholder="Select an agent for targeted export"
            allowClear
            onChange={handleAgentChange}
            loading={isLoadingAgents}
            showSearch
            filterOption={(input, option) =>
              (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
            }
          >
            {agents.map((agent) => (
              <Select.Option key={agent.id} value={agent.id}>
                {agent.name} ({agent.id})
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        {selectedAgent && (
          <Alert
            message={`Selected Agent: ${selectedAgent.name}`}
            description={
              <div>
                <p><strong>Process Filters:</strong> {selectedAgent.process_filters.length > 0 ? selectedAgent.process_filters.join(', ') : 'All processes'}</p>
                <p><strong>Capabilities:</strong> {selectedAgent.capabilities.join(', ')}</p>
                <p className="text-muted small">The export will be filtered to include only data relevant to this agent's training requirements.</p>
              </div>
            }
            type="info"
            showIcon
            className="mb-3"
          />
        )}

        <Form.Item
          label="Process Filters"
          name="processes"
          tooltip={
            selectedAgent 
              ? "Process filters are automatically set based on the selected agent. You can modify them manually if needed."
              : "Enter process names to filter by. Use comma to separate multiple processes (e.g., 'nginx,apache,postgres'). Leave empty to include all processes."
          }
        >
          <Input 
            placeholder={selectedAgent ? "Auto-populated from agent config" : "e.g., nginx,apache,postgres"}
            onChange={handleProcessChange}
            disabled={isLoadingAgents}
          />
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