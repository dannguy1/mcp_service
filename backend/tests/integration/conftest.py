import pytest
import asyncio
from prometheus_client import CollectorRegistry

@pytest.fixture(scope="module")
def test_registry():
    """Create a test Prometheus registry."""
    registry = CollectorRegistry()
    yield registry

@pytest.fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for the test module."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def test_db():
    """Set up test database and clean up after tests."""
    from app.data_service import data_service
    
    # Initialize database
    await data_service.initialize()
    
    # Create test tables
    await data_service.execute("""
        CREATE TABLE IF NOT EXISTS wifi_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            device_id VARCHAR(50) NOT NULL,
            signal_strength INTEGER NOT NULL,
            channel INTEGER NOT NULL,
            data_rate INTEGER NOT NULL,
            packets_sent INTEGER NOT NULL,
            packets_received INTEGER NOT NULL,
            retry_count INTEGER NOT NULL
        )
    """)
    
    await data_service.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            device_id VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            type VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            status VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    yield data_service
    
    # Clean up
    await data_service.execute("DROP TABLE IF EXISTS wifi_logs")
    await data_service.execute("DROP TABLE IF EXISTS alerts")
    await data_service.close()

@pytest.fixture
def agent_config():
    """Create test configuration for WiFi agent."""
    return {
        'processing_interval': 1,  # Short interval for testing
        'batch_size': 1000,
        'lookback_window': 30,
        'model_path': 'test_model.joblib',
        'resource_monitoring': {
            'enabled': True,
            'check_interval': 1,
            'thresholds': {
                'cpu': 80,
                'memory': 85,
                'disk': 90,
                'network': 1_000_000
            }
        }
    }

@pytest.fixture
async def wifi_agent(agent_config, test_db, test_registry):
    """Create and initialize a WiFi agent for testing."""
    from app.agents.wifi_agent import WiFiAgent
    
    agent = WiFiAgent(agent_config)
    await agent.start()
    yield agent
    await agent.stop()

@pytest.fixture
async def sample_logs(test_db):
    """Insert sample logs into the database."""
    from datetime import datetime, timedelta
    
    base_time = datetime.now()
    logs = [
        (base_time, 'device1', -50, 1, 54, 100, 95, 2),
        (base_time + timedelta(minutes=1), 'device1', -55, 1, 48, 120, 110, 3),
        (base_time + timedelta(minutes=2), 'device2', -60, 6, 36, 90, 80, 5)
    ]
    
    for log in logs:
        await test_db.execute("""
            INSERT INTO wifi_logs 
            (timestamp, device_id, signal_strength, channel, data_rate, 
             packets_sent, packets_received, retry_count)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, *log)
    
    return logs 