"""
config.yaml loader + validation. Only NON-risk knobs live here (strategy choice, symbols,
interval, poll cadence, execution mode, offsets/timeouts). The $500-book risk caps are
NEVER read from this file — see bot/caps.py (hardcoded, outside any config/LLM override).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

import yaml

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")

VALID_MODES = ("notify", "paper", "live")


class ConfigError(Exception):
    pass


@dataclass
class BotConfig:
    mode: str = "notify"
    strategy_key: str = "dummy_flat"
    strategy_params: dict = field(default_factory=dict)
    symbols: list = field(default_factory=lambda: ["BTC/USD"])
    interval: str = "5m"
    poll_seconds: int = 300
    lookback_bars: int = 300
    maker_offset_bps: float = 5.0       # how far inside the touch to rest the post-only limit
    fill_timeout_seconds: int = 300      # timeout before escalating to market (if allowed)
    allow_timeout_escalation: bool = True
    state_dir: str = "state"
    max_loop_iterations: Optional[int] = None  # None = run forever; set for smoke tests
    dry_run_once: bool = False           # run exactly one cycle then exit (smoke test hook)

    @property
    def account_type(self) -> str:
        """alpaca-py wants 'paper'/'live' account routing distinct from our notify mode."""
        return "paper" if self.mode in ("notify", "paper") else "live"


def load_config(path: str = DEFAULT_CONFIG_PATH) -> BotConfig:
    if not os.path.exists(path):
        raise ConfigError(f"config file not found: {path}")
    with open(path) as f:
        raw = yaml.safe_load(f) or {}

    mode = raw.get("mode", "notify")
    if mode not in VALID_MODES:
        raise ConfigError(f"mode must be one of {VALID_MODES}, got {mode!r}")

    cfg = BotConfig(
        mode=mode,
        strategy_key=raw.get("strategy_key", "dummy_flat"),
        strategy_params=raw.get("strategy_params", {}) or {},
        symbols=raw.get("symbols", ["BTC/USD"]),
        interval=raw.get("interval", "5m"),
        poll_seconds=int(raw.get("poll_seconds", 300)),
        lookback_bars=int(raw.get("lookback_bars", 300)),
        maker_offset_bps=float(raw.get("maker_offset_bps", 5.0)),
        fill_timeout_seconds=int(raw.get("fill_timeout_seconds", 300)),
        allow_timeout_escalation=bool(raw.get("allow_timeout_escalation", True)),
        state_dir=raw.get("state_dir", "state"),
        max_loop_iterations=raw.get("max_loop_iterations"),
        dry_run_once=bool(raw.get("dry_run_once", False)),
    )

    # reject any attempt to smuggle risk caps into config.yaml — those are code-only (bot/caps.py)
    forbidden = {"max_order_notional", "max_position_notional", "max_gross_notional",
                 "max_daily_loss", "max_orders_per_day", "allow_shorts", "kill_switch_file"}
    present = forbidden & set(raw.keys())
    if present:
        raise ConfigError(
            f"config.yaml may not set risk caps {sorted(present)} — hardcoded in bot/caps.py "
            f"by house rule, outside any config/LLM override"
        )
    return cfg
