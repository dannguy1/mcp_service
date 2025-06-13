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