"""
Dynamic strategy loader — imports intraday-bot/strategies/<key>.py, the EXACT SAME module
used by the backtests (core/gate.py), so live/paper signals can never drift from what was
actually gated. `key` comes from config.yaml's strategy_key.
"""
from __future__ import annotations

import importlib
import os
import sys

STRATEGIES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "strategies"
)


class StrategyLoadError(Exception):
    pass


def load_strategy(key: str):
    """Returns the `signals(df_dict, params) -> dict[str, pd.Series]` callable from
    strategies/<key>.py. Raises StrategyLoadError if the module or the required `signals`
    function is missing — never falls back to a default strategy silently."""
    root = os.path.dirname(STRATEGIES_DIR)
    if root not in sys.path:
        sys.path.insert(0, root)

    module_path = os.path.join(STRATEGIES_DIR, f"{key}.py")
    if not os.path.exists(module_path):
        raise StrategyLoadError(f"no strategy module at {module_path} for key={key!r}")

    try:
        mod = importlib.import_module(f"strategies.{key}")
    except Exception as e:  # noqa: BLE001
        raise StrategyLoadError(f"failed to import strategies.{key}: {e}") from e

    if not hasattr(mod, "signals"):
        raise StrategyLoadError(f"strategies.{key} has no signals(df_dict, params) function")

    return mod.signals
