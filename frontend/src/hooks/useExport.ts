import { useState } from 'react';
import { endpoints } from '../services/api';

interface ExportConfig {
  start_date?: string;
  end_date?: string;
  data_types: string[];
  filters?: Record<string, any>;
  batch_size: number;
  include_metadata: boolean;
  validation_level: string;
  output_format: string;
  compression: boolean;
  processes?: string[];
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

interface ListExportsResponse {
  items: ExportRecord[];
  total: number;
}

export const useExport = () => {
  const [isExporting, setIsExporting] = useState(false);

  const createExport = async (config: ExportConfig): Promise<ExportRecord> => {
    setIsExporting(true);
    try {
      return await endpoints.createExport(config);
    } finally {
      setIsExporting(false);
    }
  };

  const getExportStatus = async (exportId: string): Promise<ExportStatus> => {
    return await endpoints.getExportStatus(exportId);
  };

  const getExportProgress = async (exportId: string): Promise<any> => {
    return await endpoints.getExportProgress(exportId);
  };

  const listExports = async (page = 1, pageSize = 10): Promise<ListExportsResponse> => {
    const offset = (page - 1) * pageSize;
    const result = await endpoints.listExports({ limit: pageSize, offset });
    return {
      items: result,
      total: result.length // This would need to be updated if the API returns total count
    };
  };

  const deleteExport = async (exportId: string): Promise<void> => {
    await endpoints.deleteExport(exportId);
  };

  const downloadExport = async (exportId: string): Promise<void> => {
    try {
      const blob = await endpoints.downloadExport(exportId);
      
      // Create a filename for the download
      const filename = `export_${exportId}.json`;
      
      // Create a blob URL and trigger download
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
      throw error;
    }
  };

  const cleanupExports = async (): Promise<any> => {
    try {
      return await endpoints.cleanupExports();
    } catch (error) {
      console.error('Cleanup failed:', error);
      throw error;
    }
  };

  const getExportStats = async (): Promise<any> => {
    try {
      return await endpoints.getExportStats();
    } catch (error) {
      console.error('Failed to get stats:', error);
      throw error;
    }
  };

  return {
    isExporting,
    createExport,
    getExportStatus,
    getExportProgress,
    listExports,
    deleteExport,
    downloadExport,
    cleanupExports,
    getExportStats
  };
}; 