import React from "react";
import { useQuery } from "@tanstack/react-query";
import StatusPanel from "../components/dashboard/StatusPanel";
import { Card } from "react-bootstrap";
import { endpoints } from "../services/api";
import type { DashboardData } from "../services/types";

const Dashboard: React.FC = () => {
  const { data, isLoading, error } = useQuery<DashboardData>({
    queryKey: ["dashboard"],
    queryFn: () => endpoints.getDashboardData()
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading dashboard data</div>;
  if (!data) return null;

  return (
    <div>
      <h2 className="mb-4">Dashboard</h2>
      <StatusPanel data={data.system_status} />
      
      <Card className="mb-4">
        <Card.Header>Recent Anomalies</Card.Header>
        <Card.Body>
          {data.recent_anomalies.length === 0 ? (
            <p>No recent anomalies detected</p>
          ) : (
            <ul className="list-unstyled">
              {data.recent_anomalies.map((anomaly) => (
                <li key={anomaly.id} className="mb-2">
                  <strong>{anomaly.timestamp}</strong> - {anomaly.description}
                  <span className={`badge bg-${anomaly.severity > 7 ? "danger" : anomaly.severity > 4 ? "warning" : "info"} ms-2`}>
                    Severity: {anomaly.severity}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card.Body>
      </Card>
    </div>
  );
};

export default Dashboard;