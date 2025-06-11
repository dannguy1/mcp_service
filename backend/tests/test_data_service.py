import pytest
import json
from datetime import datetime, timedelta
from mcp_service.data_service import DataService
from mcp_service.config import Config

@pytest.fixture
async def data_service():
    """Create a DataService instance for testing."""
    config = Config()
    service = DataService(config)
    await service.start()
    yield service
    await service.stop()

@pytest.fixture
def mock_logs():
    """Create mock log entries for testing."""
    return [
        {
            'timestamp': (datetime.now() - timedelta(minutes=4)).isoformat(),
            'message': 'wlan0: STA 00:11:22:33:44:55 IEEE 802.11: authenticated',
            'program': 'hostapd',
            'device_id': 1
        },
        {
            'timestamp': (datetime.now() - timedelta(minutes=3)).isoformat(),
            'message': 'wlan0: STA 00:11:22:33:44:55 IEEE 802.11: associated',
            'program': 'hostapd',
            'device_id': 1
        },
        {
            'timestamp': (datetime.now() - timedelta(minutes=2)).isoformat(),
            'message': 'wlan0: STA 00:11:22:33:44:55 IEEE 802.11: disassociated',
            'program': 'hostapd',
            'device_id': 1
        },
        {
            'timestamp': (datetime.now() - timedelta(minutes=1)).isoformat(),
            'message': 'wlan0: STA 00:11:22:33:44:55 IEEE 802.11: deauthenticated',
            'program': 'hostapd',
            'device_id': 1
        }
    ]

@pytest.fixture
def mock_anomaly():
    """Create a mock anomaly for testing."""
    return {
        'agent_name': 'WiFiAgent',
        'device_id': 1,
        'timestamp': datetime.now().isoformat(),
        'anomaly_type': 'auth_failure',
        'severity': 3,
        'confidence': 0.95,
        'description': 'Multiple authentication failures detected',
        'features': json.dumps({
            'auth_failures': 5,
            'deauth_count': 2,
            'beacon_count': 100,
            'unique_mac_count': 3,
            'unique_ssid_count': 2,
            'reason_codes': {'3': 2, '4': 1},
            'status_codes': {'0': 1, '1': 1}
        }),
        'status': 'new',
        'synced': 0,
        'resolution_status': 'open'
    }

@pytest.mark.asyncio
async def test_get_logs_by_program(data_service, mock_logs):
    """Test retrieving logs by program."""
    # Mock the PostgreSQL query
    data_service.pg_pool = type('MockPool', (), {
        'fetch': lambda *args, **kwargs: mock_logs
    })
    
    logs = await data_service.get_logs_by_program(
        start_time=(datetime.now() - timedelta(minutes=5)).isoformat(),
        end_time=datetime.now().isoformat(),
        programs=['hostapd']
    )
    
    assert len(logs) == 4
    assert all(log['program'] == 'hostapd' for log in logs)

@pytest.mark.asyncio
async def test_store_anomaly(data_service, mock_anomaly):
    """Test storing an anomaly."""
    anomaly_id = await data_service.store_anomaly(mock_anomaly)
    assert anomaly_id is not None
    
    # Verify the anomaly was stored
    stored_anomaly = await data_service.get_anomaly(anomaly_id)
    assert stored_anomaly['agent_name'] == mock_anomaly['agent_name']
    assert stored_anomaly['anomaly_type'] == mock_anomaly['anomaly_type']
    assert stored_anomaly['severity'] == mock_anomaly['severity']

@pytest.mark.asyncio
async def test_get_anomalies(data_service, mock_anomaly):
    """Test retrieving anomalies with filters."""
    # Store a test anomaly
    await data_service.store_anomaly(mock_anomaly)
    
    # Test different filter combinations
    anomalies = await data_service.get_anomalies(
        limit=10,
        offset=0,
        agent_name='WiFiAgent',
        status='new',
        resolution_status='open'
    )
    
    assert len(anomalies) > 0
    assert all(a['agent_name'] == 'WiFiAgent' for a in anomalies)
    assert all(a['status'] == 'new' for a in anomalies)
    assert all(a['resolution_status'] == 'open' for a in anomalies)

@pytest.mark.asyncio
async def test_update_anomaly_status(data_service, mock_anomaly):
    """Test updating anomaly status."""
    # Store a test anomaly
    anomaly_id = await data_service.store_anomaly(mock_anomaly)
    
    # Update the status
    await data_service.update_anomaly_status(
        anomaly_id,
        status='acknowledged',
        resolution_status='resolved',
        resolution_notes='Fixed by restarting the access point'
    )
    
    # Verify the update
    updated_anomaly = await data_service.get_anomaly(anomaly_id)
    assert updated_anomaly['status'] == 'acknowledged'
    assert updated_anomaly['resolution_status'] == 'resolved'
    assert updated_anomaly['resolution_notes'] == 'Fixed by restarting the access point'

@pytest.mark.asyncio
async def test_cache_operations(data_service, mock_logs):
    """Test Redis cache operations."""
    # Test cache set and get
    cache_key = 'test_logs'
    await data_service.cache.set(cache_key, json.dumps(mock_logs))
    
    cached_logs = await data_service.cache.get(cache_key)
    assert cached_logs is not None
    assert len(json.loads(cached_logs)) == len(mock_logs)
    
    # Test cache delete
    await data_service.cache.delete(cache_key)
    cached_logs = await data_service.cache.get(cache_key)
    assert cached_logs is None 