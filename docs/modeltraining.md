# **Design Specification: Model Training and Deployment Workflow**

## **1\. Overview**

This document details the process for training anomaly detection models (e.g., Isolation Forest) and deploying them to the **Modular, Extensible AI Processing Service**. The workflow is designed to be **decoupled**, with resource-intensive training performed in a separate, more powerful environment (the "Training Environment") and the lightweight inference performed by the service on a device like a Raspberry Pi 5\.

The core principle is that the AI processing service is a consumer of pre-trained models. It does not perform training itself. Models and their associated metadata are stored on disk, allowing for simple, file-based updates.

### **Workflow Stages**

1. **Data Export**: Extracting a representative dataset of logs from the production database.  
2. **Model Training**: Using the exported data in a dedicated environment to train a new model and generate associated metadata.  
3. **Model Deployment**: Securely transferring the new model files to the AI processing service's model storage.  
4. **Model Loading**: The running service automatically detects and loads the new active model for inference without requiring a restart.

## **2\. Architecture for Training**

The training process occurs entirely outside the runtime environment of the AI processing service.

Code snippet

graph TD  
    subgraph ProductionEnvironment\["Production Environment (e.g., Raspberry Pi)"\]  
        direction LR  
        MCPService\["Modular AI Service"\]  
        DB\[(PostgreSQL Database)\]  
        ModelStorage\[(Disk Model Storage\\n/app/models)\]  
    end

    subgraph TrainingEnvironment\["Training Environment (e.g., Developer Laptop/Cloud VM)"\]  
        direction LR  
        TrainingScripts\["Training Scripts"\]  
        LocalModelFiles\["Local Model Files"\]  
        ExportedData\["Exported Log Data (CSV)"\]  
    end

    DB \-- 1\. Export Logs \--\> ExportedData  
    TrainingScripts \-- 2\. Read Data \--\> ExportedData  
    TrainingScripts \-- 3\. Train Model \--\> LocalModelFiles  
    LocalModelFiles \-- 4\. Deploy via SCP/SFTP \--\> ModelStorage  
    MCPService \-- 5\. Load New Model \--\> ModelStorage

## **3\. Data Management for Training**

### **3.1. Data Export**

A utility script will be used to extract a large, representative dataset of "normal" logs from the production log\_entries table.

* **Script**: export\_logs.py  
* **Functionality**:  
  * Connects securely to the production PostgreSQL database (read-only credentials recommended).  
  * Queries the log\_entries table for a specified time range (e.g., the last 30 days).  
  * Filters for logs relevant to the agent being trained (e.g., program IN ('hostapd', 'wpa\_supplicant') for the WiFiAgent).  
  * Exports the data to a local .csv file (training\_data\_wifi.csv).  
* **Example Usage**:  
  Bash  
  python export\_logs.py \\  
      \--start-date "2025-05-01" \\  
      \--end-date "2025-06-01" \\  
      \--output-file "training\_data\_wifi.csv" \\  
      \--programs "hostapd,wpa\_supplicant"

### **3.2. Data Storage**

* **Format**: The exported log data is stored in CSV format for portability and ease of use with data science libraries like Pandas.  
* **Location**: The CSV file is transferred to the Training Environment. It is not stored within the AI service's runtime environment.

## **4\. Model Training Process**

The training process is executed manually or via automation in the Training Environment using a dedicated script.

* **Script**: train\_model.py  
* **Workflow**:  
  1. **Load Data**: The script loads the training\_data\_wifi.csv into a Pandas DataFrame.  
  2. **Feature Extraction**: It uses the same FeatureExtractor class that the production WiFiAgent uses. This is crucial for consistency. The features are generated from the raw log data.  
  3. **Model Initialization**: An Isolation Forest model is initialized with a specific contamination parameter (the expected ratio of anomalies, a key hyperparameter).  
  4. **Training**: The model.fit() method is called on the extracted features.  
  5. **Serialization**: The trained model object is serialized to a file using joblib.dump().  
  6. **Metadata Generation**: A corresponding metadata JSON file is created, containing information about the training.

### **4.1. Model Files and Naming Convention**

For each trained model, two files are generated:

1. **Model Binary**: wifi\_model\_YYYYMMDD\_HHMMSS.joblib  
   * Contains the serialized, trained IsolationForest object.  
   * The timestamp in the filename serves as the version identifier.  
2. **Metadata File**: wifi\_metadata\_YYYYMMDD\_HHMMSS.json  
   * A JSON file containing critical information about the model.  
   * This file is used by the ModelManager in the production service to understand and validate the model.  
* **Example Metadata File (wifi\_metadata\_20250607\_230000.json)**:  
  JSON  
  {  
    "model\_version": "20250607\_230000",  
    "model\_file": "wifi\_model\_20250607\_230000.joblib",  
    "agent\_name": "wifi",  
    "training\_date": "2025-06-07T23:00:00Z",  
    "training\_data\_source": "training\_data\_wifi.csv",  
    "training\_log\_count": 1572030,  
    "hyperparameters": {  
      "n\_estimators": 100,  
      "contamination": 0.01,  
      "max\_samples": "auto",  
      "random\_state": 42  
    },  
    "features\_used": \[  
      "log\_count",  
      "error\_log\_ratio",  
      "unique\_program\_count",  
      "disassociation\_events"  
    \]  
  }

## **5\. Model Deployment**

Deployment is a file-based operation.

1. **Transfer**: The newly created .joblib and .json files are securely transferred (e.g., using SCP, SFTP, or an equivalent secure method) from the Training Environment to the production service's model directory.  
   * **Destination**: /app/models/ inside the Docker container, which maps to the models Docker volume.  
2. **Activation**: To make a new model the active one for inference, a simple symbolic link is used within the model directory.  
   * The ModelManager in the service looks for wifi\_model\_active.joblib and wifi\_metadata\_active.json.  
   * The deployment process involves updating this symlink to point to the new version files.  
     Bash  
     \# On the host machine running Docker, within the 'models' volume directory  
     ln \-snf wifi\_model\_20250607\_230000.joblib wifi\_model\_active.joblib  
     ln \-snf wifi\_metadata\_20250607\_230000.json wifi\_metadata\_active.json

## **6\. Model Loading and Inference in Production**

The AI processing service is designed to load and use the deployed models seamlessly.

### **ModelManager Responsibilities**

* **start()**: On service startup, the ModelManager loads the model pointed to by the wifi\_model\_active.joblib symlink.  
* **Hot-Reload (optional enhancement)**: The ModelManager can be designed to periodically check if the wifi\_model\_active.joblib symlink has changed. If it has, it can load the new model into memory without requiring a service restart, allowing for zero-downtime model updates.  
* **infer()**: During each analysis cycle, the agent passes features to the ModelManager, which uses the loaded model object to call model.predict() and return the anomaly scores.

### **Code Snippet: WiFiModelManager**

Python

\# mcp\_service/components/wifi\_model\_manager.py  
import joblib  
import json  
import os  
import logging

class WiFiModelManager:  
    def \_\_init\_\_(self, config):  
        self.model\_dir \= "/app/models"  
        self.active\_model\_path \= os.path.join(self.model\_dir, "wifi\_model\_active.joblib")  
        self.active\_metadata\_path \= os.path.join(self.model\_dir, "wifi\_metadata\_active.json")  
        self.model \= None  
        self.metadata \= None  
        self.logger \= logging.getLogger("WiFiModelManager")

    async def start(self):  
        """Loads the active model from disk."""  
        if not os.path.exists(self.active\_model\_path):  
            self.logger.error(f"Active model not found at {self.active\_model\_path}")  
            return  
              
        try:  
            self.model \= joblib.load(self.active\_model\_path)  
            with open(self.active\_metadata\_path, 'r') as f:  
                self.metadata \= json.load(f)  
            self.logger.info(f"Successfully loaded model version: {self.metadata.get('model\_version')}")  
        except Exception as e:  
            self.logger.error(f"Failed to load model: {e}")  
            self.model \= None  
            self.metadata \= None

    def infer(self, features):  
        """Runs inference using the loaded model."""  
        if self.model is None:  
            self.logger.warning("No model loaded, skipping inference.")  
            return \[\]  
          
        \# The model's predict method returns \-1 for anomalies, 1 for inliers  
        predictions \= self.model.predict(features)  
        return predictions

## **7\. Conclusion**

This decoupled training workflow provides a clear and robust separation of concerns. It allows for resource-intensive training to be performed in a suitable environment without impacting the performance of the lightweight, production inference service. The file-based deployment mechanism is simple, scriptable, and well-suited for the target architecture, ensuring that updated models can be deployed reliably and used by the service for improved anomaly detection.