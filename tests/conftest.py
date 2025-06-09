import asyncio
import os
import pytest
from typing import AsyncGenerator, Generator

import asyncpg
import redis.asyncio as redis
from prometheus_client import CollectorRegistry

from config import settings
from data_service import data_service

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
    # Connect to default database to create test database
    sys_conn = await asyncpg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database='postgres'
    )
    
    # Create test database
    await sys_conn.execute(f'DROP DATABASE IF EXISTS {TEST_DB_NAME}')
    await sys_conn.execute(f'CREATE DATABASE {TEST_DB_NAME}')
    await sys_conn.close()
    
    # Connect to test database
    conn = await asyncpg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=TEST_DB_NAME
    )
    
    yield conn
    
    # Cleanup
    await conn.close()
    sys_conn = await asyncpg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database='postgres'
    )
    await sys_conn.execute(f'DROP DATABASE IF EXISTS {TEST_DB_NAME}')
    await sys_conn.close()

@pytest.fixture(scope="session")
async def test_redis() -> AsyncGenerator:
    """Create a test Redis connection."""
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=TEST_REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=True
    )
    
    yield redis_client
    
    # Cleanup
    await redis_client.flushdb()
    await redis_client.close()

@pytest.fixture(scope="session")
def test_registry() -> CollectorRegistry:
    """Create a test Prometheus registry."""
    return CollectorRegistry()

@pytest.fixture(autouse=True)
async def setup_test_env(test_db, test_redis):
    """Setup test environment before each test."""
    # Override settings for testing
    os.environ['POSTGRES_DB'] = TEST_DB_NAME
    os.environ['REDIS_DB'] = str(TEST_REDIS_DB)
    
    # Initialize data service with test connections
    await data_service.initialize()
    
    yield
    
    # Cleanup
    await data_service.close()

@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing."""
    monkeypatch.setattr(settings, 'POSTGRES_DB', TEST_DB_NAME)
    monkeypatch.setattr(settings, 'REDIS_DB', TEST_REDIS_DB)
    monkeypatch.setattr(settings, 'DEBUG', True)
    return settings
