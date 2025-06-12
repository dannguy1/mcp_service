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
  id: number;
  timestamp: string;
  type: string;
  severity: number;
  description: string;
  status: string;
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
  name: string;
  is_active: boolean;
  metadata: {
    version: string;
    created_at: string;
    metrics: Record<string, number>;
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
  logs: LogsData;
  total: number;
  filters: {
    severity: string[];
    programs: string[];
  };
}

export interface ModelsResponse {
  models: Model[];
  active_model: Model | null;
  metadata: Record<string, any>;
}