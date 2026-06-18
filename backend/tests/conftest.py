"""Pytest configuration and fixtures."""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def temp_memory_dir():
    """Create a temporary memory directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def mock_bedrock():
    """Mock Bedrock client."""
    with patch('server.bedrock_client') as mock:
        yield mock


@pytest.fixture
def test_client(temp_memory_dir):
    """Create a test client with mocked environment."""
    with patch.dict(os.environ, {
        'USE_S3': 'false',
        'MEMORY_DIR': temp_memory_dir,
        'CORS_ORIGINS': 'http://localhost:3000',
        'DEFAULT_AWS_REGION': 'us-east-2',
        'BEDROCK_MODEL_ID': 'amazon.nova-lite-v1:0',
    }):
        # Import after path is set
        from server import app
        client = TestClient(app)
        yield client


@pytest.fixture
def sample_conversation():
    """Sample conversation history."""
    return [
        {
            "role": "user",
            "content": "Hello, who are you?",
            "timestamp": "2024-01-01T10:00:00"
        },
        {
            "role": "assistant",
            "content": "I'm Brian's digital twin.",
            "timestamp": "2024-01-01T10:00:01"
        }
    ]


@pytest.fixture
def sample_facts():
    """Sample facts dictionary."""
    return {
        "full_name": "Brian Kane",
        "name": "Brian",
        "email": "brian@example.com"
    }

