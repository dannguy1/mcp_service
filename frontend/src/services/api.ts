import axios from "axios";
import type { DashboardData, LogsResponse, ModelsResponse, ServerStats, Anomaly, Log, Model, ServerStatus, ChangePasswordForm, ModelInfo } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api/v1";

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
};