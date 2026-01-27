import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    POLL_TIMEOUT: float = float(os.getenv("POLL_TIMEOUT", 6.0))
    POLL_INTERVAL: float = float(os.getenv("POLL_INTERVAL", 0.1))
    DISCORD_RPC_PORT: int = 9222


config = AppConfig()
