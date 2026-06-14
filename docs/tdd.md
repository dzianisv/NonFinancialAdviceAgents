# TDD — Proactive AI Financial Advisor

Aligns to `docs/prd.md`. RECOMMEND-ONLY. Never trades. Honest-or-`[UNAVAILABLE]`. Same-day DM for next Google/SanDisk/BTC-dip before window closes.

## 1. Architecture

Four layers. Data flows up, decision down, alert out.

```
 (d) NOTIFY        DM owner (Telegram CLI / osascript / hermes deliver)
                        ▲  only when alert condition fires; else SILENT
 (c) SCHEDULER     per-agent native primitive wakes the agent on a time slot
                        ▲  openclaw heartbeat 15m | claude-code crontab | hermes sched
 (b) SKILL.md      agent READS skill, runs script, applies gate, DECIDES alert vs pool
                        ▲  regime gate, F&G gate, ≥2-source gate, risk VETO
 (a) DATA .py      deterministic, no fabrication, emit [UNAVAILABLE] on fetch fail
                        live web: yfinance / FRED / alternative.me / binance
```

- (a) `.py` scripts: pure fetch+compute, `--json` contract, exceptions → skip/empty, never invent a number.
- (b) `SKILL.md`: the judgment layer. Reads script JSON, checks gates, writes pools or DMs.
- (c) Scheduler: NOT in-script. The backend's own primitive fires the agent (§3).
- (d) Notify: any non-`SILENT` output → owner channel. DM = something real fired.

## 2. Skills

| skill | script | data source (exact) | failure mode | alert trigger |
|---|---|---|---|---|
| dip-screener | `dip_screener.py` | yfinance, `SP100[]` (100 tickers), 1y `Close` | batch try/except → skip batch; ticker drop → skip | HIGH (`≤−30%` from 52w ATH) AND regime=RISK_ON → DM. MEDIUM (`−25..−30%`) → `/tmp/dip_candidates.jsonl` |
| crypto-dip-scanner | `crypto_dip_scanner.py` | yfinance BTC/ETH/SOL/BNB/AVAX/LINK `-USD`; F&G `api.alternative.me/fng/?limit=1`; funding `fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT` | F&G/funding fetch fail → `None` (omit line); funding 451 geo-block → omit | PRIMARY: any coin `≤−30%` from ATH AND F&G `<25` → DM. Funding = bonus only, never required |
| signal-convergence-alert | `convergence.py` | reads `/tmp/dip_candidates.jsonl`, `/tmp/narrative.jsonl`, 13F ledger (`~/.openclaw/workspace/investor/13f/recommended.jsonl`, 14d), congress ledger (`…/congress/recommended.jsonl`, 14d) | missing pool → skipped silently; bad JSON line → skipped | `n_sources ≥ 2` same ticker → DM; `≥ 3` → route `/multi-lens-quorum` |
| regime-detection | `regime_monitor.py` | yfinance `SPY`,`^VIX`,`^VIX3M`; FRED CSV `BAMLH0A0HYM2` | FRED fail → `credit=0`; VIX NaN → `vix_ts=0` | weights: sma200×3, vix_ts×2, credit×2 → score → RISK_ON/NEUTRAL/RISK_OFF |

Tiers — dip stock: HIGH `≤−30`, MED `≤−25`, WATCH `≤−20`. Crypto: HIGH `≤−40`, MED `≤−30`, WATCH `≤−20`.
Regime map: `score≥0.5`→1.0x RISK_ON | `≥0.0`→0.7x NEUTRAL | `≥−0.5`→0.5x RISK_OFF(mild) | `<−0.5`→0.3x RISK_OFF.

## 3. Proactive Scheduling — 3 backends

Same skills, same 6 slots (all UTC). Each backend uses its NATIVE primitive — no shared scheduler.

### openclaw — heartbeat (`SETUP-openclaw.md`)
- `agents.defaults.heartbeat`: `{ every:"15m", target:"last", lightContext:true, skipWhenBusy:true, model:"litellm/gpt-5-mini" }`.
- Every 15m tick: agent reads per-agent `HEARTBEAT.md` = time-gated playbook. Checks clock, runs only the DUE slot, DMs only on alert, else silent.
- State file `~/.openclaw/workspace/investor/.heartbeat-state.json` maps `task→last_run_date`; prevents double-fire same day.
- `lightContext:true` loads only HEARTBEAT.md (cheap clock-check); brief can escalate model.
- Agent-side cron flagged (incident #1787) → heartbeat is the path. Workspace files persist → survive pod restart.

### claude-code — crontab → `claude -p` (`SETUP-claudecode.md`)
- No daemon. System crontab (`CRON_TZ=UTC`) wakes headless: `claude --bare -p "$PROMPT" --allowedTools "Bash,Read,Write,WebFetch,WebSearch" --append-system-prompt "<RECOMMEND-ONLY…SILENT>" --output-format text`.
- `--bare` = deterministic (skips hook/MCP discovery). Wrapper drops `SILENT`; non-SILENT → notifier.
- Weekly brief = dynamic workflow: `ultracode` keyword authors+runs `weekly-brief.workflow.js`, fanning quorum lenses in PARALLEL.
- Auth: `ANTHROPIC_API_KEY` in cron env. Subscription headless draws Agent SDK credit (effective 2026-06-15).

### hermes-ai — hermes scheduler / crontab (`SETUP-hermes.md`)
- `hermes -s <skills> -p "$1"` one-shot. Register slots in native scheduler, else crontab (`CRON_TZ=UTC`).
- Mandate: paste `AGENTS.template.md` into hermes investor system prompt (persists across sessions).
- URL skill install pulls SKILL.md only → vendor `.py` via `npx skills add … --copy`.

### Cadence (identical across backends)
| UTC | Days | Task | DM only if |
|---|---|---|---|
| 07:45 | M–F | dip-screener | HIGH dip AND RISK_ON |
| 07:50 | M–F | crypto-dip-scanner | coin `≤−30%` AND F&G`<25` |
| 08:00 | M–F | regime + fomc | regime flipped OR new FOMC |
| 08:15 | M–F | trend-stock-research broad | never — append `/tmp/narrative.jsonl` |
| 08:30 | M–F | signal-convergence-alert | ticker in ≥2 sources |
| 09:30 | Mon | weekly brief | always |

## 4. Data Contracts

`dip_screener.py --json` → array:
```json
[{"ticker":"GOOGL","current":150.2,"ath_52w":214.0,"pct_from_ath":-29.8,"sma200":175.1,"pct_vs_200d":-14.2,"conviction":"MEDIUM"}]
```

`crypto_dip_scanner.py --json`:
```json
{"dips":[{"ticker":"BTC","current_usd":61000,"ath_52w_usd":108000,"pct_from_ath":-43.5,"sma200_usd":78000,"pct_vs_200d":-21.8,"conviction":"HIGH"}],
 "fear_greed":{"value":18,"label":"Extreme Fear"},"btc_funding_rate_pct":-0.012}
```
`fear_greed`/`btc_funding_rate_pct` may be `null` (fetch fail / geo-block).

`convergence.py --json`:
```json
{"min_sources":2,"convergences":[{"ticker":"WDC","sources":["13f","dip","journalism"],"n_sources":3,"notes":["dip: -31% from ATH","journalism: 3 FT/WSJ mentions"]}],"pools_read":["/tmp/dip_candidates.jsonl"]}
```

`regime_monitor.py --json`:
```json
{"regime":"RISK_ON","exposure_multiplier":1.0,"score":0.71,"signals":{"sma200":1,"vix_ts":0,"credit":1},
 "weights":{"sma200":3,"vix_ts":2,"credit":2},"price":..,"sma200":..,"vix":..,"vix3m":..,"hy_oas_pct":..,"note":".."}
```

Pool files = JSONL, one obj/line, each needs `ticker` (or `symbol`); optional `note`/`reason`/`why`; ledgers add `date`/`recorded`/`ts` for 14d window. Convergence keys on `ticker` upper-cased.

`.heartbeat-state.json` = flat `task→YYYY-MM-DD`:
```json
{"dip-screener":"2026-06-14","crypto-dip-scanner":"2026-06-14","regime-fed":"2026-06-14","journalism":"2026-06-14","convergence":"2026-06-14","weekly-brief":"2026-06-08"}
```

## 5. Weekly Brief Workflow (`weekly-brief.workflow.js`)

3 phases. Parallelism is the point — lenses don't block each other.

1. **Collect** — `parallel()` 6 agents, one skill each (regime, fed, 13f, congress, journalism, dips), each returns `CAND_SCHEMA {candidates[],summary}`. Cross-ref: build `bySources[ticker]→Set(source)`; rank by `n` (source count); take top 5. **Ticker in ≥2 sources elevated.**
2. **Quorum** — nested `parallel`: per top-5 candidate × 4 lenses, each emits `VERDICT_SCHEMA {verdict∈BUY/ADD/HOLD/TRIM/SELL, conviction 1-5, reason, invalidation, dissent}`. Lenses: `analytics-warren-buffett`, `analytics-stanley-druckenmiller`, `analytics-lyn-alden`, `fundamental-analysis`.
3. **Synthesize** — per candidate `/risk-management` VETO (name >10% book OR RISK_OFF → VETO). Final agent writes INVESTMENT BRIEF: header (REGIME/FED), PRIORITY ACTIONS, NEW BUY IDEAS (risk=PASS only, w/ conviction+dissent+invalidation), HOLDS, COULD NOT VERIFY; states 13F 45d / STOCK Act 30-45d lag; preserves dissent (no averaging).

## 6. Known Limitations / Failure Modes

- **Capitol Trades (congressman-stock-watch):** 403/429 from pod network (Cloudflare/Vercel bot-block) → degrades to `[SIGNAL UNAVAILABLE]`, no fabrication. Convergence simply loses that pool.
- **Binance funding (`fapi.binance.com`):** geo-blocked 451 from US/pod → crypto scanner omits funding line. Alert logic does NOT require funding — dip+F&G is primary trigger.
- **regime-detection single point of failure:** lost stooq fallback → now Yahoo `query2`/yfinance single source. Robustness regression. FRED CSV verified working.
- **yfinance multi-download drops a ticker** (e.g. MMC "delisted") → handled gracefully (`if col not in data.columns: skip`), no crash, that name silently absent.
- **A SKILL.md on disk is NOT validated.** Every modification MUST run the execute→evaluate→improve loop (AGENTS.md). Verify load: `node openclaw.mjs skills list --agent investor --json` → `eligible:true && modelVisible:true`.

## 7. Security / Invariants

- **RECOMMEND-ONLY.** No trade tools wired. Output = candidates for quorum, never orders.
- **No secrets in skills.** Free data only (yfinance/FRED/alternative.me). Auth (API key) lives in cron/pod env, never in SKILL.md or `.py`.
- **No fabricated numbers.** Fetch fail → `[UNAVAILABLE]`/`null`. Honest or silent.
- **risk-management VETO** over every buy: any name >10% book OR RISK_OFF → VETO all buys.
- **Dedup ledgers idempotent.** Never re-propose a ticker already in 13F / congress ledger.
- **Silence default.** A DM = a real fired condition; no "all quiet" chatter.
