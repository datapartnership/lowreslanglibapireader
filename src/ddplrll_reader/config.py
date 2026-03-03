"""Configuration via environment variables or .env file."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All settings can be overridden with environment variables prefixed ``DDPLRLL_``."""

    model_config = SettingsConfigDict(
        env_prefix="DDPLRLL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── API connection ────────────────────────────────────────────────
    api_base_url: str = "https://lrllapi.azurewebsites.net"
    """Base URL of the DDPLRLL Dataset API (no trailing slash)."""

    api_key: str = ""
    """Value sent in the ``X-Api-Key`` header."""

    # ── Query defaults ────────────────────────────────────────────────
    keyword: str | None = None
    theme: str | None = None
    author: str | None = None
    year: str | None = None
    limit: int = 30

    # ── Download behaviour ────────────────────────────────────────────
    output_dir: str = "./output"
    """Directory where the JSON-LD file and downloaded PDFs are stored."""

    download_files: bool = True
    """Whether to download the PDFs referenced in contentUrl."""

    max_concurrent_downloads: int = 5
    """Maximum number of parallel file downloads."""

    request_timeout: float = 30.0
    """HTTP timeout in seconds for API requests."""

    download_timeout: float = 120.0
    """HTTP timeout in seconds for file downloads."""

    verify_ssl: bool = True
    """Set to False to skip SSL certificate verification (e.g. self-signed certs)."""
