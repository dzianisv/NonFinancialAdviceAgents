"""
$500-book CapConfig — deterministic, IN CODE, outside any LLM/config override.

House rule: max order $250, max position $500, no shorts, no leverage. These numbers are
hardcoded HERE (not read from config.yaml) so a config edit can never loosen them. Reuses
connectors/hard_caps.py's CapConfig/Order/BookState/check() — this module does not fork or
reimplement the cap logic, it only pins the $500-book numbers.
"""
from __future__ import annotations

import os
import sys

_CONNECTORS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "connectors"
)
if _CONNECTORS_DIR not in sys.path:
    sys.path.insert(0, _CONNECTORS_DIR)

from hard_caps import Order, BookState, CapConfig, CapViolation, check, would_pass  # noqa: E402

# ---- $500 book, hardcoded (house rule, binding) ----
BOOK_500_CAPS = CapConfig(
    max_order_notional=250.0,
    max_position_notional=500.0,
    max_gross_notional=500.0,
    max_daily_loss=25.0,
    max_orders_per_day=20,
    allow_shorts=False,
    kill_switch_file=".KILL",
)

__all__ = [
    "Order", "BookState", "CapConfig", "CapViolation", "check", "would_pass", "BOOK_500_CAPS",
]
