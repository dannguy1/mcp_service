import asyncio
import os
import pytest
from typing import AsyncGenerator, Generator

import asyncpg
import redis.asyncio as redis
from prometheus_client import CollectorRegistry

from app.config.config import config
from app.mcp_service.data_service import DataService

# Test configuration
TEST_DB_NAME = "mcp_service_test"
TEST_REDIS_DB = 1

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db() -> AsyncGenerator:
    """Create a test database and yield a connection."""
    # For now, skip database setup since we're testing export functionality
    # that doesn't require a full database setup
    yield None

@pytest.fixture(scope="session")
async def test_redis() -> AsyncGenerator:
    """Create a test Redis connection."""
    # For now, skip Redis setup since we're testing export functionality
    # that doesn't require Redis
    yield None

@pytest.fixture(scope="session")
def test_registry() -> CollectorRegistry:
    """Create a test Prometheus registry."""
    return CollectorRegistry()

@pytest.fixture(autouse=True)
async def setup_test_env(test_db, test_redis):
    """Setup test environment before each test."""
    # For now, skip complex setup since we're testing export functionality
    yield

@pytest.fixture
def mock_config(monkeypatch):
    """Mock config for testing."""
    monkeypatch.setattr(config, 'DEBUG', True)
    return config
