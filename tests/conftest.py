"""
Test configuration.
"""
import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

pytest_plugins = []


@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture."""
    return {
        "test_mode": True,
        "api_url": "http://localhost:8000"
    }

