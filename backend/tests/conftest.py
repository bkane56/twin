"""Shared pytest setup for the FastAPI backend tests.

These tests intentionally run without AWS credentials. External AWS calls are
mocked at the application boundary.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Keep boto3 from trying to reach the EC2 metadata service during import.
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
os.environ.setdefault("DEFAULT_AWS_REGION", "us-east-2")
os.environ.setdefault("USE_S3", "false")
os.environ.setdefault("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import server  # noqa: E402  pylint: disable=wrong-import-position


@pytest.fixture()
def app_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    """Return a TestClient configured for isolated local-memory tests."""
    monkeypatch.setattr(server, "USE_S3", False)
    monkeypatch.setattr(server, "MEMORY_DIR", str(tmp_path))
    return TestClient(server.app)


@pytest.fixture()
def server_module():
    """Expose the imported server module to tests without repeated imports."""
    return server
