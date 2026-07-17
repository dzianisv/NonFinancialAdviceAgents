# watchlist-alerts

Self-contained Bun/TypeScript script that checks the "Watchlist" Google Sheet
(canonical alert trigger registry), evaluates each `ACTIVE*` alert against
live market data, and for triggered alerts posts to a Telegram topic and
writes the result back to the sheet.

Designed to be run repeatedly by cron — idempotent by construction (the
sheet `Status` column IS the dedup state; a row already `TRIGGERED` is
never re-evaluated or re-posted).

## Files

- `watchlist-alerts.ts` — the whole thing, one file, no dependencies beyond
  Bun's built-ins (`fetch`, `Bun.spawnSync`) and the `gws` CLI on `PATH`.

## Usage

```bash
bun watchlist-alerts.ts [--dry-run] [--only SYMBOL]
```

- `--dry-run` — force dry-run even if Telegram env vars are set. Prints
  every message that *would* be sent, does not call Telegram, does not
  write the sheet.
- `--only SYMBOL` — restrict evaluation to one symbol (e.g. `--only BTC-USD`).

If any of `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALERTS_CHAT_ID`,
`TELEGRAM_ALERTS_THREAD_ID` are unset, the script **automatically** runs in
dry-run mode regardless of the `--dry-run` flag — so it's safe to run with
no env configured at all.

## Env vars (only needed for live posting + sheet write-back)

| Var | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot API token |
| `TELEGRAM_ALERTS_CHAT_ID` | Chat ID of the group hosting the "Market Alerts" topic |
| `TELEGRAM_ALERTS_THREAD_ID` | `message_thread_id` of the "Market Alerts" topic |

The `gws` CLI must be authenticated (`gws auth login` or equivalent) for
sheet reads/writes — this script shells out to it via `Bun.spawnSync`, it
does not talk to the Sheets API directly.

## The sheet

- Spreadsheet ID `1aunLbpNGo85WqrMHiIsy6nFUija4Lnjot-rIhE-pGU8`, tab title
  `Watchlist` (matched case-insensitively; sheetId resolved dynamically via
  `spreadsheets.get`, not hardcoded).
- Columns A:J are the ones this script reads/writes: Alert ID, Symbol, Desk,
  Status, Conditions, Match, Action / Entry, Reason / Thesis, Data Source,
  Invalidation / Re-evaluate. Columns K:R (Position Target, Channel,
  Created At, etc.) are read but untouched.
- A row only counts as a real alert row if both Alert ID (col A) and Status
  (col D) are non-empty — this naturally skips the trailing freeform
  scratch rows at the bottom of the tab (e.g. `["META", "Considered
  cheap"]`) without special-casing them.
- Only rows whose Status **starts with** `ACTIVE` are evaluated (`ACTIVE`,
  `ACTIVE_REVIEW_ONLY`). `SUPERSEDED` and anything else is skipped.
- `ACTIVE_REVIEW_ONLY` rows, when triggered, get `⚠️ REVIEW ONLY — no
  auto-action.` prepended to the Telegram message — never implies an
  automatic buy.

### Sheet I/O is abstracted

`readWatchlist()` and `updateAlertRow()` are the only two functions that
touch the sheet. Both currently shell out to `gws`; swapping to a direct
Sheets API client later means touching only these two functions.

### Write-back mechanics (untested against the live sheet — see below)

Per this project's documented convention (`AGENTS.md`), writes use
`gws sheets spreadsheets batchUpdate` with a numeric `gridRange` /
`updateCells` against the sheet's numeric `sheetId` — **not**
`values.update` with an A1 range. `updateAlertRow()`:

1. Re-reads cell D of the target row immediately before writing. If it's
   already `TRIGGERED`, no-ops (handles races / accidental double-runs).
2. Writes Status (col D) → `TRIGGERED` and Match (col F) →
   `FIRED <ISO date> price=<price> rsi=<rsi>` (price/rsi omitted for
   pure date-based alerts, which have no market data).
3. Reads Status back and throws if it didn't actually become `TRIGGERED`
   (write verification, per project convention).

**This path was not exercised against the real sheet during this build** —
doing so would flip real `ACTIVE` alerts to `TRIGGERED`. It's implemented
and follows the documented batchUpdate shape exactly, but is
untested-until-live. Dry-run mode (see Verification below) never calls it.

## Condition grammar

Parsed from the `Conditions` column (`E`):

| Syntax | Meaning |
|---|---|
| `above:<num>` | `price >= num` |
| `below:<num>` | `price <= num` |
| `rsi_above:<num>` or `rsi_above(<period>):<num>` | `RSI(period, default 14) >= num` |
| `rsi_below:<num>` or `rsi_below(<period>):<num>` | `RSI(period) <= num` |
| `pct_below_52wk_high:<pct>` | `price <= high52 * (1 - pct/100)` — fires when price has dropped at least `pct`% off the rolling 52-week high (max daily HIGH over the last ~1y) |
| `record:<YYYY-MM-DD>` / `payment:<YYYY-MM-DD>` | fires on/after that UTC calendar date; no market data needed |
| `A AND B` | both must hold — split on the literal string `" AND "` |

Only `AND` is implemented (matches every row currently in the sheet, all of
which have `Match = all`). `OR`/`any` is not implemented — extend
`parseConditions`/evaluation in `watchlist-alerts.ts` if a row ever needs
it.

An unrecognized or malformed condition token skips just that row (logged
under "Skipped" in the summary with the offending token) — it never
crashes the run.

## Market data

`getQuote(symbol)` hits
`https://query1.finance.yahoo.com/v8/finance/chart/<SYMBOL>?interval=1d&range=1y`
with a browser `User-Agent`, takes the last non-null daily close as
`price`, computes `RSI(14)` (Wilder's smoothing) from the full close
series, and computes `high52` as the max daily **HIGH** (not close) over
the returned ~1-year window (used by `pct_below_52wk_high`). Each unique
symbol is fetched once per run and cached; a symbol-level fetch failure
only skips the rows that need that symbol's price/RSI/high52 (rows whose
conditions are purely date-based never trigger a fetch at all).

Swap data sources by replacing `fetchYahooChart` / `getQuote` — nothing
else in the script depends on Yahoo specifically.

## Message format

```
🔔 {SYMBOL} {condition met} @ {price} (RSI {rsi})
{Action / Entry}
Why: {first ~140 chars of Reason / Thesis}
Alert: {Alert ID}
```

Date-only alerts (no market data) omit the `@ price (RSI ...)` segment.
`ACTIVE_REVIEW_ONLY` rows get the `⚠️ REVIEW ONLY` line prepended.

## Idempotency

The sheet `Status` column is the single source of truth for "has this
already fired." A row already `TRIGGERED` is filtered out before
evaluation even starts. There's a small race window on concurrent runs
(re-check happens right before the write, not atomically with it) — fine
for a serial cron job, not safe for parallel invocations.

## Cron

Point a cron entry (e.g. via the `hermes-agent` cron feature referenced in
the project `AGENTS.md`) at:

```bash
TELEGRAM_BOT_TOKEN=... TELEGRAM_ALERTS_CHAT_ID=... TELEGRAM_ALERTS_THREAD_ID=... \
  bun /Users/engineer/workspace/backtest/.agents/skills/watchlist-alerts/watchlist-alerts.ts
```

Omit the env vars (or keep `--dry-run`) to test without side effects.

## Verification performed for this build

- `bun --version` → `1.3.14` — Bun available.
- `bun watchlist-alerts.ts --dry-run` run against the **real** sheet and
  **real** Yahoo Finance data (no Telegram env set, so it auto-dry-runs
  regardless). Read all 18 active/review rows (of 19 real alert rows; 1
  `SUPERSEDED` correctly excluded), parsed every condition (plain,
  compound-AND, RSI, and the date-based `record`/`payment` compound row)
  without error, fetched all 10 distinct symbols from Yahoo successfully
  (no fetch failures on this run), and printed live triggered/not-triggered
  status with real prices and RSI for every row.
- `--only BTC-USD` filter verified in isolation (5 BTC-USD rows, 3 fired).
- Isolated smoke test of the Yahoo fetch/error path against a nonexistent
  ticker confirmed `HTTP 404` is caught and surfaces as a clean error (the
  same try/catch shape used in the main per-symbol fetch loop).
- The `updateAlertRow` write path (`gws sheets spreadsheets batchUpdate`)
  was **not** run live — see the write-back section above.
