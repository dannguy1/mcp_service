import pytest
from unittest.mock import patch, MagicMock
import psutil

from components.resource_monitor import ResourceMonitor

@pytest.fixture
def resource_monitor(test_registry):
    """Create a ResourceMonitor instance for testing."""
    return ResourceMonitor(registry=test_registry)

def test_resource_monitor_initialization(resource_monitor):
    """Test ResourceMonitor initialization."""
    assert resource_monitor.thresholds['cpu'] == 80
    assert resource_monitor.thresholds['memory'] == 85
    assert resource_monitor.thresholds['disk'] == 90
    assert resource_monitor.thresholds['network'] == 1_000_000  # 1MB/s

def test_get_set_thresholds(resource_monitor):
    """Test getting and setting thresholds."""
    # Test getting thresholds
    thresholds = resource_monitor.get_thresholds()
    assert thresholds['cpu'] == 80
    assert thresholds['memory'] == 85
    assert thresholds['disk'] == 90
    assert thresholds['network'] == 1_000_000

    # Test setting thresholds
    new_thresholds = {
        'cpu': 70,
        'memory': 75,
        'disk': 80,
        'network': 2_000_000
    }
    resource_monitor.set_thresholds(new_thresholds)
    
    updated_thresholds = resource_monitor.get_thresholds()
    assert updated_thresholds['cpu'] == 70
    assert updated_thresholds['memory'] == 75
    assert updated_thresholds['disk'] == 80
    assert updated_thresholds['network'] == 2_000_000

@patch('psutil.cpu_percent')
@patch('psutil.virtual_memory')
@patch('psutil.disk_usage')
@patch('psutil.net_io_counters')
def test_check_resources(mock_net_io, mock_disk, mock_memory, mock_cpu, resource_monitor):
    """Test resource checking functionality."""
    # Mock system metrics
    mock_cpu.return_value = 50.0
    mock_memory.return_value = MagicMock(percent=60.0)
    mock_disk.return_value = MagicMock(percent=70.0)
    mock_net_io.return_value = MagicMock(
        bytes_sent=1000000,
        bytes_recv=1000000
    )

    # Check resources
    resources = resource_monitor.check_resources()
    
    assert resources['cpu'] == 50.0
    assert resources['memory'] == 60.0
    assert resources['disk'] == 70.0
    assert resources['network']['sent'] == 1000000
    assert resources['network']['received'] == 1000000

@patch('psutil.cpu_percent')
@patch('psutil.virtual_memory')
@patch('psutil.disk_usage')
@patch('psutil.net_io_counters')
def test_check_alerts(mock_net_io, mock_disk, mock_memory, mock_cpu, resource_monitor):
    """Test alert generation functionality."""
    # Mock system metrics above thresholds
    mock_cpu.return_value = 90.0  # Above 80% threshold
    mock_memory.return_value = MagicMock(percent=90.0)  # Above 85% threshold
    mock_disk.return_value = MagicMock(percent=95.0)  # Above 90% threshold
    mock_net_io.return_value = MagicMock(
        bytes_sent=2000000,  # Above 1MB/s threshold
        bytes_recv=2000000
    )

    # Check for alerts
    alerts = resource_monitor.check_alerts()
    
    assert len(alerts) == 4
    assert any(alert['type'] == 'cpu' and alert['value'] == 90.0 for alert in alerts)
    assert any(alert['type'] == 'memory' and alert['value'] == 90.0 for alert in alerts)
    assert any(alert['type'] == 'disk' and alert['value'] == 95.0 for alert in alerts)
    assert any(alert['type'] == 'network' and alert['value'] == 2000000 for alert in alerts)

def test_get_process_info(resource_monitor):
    """Test process information retrieval."""
    process_info = resource_monitor.get_process_info()
    
    assert 'pid' in process_info
    assert 'cpu_percent' in process_info
    assert 'memory_percent' in process_info
    assert 'num_threads' in process_info
    assert 'create_time' in process_info

@patch('psutil.cpu_percent')
@patch('psutil.virtual_memory')
@patch('psutil.disk_usage')
@patch('psutil.net_io_counters')
def test_metrics_recording(mock_net_io, mock_disk, mock_memory, mock_cpu, resource_monitor, test_registry):
    """Test Prometheus metrics recording."""
    # Mock system metrics
    mock_cpu.return_value = 50.0
    mock_memory.return_value = MagicMock(percent=60.0)
    mock_disk.return_value = MagicMock(percent=70.0)
    mock_net_io.return_value = MagicMock(
        bytes_sent=1000000,
        bytes_recv=1000000
    )

    # Check resources to trigger metrics recording
    resource_monitor.check_resources()
    
    # Verify metrics were recorded
    metrics = {m.name: m for m in test_registry.collect()}
    assert 'cpu_usage_percent' in metrics
    assert 'memory_usage_percent' in metrics
    assert 'disk_usage_percent' in metrics
    assert 'network_io_bytes' in metrics 