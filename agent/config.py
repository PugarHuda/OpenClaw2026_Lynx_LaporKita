"""Centralized configuration for Rasain, loaded from .env with type validation.

Uses pydantic-settings so a malformed env var fails at startup, not mid-demo.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Anthropic Claude ---
    # Optional: kalau kosong, Claude Agent SDK pakai auth Claude Code CLI.
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-6"
    anthropic_vision_model: str = "claude-sonnet-4-6"

    # --- Sumopod AI (OpenAI-compatible gateway — vision classifier) ---
    # gpt-4o-mini: vision + tool-calling, ~$0.0004/call — cost-efficient default.
    sumopod_api_key: str = ""
    sumopod_base_url: str = "https://ai.sumopod.com/v1"
    sumopod_vision_model: str = "gpt-4o-mini"

    # --- DOKU ---
    doku_client_id: str = ""
    doku_api_key: str = ""
    doku_secret_key: str = ""
    doku_authorization_base64: str = ""
    doku_base_url: str = "https://api-sandbox.doku.com"
    doku_mcp_url: str = "https://api-sandbox.doku.com/doku-mcp-server/mcp"

    # --- Mem9 ---
    mem9_api_key: str = ""
    mem9_base_url: str = "https://api.mem9.ai"

    # --- Solana ---
    solana_rpc_url: str = "https://api.devnet.solana.com"
    helius_api_key: str = ""
    solana_mint_authority_keypair_path: str = ""
    rsn_mint_address: str = ""

    # --- Notif ---
    fonnte_token: str = ""
    telegram_bot_token: str = ""

    # --- App ---
    app_port: int = 8000
    app_host: str = "0.0.0.0"
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./rasain.db"

    # --- Business Rules ---
    earn_rsn_per_verified_report: int = 10
    mint_threshold_rsn: int = 10
    redemption_rate_idr_per_rsn: int = 1000


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — env di-parse sekali per proses."""
    return Settings()
