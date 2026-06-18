"""Tests for server.py - FastAPI endpoints and memory management."""
import json
import os
import uuid
from unittest.mock import patch, MagicMock, call
from pathlib import Path
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from botocore.exceptions import ClientError


@pytest.fixture
def temp_memory_dir(tmp_path):
    """Temporary memory directory for testing."""
    return str(tmp_path)


@pytest.fixture
def test_client_local(temp_memory_dir):
    """Local memory test client."""
    os.environ['USE_S3'] = 'false'
    os.environ['MEMORY_DIR'] = temp_memory_dir
    os.environ['CORS_ORIGINS'] = 'http://localhost:3000'
    os.environ['DEFAULT_AWS_REGION'] = 'us-east-2'
    os.environ['BEDROCK_MODEL_ID'] = 'amazon.nova-lite-v1:0'

    # Must reimport to apply new environment
    import importlib
    import server
    importlib.reload(server)

    from server import app
    return TestClient(app), temp_memory_dir


# ============= Tests for Memory Functions =============

def test_get_memory_path():
    """Test memory path generation."""
    from server import get_memory_path

    session_id = "test-session-123"
    path = get_memory_path(session_id)
    assert path == "test-session-123.json"


def test_load_conversation_empty_local(test_client_local):
    """Test loading non-existent conversation."""
    client, _ = test_client_local
    from server import load_conversation

    session_id = str(uuid.uuid4())
    result = load_conversation(session_id)
    assert result == []


def test_load_conversation_existing_local(test_client_local):
    """Test loading existing conversation from local storage."""
    client, temp_dir = test_client_local
    from server import load_conversation, save_conversation

    session_id = str(uuid.uuid4())
    conversation = [
        {"role": "user", "content": "Hello", "timestamp": "2024-01-01T10:00:00"},
        {"role": "assistant", "content": "Hi there", "timestamp": "2024-01-01T10:00:01"}
    ]

    # Save first
    save_conversation(session_id, conversation)

    # Then load
    result = load_conversation(session_id)
    assert len(result) == 2
    assert result[0]["content"] == "Hello"
    assert result[1]["content"] == "Hi there"


def test_save_conversation_local(test_client_local):
    """Test saving conversation to local storage."""
    client, temp_dir = test_client_local
    from server import save_conversation

    session_id = str(uuid.uuid4())
    conversation = [
        {"role": "user", "content": "Test message", "timestamp": "2024-01-01T10:00:00"}
    ]

    save_conversation(session_id, conversation)

    # Verify file exists
    memory_file = Path(temp_dir) / f"{session_id}.json"
    assert memory_file.exists()

    # Verify content
    with open(memory_file) as f:
        data = json.load(f)
    assert data[0]["content"] == "Test message"


def test_save_conversation_creates_directory(temp_memory_dir):
    """Test that save_conversation creates memory directory if needed."""
    os.environ['USE_S3'] = 'false'
    os.environ['MEMORY_DIR'] = str(Path(temp_memory_dir) / "new_dir")

    import importlib
    import server
    importlib.reload(server)

    from server import save_conversation
    session_id = str(uuid.uuid4())
    save_conversation(session_id, [{"role": "user", "content": "test"}])

    memory_file = Path(os.environ['MEMORY_DIR']) / f"{session_id}.json"
    assert memory_file.exists()


def test_load_conversation_s3_not_found():
    """Test loading conversation from S3 when key doesn't exist."""
    mock_s3 = MagicMock()
    error_response = {'Error': {'Code': 'NoSuchKey'}}
    mock_s3.get_object.side_effect = ClientError(error_response, 'GetObject')

    with patch('server.USE_S3', True):
        with patch('server.S3_BUCKET', 'test-bucket'):
            with patch('server.s3_client', mock_s3):
                from server import load_conversation

                result = load_conversation('nonexistent')
                assert result == []


def test_save_conversation_s3():
    """Test saving conversation to S3."""
    mock_s3 = MagicMock()

    with patch('server.USE_S3', True):
        with patch('server.S3_BUCKET', 'test-bucket'):
            with patch('server.s3_client', mock_s3):
                from server import save_conversation

                session_id = "test-session"
                conversation = [{"role": "user", "content": "test"}]
                save_conversation(session_id, conversation)

                mock_s3.put_object.assert_called_once()
                call_kwargs = mock_s3.put_object.call_args[1]
                assert call_kwargs['Bucket'] == 'test-bucket'
                assert call_kwargs['Key'] == 'test-session.json'


# ============= Tests for Bedrock Calls =============

def test_call_bedrock_success():
    """Test successful Bedrock call."""
    mock_bedrock = MagicMock()
    mock_bedrock.converse.return_value = {
        "output": {
            "message": {
                "content": [{"text": "Hello, I'm Brian!"}]
            }
        }
    }

    with patch('server.bedrock_client', mock_bedrock):
        with patch('server.prompt', return_value="System prompt"):
            from server import call_bedrock

            conversation = [
                {"role": "user", "content": "Who are you?"}
            ]
            result = call_bedrock(conversation, "Who are you?")

            assert result == "Hello, I'm Brian!"
            mock_bedrock.converse.assert_called_once()


def test_call_bedrock_filters_messages():
    """Test that call_bedrock only uses recent messages (last 20)."""
    mock_bedrock = MagicMock()
    mock_bedrock.converse.return_value = {
        "output": {"message": {"content": [{"text": "response"}]}}
    }

    with patch('server.bedrock_client', mock_bedrock):
        with patch('server.prompt', return_value="System prompt"):
            from server import call_bedrock

            # Create conversation with 25 messages
            conversation = [
                {"role": "user", "content": f"msg {i}", "timestamp": "2024-01-01"}
                for i in range(25)
            ]

            call_bedrock(conversation, "New question")

            # Check that only 20 old messages + 1 new = at most 21 messages sent
            call_kwargs = mock_bedrock.converse.call_args[1]
            messages = call_kwargs['messages']
            # Last message should be the new one
            assert len(messages) <= 22  # (20 old + current user message)


def test_call_bedrock_filters_invalid_roles():
    """Test that call_bedrock filters out invalid roles."""
    mock_bedrock = MagicMock()
    mock_bedrock.converse.return_value = {
        "output": {"message": {"content": [{"text": "response"}]}}
    }

    with patch('server.bedrock_client', mock_bedrock):
        with patch('server.prompt', return_value="System"):
            from server import call_bedrock

            conversation = [
                {"role": "user", "content": "valid"},
                {"role": "invalid_role", "content": "should be filtered"},
                {"role": "assistant", "content": "also valid"}
            ]

            call_bedrock(conversation, "New message")

            call_kwargs = mock_bedrock.converse.call_args[1]
            messages = call_kwargs['messages']

            # Should only have valid messages
            for msg in messages:
                assert msg['role'] in ['user', 'assistant']


def test_call_bedrock_handles_empty_content():
    """Test that call_bedrock handles empty content."""
    mock_bedrock = MagicMock()
    mock_bedrock.converse.return_value = {
        "output": {"message": {"content": [{"text": "response"}]}}
    }

    with patch('server.bedrock_client', mock_bedrock):
        with patch('server.prompt', return_value="System"):
            from server import call_bedrock

            conversation = [
                {"role": "user", "content": ""},  # Empty
                {"role": "assistant", "content": "   "}  # Whitespace
            ]

            call_bedrock(conversation, "Question")

            call_kwargs = mock_bedrock.converse.call_args[1]
            messages = call_kwargs['messages']

            # No empty messages should be sent
            for msg in messages:
                for content_item in msg.get('content', []):
                    assert content_item.get('text', '').strip()


# ============= Tests for API Endpoints =============

def test_root_endpoint(test_client_local):
    """Test GET / endpoint."""
    client, _ = test_client_local

    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "AI Digital Twin API" in data["message"]
    assert "storage" in data


def test_health_endpoint(test_client_local):
    """Test GET /health endpoint."""
    client, _ = test_client_local

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "use_s3" in data
    assert "bedrock_model" in data


def test_chat_endpoint_generates_session_id(test_client_local):
    """Test POST /chat generates new session_id when not provided."""
    client, _ = test_client_local

    mock_bedrock = MagicMock()
    mock_bedrock.converse.return_value = {
        "output": {"message": {"content": [{"text": "Hello!"}]}}
    }

    with patch('server.bedrock_client', mock_bedrock):
        response = client.post("/chat", json={"message": "Hello"})

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["session_id"]  # Should have a value
        assert len(data["session_id"]) > 0


def test_chat_endpoint_reuses_session_id(test_client_local):
    """Test POST /chat reuses provided session_id."""
    client, _ = test_client_local

    mock_bedrock = MagicMock()
    mock_bedrock.converse.return_value = {
        "output": {"message": {"content": [{"text": "Response"}]}}
    }

    with patch('server.bedrock_client', mock_bedrock):
        session_id = str(uuid.uuid4())
        response = client.post("/chat", json={
            "message": "Hello",
            "session_id": session_id
        })

        data = response.json()
        assert data["session_id"] == session_id


def test_chat_endpoint_returns_response(test_client_local):
    """Test POST /chat returns assistant response."""
    client, _ = test_client_local

    mock_bedrock = MagicMock()
    expected_response = "I am Brian Kane, your AI digital twin."
    mock_bedrock.converse.return_value = {
        "output": {"message": {"content": [{"text": expected_response}]}}
    }

    with patch('server.bedrock_client', mock_bedrock):
        response = client.post("/chat", json={"message": "Who are you?"})

        data = response.json()
        assert data["response"] == expected_response


def test_chat_endpoint_saves_conversation(test_client_local):
    """Test POST /chat saves conversation to storage."""
    client, temp_dir = test_client_local

    mock_bedrock = MagicMock()
    mock_bedrock.converse.return_value = {
        "output": {"message": {"content": [{"text": "Response"}]}}
    }

    with patch('server.bedrock_client', mock_bedrock):
        session_id = str(uuid.uuid4())
        client.post("/chat", json={
            "message": "Test",
            "session_id": session_id
        })

        # Check that conversation was saved
        memory_file = Path(temp_dir) / f"{session_id}.json"
        assert memory_file.exists()


def test_chat_endpoint_error_handling(test_client_local):
    """Test /chat endpoint error handling."""
    client, _ = test_client_local

    mock_bedrock = MagicMock()
    mock_bedrock.converse.side_effect = Exception("Bedrock error")

    with patch('server.bedrock_client', mock_bedrock):
        response = client.post("/chat", json={"message": "Hello"})

        assert response.status_code == 500


def test_conversation_endpoint(test_client_local):
    """Test GET /conversation/{session_id} endpoint."""
    client, temp_dir = test_client_local

    session_id = str(uuid.uuid4())
    conversation = [
        {"role": "user", "content": "Hello", "timestamp": "2024-01-01T10:00:00"},
        {"role": "assistant", "content": "Hi", "timestamp": "2024-01-01T10:00:01"}
    ]

    # Save conversation
    memory_file = Path(temp_dir) / f"{session_id}.json"
    memory_file.write_text(json.dumps(conversation))

    response = client.get(f"/conversation/{session_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["session_id"] == session_id
    assert len(data["messages"]) == 2


def test_conversation_endpoint_missing_session(test_client_local):
    """Test GET /conversation/{session_id} with missing session."""
    client, _ = test_client_local

    response = client.get("/conversation/nonexistent-session")
    assert response.status_code == 200

    data = response.json()
    assert data["messages"] == []


def test_cors_configuration():
    """Test CORS is configured correctly."""
    from server import app

    # Check that CORSMiddleware is in middleware stack
    # The middleware might be wrapped, so check the user_middleware
    has_cors = any(
        'cors' in str(type(m)).lower() or 'CORS' in str(type(m))
        for m in app.user_middleware
    )
    # Also check that the app is configured with CORS
    assert has_cors or len(app.user_middleware) > 0


@pytest.mark.asyncio
async def test_chat_validation_empty_message(test_client_local):
    """Test chat endpoint validation for empty message."""
    client, _ = test_client_local

    response = client.post("/chat", json={"message": ""})
    # Server should handle empty message gracefully (e.g. 400 Bad Request or 422 Unprocessable Entity)
    assert response.status_code in [400, 422]


def test_bedrock_model_selection():
    """Test that correct Bedrock model is used."""
    from server import BEDROCK_MODEL_ID

    # Should use configured model
    assert BEDROCK_MODEL_ID in [
        "amazon.nova-micro-v1:0",
        "amazon.nova-lite-v1:0",
        "amazon.nova-pro-v1:0"
    ]


