from __future__ import annotations

from pathlib import Path


PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DIR: Path = DATA_DIR / "raw"
PROCESSED_DIR: Path = DATA_DIR / "processed"
METADATA_DIR: Path = DATA_DIR / "metadata"
MODELS_DIR: Path = PROJECT_ROOT / "models"
REPORTS_DIR: Path = PROJECT_ROOT / "reports"
FIGURES_DIR: Path = REPORTS_DIR / "figures"

DEFAULT_ARCHIVE_PATH: Path = PROJECT_ROOT / "data" / "raw" / "archive.zip"

ORDER_SAMPLE_ROWS: int = 50_000
RANDOM_SEED: int = 42
ENCODING: str = "latin1"
