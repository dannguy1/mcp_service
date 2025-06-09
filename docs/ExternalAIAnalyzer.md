# External AI Analyzer Module

## Overview

The External AI Analyzer module is designed to read logs from and add anomaly records to the Log Monitor System's database. This document provides comprehensive details about the database schema, log structure, and anomaly records.

## Database Schema

### Log Entries Table
```sql
CREATE TABLE log_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    facility INTEGER NOT NULL,
    severity INTEGER NOT NULL,
    priority INTEGER NOT NULL,
    hostname VARCHAR(255),
    program VARCHAR(255),
    pid INTEGER,
    message TEXT NOT NULL,
    raw_message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

-- Indexes for efficient querying
CREATE INDEX idx_log_entries_device_id ON log_entries(device_id);
CREATE INDEX idx_log_entries_timestamp ON log_entries(timestamp);
CREATE INDEX idx_log_entries_severity ON log_entries(severity);
CREATE INDEX idx_log_entries_priority ON log_entries(priority);
```

### Anomaly Records Table
```sql
CREATE TABLE anomaly_records (
    id SERIAL PRIMARY KEY,
    log_entry_id INTEGER REFERENCES log_entries(id),
    device_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    severity INTEGER NOT NULL,
    confidence FLOAT NOT NULL,
    description TEXT,
    metadata JSONB,
    status VARCHAR(20) DEFAULT 'new',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

-- Indexes for efficient querying
CREATE INDEX idx_anomaly_records_device_id ON anomaly_records(device_id);
CREATE INDEX idx_anomaly_records_timestamp ON anomaly_records(timestamp);
CREATE INDEX idx_anomaly_records_anomaly_type ON anomaly_records(anomaly_type);
CREATE INDEX idx_anomaly_records_severity ON anomaly_records(severity);
CREATE INDEX idx_anomaly_records_status ON anomaly_records(status);
```

### Anomaly Patterns Table
```sql
CREATE TABLE anomaly_patterns (
    id SERIAL PRIMARY KEY,
    pattern_name VARCHAR(100) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    pattern_definition JSONB NOT NULL,
    severity INTEGER NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX idx_anomaly_patterns_pattern_type ON anomaly_patterns(pattern_type);
CREATE INDEX idx_anomaly_patterns_is_active ON anomaly_patterns(is_active);
```

## Log Structure

### Log Entry Fields
1. **id**: Unique identifier for the log entry
2. **device_id**: Reference to the device that generated the log
3. **timestamp**: When the log was generated (UTC)
4. **facility**: Syslog facility number (0-23)
5. **severity**: Syslog severity level (0-7)
6. **priority**: Calculated priority (facility * 8 + severity)
7. **hostname**: Name of the device that generated the log
8. **program**: Name of the program that generated the log
9. **pid**: Process ID of the program
10. **message**: The actual log message
11. **raw_message**: Original unparsed log message
12. **created_at**: When the log was stored in the database

### Severity Levels
- 0: Emergency
- 1: Alert
- 2: Critical
- 3: Error
- 4: Warning
- 5: Notice
- 6: Informational
- 7: Debug

## Anomaly Records

### Anomaly Record Fields
1. **id**: Unique identifier for the anomaly record
2. **log_entry_id**: Reference to the associated log entry
3. **device_id**: Reference to the device where the anomaly was detected
4. **timestamp**: When the anomaly was detected (UTC)
5. **anomaly_type**: Type of anomaly detected
6. **severity**: Severity level of the anomaly (0-7)
7. **confidence**: Confidence score of the detection (0.0-1.0)
8. **description**: Human-readable description of the anomaly
9. **metadata**: Additional JSON data about the anomaly
10. **status**: Current status of the anomaly (new, investigating, resolved, etc.)
11. **created_at**: When the anomaly was recorded
12. **updated_at**: When the anomaly record was last updated

### Anomaly Types
1. **pattern_match**: Matches a known anomaly pattern
2. **statistical_anomaly**: Deviates from normal statistical patterns
3. **sequence_anomaly**: Unusual sequence of events
4. **frequency_anomaly**: Unusual frequency of events
5. **correlation_anomaly**: Unusual correlation between events
6. **custom_anomaly**: Custom anomaly type defined by patterns

### Anomaly Status Values
1. **new**: Newly detected anomaly
2. **investigating**: Under investigation
3. **resolved**: Issue has been resolved
4. **false_positive**: Not a real anomaly
5. **ignored**: Intentionally ignored
6. **escalated**: Escalated to higher priority

## Integration Guidelines

### Database Connection
```python
DATABASE_URL = "postgresql://netmonitor_user:netmonitor_password@192.168.10.14:5432/netmonitor_db"
```

### Reading Logs
1. Query logs within a time range:
```sql
SELECT * FROM log_entries 
WHERE timestamp BETWEEN :start_time AND :end_time 
ORDER BY timestamp DESC;
```

2. Query logs by device:
```sql
SELECT * FROM log_entries 
WHERE device_id = :device_id 
ORDER BY timestamp DESC;
```

3. Query logs by severity:
```sql
SELECT * FROM log_entries 
WHERE severity <= :severity 
ORDER BY timestamp DESC;
```

### Adding Anomaly Records
1. Basic anomaly record:
```sql
INSERT INTO anomaly_records (
    log_entry_id, device_id, timestamp, anomaly_type,
    severity, confidence, description, metadata
) VALUES (
    :log_entry_id, :device_id, :timestamp, :anomaly_type,
    :severity, :confidence, :description, :metadata
);
```

2. Update anomaly status:
```sql
UPDATE anomaly_records 
SET status = :new_status, updated_at = CURRENT_TIMESTAMP 
WHERE id = :anomaly_id;
```

## Best Practices

### Log Processing
1. Process logs in chronological order
2. Use batch processing for efficiency
3. Implement proper error handling
4. Log all processing activities
5. Monitor processing performance

### Anomaly Detection
1. Use appropriate confidence thresholds
2. Implement rate limiting for anomaly creation
3. Avoid duplicate anomaly records
4. Group related anomalies
5. Maintain anomaly history

### Performance Considerations
1. Use appropriate indexes
2. Implement connection pooling
3. Use batch operations when possible
4. Monitor query performance
5. Implement caching where appropriate

### Security
1. Use secure database connections
2. Implement proper access controls
3. Encrypt sensitive data
4. Monitor access patterns
5. Maintain audit logs

## Example Implementation

### Python Example
```python
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import json

class ExternalAIAnalyzer:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        
    def get_recent_logs(self, minutes=5):
        """Get logs from the last N minutes"""
        with self.engine.connect() as conn:
            query = text("""
                SELECT * FROM log_entries 
                WHERE timestamp > :start_time 
                ORDER BY timestamp DESC
            """)
            result = conn.execute(
                query, 
                {"start_time": datetime.utcnow() - timedelta(minutes=minutes)}
            )
            return result.fetchall()
            
    def add_anomaly(self, log_entry_id, device_id, anomaly_type, 
                    severity, confidence, description, metadata=None):
        """Add a new anomaly record"""
        with self.engine.connect() as conn:
            query = text("""
                INSERT INTO anomaly_records (
                    log_entry_id, device_id, timestamp, anomaly_type,
                    severity, confidence, description, metadata
                ) VALUES (
                    :log_entry_id, :device_id, :timestamp, :anomaly_type,
                    :severity, :confidence, :description, :metadata
                ) RETURNING id
            """)
            result = conn.execute(
                query,
                {
                    "log_entry_id": log_entry_id,
                    "device_id": device_id,
                    "timestamp": datetime.utcnow(),
                    "anomaly_type": anomaly_type,
                    "severity": severity,
                    "confidence": confidence,
                    "description": description,
                    "metadata": json.dumps(metadata) if metadata else None
                }
            )
            return result.fetchone()[0]
```

## Monitoring and Maintenance

### Key Metrics to Monitor
1. Log processing rate
2. Anomaly detection rate
3. Database query performance
4. Connection pool usage
5. Error rates

### Regular Maintenance Tasks
1. Clean up old anomaly records
2. Update anomaly patterns
3. Optimize database indexes
4. Monitor disk usage
5. Backup critical data

## Troubleshooting

### Common Issues
1. Database connection failures
2. Slow query performance
3. Duplicate anomaly records
4. Missing log entries
5. Incorrect anomaly classifications

### Debugging Steps
1. Check database connectivity
2. Verify query performance
3. Review error logs
4. Check system resources
5. Validate anomaly patterns

## Future Enhancements

### Planned Features
1. Real-time anomaly detection
2. Advanced pattern matching
3. Machine learning integration
4. Automated response actions
5. Enhanced reporting capabilities

### Potential Improvements
1. Distributed processing
2. Advanced caching
3. Enhanced security features
4. Improved monitoring
5. Better integration capabilities 