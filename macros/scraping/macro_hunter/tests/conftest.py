#!/usr/bin/env python3
import pytest
import platform
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Any

class TestError(Exception):
    """Base class for test-related exceptions"""
    pass

class TestSetupError(TestError):
    """Raised when test setup fails"""
    pass

class TestCleanupError(TestError):
    """Raised when test cleanup fails"""
    pass

@pytest.fixture
def temp_dir() -> Generator[Path, Any, None]:
    """Provide a clean temporary directory for tests"""
    try:
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)
    except Exception as e:
        raise TestSetupError(f"Failed to create temporary directory: {e}")

@pytest.fixture
def sample_docm() -> Generator[Path, Any, None]:
    """Create a mock .docm file for testing"""
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.docm', delete=False) as tf:
            temp_file = Path(tf.name)
            yield temp_file
    except Exception as e:
        raise TestSetupError(f"Failed to create sample docm: {e}")
    finally:
        if temp_file:
            try:
                temp_file.unlink(missing_ok=True)
            except Exception as e:
                raise TestCleanupError(f"Failed to cleanup sample docm: {e}")

@pytest.fixture
def mock_venv_path(temp_dir: Path) -> Generator[Path, Any, None]:
    """Create a mock virtual environment structure"""
    try:
        if platform.system() == 'Windows':
            python_path = temp_dir / 'Scripts' / 'python.exe'
        else:
            python_path = temp_dir / 'bin' / 'python'
        
        python_path.parent.mkdir(parents=True)
        python_path.touch()
        yield temp_dir
    except Exception as e:
        raise TestSetupError(f"Failed to create mock venv: {e}")
