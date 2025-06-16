# Export Enhancement Implementation Plan - Updated for FastAPI Migration

## Overview
This document outlines the updated plan to enhance the export functionality of the MCP service for AI model training, taking into account the successful migration from Flask to FastAPI. The system now has a unified FastAPI architecture that supports the export functionality requirements.

## Current State Analysis

### ✅ Completed Components
1. **FastAPI Migration**: Successfully migrated from Flask to FastAPI
2. **Core Export Infrastructure**: 
   - `DataExporter` class with batch processing
   - `DataValidator` with comprehensive validation
   - `DataTransformer` with data standardization
   - `ExportStatusManager` for status tracking
3. **Database Models**: 
   - `ExportStatus` model for tracking export progress
   - `ExportMetadata` and `ExportConfig` Pydantic models
4. **Service Architecture**: Async database operations with SQLAlchemy
5. **Basic API Structure**: FastAPI app with health checks and metrics

### 🔄 Partially Implemented Components
1. **Export API Endpoints**: Core services exist but API endpoints are missing
2. **Status Tracking**: Database model exists but real-time updates not implemented
3. **Frontend Integration**: Basic hooks exist but UI components need completion

### ❌ Missing Components
1. **Export API Router**: No FastAPI router for export endpoints
2. **Background Task Processing**: No async export processing
3. **Real-time Status Updates**: No WebSocket or polling mechanism
4. **Frontend Export UI**: No complete export interface
5. **Date Range Flexibility**: Current implementation requires date ranges

## Updated Implementation Phases

### Phase 1: Export API Integration (Priority: High)
**Goal**: Create FastAPI endpoints for export functionality

#### 1.1 Create Export Router
```python
# backend/app/api/endpoints/export.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Optional
from datetime import datetime

from app.models.export import ExportConfig, ExportMetadata
from app.services.export.data_exporter import DataExporter
from app.services.export.status_manager import ExportStatusManager

router = APIRouter(prefix="/export", tags=["export"])

@router.post("/", response_model=ExportMetadata)
async def create_export(
    config: ExportConfig,
    background_tasks: BackgroundTasks
) -> ExportMetadata:
    """Create a new export job"""
    try:
        # Initialize exporter
        exporter = DataExporter(config)
        
        # Add to background tasks
        background_tasks.add_task(exporter.export_data, config)
        
        # Return initial metadata
        return ExportMetadata(
            export_id=str(uuid.uuid4()),
            data_version="1.0.0",
            export_config=config.dict(),
            record_count=0,
            file_size=0,
            status="pending"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{export_id}/status")
async def get_export_status(export_id: str):
    """Get export status"""
    try:
        status = await ExportStatusManager.get_status(export_id)
        if not status:
            raise HTTPException(status_code=404, detail="Export not found")
        return status.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[ExportMetadata])
async def list_exports(
    limit: int = 100,
    offset: int = 0
):
    """List export history"""
    try:
        statuses = await ExportStatusManager.list_statuses(limit, offset)
        return [status.to_dict() for status in statuses]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 1.2 Update Main FastAPI App
```python
# backend/app/main.py - Add to existing imports
from app.api.endpoints.export import router as export_router

# Add to existing app
app.include_router(export_router, prefix="/api/v1")
```

#### 1.3 Enhanced ExportConfig Model
```python
# backend/app/models/export.py - Update ExportConfig
class ExportConfig(BaseModel):
    """Configuration for data export."""
    start_date: Optional[datetime] = Field(None, description="Start date for data export (optional)")
    end_date: Optional[datetime] = Field(None, description="End date for data export (optional)")
    data_types: List[str] = Field(..., description="Types of data to export")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Additional filters")
    batch_size: int = Field(default=1000, description="Number of records per batch")
    include_metadata: bool = Field(default=True, description="Whether to include metadata")
    validation_level: str = Field(default="basic", description="Level of validation to perform")
    output_format: str = Field(default="json", description="Output format for export")
    compression: bool = Field(default=False, description="Whether to compress output")
    processes: List[str] = Field(default_factory=list, description="List of processes to filter by")
    
    @validator('data_types')
    def validate_data_types(cls, v):
        valid_types = ['logs', 'anomalies', 'ips']
        for data_type in v:
            if data_type not in valid_types:
                raise ValueError(f"Invalid data type: {data_type}")
        return v
```

### Phase 2: Enhanced Data Exporter (Priority: High)
**Goal**: Update DataExporter to support optional date ranges and flexible filtering

#### 2.1 Update DataExporter Class
```python
# backend/app/services/export/data_exporter.py - Add new method
async def export_data(self, config: ExportConfig) -> ExportMetadata:
    """Export data based on configuration with optional date ranges."""
    try:
        # Generate export ID
        export_id = str(uuid.uuid4())
        
        # Initialize metadata
        metadata = ExportMetadata(
            export_id=export_id,
            data_version="1.0.0",
            export_config=config.dict(),
            record_count=0,
            file_size=0,
            status="running"
        )
        
        # Create status in database
        await ExportStatusManager.create_status(metadata.dict())
        
        # Process each data type
        for data_type in config.data_types:
            await self._process_data_type(data_type, config, metadata)
            
        # Update final status
        metadata.status = "completed"
        await ExportStatusManager.update_status(export_id, {"status": "completed"})
        
        return metadata
        
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        if metadata:
            metadata.status = "failed"
            metadata.error_message = str(e)
            await ExportStatusManager.update_status(export_id, {
                "status": "failed",
                "error_message": str(e)
            })
        raise

async def _process_data_type(self, data_type: str, config: ExportConfig, metadata: ExportMetadata):
    """Process a specific data type for export."""
    try:
        # Get total count for progress tracking
        total_records = await self._get_total_count(data_type, config)
        
        # Create export directory
        export_path = self.export_dir / f"{data_type}_{metadata.export_id}"
        export_path.mkdir(exist_ok=True)
        
        # Process in batches
        batch_number = 0
        processed_records = 0
        
        while True:
            # Fetch batch
            batch = await self._fetch_batch(data_type, config, batch_number)
            if not batch:
                break
                
            # Validate and transform batch
            valid_records = []
            for record in batch:
                validation = self.validator.validate_record(data_type, record)
                if validation.is_valid:
                    transformed = self.transformer.transform(data_type, record)
                    valid_records.append(transformed)
                    
            # Write batch
            if valid_records:
                batch_file = export_path / f"batch_{batch_number}.json"
                if config.compression:
                    batch_file = batch_file.with_suffix('.json.gz')
                file_size = self._write_data(valid_records, batch_file)
                processed_records += len(valid_records)
                
            # Update progress
            await ExportStatusManager.update_record_counts(
                metadata.export_id, 
                data_type, 
                processed_records
            )
            
            batch_number += 1
            
        # Update metadata
        metadata.record_count += processed_records
        metadata.file_size += self._get_export_size(export_path)
        
    except Exception as e:
        logger.error(f"Error processing {data_type}: {str(e)}")
        raise
```

#### 2.2 Add Flexible Data Fetching
```python
# backend/app/services/export/data_exporter.py - Add new methods
async def _get_total_count(self, data_type: str, config: ExportConfig) -> int:
    """Get total count of records for a data type."""
    async with AsyncSession(get_db()) as session:
        if data_type == "logs":
            query = select(func.count(LogEntry.id))
        elif data_type == "anomalies":
            query = select(func.count(AnomalyDetection.id))
        elif data_type == "ips":
            query = select(func.count(IPAddress.id))
        else:
            raise ValueError(f"Unsupported data type: {data_type}")
            
        # Apply date filters if provided
        if config.start_date or config.end_date:
            if data_type == "logs":
                conditions = []
                if config.start_date:
                    conditions.append(LogEntry.timestamp >= config.start_date)
                if config.end_date:
                    conditions.append(LogEntry.timestamp <= config.end_date)
                query = query.where(and_(*conditions))
            # Similar for other data types...
            
        result = await session.execute(query)
        return result.scalar()

async def _fetch_batch(self, data_type: str, config: ExportConfig, batch_number: int) -> List[Dict[str, Any]]:
    """Fetch a batch of records for a data type."""
    async with AsyncSession(get_db()) as session:
        offset = batch_number * config.batch_size
        limit = config.batch_size
        
        if data_type == "logs":
            query = select(LogEntry)
            # Apply filters
            if config.start_date or config.end_date:
                conditions = []
                if config.start_date:
                    conditions.append(LogEntry.timestamp >= config.start_date)
                if config.end_date:
                    conditions.append(LogEntry.timestamp <= config.end_date)
                query = query.where(and_(*conditions))
                
            if config.processes:
                query = query.where(LogEntry.process_name.in_(config.processes))
                
        # Similar for other data types...
        
        query = query.offset(offset).limit(limit)
        result = await session.execute(query)
        records = result.scalars().all()
        
        return [record.to_dict() for record in records]
```

### Phase 3: Real-time Status Updates (Priority: Medium)
**Goal**: Implement real-time status tracking for export progress

#### 3.1 Enhanced Status Manager
```python
# backend/app/services/export/status_manager.py - Add new methods
class ExportStatusManager:
    @staticmethod
    async def update_progress(
        export_id: str,
        data_type: str,
        processed: int,
        total: int
    ) -> None:
        """Update progress for a specific data type."""
        status = await ExportStatusManager.get_status(export_id)
        if status:
            if not status.progress:
                status.progress = {}
            status.progress[data_type] = (processed / total) * 100
            status.processed_records = processed
            await ExportStatusManager.update_status(export_id, {
                "progress": status.progress,
                "processed_records": processed
            })

    @staticmethod
    async def update_batch_progress(
        export_id: str,
        current_batch: int,
        total_batches: int
    ) -> None:
        """Update batch processing progress."""
        await ExportStatusManager.update_status(export_id, {
            "current_batch": current_batch,
            "total_batches": total_batches
        })
```

#### 3.2 Status Polling Endpoint
```python
# backend/app/api/endpoints/export.py - Add new endpoint
@router.get("/{export_id}/progress")
async def get_export_progress(export_id: str):
    """Get detailed export progress"""
    try:
        status = await ExportStatusManager.get_status(export_id)
        if not status:
            raise HTTPException(status_code=404, detail="Export not found")
            
        return {
            "export_id": export_id,
            "status": status.status,
            "progress": status.progress or {},
            "current_batch": getattr(status, 'current_batch', 0),
            "total_batches": getattr(status, 'total_batches', 0),
            "processed_records": status.processed_records,
            "total_records": status.total_records,
            "start_time": status.created_at.isoformat(),
            "end_time": status.updated_at.isoformat() if status.status in ["completed", "failed"] else None,
            "error_message": status.error_message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Phase 4: Frontend Export Interface (Priority: Medium)
**Goal**: Create complete frontend interface for export functionality

#### 4.1 Export Control Component
```typescript
// frontend/src/components/export/ExportControl.tsx
import React, { useState } from 'react';
import { useExport } from '../../hooks/useExport';

interface ExportConfig {
  startDate?: Date;
  endDate?: Date;
  dataTypes: string[];
  filters: Record<string, any>;
  batchSize: number;
  includeMetadata: boolean;
  outputFormat: string;
  compression: boolean;
}

export const ExportControl: React.FC = () => {
  const [config, setConfig] = useState<ExportConfig>({
    dataTypes: ['logs'],
    filters: {},
    batchSize: 1000,
    includeMetadata: true,
    outputFormat: 'json',
    compression: false
  });
  
  const { createExport, isExporting } = useExport();
  
  const handleExport = async () => {
    try {
      const result = await createExport(config);
      // Handle success
    } catch (error) {
      // Handle error
    }
  };
  
  return (
    <div className="export-control">
      <h3>Export Data for AI Training</h3>
      
      {/* Date Range (Optional) */}
      <div className="form-group">
        <label>Date Range (Optional)</label>
        <input
          type="datetime-local"
          onChange={(e) => setConfig({...config, startDate: new Date(e.target.value)})}
        />
        <input
          type="datetime-local"
          onChange={(e) => setConfig({...config, endDate: new Date(e.target.value)})}
        />
      </div>
      
      {/* Data Types */}
      <div className="form-group">
        <label>Data Types</label>
        {['logs', 'anomalies', 'ips'].map(type => (
          <label key={type}>
            <input
              type="checkbox"
              checked={config.dataTypes.includes(type)}
              onChange={(e) => {
                if (e.target.checked) {
                  setConfig({...config, dataTypes: [...config.dataTypes, type]});
                } else {
                  setConfig({...config, dataTypes: config.dataTypes.filter(t => t !== type)});
                }
              }}
            />
            {type}
          </label>
        ))}
      </div>
      
      {/* Export Button */}
      <button 
        onClick={handleExport}
        disabled={isExporting || config.dataTypes.length === 0}
      >
        {isExporting ? 'Exporting...' : 'Start Export'}
      </button>
    </div>
  );
};
```

#### 4.2 Export Status Component
```typescript
// frontend/src/components/export/ExportStatus.tsx
import React, { useEffect, useState } from 'react';
import { useExport } from '../../hooks/useExport';

interface ExportStatus {
  exportId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: Record<string, number>;
  processedRecords: number;
  totalRecords: number;
  startTime: string;
  endTime?: string;
  errorMessage?: string;
}

export const ExportStatus: React.FC<{ exportId: string }> = ({ exportId }) => {
  const [status, setStatus] = useState<ExportStatus | null>(null);
  const { getExportStatus } = useExport();
  
  useEffect(() => {
    const pollStatus = async () => {
      try {
        const result = await getExportStatus(exportId);
        setStatus(result);
        
        // Continue polling if export is running
        if (result.status === 'running') {
          setTimeout(pollStatus, 2000);
        }
      } catch (error) {
        console.error('Failed to fetch export status:', error);
      }
    };
    
    pollStatus();
  }, [exportId]);
  
  if (!status) return <div>Loading...</div>;
  
  return (
    <div className="export-status">
      <h4>Export Status: {status.status}</h4>
      
      {/* Progress Bars */}
      {Object.entries(status.progress).map(([type, progress]) => (
        <div key={type} className="progress-bar">
          <label>{type}: {progress.toFixed(1)}%</label>
          <div className="progress">
            <div 
              className="progress-fill" 
              style={{width: `${progress}%`}}
            />
          </div>
        </div>
      ))}
      
      {/* Record Count */}
      <p>Processed: {status.processedRecords} / {status.totalRecords} records</p>
      
      {/* Error Display */}
      {status.errorMessage && (
        <div className="error">
          <strong>Error:</strong> {status.errorMessage}
        </div>
      )}
    </div>
  );
};
```

### Phase 5: Testing and Validation (Priority: Medium)
**Goal**: Comprehensive testing of export functionality

#### 5.1 Unit Tests
```python
# backend/tests/unit/test_export.py
import pytest
from datetime import datetime, timedelta
from app.models.export import ExportConfig
from app.services.export.data_exporter import DataExporter
from app.services.export.data_validator import DataValidator

class TestDataExporter:
    @pytest.fixture
    def config(self):
        return ExportConfig(
            data_types=["logs"],
            batch_size=100,
            include_metadata=True,
            validation_level="basic",
            output_format="json",
            compression=False
        )
    
    @pytest.fixture
    def exporter(self, config):
        return DataExporter(config)
    
    async def test_export_without_date_range(self, exporter, config):
        """Test export without date range constraints."""
        metadata = await exporter.export_data(config)
        assert metadata.status == "completed"
        assert metadata.record_count >= 0
    
    async def test_export_with_date_range(self, exporter):
        """Test export with date range constraints."""
        config = ExportConfig(
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow(),
            data_types=["logs"],
            batch_size=100
        )
        metadata = await exporter.export_data(config)
        assert metadata.status == "completed"
```

#### 5.2 Integration Tests
```python
# backend/tests/integration/test_export_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestExportAPI:
    def test_create_export(self):
        """Test creating an export job."""
        response = client.post("/api/v1/export/", json={
            "data_types": ["logs"],
            "batch_size": 100,
            "include_metadata": True,
            "output_format": "json",
            "compression": False
        })
        assert response.status_code == 200
        data = response.json()
        assert "export_id" in data
        assert data["status"] == "pending"
    
    def test_get_export_status(self):
        """Test getting export status."""
        # First create an export
        create_response = client.post("/api/v1/export/", json={
            "data_types": ["logs"],
            "batch_size": 100
        })
        export_id = create_response.json()["export_id"]
        
        # Then get status
        status_response = client.get(f"/api/v1/export/{export_id}/status")
        assert status_response.status_code == 200
        data = status_response.json()
        assert data["export_id"] == export_id
```

### Phase 6: Documentation and Deployment (Priority: Low)
**Goal**: Complete documentation and deployment preparation

#### 6.1 API Documentation
- Update OpenAPI documentation
- Create usage examples
- Document error codes and responses

#### 6.2 User Guide
- Create step-by-step export guide
- Document configuration options
- Provide troubleshooting guide

## Implementation Order and Timeline

### Week 1: API Integration
- [ ] Create export router (`backend/app/api/endpoints/export.py`)
- [ ] Update main FastAPI app to include export routes
- [ ] Update ExportConfig model for optional date ranges
- [ ] Basic API testing

### Week 2: Enhanced Data Exporter
- [ ] Update DataExporter for flexible date ranges
- [ ] Implement batch processing with progress tracking
- [ ] Add comprehensive error handling
- [ ] Unit tests for exporter

### Week 3: Status Tracking
- [ ] Enhance ExportStatusManager with progress updates
- [ ] Implement real-time status endpoints
- [ ] Add status polling mechanism
- [ ] Integration tests

### Week 4: Frontend Interface
- [ ] Create ExportControl component
- [ ] Create ExportStatus component
- [ ] Implement export history view
- [ ] Frontend testing

### Week 5: Testing and Polish
- [ ] Comprehensive testing suite
- [ ] Performance optimization
- [ ] Documentation updates
- [ ] Deployment preparation

## Success Criteria

1. **Functional Requirements**:
   - Export works without date range constraints
   - All data matching filter criteria is exported
   - Real-time progress tracking works
   - Export status is accurately maintained

2. **Performance Requirements**:
   - Large datasets (100K+ records) export successfully
   - Memory usage remains stable during export
   - Export completes within reasonable time

3. **User Experience**:
   - Clear progress indication
   - Intuitive export configuration
   - Helpful error messages
   - Export history tracking

4. **Technical Requirements**:
   - Async processing with background tasks
   - Proper error handling and recovery
   - Database transaction safety
   - API consistency with FastAPI standards

## Notes

- The migration to FastAPI provides a solid foundation for async processing
- The existing export infrastructure can be enhanced rather than rebuilt
- Focus on making date ranges truly optional while maintaining data quality
- Ensure backward compatibility with existing export configurations
- Consider implementing export scheduling for recurring exports 