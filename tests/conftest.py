import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temporary_directory():
    """Provides a temporary directory that is removed after the test."""
    directory = tempfile.mkdtemp()
    yield Path(directory)
    shutil.rmtree(directory)
