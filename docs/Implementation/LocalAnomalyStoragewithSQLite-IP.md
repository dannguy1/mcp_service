# **Local Anomaly Storage with SQLite**

## **1\. Overview and Objectives**

This document outlines the implementation plan to modify the AnalyzerMCPServer to store detected anomalies in a local **SQLite database** instead of the source PostgreSQL database. This architectural change enhances service decoupling, reduces write-load on the central database, and makes the service more self-contained.

To ensure the main Log Monitor application can display these anomalies, this plan includes the creation of a secure API endpoint within the service to expose the locally stored data.

### **Key Objectives**

* **Modify Data Storage**: Reroute anomaly storage from PostgreSQL to a local SQLite database file.  
* **Enhance Decoupling**: Make the service's only dependency on the source database read-only.  
* **Expose Data via API**: Create a new, authenticated REST API endpoint (GET /api/v1/anomalies) for the main application to retrieve anomaly data.  
* **Persist Local Data**: Ensure the SQLite database is persisted across container restarts using a Docker volume.  
* **Maintain Modularity**: Ensure the existing agent-based architecture continues to function seamlessly with the new storage backend.

## **2\. Architectural Changes**

The core architecture remains the same, but the data flow for anomaly storage and retrieval is significantly altered.

### **Revised Architecture Diagram**

Code snippet

flowchart TD  
    subgraph ModularMCPService\["Modular AI Service (Single Process)"\]  
        direction LR  
        DataService\["DataService"\]  
          
        subgraph Agents\["Analysis Agents"\]  
            direction TB  
            WifiAgent\["WiFiAgent"\]  
        end

        subgraph LocalStorage\["Local Storage"\]  
            SQLiteDB\[(Local SQLite DB\\n/data/mcp\_anomalies.db)\]  
            ModelStorage\[(Disk Model Storage\\n/app/models)\]  
        end

        subgraph SharedComponents  
            Pool\[(PG Read Pool)\]  
            APIEndpoints\["API Endpoints\\n/health\\n/api/v1/anomalies"\]  
        end

        DataService \-- Manages \--\> Pool  
        DataService \-- Manages \--\> SQLiteDB  
          
        WifiAgent \-- Uses \--\> DataService  
        APIEndpoints \-- Calls \--\> DataService  
    end

    subgraph LogMonitorApp\["Log Monitor Main App (External)"\]  
        direction TB  
        MainBackend\["Main Flask Backend"\]  
        MainUI\["React Frontend"\]  
    end  
      
    subgraph External\["External Systems"\]  
        SourceDB\[(PostgreSQL Database)\]  
    end

    DataService \--\>|Reads Logs| SourceDB  
    WifiAgent \--\>|Reads Models| ModelStorage  
    MainBackend \--\>|Queries Anomalies| APIEndpoints

### **Summary of Changes**

1. **New SQLite Database**: A mcp\_anomalies.db file will be created and managed within the service's Docker volume.  
2. **DataService Update**: The DataService will now manage two database connections: an asyncpg pool for reading source logs and an aiosqlite connection for reading/writing local anomalies.  
3. **New API Endpoint**: An aiohttp endpoint, GET /api/v1/anomalies, will be added to serve data from the SQLite database.  
4. **New Docker Volume**: A /data volume will be added to docker-compose.yml to persist the SQLite file.

## ---

**Phase 1: Setup and Configuration**

### **1.1. Update Dependencies (requirements.txt)**

A new library is required for asynchronous SQLite operations.

Plaintext

\# Add this line to requirements.txt  
aiosqlite==0.19.0

### **1.2. Update Docker Configuration (docker-compose.yml)**

Add a new volume for persisting the SQLite database.

YAML

version: '3.8'  
services:  
  mcp-service:  
    \# ... existing configuration ...  
    volumes:  
      \- models:/app/models  
      \- anomaly\_data:/app/data  \# \<-- Add this line  
\# ... existing configuration ...  
volumes:  
  models:  
  anomaly\_data: {}  \# \<-- Add this line

### **1.3. Update Environment Setup**

Add the path for the SQLite database to .env.example and config.py.

* **.env.example**:  
  Plaintext  
  \# ... existing variables ...  
  SQLITE\_DB\_PATH=/app/data/mcp\_anomalies.db

* **config.py**:  
  Python  
  \# In Config.\_\_init\_\_  
  self.sqlite\_db\_path \= os.getenv('SQLITE\_DB\_PATH', '/app/data/mcp\_anomalies.db')

## ---

**Phase 2: Database Layer Modification**

### **2.1. New Local Database Initializer (init\_local\_db.py)**

This script will create the SQLite database and mcp\_anomalies table.

Python

\# mcp\_service/init\_local\_db.py  
import asyncio  
import aiosqlite  
import os  
from config import Config  
import logging

async def init\_local\_db(config):  
    logger \= logging.getLogger("InitLocalDB")  
    db\_path \= config.sqlite\_db\_path  
    os.makedirs(os.path.dirname(db\_path), exist\_ok=True)  
      
    try:  
        async with aiosqlite.connect(db\_path) as db:  
            await db.execute('''  
                CREATE TABLE IF NOT EXISTS mcp\_anomalies (  
                    id INTEGER PRIMARY KEY AUTOINCREMENT,  
                    agent\_name TEXT NOT NULL,  
                    device\_id INTEGER,  
                    timestamp TEXT NOT NULL,  
                    anomaly\_type TEXT NOT NULL,  
                    confidence REAL NOT NULL,  
                    description TEXT,  
                    features TEXT, \-- Storing JSON as TEXT  
                    created\_at TEXT DEFAULT CURRENT\_TIMESTAMP  
                );  
            ''')  
            await db.execute('''  
                CREATE INDEX IF NOT EXISTS idx\_anomalies\_timestamp ON mcp\_anomalies(timestamp);  
            ''')  
            await db.execute('''  
                CREATE INDEX IF NOT EXISTS idx\_anomalies\_agent ON mcp\_anomalies(agent\_name);  
            ''')  
            await db.commit()  
            logger.info(f"Local SQLite database initialized successfully at {db\_path}")  
    except Exception as e:  
        logger.error(f"Failed to initialize local database: {e}")  
        raise

if \_\_name\_\_ \== "\_\_main\_\_":  
    config \= Config()  
    \# It's better to setup logging before running  
    \# from logging\_config import setup\_logging  
    \# setup\_logging(config.log\_level)  
    asyncio.run(init\_local\_db(config))

**Instruction**: Run this script once before starting the service for the first time: python init\_local\_db.py.

### **2.2. Update DataService (data\_service.py)**

Modify the DataService to handle both PostgreSQL and SQLite connections. The store\_anomalies method is rewritten, and a new get\_anomalies method is added.

Python

\# mcp\_service/data\_service.py  
import asyncpg  
import aiosqlite  
import json  
\# ... other imports ...

class DataService:  
    def \_\_init\_\_(self, config):  
        \# ... existing initializations ...  
        self.sqlite\_db\_path \= config.sqlite\_db\_path  
        self.sqlite\_conn \= None

    async def start(self):  
        try:  
            \# Start PostgreSQL pool  
            self.pool \= await asyncpg.create\_pool(\*\*self.db\_config)  
              
            \# Start SQLite connection  
            self.sqlite\_conn \= await aiosqlite.connect(self.sqlite\_db\_path)  
              
            \# Start Redis  
            self.redis \= redis.Redis(\*\*self.redis\_config)  
            self.logger.info("Initialized PostgreSQL, SQLite, and Redis connections")  
        except Exception as e:  
            self.logger.error(f"Failed to start DataService: {e}")  
            raise

    async def stop(self):  
        try:  
            if self.pool: await self.pool.close()  
            if self.sqlite\_conn: await self.sqlite\_conn.close()  
            if self.redis: await self.redis.close()  
            self.logger.info("Closed all database and Redis connections")  
        except Exception as e:  
            self.logger.error(f"Failed to stop DataService cleanly: {e}")

    \# get\_logs\_by\_program method remains the same...

    async def store\_anomalies(self, anomalies: list):  
        """Rewritten to store anomalies in the local SQLite database."""  
        try:  
            for anomaly in anomalies:  
                await self.sqlite\_conn.execute(  
                    """  
                    INSERT INTO mcp\_anomalies (agent\_name, device\_id, timestamp, anomaly\_type, confidence, description, features)  
                    VALUES (?, ?, ?, ?, ?, ?, ?)  
                    """,  
                    (  
                        anomaly.get("agent\_name"),  
                        anomaly.get("device\_id"),  
                        anomaly.get("timestamp"),  
                        anomaly.get("anomaly\_type"),  
                        anomaly.get("confidence"),  
                        anomaly.get("description"),  
                        json.dumps(anomaly.get("features", {})) \# Store features as JSON text  
                    )  
                )  
            await self.sqlite\_conn.commit()  
            self.logger.info(f"Stored {len(anomalies)} anomalies to local SQLite DB")  
        except Exception as e:  
            self.logger.error(f"Failed to store anomalies to SQLite: {e}")  
            raise

    async def get\_anomalies(self, limit=100, offset=0, agent\_name=None):  
        """New method to retrieve anomalies from the local SQLite database."""  
        try:  
            query \= "SELECT \* FROM mcp\_anomalies"  
            params \= \[\]  
            if agent\_name:  
                query \+= " WHERE agent\_name \= ?"  
                params.append(agent\_name)  
              
            query \+= " ORDER BY timestamp DESC LIMIT ? OFFSET ?"  
            params.extend(\[limit, offset\])

            cursor \= await self.sqlite\_conn.execute(query, tuple(params))  
            rows \= await cursor.fetchall()  
              
            \# Convert rows to dictionaries  
            columns \= \[desc\[0\] for desc in cursor.description\]  
            anomalies \= \[dict(zip(columns, row)) for row in rows\]

            \# Parse features string back to dict  
            for anomaly in anomalies:  
                if anomaly.get('features'):  
                    anomaly\['features'\] \= json.loads(anomaly\['features'\])

            return anomalies  
        except Exception as e:  
            self.logger.error(f"Failed to retrieve anomalies from SQLite: {e}")  
            return \[\]

    \# health() method remains the same...

## ---

**Phase 3: API Endpoint Implementation**

### **3.1. Update Main Entrypoint (mcp\_service.py)**

Add the new API endpoint and its handler to the aiohttp web application.

Python

\# mcp\_service/mcp\_service.py  
\# ... other imports ...

async def get\_anomalies\_handler(request):  
    """Handler for the new /api/v1/anomalies endpoint."""  
    logger \= logging.getLogger("API")  
    try:  
        \# Secure this endpoint with the same token  
        token \= request.headers.get('Authorization', '').replace('Bearer ', '')  
        if token \!= request.app\['config'\].health\_token:  
            logger.warning("Invalid token for /api/v1/anomalies")  
            return web.json\_response({"error": "Unauthorized"}, status=401)  
          
        \# Get query parameters  
        limit \= int(request.query.get('limit', 100))  
        offset \= int(request.query.get('offset', 0))  
        agent\_name \= request.query.get('agent\_name')

        data\_service \= request.app\['data\_service'\]  
        anomalies \= await data\_service.get\_anomalies(  
            limit=limit, offset=offset, agent\_name=agent\_name  
        )  
        return web.json\_response(anomalies, status=200)

    except Exception as e:  
        logger.error(f"Error in get\_anomalies\_handler: {e}")  
        return web.json\_response({"error": "Internal Server Error"}, status=500)

async def main():  
    \# ... existing main function logic ...  
      
    \# In the web server setup section:  
    app \= web.Application()  
    app\['data\_service'\] \= data\_service  
    app\['config'\] \= config  
    app.router.add\_get("/health", health\_check\_handler)  
    app.router.add\_get("/api/v1/anomalies", get\_anomalies\_handler) \# \<-- Add this route  
    runner \= web.AppRunner(app)  
    \# ... rest of main function ...

## ---

**Phase 4: Testing and Validation**

### **4.1. Update Tests**

* **tests/test\_data\_service.py**:  
  * Modify tests for store\_anomalies to mock aiosqlite instead of asyncpg.  
  * Add new tests for the get\_anomalies method, checking filtering by agent\_name and pagination with limit/offset.

### **4.2. New API Tests (tests/test\_api.py)**

Create a new test file to validate the API endpoint.

Python

\# mcp\_service/tests/test\_api.py  
import pytest  
from unittest.mock import AsyncMock, patch

\# This requires pytest-aiohttp  
\# Add to requirements.txt: pytest-aiohttp

\# A basic example structure  
@pytest.mark.asyncio  
async def test\_get\_anomalies\_unauthorized(aiohttp\_client, loop):  
    \# Mock necessary parts and create the app  
    app \= \# ... create aiohttp app instance  
    client \= await aiohttp\_client(app)  
    resp \= await client.get("/api/v1/anomalies")  
    assert resp.status \== 401

@pytest.mark.asyncio  
async def test\_get\_anomalies\_success(aiohttp\_client, loop):  
    \# Mock the DataService.get\_anomalies method  
    with patch('data\_service.DataService.get\_anomalies', new=AsyncMock()) as mock\_get:  
        mock\_get.return\_value \= \[{'agent\_name': 'wifi', 'description': 'Test'}\]  
        app \= \# ... create app instance with mocked service  
        client \= await aiohttp\_client(app)  
          
        \# Make request with valid token  
        headers \= {'Authorization': 'Bearer your-secret-token'}  
        resp \= await client.get("/api/v1/anomalies", headers=headers)  
          
        assert resp.status \== 200  
        data \= await resp.json()  
        assert len(data) \== 1  
        assert data\[0\]\['agent\_name'\] \== 'wifi'

## ---

**Phase 5: Documentation and UI Integration Path**

### **5.1. Update API Documentation (docs/api.md)**

Add the specification for the new endpoint.

Markdown

\#\# Get Anomalies  
\- **\*\*URL\*\***: \`/api/v1/anomalies\`  
\- **\*\*Method\*\***: GET  
\- **\*\*Headers\*\***:  
  \- \`Authorization: Bearer \<HEALTH\_TOKEN\>\`  
\- **\*\*Query Parameters\*\***:  
  \- \`limit\` (integer, optional, default: 100): Number of records to return.  
  \- \`offset\` (integer, optional, default: 0): Number of records to skip for pagination.  
  \- \`agent\_name\` (string, optional): Filter anomalies by a specific agent (e.g., \`wifi\`).  
\- **\*\*Success Response (200 OK)\*\***:  
  \`\`\`json  
  \[  
    {  
      "id": 1,  
      "agent\_name": "wifi",  
      "device\_id": null,  
      "timestamp": "2025-06-10T17:30:00",  
      "anomaly\_type": "wifi\_anomaly",  
      "confidence": 0.98,  
      "description": "High WiFi disassociation events detected (15)",  
      "features": {"log\_count": 500, "disassociation\_events": 15},  
      "created\_at": "2025-06-10T17:31:05"  
    }  
  \]

\#\#\# 5.2. Integration Path for Log Monitor UI  
The main Log Monitor application (the Flask backend) must be modified to fetch anomalies from this new source.

1\.  \*\*Remove Direct DB Queries\*\*: The code in the main Flask application that queries the PostgreSQL \`mcp\_anomalies\` table should be removed.  
2\.  \*\*Implement API Client\*\*: Add a function in the Flask backend that makes a \`GET\` request to \`http://mcp-service:5555/api/v1/anomalies\` (using the Docker service name). This function should include the shared \`HEALTH\_TOKEN\` in the Authorization header.  
3\.  \*\*Update UI Routes\*\*: The Flask routes that serve data to the frontend log viewer/dashboard must be updated to call this new API client function to get their data.

This completes the transition to a fully decoupled anomaly detection service with local storage.  
