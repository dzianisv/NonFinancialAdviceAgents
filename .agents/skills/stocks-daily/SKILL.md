---
name: stocks-daily
description: >
  Daily portfolio accumulation monitor. Reads the user's cached positions
  (.cache/stocks-daily/positions.csv), runs the stocks-advisor 6-seat holdings panel,
  ranks which holdings are undervalued enough to BUY MORE of today, and emits a SWAP
  table where every buy is paired with a funding SELL (the user is fully invested, so
  buys are sourced from broken/no-catalyst names that are NOT flagged hold-only by the
  caller). Publishes three
  outputs: (1) a dated Notion page (via stocks-advisor), (2) a per-stock recap + swap
  to the configured Telegram channel (target read from .cache/stocks-daily/telegram.yaml
  at runtime, never hardcoded), and (3) optionally a short X.com tweet. Triggers on:
  "/stocks-daily", "what should I buy more of", "what's undervalued now", "post stocks
  to telegram". Educational, not financial advice.
license: MIT
compatibility: opencode
metadata:
  audience: equity-allocators
  domain: equity-portfolio-management
---

# stocks-daily

**One-liner:** A DAILY monitor of the user's book answering one question — *"what that I own (or want) is undervalued enough to buy MORE of today, and what do I sell to fund it?"* Reads cached positions, runs the stocks-advisor 6-seat panel, ranks accumulate-on-weakness candidates, and emits a **SWAP table** (every buy paired with a funding sell). Publishes to three outputs: (1) a dated Notion page (via stocks-advisor), (2) a per-stock recap + swap to the **Telegram channel** (config-driven target), and (3) optionally a short X.com tweet. Educational, not investment advice.

**Triggers:** `/stocks-daily`, "run the daily stocks monitor", "what should I buy more of / what's undervalued", "publish stocks report", "post stocks to telegram"

---

> **Disclaimer:** Output is educational analysis for a backtesting research environment. Nothing here is financial advice. All verdicts must be validated against your own risk tolerance and a licensed advisor before acting.

---

## CONFIG

```
POSITIONS_CSV  = /Users/engineer/workspace/backtest/.cache/stocks-daily/positions.csv
TELEGRAM_YAML  = /Users/engineer/workspace/backtest/.cache/stocks-daily/telegram.yaml   # channel target (read at runtime)
NOTION_YAML    = /Users/engineer/workspace/backtest/.cache/stocks-advisor/notion.yaml    # Notion target (owned by stocks-advisor)
```

- `POSITIONS_CSV` — the user maintains this file; the skill NEVER invents or edits it.
- `TELEGRAM_YAML` — holds `channel_id` (e.g. `-1004393946155`) + `invite_link`. **Read the channel id at
  runtime — never hardcode it in this file or in a message.** If the file is missing or `channel_id` is
  empty, **skip the Telegram step silently** (absence is not an error).
- `NOTION_YAML` — read by stocks-advisor; Notion publishing is delegated there (Step 4).

---

## Core purpose & funding discipline (READ FIRST — this shapes every output)

**Purpose:** a DAILY monitor of the user's book for the question *"what do I already own (or want to own)
that is UNDERVALUED enough to buy MORE of today?"* — accumulation-of-quality-on-weakness, not churn.

**Funding discipline (the hard rule):** the user is ~fully invested — there is little idle cash. So **every
BUY/ADD recommendation MUST be paired with an explicit funding SELL** (the source of the dollars). A naked
"buy more X" with no "sell Y to pay for it" is incomplete and must not be emitted. The only exceptions:
- a `cash_to_deploy` amount is explicitly provided (then the buy is funded from cash), or
- the buy is a TRIM-and-rotate within the same name (stated as such).

This makes the core output a **SWAP table**: *Sell $N of {overvalued / broken / no-catalyst name} →
Buy $N of {more-undervalued, better-catalyst name}*, each row carrying the one-line reason the buy-side is a
better hold than the sell-side over the 1–2yr horizon. Tax-loss harvest is only recommended when the SWAP
names a concrete redeploy target — a sell with no "buy this instead" is not an action, it is just raising
cash and must be labelled as such.

**Positions the caller flags HOLD-ONLY stay HOLD-ONLY** (Step 1) — they are never the funding SELL. This
skill has no built-in bias toward or against any asset or sector; the HOLD-ONLY set is entirely
caller-supplied (see Step 1.4). Fund buys from broken/extended non-hold-only names instead.

---

1. Read `POSITIONS_CSV`. Schema: `Position,Quantity,Type,Unrealized_PnL`.
2. If the file is missing or empty, stop immediately. Tell the user:
   > "Create `{POSITIONS_CSV}` with columns: Position,Quantity,Type,Unrealized_PnL. One row per holding."
3. Parse into a holdings list: ticker, qty, type, pnl.
4. Tag positions HOLD-ONLY from **caller-supplied sources only** — this skill names no tickers itself and
   carries no built-in stance on any name or sector:
   - any ticker whose `Type` column in `POSITIONS_CSV` the user has tagged with a hold-only marker (e.g.
     `crypto-beta`, or literally `hold-only`) — that tag is the user's own data, maintained by them; or
   - any ticker/mandate stated explicitly in this run's invocation (e.g. a caller passes a list of
     tickers, or says "treat X as hold-only for this run").
   *Example, not a rule:* a crypto-bullish user might tag `COIN, TONX, CRCL, HOOD, SOFI, IBKR, BTC` as
   `crypto-beta` in their CSV — a different user's book would tag different names, or none at all.
   Pass all positions through to analysis unbiased; only mark caller-tagged ones exempt from EXIT/TRIM.

---

## Step 2 — Run the analysis (delegate to stocks-advisor; do NOT reimplement)

1. Read the project daily log (`.agents/memory/YYYY-MM-DD.md`) to extract any prior context for these
   tickers — pass it as `prior_context` to bias the run toward changed names and known watch levels.
2. Invoke the `stocks-advisor` skill in **holdings-review mode** on the parsed positions list.
   stocks-advisor handles: Step -1 memory recall, Step 0.7 TradingView health check (DEGRADED fallback = MA-only, WATCH-only verdicts), Step 0.8 triage (N>12 → full-panel top K≈10, one-line screen the rest), 6-seat panel analysis, Step 3.5 SOURCES & DATA appendix, Step 3.6 high-confidence RECAP + SETUP ALERTS.
3. Do NOT pull TradingView data, yfinance, or fundamentals yourself — stocks-advisor's orchestrator does that.
4. **Rank for accumulation.** From the panel output, rank holdings by *undervaluation + intact thesis +
   near-term catalyst* — the names worth buying MORE of today. A cheap name with NO catalyst is a value trap,
   not an accumulate candidate; say so. This ranked list feeds the SWAP table (Step 3c).
5. **Pair each accumulate candidate with a funding SELL.** For every ADD, name the non-hold-only holding to
   sell to fund it (broken/below-200d/no-catalyst/extended names are the funding pool), and state in one line
   why the buy-side is the better 1–2yr hold than the sell-side. Never emit a naked buy (Core funding rule).
6. Collect stocks-advisor's full output for assembly in Step 3.

---

## Step 3 — Assemble the report

Compose a single Markdown document in this order:

### (a) Date + Book Snapshot
- Report date
- Total equity (sum of positions × approximate price or use PnL + cost basis from CSV if available)
- Top-10 concentration % (top 10 positions as % of total book)
- Hold-only % (caller-flagged HOLD-ONLY names as % of total book)

### (b) Financial Narrative
- Sourced narrative from stocks-advisor's narrative seat.
- Every factual claim MUST include a URL citation. Reuse stocks-advisor's narrative output verbatim where possible.

### (c) SWAP TABLE — the headline output (accumulate-on-weakness, funded by a sell)
The most important section. One row per paired action. **No naked buys** (Core funding discipline).
Columns: `SELL (source) | $ | → | BUY (accumulate) | $ | Why buy-side is the better 1–2yr hold`.
- Buy-side = the highest-ranked undervalued-with-catalyst names from Step 2.4.
- Sell-side = non-hold-only broken/extended/no-catalyst funding names. Never a caller-flagged HOLD-ONLY name.
- If `cash_to_deploy` was provided, add cash-funded buy rows (SELL column = "CASH $N").
- If a name is cheap but has NO catalyst, it goes in the DROP list (e) as raise-cash, NOT here as a buy —
  and it may only be SOLD if its dollars are assigned to a specific BUY row (else label it "raise cash, no
  redeploy target yet").

### (d) ACCUMULATE WATCH — undervalued, buy MORE only when a condition fires
- Names that are undervalued but not buy-today (need a level/indicator trigger). Source: stocks-advisor
  Step 3.6 SETUP ALERTS. Columns: Asset | Exact condition | Then buy $N (funded by → SELL Y) | Thesis.
- After the table, add: "Register these alerts via the `mkt` skill."

### (e) DROP / FUNDING POOL List
- Non-hold-only EXIT and TRIM candidates with one-line reasoning — these are the SELL side of the swaps.
- For each, state whether its dollars are assigned to a BUY row (c) or are "raise cash, no redeploy target".
- Never include caller-flagged HOLD-ONLY names here.

### (f) ETF Section
- Which ETFs in the portfolio are fair/undervalued vs extended, per stocks-advisor ETF analysis.
- Note if only trend/MA data was available (no fundamental data for ETFs).

### (g) SOURCES & DATA Appendix
- All web-fetched URLs used in analysis.
- Fundamentals.py provenance (which tickers used live data vs cached).
- Reuse stocks-advisor Step 3.5 output verbatim.

---

## Step 4 — Publishing (delegated to stocks-advisor)

Notion publishing is owned by `stocks-advisor`. When `.cache/stocks-advisor/notion.yaml` is configured, the Step 2 delegation to stocks-advisor publishes the research as a dated Notion page (title `YYYY-MM-DD <narrative>`) and returns its URL. stocks-daily does NOT publish separately — this avoids duplicated publish logic. Capture the URL stocks-advisor returns for the Telegram link (Step 4.5) and the memory step. If stocks-advisor's Notion config is absent, no page is published (publishing is opt-in there); surface that to the user rather than re-implementing publishing here.

---

## Step 4.5 — Post the per-stock recap to the Telegram channel

This is the user-facing deliverable. It must be **self-contained** (the reader never has to open the prior
day's report or the Notion page to understand a verdict) and **scannable in seconds on a phone**.

**4.5a — Read the channel target at runtime (never hardcode):**
```bash
TELEGRAM_CLI=~/.agents/skills/telegram-cli/telegram-cli.py
CHANNEL=$(grep '^channel_id:' .cache/stocks-daily/telegram.yaml 2>/dev/null | sed -E 's/.*"([-0-9]+)".*/\1/')
[ -z "$CHANNEL" ] && echo "No telegram.yaml channel_id — skipping Telegram (not an error)" # then skip 4.5
```

**Recap style rules (mandatory — read before building the message):**

1. **No provenance-as-content.** Never write `"carried from MM-DD"` or `"no data this run"` as a seat's
   line — those are not findings, they're metadata. Rules:
   - Fresh this run → print the finding, no tag.
   - Reused from a prior run (not re-fetched today) → print the **actual finding/metric** from that prior
     verdict (e.g. "Sentiment: NEUTRAL — inst 62%, shorts 2.1%"), then append a compact `(as of MM-DD)`
     staleness tag at the end of the line. The tag is a suffix, never the whole line.
   - Genuinely nothing (source blocked AND no prior verdict exists for this seat/ticker) → **drop that seat
     line entirely** for that stock. Do not pad the block with a placeholder row.
   - Roll every dropped seat across the message into **one compact line**: `⚠️ dark seats: TICKER (Seat,
     Seat — reason); TICKER2 (...)`. One line total, not one per stock.
   - Net effect: a stock block shows only the seats that have real content — 3 lines and 6 lines are both
     fine; a padded 6-line block with "no data" filler is not.
2. **Lead with an action summary, then group by action — not by ticker order.** A reader must get the whole
   picture from the first few lines without scrolling through prose.

**4.5b — Build the message(s).** Use the exact stocks-advisor seat labels — Fundamental / Technical /
Narrative / Sentiment / Smart-Money / Sell-side — NOT the crypto seats.

```
📊 Stocks Daily — {TODAY} | Regime: {one phrase, e.g. "risk-off, debasement unwind"}
{1-sentence macro context — the single dominant driver this week}

⚡ ACTION SUMMARY
{EMOJI} {TICKER} {ACTION} — {single controlling reason, ≤10 words}
...one line per actionable ticker (every BUY/ADD/TRIM/EXIT), SELL/TRIM/EXIT first then ADD/BUY...

━━━━━━━━━━━━━━━━━━━━━━
🔻 SELLS / TRIMS / EXITS
━━━━━━━━━━━━━━━━━━━━━━
{EMOJI} {TICKER} ${PRICE} — {DECISION}
  📊 Fundamental:  {finding (plain explanation in parens)} [(as of MM-DD) if reused]
  📈 Technical:    {finding (plain explanation in parens)} [(as of MM-DD) if reused]
  📰 Narrative:    {finding (plain explanation in parens)} [(as of MM-DD) if reused]
  🌡 Sentiment:    {finding (plain explanation in parens)} [(as of MM-DD) if reused]
  🐋 Smart-Money:  {finding (plain explanation in parens)} [(as of MM-DD) if reused]
  🏦 Sell-side:    {finding (plain explanation in parens)} [(as of MM-DD) if reused]
...only seats with real content — see rule 1. Repeat block per stock in this bucket...

━━━━━━━━━━━━━━━━━━━━━━
🟢 ADDS / BUYS
━━━━━━━━━━━━━━━━━━━━━━
...same per-stock block shape...

🔁 TODAY'S SWAPS (every buy funded by a sell):
  SELL {Y} ${N} → BUY {X} ${N}  — {≤10-word why X is the better hold}
  ...one line per swap...

[--- PART 2 (only if needed) starts here ---]

━━━━━━━━━━━━━━━━━━━━━━
🟡 NOTABLE HOLDS / WATCH
━━━━━━━━━━━━━━━━━━━━━━
...per-stock block for holds with a material change or new finding only...
🟡 HOLD (no change): {space-separated tickers — quiet holds get one line, not a block}

⚠️ dark seats: {TICKER (Seat, Seat — reason); ...}  [omit line entirely if nothing is dark]

📋 Full 6-seat report (Notion):
{NOTION_PUBLIC_URL}

DYOR. Educational only. Not financial advice. #Stocks #Investing
```

**Concrete stock block example (fresh + reused seats mixed, per rule 1):**
```
🔴 COIN $149 — TRIM
  📊 Fundamental:  Fwd P/E 38, FCF yield 1.1% (rich); rev tied to crypto volume (cyclical, not steady).
  📈 Technical:    Below 200d MA ($178 long-term avg), RSI 41 (weak), MACD bearish — downtrend intact.
  📰 Narrative:    Debasement trade unwinding (gold −12% MTD, BTC down) — crypto-beta out of favor. (as of 07-07)
  🌡 Sentiment:    22.7% of the book in one name — extreme single-name concentration risk.
  ⚠️ dark seats: COIN (Smart-Money — openinsider blocked, no prior verdict)

🟢 KHC $25.30 — ADD
  📊 Fundamental:  Cheap (fwd P/E 12.1), FCF yield 10.7%, genuine 6.45% dividend. (as of 07-07)
  📈 Technical:    Above 200d MA (+7.0%) — uptrend confirmed.
  📰 Narrative:    CEO bought $4.99M open-market. (as of 07-07)
  🌡 Sentiment:    NEUTRAL — inst ~65%, short interest ~2% (light, no crowding). (as of 07-07)
  🐋 Smart-Money:  CEO open-market buy is the smart-money signal — no separate 13F delta this week. (as of 07-07)
```

**⛔ Rules (mirror crypto-daily):**
- Apply the **Recap style rules** above to every seat line and to message structure — no exceptions.
- Keep the technical term, then follow it with `(plain explanation)` in parentheses — write for a non-expert.
- Use concrete numbers where available ($, %, P/E, RSI).
- Signal emoji: **🟢 BUY / ADD · 🟡 HOLD / WATCH · 🔴 TRIM / EXIT / SELL**. HOLD is 🟡, never 🔴 — red is
  reserved for reduce-the-position actions only.
- **Caller-flagged HOLD-ONLY names** (Step 1: tagged via the CSV `Type` column or stated in this run's
  invocation) — if the panel said EXIT/TRIM but the name is HOLD-ONLY, show it as 🟡 HOLD on Telegram. The
  one exception: if the user's own review this run explicitly approved a TRIM (e.g. trimming a 22%
  concentration down to target), honor that TRIM.
- The ACTION SUMMARY reason must be the single controlling factor, ≤10 words — not a restated seat line.
- The BUY/ADD summary line and ACTION SUMMARY MUST include price for every ticker.
- No raw URLs inline — the Notion link is the ONLY URL in the message.
- **Length:** split at section/stock boundaries into multiple messages, not mid-block:
  - Part 1: header + macro + ACTION SUMMARY + every SELL/TRIM/EXIT block + every ADD/BUY block + SWAP table
  - Part 2 (only if needed): NOTABLE HOLDS/WATCH blocks + quiet-holds line + dark-seats line + Notion link + disclaimer
  - Verify each part: `echo -n "$PART" | wc -c` — must be ≤ 4096.

**4.5c — Send via telegram-cli (numeric channel id from config):**
```bash
python3 "$TELEGRAM_CLI" send "$CHANNEL" "$PART1"
python3 "$TELEGRAM_CLI" send "$CHANNEL" "$PART2"   # if multi-part
```

**4.5d — Verify delivery:**
```bash
python3 "$TELEGRAM_CLI" read "$CHANNEL" --limit 1
```
The sent message appears as the most recent. Confirm the Notion URL is live before sending.

**Error handling:**
| Error | Fix |
|---|---|
| `session not authenticated` | `python3 "$TELEGRAM_CLI" login` |
| `ChatWriteForbiddenError` | The account must be a member with post rights on the channel |
| `Cannot find any entity corresponding to` | Re-confirm `channel_id` in telegram.yaml; the account must have joined the invite link first |
| Notion URL not accessible | Enable "Share to web" in Notion before sending |

---

## Step 5 — Persist memory (mandatory; do BEFORE replying to user)

Append to `.agents/memory/$(date +%F).md` using the standard workflow_memory_format:

```markdown
## stocks-daily — YYYY-MM-DD
**Query:** Daily accumulation monitor (what to buy more of, funded by what)
**Assets found:** [comma-separated tickers reviewed]
**Swaps:**
- SELL {Y} $N → BUY {X} $N | why: [one line]
**Verdicts:**
- TICKER: [T1/T2/T3/AVOID] [ACCUMULATE/WAIT/AVOID/HOLD] | entry: [price zone or condition] | catalyst: [trigger] | invalidation: [kill condition]
**Key delta:** [what changed vs prior run — one sentence]
**Report:** [Notion page URL returned by stocks-advisor, or "inline" if unpublished]
```

stocks-advisor writes per-ticker detail memory; this step adds the daily roll-up + the swap decisions. Do not skip.

---

## Scheduling (document only; do not auto-create)

To automate: use the `schedule` skill or configure a cron that fires `/stocks-daily` once a day (e.g., before the US open or after the close).

The skill is **idempotent per run** — re-running creates another dated Notion page; no harm done.

---

## Done when

- [ ] `positions.csv` read and parsed without inventing data
- [ ] stocks-advisor analysis completed (holdings-review mode)
- [ ] Holdings ranked for accumulation; cheap-but-no-catalyst names labelled value traps, not buys
- [ ] **SWAP table emitted — every BUY/ADD paired with a funding SELL** (no naked buys); tax-loss harvest
      only recommended with a named redeploy target, else labelled "raise cash, no target yet"
- [ ] Report assembled: narrative + SWAP table + ACCUMULATE WATCH + DROP/funding pool + ETF section + SOURCES appendix
- [ ] Notion publishing left to stocks-advisor (no duplicate publish here); captured the returned page URL if one was produced
- [ ] **Telegram recap posted to the channel** (id from `telegram.yaml`, read at runtime) — ACTION SUMMARY
      first, detail blocks grouped SELL/TRIM/EXIT → ADD → HOLD, only substantive seat lines (no "carried
      from" / "no data this run" filler — reused findings carry an `(as of MM-DD)` tag, dark seats collapsed
      into one line), the SWAP lines, correct signal emoji (🟢/🟡/🔴), multi-part split ≤4096 bytes, Notion
      link only in the final part — or skipped silently if `telegram.yaml` is absent
- [ ] Memory entry appended to daily log (including the swaps)
- [ ] Response to user flags output as educational, not advice
