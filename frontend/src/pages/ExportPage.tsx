import React from 'react';
import { FaDownload, FaHistory, FaTrash } from 'react-icons/fa';
import ExportControl from '../components/export/ExportControl';
import ExportHistory from '../components/export/ExportHistory';
import ExportCleanup from '../components/export/ExportCleanup';
import TabbedLayout from '../components/common/TabbedLayout';
import type { TabItem } from '../components/common/types';

const ExportPage: React.FC = () => {
  // New Export Tab Content
  const NewExportContent = (
    <div>
      <h4 className="mb-3">Create New Export</h4>
      <ExportControl />
    </div>
  );

  // Export History Tab Content
  const ExportHistoryContent = (
    <div>
      <h4 className="mb-3">Export History</h4>
      <ExportHistory />
    </div>
  );

  // Export Management Tab Content
  const ExportManagementContent = (
    <div>
      <h4 className="mb-3">Export Management</h4>
      <ExportCleanup />
    </div>
  );

  const tabs: TabItem[] = [
    {
      key: 'control',
      title: 'New Export',
      icon: <FaDownload />,
      content: NewExportContent
    },
    {
      key: 'history',
      title: 'Export History',
      icon: <FaHistory />,
      content: ExportHistoryContent
    },
    {
      key: 'cleanup',
      title: 'Management',
      icon: <FaTrash />,
      content: ExportManagementContent
    }
  ];

  return (
    <div className="container-fluid">
      <TabbedLayout title="Data Export" tabs={tabs} />
    </div>
  );
};

export default ExportPage; 