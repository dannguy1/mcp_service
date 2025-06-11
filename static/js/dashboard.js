// Dashboard refresh interval (in milliseconds)
const REFRESH_INTERVAL = 30000;

// Update timestamp
function updateTimestamp() {
    const now = new Date();
    document.getElementById('last-updated').textContent = now.toLocaleTimeString();
}

// Fetch and update health status
async function updateHealthStatus() {
    try {
        const response = await fetch('/api/v1/health');
        const data = await response.json();
        
        // Update component statuses
        Object.entries(data.components).forEach(([component, status]) => {
            const element = document.getElementById(`${component}-status`);
            const indicator = element.previousElementSibling;
            
            if (element && indicator) {
                element.textContent = status;
                indicator.className = `status-indicator status-${status.toLowerCase()}`;
            }
        });
    } catch (error) {
        console.error('Failed to fetch health status:', error);
    }
}

// Fetch and update metrics
async function updateMetrics() {
    try {
        const response = await fetch('/api/v1/stats');
        const data = await response.json();
        
        // Update metric cards
        document.getElementById('model-accuracy').textContent = (data.accuracy * 100).toFixed(1) + '%';
        document.getElementById('request-latency').textContent = data.average_latency.toFixed(1);
        document.getElementById('error-rate').textContent = (data.error_rate * 100).toFixed(2) + '%';
        document.getElementById('anomaly-count').textContent = data.anomaly_count;
    } catch (error) {
        console.error('Failed to fetch metrics:', error);
    }
}

// Fetch and update recent anomalies
async function updateAnomalies() {
    try {
        const response = await fetch('/api/v1/anomalies/recent');
        const anomalies = await response.json();
        
        const tableBody = document.getElementById('anomalies-table-body');
        if (tableBody) {
            tableBody.innerHTML = anomalies.map(anomaly => `
                <tr>
                    <td>${new Date(anomaly.timestamp).toLocaleString()}</td>
                    <td><span class="badge bg-${getSeverityClass(anomaly.severity)}">${anomaly.severity}</span></td>
                    <td>${anomaly.description}</td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Failed to fetch anomalies:', error);
    }
}

// Get Bootstrap class for severity
function getSeverityClass(severity) {
    switch (severity.toLowerCase()) {
        case 'high': return 'danger';
        case 'medium': return 'warning';
        case 'low': return 'info';
        default: return 'secondary';
    }
}

// Refresh all dashboard data
async function refreshData() {
    await Promise.all([
        updateHealthStatus(),
        updateMetrics(),
        updateAnomalies()
    ]);
    updateTimestamp();
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    // Initial data load
    refreshData();
    
    // Set up periodic refresh
    setInterval(refreshData, REFRESH_INTERVAL);
}); 