# Model Loading Implementation Plan

This implementation plan is based on the requirements and workflow described in `Model-Loading-Guide.md`. It is intended to guide an AI coder or developer to implement the model loading, validation, and management features in the MCP system, ensuring the process matches the documentation and is robust, user-friendly, and maintainable.

---

## 1. Model Package Handling

### 1.1. Accepting Model Packages via ZIP Upload

- **Requirement:**  
  The system must accept model packages as ZIP files via the REST API or frontend UI.  
- **Current Status:** ❌ **MISSING** - ZIP upload endpoint not implemented
- **Implementation Steps:**
  1. **Add ZIP upload endpoint** to `backend/app/api/endpoints/model_management.py`:
     ```python
     from fastapi import File, UploadFile
     import zipfile
     import tempfile
     import shutil
     from pathlib import Path
     
     @router.post("/import")
     async def import_model_package(
         file: UploadFile = File(...),
         validate: bool = True
     ) -> Dict[str, Any]:
         """Import a model package ZIP file."""
         try:
             # Validate file type
             if not file.filename.endswith('.zip'):
                 raise HTTPException(status_code=400, detail="File must be a ZIP archive")
             
             # Validate naming convention
             if not file.filename.startswith('model_') or not file.filename.endswith('_deployment.zip'):
                 raise HTTPException(status_code=400, detail="File must follow naming convention: model_{version}_deployment.zip")
             
             # Save to temporary location
             with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                 content = await file.read()
                 tmp_file.write(content)
                 tmp_file_path = tmp_file.name
             
             # Extract and process
             result = await process_model_package(tmp_file_path, validate)
             
             # Cleanup
             os.unlink(tmp_file_path)
             
             return result
             
         except Exception as e:
             logger.error(f"Error importing model package: {e}")
             raise HTTPException(status_code=500, detail=str(e))
     ```

  2. **Implement package processing function** in `backend/app/services/model_loader.py`:
     ```python
     async def process_model_package(zip_path: str, validate: bool = True) -> Dict[str, Any]:
         """Process uploaded model package ZIP file."""
         try:
             # Extract version from filename
             filename = Path(zip_path).name
             version = filename.replace('model_', '').replace('_deployment.zip', '')
             
             # Create model directory
             model_dir = Path("backend/models") / f"model_{version}"
             model_dir.mkdir(parents=True, exist_ok=True)
             
             # Extract ZIP contents
             with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                 zip_ref.extractall(model_dir)
             
             # Validate contents
             if validate:
                 validation_result = await validate_model_contents(model_dir)
                 if not validation_result['is_valid']:
                     shutil.rmtree(model_dir)
                     raise ValueError(f"Model validation failed: {validation_result['errors']}")
             
             # Register model
             await register_model(model_dir, version)
             
             return {
                 "version": version,
                 "status": "imported",
                 "path": str(model_dir),
                 "imported_at": datetime.now().isoformat()
             }
             
         except Exception as e:
             logger.error(f"Error processing model package: {e}")
             raise
     ```

### 1.2. Manual File Placement

- **Requirement:**  
  Users may also manually copy and extract model packages into the correct directory.
- **Current Status:** ✅ **IMPLEMENTED** - Directory scanning exists
- **Implementation Steps:**
  1. **Enhance directory scanning** in `backend/app/components/model_manager.py`:
     ```python
     async def scan_model_directory(self) -> List[Dict[str, Any]]:
         """Scan models directory for new models."""
         models = []
         models_dir = Path(self.models_directory)
         
         if not models_dir.exists():
             return models
         
         for model_dir in models_dir.iterdir():
             if model_dir.is_dir() and model_dir.name.startswith('model_'):
                 try:
                     # Check if already registered
                     if not await self._is_model_registered(model_dir.name):
                         # Validate and register new model
                         validation_result = await self._validate_imported_model(str(model_dir))
                         if validation_result['is_valid']:
                             await self._update_model_registry(model_dir, 'available')
                             models.append({
                                 'version': model_dir.name,
                                 'path': str(model_dir),
                                 'status': 'available',
                                 'imported_at': datetime.now().isoformat()
                             })
                 except Exception as e:
                     logger.warning(f"Error processing model directory {model_dir}: {e}")
         
         return models
     ```

---

## 2. Model Package Extraction and Validation

### 2.1. Extraction

- **Requirement:**  
  The system must extract the ZIP archive into a versioned subdirectory under `backend/models/`.
- **Current Status:** ❌ **MISSING** - ZIP extraction not implemented
- **Implementation Steps:**
  1. **Implement ZIP extraction** with proper error handling:
     ```python
     async def extract_model_package(zip_path: str, target_dir: Path) -> bool:
         """Extract model package ZIP to target directory."""
         try:
             with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                 # Validate ZIP contents before extraction
                 required_files = [
                     'model.joblib',
                     'metadata.json', 
                     'deployment_manifest.json',
                     'validate_model.py',
                     'inference_example.py',
                     'requirements.txt',
                     'README.md'
                 ]
                 
                 zip_files = zip_ref.namelist()
                 missing_files = [f for f in required_files if f not in zip_files]
                 
                 if missing_files:
                     raise ValueError(f"Missing required files: {missing_files}")
                 
                 # Extract to target directory
                 zip_ref.extractall(target_dir)
                 
                 return True
                 
         except zipfile.BadZipFile:
             raise ValueError("Invalid ZIP file format")
         except Exception as e:
             logger.error(f"Error extracting ZIP: {e}")
             raise
     ```

### 2.2. Content Validation

- **Requirement:**  
  The extracted directory must contain all required files and pass validation.
- **Current Status:** ✅ **PARTIALLY IMPLEMENTED** - Basic validation exists
- **Implementation Steps:**
  1. **Enhance validation** in `backend/app/services/model_validator.py`:
     ```python
     async def validate_model_contents(self, model_dir: Path) -> Dict[str, Any]:
         """Validate model package contents."""
         validation_result = {
             'is_valid': True,
             'errors': [],
             'warnings': [],
             'metadata': {}
         }
         
         try:
             # Check required files
             required_files = [
                 'model.joblib',
                 'metadata.json',
                 'deployment_manifest.json',
                 'validate_model.py',
                 'inference_example.py',
                 'requirements.txt',
                 'README.md'
             ]
             
             for file in required_files:
                 if not (model_dir / file).exists():
                     validation_result['is_valid'] = False
                     validation_result['errors'].append(f"Missing required file: {file}")
             
             # Validate metadata.json
             if (model_dir / 'metadata.json').exists():
                 try:
                     with open(model_dir / 'metadata.json', 'r') as f:
                         metadata = json.load(f)
                     
                     # Check required metadata fields
                     required_fields = ['model_type', 'version', 'created_at', 'training_info']
                     for field in required_fields:
                         if field not in metadata:
                             validation_result['warnings'].append(f"Missing metadata field: {field}")
                     
                     validation_result['metadata'] = metadata
                     
                 except json.JSONDecodeError:
                     validation_result['is_valid'] = False
                     validation_result['errors'].append("Invalid metadata.json format")
             
             # Validate deployment_manifest.json
             if (model_dir / 'deployment_manifest.json').exists():
                 try:
                     with open(model_dir / 'deployment_manifest.json', 'r') as f:
                         manifest = json.load(f)
                     
                     # Verify SHA256 hashes
                     if 'file_hashes' in manifest:
                         for filename, expected_hash in manifest['file_hashes'].items():
                             file_path = model_dir / filename
                             if file_path.exists():
                                 actual_hash = self._calculate_file_hash(file_path)
                                 if actual_hash != expected_hash:
                                     validation_result['is_valid'] = False
                                     validation_result['errors'].append(f"Hash mismatch for {filename}")
                     
                 except json.JSONDecodeError:
                     validation_result['is_valid'] = False
                     validation_result['errors'].append("Invalid deployment_manifest.json format")
             
             # Test model loading
             try:
                 model_file = model_dir / 'model.joblib'
                 if model_file.exists():
                     model = joblib.load(str(model_file))
                     validation_result['metadata']['model_type'] = type(model).__name__
             except Exception as e:
                 validation_result['is_valid'] = False
                 validation_result['errors'].append(f"Failed to load model: {str(e)}")
             
         except Exception as e:
             validation_result['is_valid'] = False
             validation_result['errors'].append(f"Validation error: {str(e)}")
         
         return validation_result
     
     def _calculate_file_hash(self, file_path: Path) -> str:
         """Calculate SHA256 hash of file."""
         import hashlib
         hash_sha256 = hashlib.sha256()
         with open(file_path, "rb") as f:
             for chunk in iter(lambda: f.read(4096), b""):
                 hash_sha256.update(chunk)
         return hash_sha256.hexdigest()
     ```

---

## 3. Model Registration and Replacement

### 3.1. Model Registry

- **Requirement:**  
  The system must maintain a registry of available models, their versions, and status.
- **Current Status:** ✅ **IMPLEMENTED** - Registry exists in `backend/app/components/model_manager.py`
- **Implementation Steps:**
  1. **Enhance registry management**:
     ```python
     async def _update_model_registry(self, model_dir: Path, status: str):
         """Update model registry with new model."""
         registry = {}
         if self.model_registry_file.exists():
             with open(self.model_registry_file, 'r') as f:
                 registry = json.load(f)
         
         # Add new model to registry
         model_version = model_dir.name
         registry[model_version] = {
             'path': str(model_dir),
             'created_at': datetime.now().isoformat(),
             'status': status,
             'last_updated': datetime.now().isoformat(),
             'import_method': 'zip_upload' if status == 'imported' else 'manual_placement'
         }
         
         # Handle model replacement
         if status == 'deployed':
             # Set all other models to 'available'
             for version, model_info in registry.items():
                 if version != model_version and model_info['status'] == 'deployed':
                     model_info['status'] = 'available'
                     model_info['last_updated'] = datetime.now().isoformat()
         
         # Save updated registry
         with open(self.model_registry_file, 'w') as f:
             json.dump(registry, f, indent=2)
     ```

---

## 4. Model Deployment and Activation

### 4.1. Deployment

- **Requirement:**  
  The user must be able to deploy (activate) a validated model via API or UI.
- **Current Status:** ✅ **IMPLEMENTED** - Deployment endpoint exists
- **Implementation Steps:**
  1. **Enhance deployment logic** in `backend/app/components/model_manager.py`:
     ```python
     async def deploy_model(self, version: str) -> bool:
         """Deploy a specific model version."""
         try:
             # Validate model exists and is available
             models = await self.list_models()
             model_info = next((m for m in models if m['version'] == version), None)
             
             if not model_info:
                 logger.error(f"Model version not found: {version}")
                 return False
             
             if model_info['status'] not in ['available', 'imported']:
                 logger.error(f"Model {version} is not available for deployment")
                 return False
             
             # Load the model to validate it
             if not await self.load_model_version(version):
                 return False
             
             # Update deployment status in metadata
             await self._update_deployment_status(version, 'deployed')
             
             # Update model registry
             await self._update_model_registry(Path(self.models_directory) / version, 'deployed')
             
             # Set as current model
             self.current_model_version = version
             
             logger.info(f"Model version {version} deployed successfully")
             return True
             
         except Exception as e:
             logger.error(f"Error deploying model version {version}: {e}")
             return False
     ```

### 4.2. Rollback

- **Requirement:**  
  The user must be able to rollback to a previous model version.
- **Current Status:** ✅ **IMPLEMENTED** - Rollback endpoint exists
- **Implementation Steps:**
  1. **Enhance rollback logic**:
     ```python
     async def rollback_model(self, version: str) -> bool:
         """Rollback to a previous model version."""
         try:
             # Check if version exists
             model_dir = self.models_directory / version
             if not model_dir.exists():
                 logger.error(f"Model version not found: {version}")
                 return False
             
             # Load the rollback model
             if not await self.load_model_version(version):
                 return False
             
             # Update deployment status
             await self._update_deployment_status(version, 'deployed')
             
             # Update current model status to available
             if self.current_model_version:
                 await self._update_deployment_status(self.current_model_version, 'available')
             
             # Update model registry
             await self._update_model_registry(model_dir, 'deployed')
             
             # Set as current model
             self.current_model_version = version
             
             logger.info(f"Rolled back to model version {version}")
             return True
             
         except Exception as e:
             logger.error(f"Error rolling back to version {version}: {e}")
             return False
     ```

---

## 5. Frontend UI Integration

### 5.1. Model Import UI

- **Requirement:**  
  The UI must allow users to select a model ZIP file from the host filesystem, upload it, and display metadata for confirmation.
- **Current Status:** ❌ **MISSING** - ZIP upload UI not implemented
- **Implementation Steps:**
  1. **Update frontend file picker** in `frontend/src/pages/Models.tsx`:
     ```typescript
     const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
       if (e.target.files && e.target.files[0]) {
         const file = e.target.files[0];
         
         // Validate file type
         if (!file.name.endsWith('.zip')) {
           toast.error('Please select a ZIP file');
           return;
         }
         
         // Validate naming convention
         if (!file.name.match(/^model_.*_deployment\.zip$/)) {
           toast.error('File must follow naming convention: model_{version}_deployment.zip');
           return;
         }
         
         setSelectedFile(file);
       }
     };
     
     const handleUpload = async () => {
       if (!selectedFile) return;
       
       try {
         const formData = new FormData();
         formData.append('file', selectedFile);
         
         const result = await endpoints.importModelPackage(formData);
         
         toast.success(`Model imported successfully: ${result.version}`);
         setShowAddModal(false);
         setSelectedFile(null);
         refetch();
       } catch (error) {
         console.error('Failed to upload model:', error);
         toast.error('Failed to upload model package');
       }
     };
     ```

  2. **Update file input** in the modal:
     ```tsx
     <Form.Group className="mb-3">
       <Form.Label>Model Package (ZIP)</Form.Label>
       <Form.Control
         type="file"
         onChange={handleFileChange}
         accept=".zip"
         placeholder="Select model package ZIP file"
       />
       <Form.Text className="text-muted">
         File must follow naming convention: model_{version}_deployment.zip
       </Form.Text>
     </Form.Group>
     ```

### 5.2. Model List and Status

- **Requirement:**  
  The UI must display all available models, their status, and allow deployment/rollback/validation actions.
- **Current Status:** ✅ **IMPLEMENTED** - Model list exists
- **Implementation Steps:**
  1. **Enhance model actions** in `frontend/src/pages/Models.tsx`:
     ```typescript
     const handleDeploy = async (version: string) => {
       try {
         await endpoints.deployModelVersion(version);
         toast.success(`Model ${version} deployed successfully`);
         refetch();
       } catch (error) {
         console.error('Failed to deploy model:', error);
         toast.error('Failed to deploy model');
       }
     };
     
     const handleRollback = async (version: string) => {
       try {
         await endpoints.rollbackModel(version);
         toast.success(`Rolled back to model ${version}`);
         refetch();
       } catch (error) {
         console.error('Failed to rollback model:', error);
         toast.error('Failed to rollback model');
       }
     };
     
     const handleValidate = async (version: string) => {
       try {
         const result = await endpoints.validateModel(version);
         if (result.is_valid) {
           toast.success(`Model ${version} validation passed`);
         } else {
           toast.error(`Model ${version} validation failed: ${result.errors.join(', ')}`);
         }
       } catch (error) {
         console.error('Failed to validate model:', error);
         toast.error('Failed to validate model');
       }
     };
     ```

---

## 6. API Endpoints

### 6.1. Required Endpoints

- **Current Status:** ✅ **MOSTLY IMPLEMENTED** - Missing ZIP upload endpoint
- **Implementation Steps:**
  1. **Add missing ZIP upload endpoint** to `backend/app/api/endpoints/model_management.py`:
     ```python
     @router.post("/import")
     async def import_model_package(
         file: UploadFile = File(...),
         validate: bool = True
     ) -> Dict[str, Any]:
         """Import a model package ZIP file."""
         # Implementation as shown in section 1.1
     ```

  2. **Update existing endpoints** to handle ZIP imports:
     ```python
     @router.get("/models")
     async def list_models() -> List[Dict[str, Any]]:
         """List all available models."""
         try:
             config = ModelConfig()
             model_manager = ModelManager(config)
             
             # Scan for new models first
             await model_manager.scan_model_directory()
             
             models = await model_manager.list_models()
             return models
         except Exception as e:
             logger.error(f"Error listing models: {e}")
             raise HTTPException(status_code=500, detail=str(e))
     ```

---

## 7. Model Directory Scanning

- **Current Status:** ✅ **IMPLEMENTED** - Scanning exists
- **Implementation Steps:**
  1. **Enhance startup scanning** in `backend/app/main.py`:
     ```python
     @app.on_event("startup")
     async def startup_event():
         """Initialize services on startup."""
         try:
             # Initialize model manager
             config = ModelConfig()
             model_manager = ModelManager(config)
             
             # Scan for new models
             new_models = await model_manager.scan_model_directory()
             if new_models:
                 logger.info(f"Found {len(new_models)} new models during startup")
             
             # Load the most recent deployed model
             models = await model_manager.list_models()
             deployed_models = [m for m in models if m['status'] == 'deployed']
             
             if deployed_models:
                 latest_model = max(deployed_models, key=lambda x: x['imported_at'])
                 await model_manager.load_model_version(latest_model['version'])
                 logger.info(f"Loaded deployed model: {latest_model['version']}")
             
         except Exception as e:
             logger.error(f"Error during startup: {e}")
     ```

---

## 8. Error Handling and User Feedback

- **Current Status:** ✅ **IMPLEMENTED** - Basic error handling exists
- **Implementation Steps:**
  1. **Enhance error handling** for ZIP uploads:
     ```python
     async def import_model_package(file: UploadFile = File(...), validate: bool = True) -> Dict[str, Any]:
         """Import a model package ZIP file."""
         try:
             # File validation
             if not file.filename:
                 raise HTTPException(status_code=400, detail="No file provided")
             
             if not file.filename.endswith('.zip'):
                 raise HTTPException(status_code=400, detail="File must be a ZIP archive")
             
             if not file.filename.startswith('model_') or not file.filename.endswith('_deployment.zip'):
                 raise HTTPException(
                     status_code=400, 
                     detail="File must follow naming convention: model_{version}_deployment.zip"
                 )
             
             # File size validation
             content = await file.read()
             if len(content) > 100 * 1024 * 1024:  # 100MB limit
                 raise HTTPException(status_code=400, detail="File size exceeds 100MB limit")
             
             # Process file
             result = await process_model_package(content, file.filename, validate)
             return result
             
         except HTTPException:
             raise
         except Exception as e:
             logger.error(f"Error importing model package: {e}")
             raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
     ```

---

## 9. Security and Permissions

- **Current Status:** ❌ **MISSING** - Security measures not implemented
- **Implementation Steps:**
  1. **Add file validation**:
     ```python
     def validate_uploaded_file(file: UploadFile) -> bool:
         """Validate uploaded file for security."""
         # Check file extension
         if not file.filename.lower().endswith('.zip'):
             return False
         
         # Check file size (100MB limit)
         if hasattr(file, 'size') and file.size > 100 * 1024 * 1024:
             return False
         
         # Check for path traversal in filename
         if '..' in file.filename or '/' in file.filename:
             return False
         
         return True
     ```

  2. **Add authentication** (if required):
     ```python
     from fastapi import Depends, HTTPException, status
     from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
     
     security = HTTPBearer()
     
     @router.post("/import")
     async def import_model_package(
         file: UploadFile = File(...),
         validate: bool = True,
         credentials: HTTPAuthorizationCredentials = Depends(security)
     ) -> Dict[str, Any]:
         """Import a model package ZIP file (authenticated)."""
         # Verify authentication
         if not verify_token(credentials.credentials):
             raise HTTPException(
                 status_code=status.HTTP_401_UNAUTHORIZED,
                 detail="Invalid authentication credentials"
             )
         
         # Process file
         # ... rest of implementation
     ```

---

## 10. Documentation and Examples

- **Current Status:** ✅ **IMPLEMENTED** - Documentation exists
- **Implementation Steps:**
  1. **Update API documentation** with new endpoints
  2. **Add usage examples** for ZIP upload
  3. **Update frontend documentation**

---

# Summary Table

| Step                        | Implementation File/Area                | Status | Notes                        |
|-----------------------------|-----------------------------------------|--------|------------------------------|
| Model import API            | backend/app/api/endpoints/model_management.py | ❌ MISSING | Need ZIP upload endpoint |
| Model extraction/validation | backend/app/services/model_loader.py        | ❌ MISSING | Need ZIP extraction logic |
| Registry management         | backend/app/components/model_manager.py     | ✅ IMPLEMENTED | Tracks models and status     |
| Deployment/activation       | backend/app/components/model_manager.py     | ✅ IMPLEMENTED | Loads model for inference    |
| UI integration              | frontend/src/pages/Models.tsx           | ❌ MISSING | Need ZIP file picker |
| Directory scanning          | backend/app/components/model_manager.py     | ✅ IMPLEMENTED | On startup/reload            |
| Error handling              | All backend and frontend layers         | ✅ IMPLEMENTED | User-friendly messages       |
| Security validation         | backend/app/api/endpoints/model_management.py | ❌ MISSING | File validation needed |

---

# Implementation Notes

- **ZIP upload endpoint is the primary missing component**
- **Frontend needs ZIP file picker and upload functionality**
- **Model extraction and validation logic needs to be implemented**
- **Security measures should be added for file uploads**
- **All model imports must be user-initiated via UI or API**
- **If a model of the same type exists, it will be replaced**
- **Validation and deployment must be explicit and user-driven**

---

## Best Practices

1. **Always validate models** before deployment in production.
2. **Keep model versions** for rollback capability.
3. **Monitor performance** after model deployment.
4. **Use descriptive naming** for model directories.
5. **Document model changes** in transfer history.
6. **Test models** on sample data before deployment.
7. **Set up alerts** for model performance issues.
8. **Regular drift monitoring** to detect degradation.
9. **Validate file uploads** for security and integrity.
10. **Provide clear error messages** for failed imports.

---

## Testing Strategy

1. **Unit Tests**: Test individual components (validation, extraction, registry)
2. **Integration Tests**: Test complete import workflow
3. **API Tests**: Test all endpoints with various scenarios
4. **Frontend Tests**: Test UI components and user interactions
5. **Security Tests**: Test file upload validation and security measures

---

## Support

For additional support:

- Check the service logs for detailed error messages.
- Review the API documentation for endpoint details.
- Consult the architecture documentation for system overview.
- Contact the development team for complex issues.

---

This enhanced plan provides complete implementation guidance for an AI coder to implement the missing ZIP upload functionality and enhance the existing model management system.