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
  ModelPerformanceMetrics,
  ModelDriftResult,
  ModelTransferHistory,
  ModelCompatibilityResult,
  ModelValidationReport,
  ModelPerformanceReport
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
    return api.post<ModelCompatibilityResult>(`/model-management/${version}/validate-compatibility`, targetFeatures).then(res => res.data);
  },

  generateValidationReport: (version: string) => {
    console.log("Generating validation report for:", version);
    return api.get<ModelValidationReport>(`/model-management/${version}/validation-report`).then(res => res.data);
  },

  // Cleanup operations
  cleanupTransferHistory: (daysToKeep: number = 30) => {
    console.log("Cleaning up transfer history, keeping days:", daysToKeep);
    return api.delete(`/model-management/transfer-history?days_to_keep=${daysToKeep}`).then(res => res.data);
  },

  cleanupPerformanceMetrics: (daysToKeep: number = 30) => {
    console.log("Cleaning up performance metrics, keeping days:", daysToKeep);
    return api.delete(`/model-management/performance/cleanup?days_to_keep=${daysToKeep}`).then(res => res.data);
  },

  // Training service endpoints
  getTrainingServiceModels: () => {
    console.log("Fetching training service models...");
    return api.get('/model-management/training-service/models').then(res => res.data);
  },

  importLatestModel: (validate: boolean = true) => {
    console.log("Importing latest model, validate:", validate);
    return api.post(`/model-management/import-latest?validate=${validate}`).then(res => res.data);
  },

  importModelFromTrainingService: (modelPath: string, validate: boolean = true) => {
    console.log("Importing model from training service:", modelPath);
    return api.post(`/model-management/import/${encodeURIComponent(modelPath)}?validate=${validate}`).then(res => res.data);
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
    return api.post('/model-management/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }).then(res => res.data);
  },

  getCurrentModel: () => {
    console.log("Getting current model info...");
    return api.get('/api/v1/models/current').then(res => res.data);
  },
};