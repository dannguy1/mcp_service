import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.base_agent import BaseAgent
from app.data_service import data_service

class TestAgent(BaseAgent):
    """Test implementation of BaseAgent for testing."""
    def __init__(self):
        super().__init__("test")
        self.process_called = False
        self.process_count = 0
    
    async def _process(self):
        self.process_called = True
        self.process_count += 1

@pytest.fixture
def test_agent():
    return TestAgent()

@pytest.fixture
def mock_data_service():
    with patch('agents.base_agent.data_service') as mock:
        mock.fetch_all = AsyncMock()
        mock.execute_query = AsyncMock()
        mock.get_cached = AsyncMock()
        mock.set_cached = AsyncMock()
        yield mock

@pytest.mark.asyncio
async def test_agent_initialization(test_agent):
    """Test agent initialization."""
    assert test_agent.agent_type == "test"
    assert not test_agent.is_running
    assert test_agent.last_run is None

@pytest.mark.asyncio
async def test_agent_start_stop(test_agent):
    """Test agent start and stop functionality."""
    # Start the agent
    start_task = asyncio.create_task(test_agent.start())
    await asyncio.sleep(0.1)  # Allow time for processing
    
    assert test_agent.is_running
    assert test_agent.process_called
    assert test_agent.process_count > 0
    
    # Stop the agent
    await test_agent.stop()
    await asyncio.sleep(0.1)  # Allow time for cleanup
    
    assert not test_agent.is_running
    start_task.cancel()  # Clean up the task

@pytest.mark.asyncio
async def test_agent_double_start(test_agent):
    """Test that starting an already running agent is handled gracefully."""
    # Start the agent
    start_task = asyncio.create_task(test_agent.start())
    await asyncio.sleep(0.1)
    
    # Try to start again
    await test_agent.start()
    assert test_agent.is_running
    
    # Cleanup
    await test_agent.stop()
    start_task.cancel()

@pytest.mark.asyncio
async def test_agent_error_handling(test_agent, mock_data_service):
    """Test agent error handling."""
    # Simulate an error in _process
    async def error_process():
        raise Exception("Test error")
    
    test_agent._process = error_process
    
    # Start the agent
    start_task = asyncio.create_task(test_agent.start())
    await asyncio.sleep(0.1)
    
    # Agent should still be running despite the error
    assert test_agent.is_running
    
    # Cleanup
    await test_agent.stop()
    start_task.cancel()

@pytest.mark.asyncio
async def test_agent_data_fetching(test_agent, mock_data_service):
    """Test agent data fetching functionality."""
    # Setup mock data
    mock_data = [{"id": 1, "data": "test"}]
    mock_data_service.fetch_all.return_value = mock_data
    
    # Test fetch_data
    result = await test_agent._fetch_data("SELECT * FROM test")
    assert result == mock_data
    mock_data_service.fetch_all.assert_called_once()

@pytest.mark.asyncio
async def test_agent_cache_operations(test_agent, mock_data_service):
    """Test agent cache operations."""
    # Test cache get
    mock_data_service.get_cached.return_value = "cached_value"
    result = await test_agent._get_cached("test_key")
    assert result == "cached_value"
    mock_data_service.get_cached.assert_called_once_with("test_key")
    
    # Test cache set
    await test_agent._set_cached("test_key", "test_value", ttl=300)
    mock_data_service.set_cached.assert_called_once_with(
        "test_key", "test_value", ttl=300
    )

@pytest.mark.asyncio
async def test_agent_cache_key_generation(test_agent):
    """Test agent cache key generation."""
    key = test_agent._get_cache_key("test", "arg1", "arg2")
    assert key == "test:test:arg1:arg2"

@pytest.mark.asyncio
async def test_agent_save_anomaly(test_agent, mock_data_service):
    """Test agent anomaly saving functionality."""
    await test_agent._save_anomaly(
        device_id="test_device",
        anomaly_type="test_anomaly",
        severity=3,
        confidence=0.95,
        description="Test anomaly"
    )
    
    mock_data_service.execute_query.assert_called_once()
    call_args = mock_data_service.execute_query.call_args[0]
    assert len(call_args) == 7  # query + 6 parameters

@pytest.mark.asyncio
async def test_agent_processing_interval(test_agent):
    """Test agent processing interval."""
    # Set a custom processing interval
    test_agent._processing_interval = 0.1
    
    # Start the agent
    start_task = asyncio.create_task(test_agent.start())
    await asyncio.sleep(0.3)  # Wait for multiple processing cycles
    
    # Check that process was called multiple times
    assert test_agent.process_count >= 2
    
    # Cleanup
    await test_agent.stop()
    start_task.cancel() 