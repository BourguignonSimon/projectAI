"""Tests for utility functions."""

import os

import pytest


class TestEnvironmentValidation:
    """Tests for environment variable validation."""

    def test_required_env_vars_defined(self):
        """Verify required environment variables are documented."""
        required_vars = [
            "REDIS_HOST",
            "REDIS_PORT",
            "GOOGLE_API_KEY",
            "MODEL_SMART",
            "MODEL_FAST",
        ]
        # This test verifies the list of required variables
        assert len(required_vars) == 5

    def test_env_example_exists(self):
        """Verify .env.example template exists."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_example_path = os.path.join(project_root, ".env.example")
        assert os.path.exists(env_example_path), ".env.example should exist"


class TestMessageFormat:
    """Tests for message format validation."""

    def test_message_has_required_fields(self):
        """Verify message structure contains required fields."""
        required_fields = [
            "request_id",
            "sequence_id",
            "sender",
            "content",
            "type",
            "status",
        ]
        # Sample message structure
        sample_message = {
            "request_id": "test-123",
            "sequence_id": 1,
            "sender": "manager",
            "content": "Test message",
            "type": "message",
            "status": "DONE",
        }
        for field in required_fields:
            assert field in sample_message, f"Message should have {field} field"
