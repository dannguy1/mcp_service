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
  device_id?: string;
  model_version?: string;
  details?: any;
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

export interface ModelValidationSummary {
  required_files_present: string[];
  optional_files_missing: string[];
  warnings: string[];
}

export interface ModelImportResult {
  version: string;
  status: string;
  path: string;
  imported_at: string;
  validation_summary?: ModelValidationSummary;
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
  cpuUsage?: number;
}

export interface ServerStatus {
  status: string;
  version: string;
  uptime: string;
  load_average?: string;
  total_memory?: string;
  available_memory?: string;
  network_interfaces?: string;
  active_connections?: string;
  bytes_received?: string;
  bytes_sent?: string;
  disk_usage?: number;
  components: {
    database: string;
    model: string;
    cache: string;
    [key: string]: string;
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

export interface DatabaseConfig {
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
  min_connections?: number;
  max_connections?: number;
  pool_timeout?: number;
}

export interface DatabaseTestResult {
  status: 'success' | 'error';
  message: string;
  details?: {
    host: string;
    port: number;
    database: string;
    user: string;
    error_type?: string;
    test_query_result?: any;
    raw_error?: string;
  };
}

// Agent Management Types
export interface Agent {
  id: string;
  name: string;
  status: string;
  is_running: boolean;
  last_run: string | null;
  capabilities: string[];
  process_filters: string[];
  description: string;
  model_path: string | null;
  agent_type: string;
  config: Record<string, any>;
  model_updated_at?: string;
  updated_at?: string;
}

export interface AgentDetailedInfo {
  id: string;
  name: string;
  description: string;
  agent_type: string;
  status: string;
  is_running: boolean;
  capabilities: string[];
  data_requirements: Record<string, any>;
  export_considerations: Record<string, any>;
  configuration: Record<string, any>;
  model_info?: Record<string, any>;
  performance_metrics?: Record<string, any>;
}

export interface AgentModelRequest {
  model_path: string;
}

export interface AgentModelResponse {
  agent_id: string;
  model_path: string;
}

export interface AvailableModel {
  name: string;
  path: string;
  size: number;
  modified: string;
}

export interface AgentActionResponse {
  message: string;
  model_path?: string;
}

export interface EnhancedModel {
  version: string;
  path: string;
  status: string;
  created_at: string;
  last_updated: string;
  import_method: string;
  metadata: {
    model_info: {
      version: string;
      model_type: string;
      created_at: string;
      description: string;
    };
    training_info: {
      n_samples: number;
      n_features: number;
      feature_names: string[];
      training_date: string;
    };
    evaluation_info: {
      basic_metrics: {
        f1_score: number;
        precision: number;
        recall: number;
        roc_auc: number;
      };
    };
    deployment_info: {
      status: string;
      deployed_at: string;
      deployed_by: string | null;
    };
  };
}

// Agent Configuration Types
export interface AgentConfig {
  agent_id: string;
  name: string;
  description: string;
  agent_type: 'ml_based' | 'rule_based' | 'hybrid';
  process_filters: string[];
  model_path?: string | null;
  capabilities: string[];
  analysis_rules: Record<string, any>;
  [key: string]: any;
}

export interface AgentConfigResponse {
  agent_id: string;
  config: AgentConfig;
  saved_at: string;
  is_valid: boolean;
}

export interface AgentConfigValidationResponse {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface ConfigTemplate {
  agent_id: string;
  name: string;
  description: string;
  agent_type: 'ml_based' | 'rule_based' | 'hybrid';
  process_filters: string[];
  model_path?: string | null;
  capabilities: string[];
  analysis_rules: Record<string, any>;
}

export interface ConfigTemplates {
  ml_based: ConfigTemplate;
  rule_based: ConfigTemplate;
  hybrid: ConfigTemplate;
}

// End of types file - DatabaseConfig and DatabaseTestResult are exported above