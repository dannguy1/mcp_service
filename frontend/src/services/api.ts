import axios from "axios";
import type { DashboardData, LogsResponse, ModelsResponse, ServerStats, Anomaly } from "./types";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:5000/api/v1";

console.log("API Base URL:", baseURL);

export const api = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json"
  },
  timeout: 5000 // 5 second timeout
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
      return Promise.reject(new Error("Request timed out. Please check if the backend server is running."));
    }
    
    if (!error.response) {
      console.error("API Network Error:", error.message);
      return Promise.reject(new Error("Network error. Please check if the backend server is running at " + baseURL));
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
  }
};