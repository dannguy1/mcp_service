import axios from "axios";
import type { 
  DashboardData, 
  LogsResponse, 
  ModelsResponse, 
  ServerStats, 
  Anomaly, 
  Log, 
  Model, 
  ServerStatus, 
  ChangePasswordForm, 
  ModelInfo,
  ModelValidationResult,
  ModelValidationSummary,
  ModelImportResult,
  ModelPerformanceMetrics,
  ModelDriftResult,
  ModelTransferHistory,
  ModelCompatibilityResult,
  ModelValidationReport,
  ModelPerformanceReport,
  LogEntry,
  DatabaseConfig,
  DatabaseTestResult,
  Agent,
  AgentDetailedInfo,
  AgentModelRequest,
  AgentModelResponse,
  AvailableModel,
  AgentActionResponse,
  EnhancedModel
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

console.log("API Base URL:", API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json"
  },
  timeout: 10000 // 10 second timeout
});

api.interceptors.request.use((config) => {
  console.log("API Request:", config.method?.toUpperCase(), config.url);
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => {
    console.log("API Response:", response.status, response.config.url);
    return response;
  },
  (error) => {
    if (error.code === "ECONNABORTED") {
      console.error("API Request timed out");
      return Promise.reject(new Error("Request timed out. Please try again."));
    }
    
    if (!error.response) {
      console.error("API Network Error:", error.message);
      return Promise.reject(new Error("Network error. Please check if the backend server is running at " + API_BASE_URL));
    }

    console.error("API Error:", error.response?.status, error.config?.url, error.message);
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export const endpoints = {
  getDashboardData: () => {
    console.log("Fetching dashboard data...");
    return api.get<DashboardData>("/dashboard").then(res => res.data);
  },
  getLogs: (filters?: Record<string, any>) => {
    console.log("Fetching logs with filters:", filters);
    return api.get<LogsResponse>("/logs", { params: filters }).then(res => res.data);
  },
  getModels: () => {
    console.log("Fetching models...");
    return api.get<ModelsResponse>("/models").then(res => res.data);
  },
  getModelInfo: (modelId: string) => {
    console.log("Fetching model info for:", modelId);
    return api.get<ModelInfo>(`/models/${modelId}/info`).then(res => res.data);
  },
  getServerStats: () => {
    console.log("Fetching server stats...");
    return api.get<ServerStats>("/server/stats").then(res => res.data);
  },
  getAnomalies: () => {
    console.log("Fetching anomalies...");
    return api.get<Anomaly[]>("/anomalies").then(res => res.data);
  },
  activateModel: (modelId: string) => {
    console.log("Activating model:", modelId);
    return api.post<{ status: string; message: string }>(`/models/${modelId}/activate`).then(res => res.data);
  },
  deployModel: (modelId: string) => {
    return api.post<{ status: string; message: string }>(`/models/${modelId}/deploy`).then(res => res.data);
  },
  getHealth: () => {
    console.log("Checking health...");
    return api.get<{ status: string }>("/health").then(res => res.data);
  },
  login: (credentials: { username: string; password: string }) =>
    api.post('/auth/login', credentials).then((res) => res.data),
  changePassword: (data: ChangePasswordForm) =>
    api.post('/auth/change-password', data).then((res) => res.data),
  getServerStatus: () =>
    api.get<ServerStatus>('/server/status').then((res) => res.data),
  
  // Export endpoints
  createExport: (config: any) => {
    console.log("Creating export with config:", config);
    return api.post('/export', config).then(res => res.data);
  },
  
  getExportStatus: (exportId: string) => {
    console.log("Getting export status for:", exportId);
    return api.get(`/export/${exportId}/status`).then(res => res.data);
  },
  
  getExportProgress: (exportId: string) => {
    console.log("Getting export progress for:", exportId);
    return api.get(`/export/${exportId}/progress`).then(res => res.data);
  },
  
  listExports: (params?: { limit?: number; offset?: number }) => {
    console.log("Listing exports with params:", params);
    return api.get('/export', { params }).then(res => res.data);
  },
  
  deleteExport: (exportId: string) => {
    console.log("Deleting export:", exportId);
    return api.delete(`/export/${exportId}`).then(res => res.data);
  },
  
  downloadExport: (exportId: string) => {
    console.log("Downloading export:", exportId);
    return api.get(`/export/download/${exportId}`, {
      responseType: 'blob'
    }).then(res => res.data);
  },
  
  cleanupExports: () => {
    console.log("Cleaning up exports");
    return api.post('/export/cleanup').then(res => res.data);
  },
  
  getExportStats: () => {
    console.log("Getting export stats");
    return api.get('/export/stats').then(res => res.data);
  },

  // Enhanced Model Management endpoints
  validateModel: (version: string) => {
    console.log("Validating model:", version);
    return api.post<ModelValidationResult>(`/model-management/${version}/validate`).then(res => res.data);
  },

  deployModelVersion: (version: string) => {
    console.log("Deploying model version:", version);
    return api.post(`/model-management/${version}/deploy`).then(res => res.data);
  },

  rollbackModel: (version: string) => {
    console.log("Rolling back to model version:", version);
    return api.post(`/model-management/${version}/rollback`).then(res => res.data);
  },

  getTransferHistory: () => {
    console.log("Fetching transfer history...");
    return api.get<ModelTransferHistory[]>('/model-management/transfer-history').then(res => res.data);
  },

  listEnhancedModels: () => {
    console.log("Fetching enhanced models...");
    return api.get('/model-management/models').then(res => res.data);
  },

  getEnhancedModelInfo: (version: string) => {
    console.log("Fetching enhanced model info for:", version);
    return api.get(`/model-management/models/${version}`).then(res => res.data);
  },

  getModelPerformance: (version: string) => {
    console.log("Fetching model performance for:", version);
    return api.get<ModelPerformanceMetrics>(`/model-management/performance/${version}`).then(res => res.data);
  },

  getAllModelPerformance: () => {
    console.log("Fetching all model performance...");
    return api.get<ModelPerformanceMetrics[]>('/model-management/performance').then(res => res.data);
  },

  checkModelDrift: (version: string) => {
    console.log("Checking model drift for:", version);
    return api.post<ModelDriftResult>(`/model-management/performance/${version}/check-drift`).then(res => res.data);
  },

  generatePerformanceReport: (version: string) => {
    console.log("Generating performance report for:", version);
    return api.get<ModelPerformanceReport>(`/model-management/performance/${version}/report`).then(res => res.data);
  },

  validateModelCompatibility: (version: string, targetFeatures: string[]) => {
    console.log("Validating model compatibility for:", version);
    return api.post<ModelCompatibilityResult>(`/model-management/${version}/validate-compatibility`, { target_features: targetFeatures }).then(res => res.data);
  },

  generateValidationReport: (version: string) => {
    console.log("Generating validation report for:", version);
    return api.get<ModelValidationReport>(`/model-management/${version}/validation-report`).then(res => res.data);
  },

  // Cleanup operations
  cleanupTransferHistory: () => {
    console.log("Cleaning up transfer history...");
    return api.delete('/model-management/transfer-history').then(res => res.data);
  },

  cleanupPerformanceMetrics: () => {
    console.log("Cleaning up performance metrics...");
    return api.delete('/model-management/performance/cleanup').then(res => res.data);
  },

  // Training service endpoints
  getTrainingServiceModels: () => {
    console.log("Fetching training service models...");
    return api.get('/model-management/training-service/models').then(res => res.data);
  },

  importLatestModel: (validate: boolean = true) => {
    console.log("Importing latest model...");
    return api.post<ModelImportResult>('/model-management/import-latest', { validate }).then(res => res.data);
  },

  importModel: (modelPath: string, validate: boolean = true) => {
    console.log("Importing model:", modelPath);
    return api.post<ModelImportResult>(`/model-management/import/${modelPath}`, { validate }).then(res => res.data);
  },

  validateTrainingServiceConnection: () => {
    console.log("Validating training service connection...");
    return api.get('/model-management/training-service/connection').then(res => res.data);
  },

  // Model analysis endpoint
  analyzeLogs: (logs: LogEntry[]) => {
    console.log("Analyzing logs with current model...");
    return api.post('/api/v1/models/analyze', logs).then(res => res.data);
  },

  // Model loading and deployment
  loadModelVersion: (version: string) => {
    console.log("Loading model version:", version);
    return api.post(`/api/v1/models/${version}/load`).then(res => res.data);
  },

  // Model package import
  importModelPackage: (formData: FormData) => {
    console.log("Importing model package...");
    console.log("FormData contents:");
    for (let [key, value] of formData.entries()) {
      console.log(`${key}:`, value);
    }
    console.log("Making POST request to /model-management/import");
    return api.post<ModelImportResult>('/model-management/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }).then(res => {
      console.log("Import response:", res.data);
      return res.data;
    }).catch(error => {
      console.error("Import request failed:", error);
      console.error("Error response:", error.response?.data);
      throw error;
    });
  },

  getCurrentModel: () => {
    console.log("Getting current model info...");
    return api.get('/api/v1/models/current').then(res => res.data);
  },

  // Database configuration endpoints
  getDatabaseConfig: () => {
    console.log("Getting database configuration...");
    return api.get('/settings/database').then(res => res.data);
  },

  updateDatabaseConfig: (config: DatabaseConfig) => {
    console.log("Updating database configuration:", config);
    return api.post('/settings/database', config).then(res => res.data);
  },

  testDatabaseConnection: (config: DatabaseConfig) => {
    console.log("Testing database connection:", config);
    return api.post('/settings/database/test', config).then(res => res.data);
  },

  // Agent Management endpoints
  listAgents: () => {
    console.log("Fetching agents...");
    return api.get<Agent[]>('/agents').then(res => res.data);
  },

  getAgent: (agentId: string) => {
    console.log("Fetching agent:", agentId);
    return api.get<Agent>(`/agents/${agentId}`).then(res => res.data);
  },

  setAgentModel: (agentId: string, modelPath: string) => {
    console.log("Setting model for agent:", agentId, "to:", modelPath);
    return api.post<AgentActionResponse>(`/agents/${agentId}/set-model`, { model_path: modelPath }).then(res => res.data);
  },

  getAgentModel: (agentId: string) => {
    console.log("Getting model for agent:", agentId);
    return api.get<AgentModelResponse>(`/agents/${agentId}/model`).then(res => res.data);
  },

  restartAgent: (agentId: string) => {
    console.log("Restarting agent:", agentId);
    return api.post<AgentActionResponse>(`/agents/${agentId}/restart`).then(res => res.data);
  },

  getAvailableModels: () => {
    console.log("Fetching available models...");
    return api.get<EnhancedModel[]>('/model-management/models').then(res => {
      // Map enhanced models to AvailableModel format
      return res.data.map(model => ({
        name: model.metadata.model_info.description || model.version,
        path: model.path,
        size: 0, // Size not available in enhanced model response
        modified: model.last_updated
      }));
    });
  },

  unregisterAgent: (agentId: string) => {
    console.log("Unregistering agent:", agentId);
    return api.delete<AgentActionResponse>(`/agents/${agentId}`).then(res => res.data);
  },

  // Agent Analysis Stats endpoints
  getAnalysisOverview: () => {
    console.log("Fetching analysis overview...");
    return api.get('/agents/stats/overview').then(res => res.data);
  },

  getAgentStats: (agentId: string) => {
    console.log("Fetching agent stats for:", agentId);
    return api.get(`/agents/${agentId}/stats`).then(res => res.data);
  },

  // Agent Details endpoints
  getAgentsDetailedInfo: (agentIds?: string[]) => {
    console.log("Fetching detailed info for agents:", agentIds);
    const params = agentIds && agentIds.length > 0 ? { agent_ids: agentIds.join(',') } : {};
    return api.get<AgentDetailedInfo[]>('/agents/detailed-info', { params }).then(res => res.data);
  },

  getAgentDetailedInfo: (agentId: string) => {
    console.log("Fetching detailed info for agent:", agentId);
    return api.get<AgentDetailedInfo>(`/agents/${agentId}/detailed`).then(res => res.data);
  },

  // Agent Configuration endpoints
  getAgentConfig: (agentId: string) => {
    console.log("Fetching agent configuration:", agentId);
    return api.get(`/agents/${agentId}/config`).then(res => res.data);
  },

  saveAgentConfig: (agentId: string, config: any) => {
    console.log("Saving agent configuration:", agentId, config);
    return api.post(`/agents/${agentId}/config`, { config }).then(res => res.data);
  },

  validateAgentConfig: (agentId: string, config: any) => {
    console.log("Validating agent configuration:", agentId, config);
    return api.post(`/agents/${agentId}/config/validate`, { config }).then(res => res.data);
  },

  deleteAgentConfig: (agentId: string) => {
    console.log("Deleting agent configuration:", agentId);
    return api.delete(`/agents/${agentId}/config`).then(res => res.data);
  },

  getConfigTemplates: () => {
    console.log("Fetching configuration templates");
    return api.get('/agents/configs/templates').then(res => res.data);
  }
};