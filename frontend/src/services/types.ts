// API Types
export interface SystemStatus {
  status: string;
  uptime: string;
  version: string;
  metrics: {
    cpu_usage: number;
    memory_usage: number;
    response_time: number;
  };
  connections: {
    mcp_service: {
      status: 'connected' | 'disconnected' | 'error';
      last_check: string;
      error?: string;
    };
    backend_service: {
      status: 'connected' | 'disconnected' | 'error';
      last_check: string;
      error?: string;
    };
    data_source: {
      status: 'connected' | 'disconnected' | 'error';
      last_check: string;
      error?: string;
    };
    database: {
      status: 'connected' | 'disconnected' | 'error';
      last_check: string;
      error?: string;
    };
    model_service: {
      status: 'connected' | 'disconnected' | 'error';
      last_check: string;
      error?: string;
    };
    redis: {
      status: 'connected' | 'disconnected' | 'error';
      last_check: string;
      error?: string;
    };
  };
}

export interface ServerStats {
  cpu: {
    usage: number;
    cores: number;
    temperature: number;
  };
  memory: {
    total: number;
    used: number;
    free: number;
  };
  disk: {
    total: number;
    used: number;
    free: number;
  };
  uptime: string;
}

export interface Anomaly {
  id: string;
  timestamp: string;
  type: string;
  severity: number;
  description: string;
  status: 'detected' | 'investigating' | 'resolved';
}

export interface LogEntry {
  id: number;
  timestamp: string;
  level: string;
  program: string;
  message: string;
}

export interface Model {
  id: string;
  version: string;
  created_at: string;
  metrics: {
    accuracy: number;
    false_positive_rate: number;
    false_negative_rate: number;
  };
  status: 'active' | 'inactive' | 'error';
}

export interface ModelInfo extends Model {
  agent_info?: {
    status: string;
    is_running: boolean;
    last_run: string | null;
    capabilities: string[];
    description: string;
    model_path: string | null;
    programs: string[];
  };
}

// Enhanced Model Management Types
export interface ModelValidationResult {
  is_valid: boolean;
  score: number;
  errors: string[];
  warnings: string[];
  recommendations: string[];
  metadata?: any;
}

export interface ModelPerformanceMetrics {
  model_version: string;
  total_inferences: number;
  last_updated: string;
  performance_metrics: {
    avg_inference_time: number;
    max_inference_time: number;
    min_inference_time: number;
    avg_anomaly_score: number;
    anomaly_rate: number;
    total_anomalies: number;
  };
}

export interface ModelDriftResult {
  drift_detected: boolean;
  drift_score: number;
  confidence: number;
  indicators: {
    anomaly_rate_change: number;
    score_distribution_change: number;
    inference_time_change: number;
  };
  threshold: number;
}

export interface ModelTransferHistory {
  transfer_id: string;
  original_path: string;
  local_path: string;
  transferred_at: string;
  status: string;
}

export interface ModelCompatibilityResult {
  compatible: boolean;
  missing_features: string[];
  extra_features: string[];
  feature_mismatch_score: number;
  error?: string;
}

export interface ModelValidationReport {
  model_path: string;
  validation_timestamp: string;
  quality_validation: ModelValidationResult;
  model_info: any;
  training_info: any;
  evaluation_info: any;
  recommendations: string[];
  error?: string;
}

export interface ModelPerformanceReport {
  model_version: string;
  report_timestamp: string;
  performance_summary: ModelPerformanceMetrics;
  drift_analysis: ModelDriftResult;
  recommendations: string[];
  error?: string;
}

export interface DashboardData {
  system_status: SystemStatus;
  recent_anomalies: Anomaly[];
  performance_metrics: SystemStatus["metrics"];
}

export interface PaginationInfo {
  current_page: number;
  has_next: boolean;
  has_prev: boolean;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface LogsData {
  logs: LogEntry[];
  pagination: PaginationInfo;
}

export interface LogsResponse {
  logs: Log[];
  total: number;
  filters: {
    severity: string[];
    programs: string[];
  };
}

export interface ModelsResponse {
  models: Model[];
  total: number;
}

export interface Log {
  id: string;
  device_id: string;
  device_ip: string;
  timestamp: string;
  level: string;
  process: string;
  message: string;
  raw_message: string;
  structured_data: any;
  pushed_to_ai: boolean;
  pushed_at: string | null;
  push_attempts: number;
  last_push_error: string | null;
}

export interface Service {
  name: string;
  status: 'running' | 'stopped' | 'error';
  uptime: string;
  memoryUsage: number;
}

export interface ServerStatus {
  status: string;
  version: string;
  uptime: string;
  components: {
    database: string;
    model: string;
    cache: string;
  };
  metrics: {
    cpu_usage: number;
    memory_usage: number;
    response_time: number;
  };
  services: Service[];
}

export interface ChangePasswordForm {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}