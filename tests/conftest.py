from pathlib import Path

import pytest


@pytest.fixture
def temp_logs_dir(tmp_path: Path) -> Path:
    """
    Временная директория для логов.
    Используется при тестировании get_logger с log_file.
    """

    return tmp_path
