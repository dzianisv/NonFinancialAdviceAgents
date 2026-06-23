---
name: crypto-portfolio-manager
description: "Manages the crypto portfolio — runs analysis on every token in the universe (BTC/ETH/SOL/UNI/HYPE/AAVE/LINK) and outputs a BUY/SELL/HOLD decision per token. Run on demand or via /loop. Educational, not advice."
license: MIT
compatibility: opencode
metadata:
  audience: crypto-allocators
  domain: crypto-portfolio-management
  role: portfolio-manager
---

# Crypto Portfolio Manager

Analyze every token in the universe **sequentially** → decide BUY/SELL/HOLD per token → print the signal table.

> Educational analysis, not financial advice. No leverage. Ever.

## Quickstart

### Default daily run
```
Run the crypto portfolio manager
```
The skill analyzes the default token universe, pulls live TradingView data, runs a 5-seat quorum per token, and prints the full 3-block report (signal table + plain-English verdicts + ranked news sources). **Attach a TradingView screenshot for each token.**

### Custom token set
```
Run the crypto portfolio manager on: TON, PUMP, JUP, HYPE
```

### Full prompt (copy-paste for any session)
```
Invoke the crypto-portfolio-manager skill. Token universe for this run: [TOKEN1, TOKEN2, ...].
Follow all skill instructions:
- chart_get_state → dedup indicators → set_symbol → D OHLCV (365 summary + 210 bars) → study values → W OHLCV → capture_screenshot
- Compute MAs via .agents/skills/crypto-portfolio-manager/scripts/indicators.py
- Run 5-seat quorum inline (on-chain, sentiment, macro, order-flow, narrative)
- Narrative seat: web-fetch ≥3 sources, rank T1/T2/T3, quote exact sentences
- Print 3-block report: signal table | plain-English verdicts | news sources
- Attach TradingView screenshot for each token in the reply
Educational, not financial advice.
```

### Scheduling (continuous)
```
/loop interval=6h    ← re-runs every 6 hours, resumes from last pending todo
/stop                ← cancel the loop
```

---

## Token universe

BTC, ETH, SOL, UNI, HYPE, AAVE, LINK — edit this list to add/remove tokens.

---

## Hard constraints — read before running (these dictate the whole design)

1. **TradingView MCP tools live ONLY in the orchestrator (you).** Subagents spawned via the task tool get a fresh toolset with **no** `tradingview-*` tools — verified. So **YOU** must pull every chart datum yourself. Never tell a subagent to "pull TradingView data" — it cannot. Subagents may only *receive* an already-assembled data package and reason over it (they can still web-fetch F&G / on-chain).
2. **The chart is a single shared symbol slot.** `chart_set_symbol` changes the one global chart, so two tokens cannot be pulled at once. **Therefore the data loop is strictly sequential, one token at a time.** Track progress in the `todos` table so a `/loop` or an interrupted run resumes cleanly.
3. **Read every indicator TradingView can give from TradingView — don't recompute it.** `data_get_study_values` returns RSI(14), Bollinger(20,2), MACD(12,26,9) and Volume correctly at their standard lengths. Use those values verbatim. The **only** gap is moving averages: `chart_manage_indicator` ignores the MA `length` input (an added MA exposes `inputs:[]` and stays stuck at a short default ≈ price; verified BTC read $64,540 when SMA200 was ~$76,600) and has no `update` action. So EMA20 / SMA50 / SMA200 / 200-week-MA — and only those — are computed by `scripts/indicators.py` from the MCP's **own** returned closes (plain rolling means / EWMs; the data source stays 100% TradingView).

TradingView symbol mapping: `BINANCE:{TOKEN}USDT` (e.g. `BINANCE:BTCUSDT`). If a symbol is missing on Binance, try `OKX:{TOKEN}USDT`.

---

## Step 0 — Seed the todo list (one row per token)

```sql
INSERT INTO todos (id, title, description) VALUES
 ('tok-BTC','Analyzing BTC','Pull TradingView D/W OHLCV+studies, compute pkg, run 5-seat quorum, decide signal'),
 ('tok-ETH','Analyzing ETH','idem'), ('tok-SOL','Analyzing SOL','idem'),
 ('tok-UNI','Analyzing UNI','idem'), ('tok-HYPE','Analyzing HYPE','idem'),
 ('tok-AAVE','Analyzing AAVE','idem'), ('tok-LINK','Analyzing LINK','idem');
```

Create the verdict tracker once:

```sql
CREATE TABLE IF NOT EXISTS token_analysis (
  symbol TEXT PRIMARY KEY, quorum_verdict TEXT, dominant_zone TEXT,
  seats_bull INTEGER, seats_bear INTEGER, key_support REAL, key_resistance REAL,
  confidence TEXT, signal TEXT, status TEXT DEFAULT 'pending');
```

---

## Step 1 — Sequential per-token loop (orchestrator does this; do NOT parallelize the data pull)

Pick the next `pending` todo and `UPDATE todos SET status='in_progress'`. Then, for that token:

**1a. Pull TradingView data (MCP, in this session):**

First, call `tradingview-chart_get_state` and inspect the `studies` list.  
**Only add an indicator if its name is NOT already present** — adding a duplicate pushes a second identical series onto the chart, inflates context, and produces duplicate rows in `data_get_study_values`. Use `chart_manage_indicator action=remove` on the extra entity_id if duplicates already exist.

Required studies (add only if absent): **Relative Strength Index**, **Bollinger Bands**, **MACD**. Do NOT add length-N EMAs — the length input is ignored (constraint 3). Volume is always present.

```
tradingview-chart_get_state                                → inspect studies list; deduplicate before proceeding
tradingview-chart_set_symbol     symbol="BINANCE:{TOKEN}USDT"
tradingview-chart_set_timeframe  timeframe="D"
tradingview-data_get_ohlcv       count=365 summary=true   → 52w high/low + avg volume
tradingview-data_get_ohlcv       count=210 summary=false  → >=200 daily closes (for SMA200)
tradingview-data_get_study_values                          → RSI(14), BB(20,2), MACD, Volume (one of each)
tradingview-chart_set_timeframe  timeframe="W"
tradingview-data_get_ohlcv       count=210 summary=false  → weekly closes (for 200-week MA)
tradingview-chart_set_timeframe  timeframe="D"             → reset to daily
tradingview-capture_screenshot                             → save screenshot; then call view tool on the returned file_path to embed the image inline in your reply for this token
```

**1b. Read the indicators from TradingView; compute only the moving averages.** From `data_get_study_values` take RSI(14), Bollinger(20,2), MACD line/signal/hist, Volume — verbatim, no recompute. From the daily `summary=true` pull take 52w high/low + avg volume. Then fill the MA gap (computed MAs match TradingView's own values):
```bash
/Users/engineer/.venv/bin/python3 .agents/skills/crypto-portfolio-manager/scripts/indicators.py /tmp/{TOKEN}.json
```
Helper input: `{"symbol","price","daily_closes":[...],"weekly_closes":[...]}`. Helper output: EMA20, SMA50, SMA200, 200-week MA, and the death cross (classic SMA50/SMA200, exact). Nothing else — it does not recompute RSI/BB/MACD.

**1c. Assemble the data package** by merging the TradingView study values (RSI, BB, MACD, Volume, 52w hi/lo) with the helper's moving-average block: price, %from-52wh, EMA20, SMA50, SMA200, death_cross, RSI, MACD line/signal/hist, BB upper/mid/lower + position, volume vs 30d avg, 200-week MA + %vs it.

**1d. Run the 5-seat quorum on the package.** Either reason through the 5 seats inline, or spawn the five `analysis-*` seat subagents **in parallel** (on-chain, sentiment, macro, order-flow, narrative) with the package **injected** — seats per token may be parallel because they share nothing; only the *data pull* must be serial. Each seat returns: zone, posture (BULLISH|NEUTRAL|BEARISH), confidence, 1-line bull, 1-line bear, invalidation.

**Narrative seat — mandatory sourcing protocol.**

**⛔ HARD RULE: You MUST call `web_fetch` on a real URL before you can cite it as a source. If you did not call `web_fetch(url)` on it, it is NOT a source — do not write it down. A fabricated headline with no URL is a hallucination and invalidates the entire narrative verdict.**

**Step-by-step (do this in order, do not skip):**

> ⚠️ **Known broken sources (do NOT use)**:
> - `coindesk.com/search?q=...` — always returns the same unrelated featured article regardless of query. Never use search URLs.
> - `decrypt.co/tag/...` — 404 for most tokens.
> - `cryptopanic.com/news/...` — returns only page title, no articles.
> Use the **two-step discovery pattern** for news: (1) fetch a listing page to get current article URLs, (2) fetch the actual article URL for the quote.

1. **Call `web_fetch` on at least 3 of these starting URLs** for the token. Pick the most relevant:

   **On-chain data (T1 — always try first):**
   - Fear & Greed: `https://api.alternative.me/fng/?limit=1` (JSON — hard T1)
   - DeFiLlama chain page: `https://defillama.com/chain/ethereum` | `https://defillama.com/chain/solana` etc. (T1 — TVL, fees, revenue)
   - DeFiLlama protocol page: `https://defillama.com/protocol/{token-slug}` e.g. `aave`, `uniswap`, `chainlink` (T1)

   **News discovery — two-step (T2):**
   - Step 1: fetch the **listing page** to get current article URLs:
     - `https://www.coindesk.com/markets` → BTC/ETH price/macro news
     - `https://www.coindesk.com/tech` → DeFi/protocol news
     - `https://www.theblock.co/latest` → broad crypto news
   - Step 2: from the listing page response, extract any article URL relevant to the token (e.g. `https://www.coindesk.com/markets/2026/06/21/bitcoin-holds-near-...`), then **fetch that article URL** and quote from its body. The article URL — not the listing page — is what you cite in Block 3.

2. **Read what actually came back.** If the fetch returns an error or no relevant content, write `[FETCH FAILED: <url>]` — do NOT count it toward the 3-source minimum, do NOT invent what it "would have said."

3. **Quote verbatim** — copy an exact sentence or number from the page. Do not paraphrase from memory.

4. **Rank sources by signal quality:**
   - **Tier 1 — Primary signal**: on-chain/flow data with timestamps and hard numbers (ETF flow $, protocol revenue $, F&G index value). Weight: 3×. Drives posture.
   - **Tier 2 — Credible context**: Bloomberg/Reuters/FT/WSJ/CoinDesk/TheBlock with named sources and specific claims. Weight: 2×. Supports posture.
   - **Tier 3 — Noise/sentiment gauge**: social media, "analysts say", recycled press releases. Weight: 0.5×. Informs sentiment only, never drives posture verdict.

5. **Show the ranking reason** for each: one sentence (e.g. "T1: F&G returned value=18 with timestamp — hard data point directly measuring market fear").

6. **State the invalidation anchor**: what would reverse this verdict if the evidence were opposite.

Narrative seat output format (inline, per token):
```
NARRATIVE — {TOKEN}
Posture: BULLISH | NEUTRAL | BEARISH
Sources fetched (ranked):
  [T1] https://<actual-url-you-called-web_fetch-on> — "<verbatim quote from page>" → T1 because: <one sentence>
  [T2] https://<actual-url-you-called-web_fetch-on> — "<verbatim quote from page>" → T2 because: <one sentence>
  [T3] https://<actual-url-you-called-web_fetch-on> — "<verbatim quote from page>" → T3 because: <one sentence>
  [FETCH FAILED: https://...] — not counted
Bull: <1-line>
Bear: <1-line>
Invalidation: <what reverses this verdict>
```

**If you have fewer than 2 successfully fetched sources after trying all applicable URLs above, set posture = NEUTRAL and note "INSUFFICIENT DATA" — do not guess.**

**1e. Aggregate into the compact verdict and persist:**
```json
{"symbol":"BTC","quorum_verdict":"BULLISH|SPLIT|BEARISH|UNCERTAIN",
 "dominant_zone":"DEEP_VALUE|FAIR_VALUE|ELEVATED|EXTREME|UNKNOWN",
 "seats_bull":3,"seats_bear":2,"key_support":60000,"key_resistance":66000,"confidence":"HIGH|MED|LOW"}
```
```sql
UPDATE token_analysis SET quorum_verdict=?, dominant_zone=?, seats_bull=?, seats_bear=?,
  key_support=?, key_resistance=?, confidence=?, signal=?, status='done' WHERE symbol=?;
UPDATE todos SET status='done' WHERE id='tok-{TOKEN}';
```

**1f. Repeat** for the next `pending` todo until none remain.

---

## Step 2 — Decide per token

| Signal | Condition |
|---|---|
| **BUY** | `quorum_verdict = BULLISH`, seats_bull ≥ 3 |
| **BUY (small)** | `quorum_verdict = SPLIT`, `dominant_zone = DEEP_VALUE` |
| **SELL** | `quorum_verdict = BEARISH`, seats_bear ≥ 4 |
| **HOLD** | everything else |

## Step 3 — Print the full run report

Print **three blocks** in this exact order:

### Block 1 — Signal table (one-glance summary)
```
=== CRYPTO PORTFOLIO RUN — {timestamp} ===   (data: TradingView MCP)

Token | Signal      | Zone       | Quorum | Bulls/Bears
------|-------------|------------|--------|------------
BTC   | HOLD        | FAIR_VALUE | SPLIT  | 2 / 2
ETH   | BUY (small) | DEEP_VALUE | SPLIT  | 1 / 2
SOL   | BUY (small) | DEEP_VALUE | SPLIT  | 3 / 1
...
```

### Block 2 — Plain-English verdict per token
For every token write 3–5 sentences a non-expert can understand. Cover:
- **Why this signal**: what 1–2 facts drove the decision (price vs 200w MA, RSI, death cross, on-chain zone).
- **Main risk**: the single biggest thing that could make this call wrong.
- **What to watch**: the one trigger that would change the signal (e.g. "close above SMA50" → HOLD flips to BUY).

Example:
```
BTC — HOLD
BTC is down 42% from its all-time high and is sitting right on the 200-week
moving average (~$62k), the historical long-term floor. The RSI has recovered
to neutral (42.6) and the MACD is starting to turn up — early signs the
selling pressure is fading. However a death cross is active (50-day below
200-day), macro is hostile (Fed holding rates, strong dollar), and ETF flows
are still negative. Not cheap enough on-chain to force a buy, not broken
enough to sell. Watch for a daily close above the 50-day SMA ($71.9k) to
upgrade to BUY, or a weekly close below $60k to reassess.

ETH — BUY (small)
ETH has crashed 63% from its 52-week high and is now 30% below its 200-week
moving average — a level historically associated with cycle bottoms. One panel
seat is bullish (on-chain deep value), two are bearish (macro headwinds and
compressed fee revenue from L2 competition). The split verdict with extreme
undervaluation triggers the "small position" rule: start a toe-hold, don't
go large. Key risk: ETH could continue losing ground vs BTC if L2 fee erosion
persists. Upgrade to BUY if price reclaims the 200-week MA (~$2,472).
```

### Block 3 — News & sources used by the Narrative seat
List every URL the narrative seat fetched, with a one-line plain-English
summary of what it said and why it was ranked T1/T2/T3.

```
--- NEWS SOURCES ---
(Only URLs you actually called web_fetch on appear here. No URL = no entry.
Every entry MUST start with https:// — source name alone is NOT acceptable.)

BTC narrative (posture: BEARISH)
  [T1] https://api.alternative.me/fng/?limit=1 — "value: 18, value_classification: Extreme Fear" → T1: hard numeric index with timestamp, directly measures crowd fear
  [T2] https://www.coindesk.com/markets/2026/06/21/bitcoin-options-traders-scrambling → "Bitcoin traders are scrambling to buy options bets that would pay off if the selloff deepens" → T2: named-source journalism, live positioning data
  [T3] https://www.coindesk.com/markets/2026/06/20/bitcoin-54k-analyst-forecast → "Bitcoin price may be headed to $54,000, says analyst who forecast October's all-time high" → T3: analyst opinion, useful for risk framing, no hard data
  [FETCH FAILED: https://www.theblock.co/latest] — no BTC-specific articles visible

ETH narrative (posture: BULLISH)
  [T1] https://defillama.com/chain/ethereum — "Chain Revenue (24h)$65,225... App Revenue (24h)$1.1m... Bridged TVL$349.351b" → T1: primary on-chain metrics with exact daily figures
  [T2] https://www.coindesk.com/tech/2026/06/21/ethereum-staking-update → "SharpLink Gaming adds ETH to treasury" → T2: credible source, specific catalyst
  [FETCH FAILED: https://defillama.com/protocol/lido] — returned only funding rounds, no TVL data
```

> ⚠️ Wrong (never do this):
> ```
> T1 — CoinDesk
> Quote: "Bitcoin traders are scrambling..."
> ```
> Wrong because: no `https://` URL, no actual article link. Source name alone = hallucination risk.
>
> Right:
> ```
> [T1] https://www.coindesk.com/markets/2026/06/21/bitcoin-options-traders-... — "Bitcoin traders are scrambling..."
> ```

Self-check before printing:
- Every token has `status='done'` in `token_analysis`
- `seats_bull + seats_bear <= 5` for each token
- Every narrative source entry starts with `https://` followed by the **specific article URL** (not a listing/search page) — if any entry has only a source name or no URL, remove it and mark INSUFFICIENT DATA
- **Two-step verified**: news citations point to the article URL you fetched (step 2), not the listing page (step 1)
- A TradingView screenshot is embedded inline (via `view` tool on the `file_path`) for every token — not just captured, but visible
- **No source may be cited that was not actually fetched this run** — verify: "did I call web_fetch on this exact URL?" If no, remove it

## Step 4 — Citation validation (post-hook)

After printing Block 3, run the `reference-validator` post-hook to verify every source cited in the narrative seats is real.

**4a. Assemble the citations JSON** — collect every `[T1]`, `[T2]`, `[T3]` entry from Block 3 that has a real `https://` URL (skip `[FETCH FAILED]` entries — those are already flagged):

```json
[
  {"token":"BTC","tier":"T1","url":"https://api.alternative.me/fng/?limit=1","quote":"value: 18, value_classification: Extreme Fear"},
  {"token":"BTC","tier":"T2","url":"https://www.coindesk.com/search?q=bitcoin+ETF+2026","quote":"Bitcoin ETF products saw $218M outflow"},
  ...
]
```

**4b. Spawn `reference-validator` as a subagent** — pass the full JSON array. The validator re-fetches every URL and checks if the quoted text is actually present in the page. It can use `web_fetch` (subagents have that tool; only `tradingview-*` tools are orchestrator-only).

```
Invoke the reference-validator skill with this citations JSON:
[...paste array here...]
```

**4c. Print the validation report** returned by the subagent verbatim — do not edit it.

**4d. Act on failures:**
- Any token with ≥1 `NOT_FOUND` source → append `⚠️ CITATION_FAILED` to that token's signal in Block 1 and note it in Block 2.
- Any token with only `FETCH_FAILED` sources → append `ℹ️ UNVERIFIED` to that token's signal.
- If ALL sources for ALL tokens are `VERIFIED` or `PARTIAL` → print `✅ All citations verified`.

> **Why this step exists:** LLM agents fabricate plausible-sounding URLs and headlines. The validator re-fetches every URL cold (subagent has no memory of the original fetch) and does a literal string match. A hallucinated quote will fail even if the URL resolves — the text won't be there.

---

## Running continuously

```
/loop interval=6h
/stop
```

On each loop, re-seed any `pending`/missing todos and resume the sequential pull — never start a second data pull while one is in flight.
