"""
Tests for mode gating (notify/paper/live) — proves:
  - config.yaml can never smuggle risk caps (ConfigError)
  - notify mode never touches a broker / never requires creds
  - paper mode requires ALPACA_PAPER_KEY/SECRET, errors cleanly without them
  - live mode is hard-gated: refuses without CONFIRM_LIVE==today AND creds
  - idempotent restart: same cycle_ts/symbol/side is never double-submitted
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

from bot.caps import BOOK_500_CAPS
from bot.config import load_config, ConfigError, BotConfig, DEFAULT_CONFIG_PATH
from bot.executor import execute_order
from bot.sizing import ProposedOrder
from bot.state_store import StateStore, client_order_id


@pytest.fixture
def store(tmp_path):
    return StateStore(str(tmp_path / "state"))


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for var in ("ALPACA_PAPER_KEY", "ALPACA_PAPER_SECRET", "ALPACA_LIVE_KEY",
                "ALPACA_LIVE_SECRET", "CONFIRM_LIVE"):
        monkeypatch.delenv(var, raising=False)


def test_default_config_mode_is_notify():
    cfg = load_config(DEFAULT_CONFIG_PATH)
    assert cfg.mode == "notify"


def test_config_rejects_risk_cap_override(tmp_path):
    bad = tmp_path / "config.yaml"
    bad.write_text("mode: notify\nmax_order_notional: 999999\n")
    with pytest.raises(ConfigError):
        load_config(str(bad))


def test_config_rejects_bad_mode(tmp_path):
    bad = tmp_path / "config.yaml"
    bad.write_text("mode: yolo\n")
    with pytest.raises(ConfigError):
        load_config(str(bad))


def test_notify_mode_never_touches_broker_no_creds_needed(store):
    """notify mode must succeed with ZERO env vars set — proves no broker is contacted."""
    po = ProposedOrder("BTC/USD", "buy", 100.0, 0.2, 0.0, 100.0)
    res = execute_order(po, store, BOOK_500_CAPS, "notify", "dummy_flat", "2026-07-02T00:00",
                         last_price=60000.0)
    assert res.result == "PROPOSED"
    assert "ticket" in res.detail


def test_notify_mode_oversized_order_rejected(store):
    po = ProposedOrder("BTC/USD", "buy", 9999.0, 20.0, 0.0, 9999.0)
    res = execute_order(po, store, BOOK_500_CAPS, "notify", "dummy_flat", "2026-07-02T00:01",
                         last_price=60000.0)
    assert res.result == "REJECTED"


def test_paper_mode_without_creds_errors_cleanly(store):
    po = ProposedOrder("BTC/USD", "buy", 100.0, 0.2, 0.0, 100.0)
    res = execute_order(po, store, BOOK_500_CAPS, "paper", "dummy_flat", "2026-07-02T00:02",
                         last_price=60000.0)
    assert res.result == "ERROR"
    assert "ALPACA_PAPER_KEY" in res.detail.get("reason", "")


def test_live_mode_blocked_without_confirm_or_creds(store):
    po = ProposedOrder("BTC/USD", "buy", 100.0, 0.2, 0.0, 100.0)
    res = execute_order(po, store, BOOK_500_CAPS, "live", "dummy_flat", "2026-07-02T00:03",
                         last_price=60000.0)
    assert res.result == "LIVE_BLOCKED"


def test_live_mode_blocked_even_with_confirm_if_no_creds(store, monkeypatch):
    """CONFIRM_LIVE alone is not enough — creds must ALSO be present."""
    monkeypatch.setenv("CONFIRM_LIVE", "2026-07-02")
    po = ProposedOrder("BTC/USD", "buy", 100.0, 0.2, 0.0, 100.0)
    res = execute_order(po, store, BOOK_500_CAPS, "live", "dummy_flat", "2026-07-02T00:04",
                         last_price=60000.0)
    assert res.result == "LIVE_BLOCKED"


def test_kill_switch_blocks_notify_orders(store, tmp_path, monkeypatch):
    from bot.caps import CapConfig
    kill_file = tmp_path / ".KILL"
    kill_file.write_text("halt")
    cfg = CapConfig(kill_switch_file=str(kill_file))
    po = ProposedOrder("BTC/USD", "buy", 50.0, 0.1, 0.0, 50.0)
    res = execute_order(po, store, cfg, "notify", "dummy_flat", "2026-07-02T00:05",
                         last_price=60000.0)
    assert res.result == "REJECTED"


def test_idempotent_restart_skips_duplicate_submission(store):
    """Same cycle_ts+symbol+side after a simulated restart must be skipped, not resubmitted."""
    po = ProposedOrder("BTC/USD", "buy", 100.0, 0.2, 0.0, 100.0)
    r1 = execute_order(po, store, BOOK_500_CAPS, "notify", "dummy_flat", "2026-07-02T00:06",
                        last_price=60000.0)
    assert r1.result == "PROPOSED"

    # simulate restart: fresh StateStore instance pointed at the SAME directory
    store2 = StateStore(store.state_dir)
    r2 = execute_order(po, store2, BOOK_500_CAPS, "notify", "dummy_flat", "2026-07-02T00:06",
                        last_price=60000.0)
    assert r2.result == "SKIPPED_DUPLICATE"
    assert len(store2.read_orders()) == 1  # no duplicate line written


def test_client_order_id_deterministic():
    a = client_order_id("2026-07-02T00:00", "BTC/USD", "buy")
    b = client_order_id("2026-07-02T00:00", "BTC/USD", "buy")
    c = client_order_id("2026-07-02T00:00", "ETH/USD", "buy")
    assert a == b
    assert a != c
