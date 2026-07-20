"""Twelve-factor configuration for the API, loaded from env vars.

See docs/webui-architecture.md#Configuration.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root: src/sheet_project/api/config.py -> src/sheet_project/api -> src/sheet_project -> src -> repo root
REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    DATA_DIR: Path = REPO_ROOT / "data"
    # If unset, defaults to DATA_DIR / "characters" (computed lazily below,
    # since DATA_DIR itself may be overridden via env var).
    CHARACTERS_DIR: Optional[Path] = None
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=True)

    @property
    def characters_dir(self) -> Path:
        if self.CHARACTERS_DIR is not None:
            return Path(self.CHARACTERS_DIR)
        return Path(self.DATA_DIR) / "characters"


settings = Settings()
