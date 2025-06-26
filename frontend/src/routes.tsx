import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Logs from './pages/Logs';
import Anomalies from './pages/Anomalies';
import Models from './pages/Models';
import EnhancedModels from './pages/EnhancedModels';
import Agents from './pages/Agents';
import AnalysisStats from './pages/AnalysisStats';
import ServerStatus from './pages/ServerStatus';
import Settings from './pages/Settings';
import ExportPage from './pages/ExportPage';
import ChangePassword from './pages/ChangePassword';

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="logs" element={<Logs />} />
        <Route path="anomalies" element={<Anomalies />} />
        <Route path="models" element={<Models />} />
        <Route path="enhanced-models" element={<EnhancedModels />} />
        <Route path="agents" element={<Agents />} />
        <Route path="analysis-stats" element={<AnalysisStats />} />
        <Route path="server" element={<ServerStatus />} />
        <Route path="settings" element={<Settings />} />
        <Route path="export" element={<ExportPage />} />
        <Route path="change-password" element={<ChangePassword />} />
      </Route>
    </Routes>
  );
};

export default AppRoutes; 