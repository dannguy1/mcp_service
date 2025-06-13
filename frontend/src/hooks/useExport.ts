import { useState } from 'react';
import axios from 'axios';

interface ExportConfig {
  start_date: string;
  end_date: string;
  data_types: string[];
  batch_size: number;
  include_metadata: boolean;
  validation_level: string;
  output_format: string;
  compression: boolean;
}

interface ExportStatus {
  status: 'pending' | 'running' | 'completed' | 'failed';
  record_counts: Record<string, number>;
  file_sizes: Record<string, number>;
  total_records: number;
  total_size: number;
  error_message?: string;
}

interface ExportRecord {
  export_id: string;
  data_version: string;
  export_config: ExportConfig;
  record_count: number;
  file_size: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

interface ListExportsResponse {
  items: ExportRecord[];
  total: number;
}

export const useExport = () => {
  const [isExporting, setIsExporting] = useState(false);

  const createExport = async (config: ExportConfig): Promise<ExportRecord> => {
    setIsExporting(true);
    try {
      const response = await axios.post('/api/export', config);
      return response.data;
    } finally {
      setIsExporting(false);
    }
  };

  const getExportStatus = async (exportId: string): Promise<ExportStatus> => {
    const response = await axios.get(`/api/export/${exportId}`);
    return response.data;
  };

  const listExports = async (page = 1, pageSize = 10): Promise<ListExportsResponse> => {
    const response = await axios.get('/api/export', {
      params: { page, page_size: pageSize }
    });
    return response.data;
  };

  const deleteExport = async (exportId: string): Promise<void> => {
    await axios.delete(`/api/export/${exportId}`);
  };

  return {
    isExporting,
    createExport,
    getExportStatus,
    listExports,
    deleteExport
  };
}; 