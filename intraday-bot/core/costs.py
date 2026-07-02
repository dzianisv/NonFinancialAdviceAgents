"""
Cost model: Alpaca Crypto maker 0.15%/side, taker 0.25%/side (house rule, hardcoded here).
Forced/timeout exits ALWAYS pay taker. Includes stress multipliers and a min-fee floor.

Net of costs ALWAYS — this module is the only place fee rates are defined; nothing else
in intraday-bot should hardcode a fee number.
"""
from __future__ import annotations

from dataclasses import dataclass

MAKER_RATE = 0.0015   # 0.15% per side
TAKER_RATE = 0.0025   # 0.25% per side
MIN_FEE_USD = 0.01    # fee floor per order ($0.01 minimum notional fee)


@dataclass(frozen=True)
class CostConfig:
    maker_rate: float = MAKER_RATE
    taker_rate: float = TAKER_RATE
    min_fee_usd: float = MIN_FEE_USD
    fee_multiplier: float = 1.0   # stress tier (a): 2x fees -> set to 2.0
    extra_slippage_bps: float = 0.0  # stress tier (d): worst-5%-vol bars get +10bp


def fee(notional: float, is_maker: bool, cfg: CostConfig = CostConfig()) -> float:
    """Fee in $ for one order of given absolute notional, applying the min-fee floor and
    the stress fee_multiplier."""
    notional = abs(notional)
    rate = (cfg.maker_rate if is_maker else cfg.taker_rate) * cfg.fee_multiplier
    raw = notional * rate
    return max(raw, cfg.min_fee_usd) if notional > 0 else 0.0


def fee_rate_effective(notional: float, is_maker: bool, cfg: CostConfig = CostConfig()) -> float:
    """Fee expressed as a fraction of notional (post min-fee-floor). Useful for return-space math."""
    if notional <= 0:
        return 0.0
    return fee(notional, is_maker, cfg) / notional


def slippage_cost(notional: float, cfg: CostConfig = CostConfig()) -> float:
    """Extra $ slippage cost for stress tier (d) — worst-5%-vol bars get +10bp."""
    return abs(notional) * (cfg.extra_slippage_bps / 10_000.0)


STRESS_2X_FEES = CostConfig(fee_multiplier=2.0)
STRESS_EXTRA_SLIPPAGE = CostConfig(extra_slippage_bps=10.0)
