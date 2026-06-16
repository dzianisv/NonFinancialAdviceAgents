---
name: congressman-stock-watch
description: "Watch recent congressional stock disclosures (STOCK Act — House + Senate) and propose NEW buy-candidates from what members of Congress just purchased. Use when asked \"what stocks are congressmen buying\", \"track congressional trades\", \"what did Pelosi/McCaul buy\", \"run the congressional watcher\", \"congressman stock picks\", \"STOCK Act tracker\", or on a schedule. Fetches Capitol Trades via WebFetch (free, no API key), filters for PURCHASES only, deduplicates against a ledger so the same ticker is never proposed twice. Recommend-only — never trades. Educational, not advice. Note: disclosures lag 30-45 days; congress-members are long-only (personal accounts), not macro smart-money."
license: MIT
compatibility: opencode
metadata:
  audience: event-driven-and-political-alpha-investors
  domain: congressional-disclosure-watchlist
  role: stock-act-buy-watcher-and-deduper
  source: "Capitol Trades (https://www.capitoltrades.com)"
---

# Congressional Stock Watch (propose new buys from STOCK Act filings)

Scan recent House + Senate STOCK Act disclosures, surface what members of Congress newly **purchased**, and propose the un-proposed ones as buy-candidates. The point is a *standing watchlist that never repeats itself* — every ticker is deduped against the ledger before it's proposed.

## Recommend-only (hard rule)

This **proposes / notifies** — it **never trades** and never sizes a real order. Output is a candidate list for the decision pipeline. Educational, not advice.

## Important caveats

- **30–45 day lag:** STOCK Act requires disclosure within 45 calendar days of a transaction.
- **Long-only, personal accounts:** Not macro smart-money. Focus on clusters (≥3 members same ticker).
- **Purchases only:** Ignore sales, partial sales, exchanges.

## Data source

**Capitol Trades** (https://www.capitoltrades.com) — free, no API key, aggregates both chambers.

**Background:** housestockwatcher.com and senatestockwatcher.com are permanently decommissioned (no DNS A record). Their S3 mirrors are private (403). Capitol Trades is the working replacement.

## Fetch procedure (WebFetch — do NOT spawn a Python subprocess for the fetch)

```
WebFetch: https://www.capitoltrades.com/trades?txType=buy&govBody=congress&orderBy=-txDate&pageSize=96

Parse the result:
- If the page contains a trade table or JSON data: extract each row.
- Fields to capture per trade: Ticker, Member name, Chamber (House/Senate),
  Transaction date, Amount range, Asset name.
- Keep only PURCHASES (txType=buy). Drop sales/exchanges.
- Filter to last 90 days only.
```

If Capitol Trades returns a 429 or is blocked: emit `[SIGNAL UNAVAILABLE — Capitol Trades rate-limited]` and continue with the rest of the pipeline. Do NOT fabricate transactions.

## The loop

After fetching and parsing trades from WebFetch above:

```bash
W="python3 .agents/skills/congressman-stock-watch/watch.py"
```

1. **Keep only PURCHASES** in last 90 days. Drop: Sales, Exchanges, Partial Sales, options.
2. **Rank by conviction**, strongest first:
   - **Cross-member cluster** — ≥3 different members buying the same ticker (strongest signal).
   - **Dollar range** — `$1,000,001+` or `$500,001–$1,000,000` beat sub-$50k buys.
3. **DEDUPE — the core rule.** For each candidate ticker:
   ```bash
   $W seen <TICKER>
   ```
   - exit 0 (`SEEN … SKIP`) → already recommended; drop it.
   - exit 1 (`NEW`) → ok to propose.
4. **Propose the NEW ones** (recommend-only): ticker, member(s), chamber, date, dollar-range, WHY. Then **record each**:
   ```bash
   $W record --ticker NVDA --member "Nancy Pelosi" --chamber house \
             --date 2026-01-15 --amount "$1,000,001+" --action purchase \
             --reason "Bought ahead of CHIPS Act procurement cycle"
   ```
5. **Cross-check with 13f-watch:** ticker in a recent super-investor 13F buy → note overlap (upgrades conviction).
6. **DM the NEW proposals** only. Include: ticker, member(s), transaction date, disclosure date, dollar range, cluster size.

## Ledger management

```bash
python3 .agents/skills/congressman-stock-watch/watch.py list               # all recommended so far
python3 .agents/skills/congressman-stock-watch/watch.py list --since 2026-01-01
python3 .agents/skills/congressman-stock-watch/watch.py seen NVDA          # exit 0=seen, 1=new
```

Ledger path: `$CONGRESS_LEDGER` or `./congress/recommended.jsonl`

## Success criteria

- [ ] WebFetched Capitol Trades and parsed at least some trades (or noted unavailability).
- [ ] Output shows only PURCHASES, not sales.
- [ ] Every candidate checked against dedup ledger; none previously recommended re-proposed.
- [ ] Cluster counts computed (cross-member buys of same ticker).
- [ ] New tickers recorded in ledger after proposal.

## Schedule

Run **weekly on Mondays**. Set `$CONGRESS_LEDGER` to a persistent path so dedup carries across runs.
