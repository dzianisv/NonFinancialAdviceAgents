---
name: congressman-stock-watch
description: Watch recent congressional stock disclosures (STOCK Act — House + Senate) and propose NEW buy-candidates from what members of Congress just purchased. Use when asked "what stocks are congressmen buying", "track congressional trades", "what did Pelosi/McCaul buy", "run the congressional watcher", "congressman stock picks", "STOCK Act tracker", or on a schedule. Fetches from housestockwatcher.com + senatestockwatcher.com APIs, filters for PURCHASES only, deduplicates against a ledger so the same ticker is never proposed twice. Recommend-only — never trades. Educational, not advice. Note: disclosures lag 30-45 days; congress-members are long-only (personal accounts), not macro smart-money.
license: MIT
compatibility: opencode
metadata:
  audience: event-driven-and-political-alpha-investors
  domain: congressional-disclosure-watchlist
  role: stock-act-buy-watcher-and-deduper
  source: "housestockwatcher.com + senatestockwatcher.com (community STOCK Act aggregators)"
---

# Congressional Stock Watch (propose new buys from STOCK Act filings)

Scan recent House + Senate STOCK Act disclosures for members of Congress, surface what they **newly purchased**, and propose the **un-proposed** ones as buy-candidates. The point is a *standing watchlist that never repeats itself* — every ticker is deduped against the ledger before it's proposed.

## Recommend-only (hard rule)

This **proposes / notifies** — it **never trades** and never sizes a real order. Output is a candidate list for the decision pipeline. Educational, not advice.

## Important caveats

- **30–45 day lag:** STOCK Act requires disclosure within 45 calendar days of a transaction. You are seeing what was traded a month-plus ago, not today.
- **Long-only, personal accounts:** These are members' personal brokerage accounts. Not macro smart-money. Some may trade on non-public information (illegal but hard to prove); most are just wealthy individuals.
- **Do not rely on sells:** Sells can be for many reasons (tax, divorce, rebalancing). Focus on **PURCHASES** with a notable dollar-range.
- **Cluster signal:** A ticker appearing in ≥3 purchases across different members in the same filing period is a stronger signal than a single buy.

## Data sources

```
https://housestockwatcher.com/api/transactions         — House disclosures JSON
https://senatestockwatcher.com/api/transactions        — Senate disclosures JSON
```

Both APIs are maintained by open-source community projects (not official .gov). Always verify notable transactions against the official EFTS eForms search:
```
https://efts.sec.gov/LATEST/search-index?q=%22Form+8%22&dateRange=custom...
```

## The loop

```bash
W="python3 .agents/skills/congressman-stock-watch/watch.py"

$W roster        # list tracked legislators (optional — defaults to all from API)
$W recent        # pull & print the most recent 90 days of PURCHASE transactions
```

1. **Pull recent disclosures** from housestockwatcher.com + senatestockwatcher.com APIs. Use the `watch.py recent` command — it does the HTTP fetch, filters PURCHASE-only, ranks by cluster and dollar size.
2. **Keep only PURCHASES.** Drop: Sales, Exchanges, Partial Sales, options-only transactions.
3. **Rank by conviction**, strongest first:
   - **Cross-member cluster** — ≥3 different members buying the same ticker in the last 90 days (strongest signal).
   - **Dollar range** — `$1,000,001+` or `$500,001–$1,000,000` ranges beat sub-$50k buys.
   - **Committee relevance** — member sits on committee with regulatory oversight of that industry.
4. **DEDUPE — the core rule.** For each candidate: `$W seen <TICKER>`.
   - exit 0 (`SEEN … SKIP`) → **already recommended, drop it.** Do not propose again.
   - exit 1 (`NEW`) → ok to propose.
5. **Propose the NEW ones** (recommend-only): ticker, member(s), chamber, date, dollar-range, committee hint if any, the WHY (1-2 lines). Then **record each** so it's never repeated:
   ```bash
   $W record --ticker NVDA --member "Nancy Pelosi" --chamber house \
             --date 2026-01-15 --amount "$1,000,001+" --action purchase \
             --reason "Bought ahead of CHIPS Act procurement cycle"
   ```
6. **Cross-check with 13f-watch:** If the ticker was ALSO in a recent super-investor 13F buy — note the overlap; it upgrades the signal.
7. **Route to superforecasting** for a dated probability if it merits it.
8. **DM the NEW proposals** (never the already-seen ones). Include: ticker, member(s), date of transaction, disclosure date (when we learned), dollar range, cluster size, committee hint, put-checked (congressional buys are personal longs, not puts), confidence level.

## Success criteria ("Done when")

- [ ] Pulled fresh disclosures from both House + Senate APIs (or gracefully notes API unavailability).
- [ ] Output shows only PURCHASES, not sales or other transaction types.
- [ ] Every candidate checked against dedup ledger; none previously recommended are re-proposed.
- [ ] Cluster counts are computed (cross-member buys of same ticker).
- [ ] Output is actionable: ticker, member, chamber, date, dollar-range, WHY, cluster-count.
- [ ] New tickers recorded in ledger after proposal.

## Ledger management

```bash
python3 .agents/skills/congressman-stock-watch/watch.py list        # all recommended so far
python3 .agents/skills/congressman-stock-watch/watch.py list --since 2026-01-01
python3 .agents/skills/congressman-stock-watch/watch.py seen NVDA   # exit 0=seen, exit 1=new
```

Ledger path: `$CONGRESS_LEDGER` or `./congress/recommended.jsonl`

## Schedule recommendation

Run **weekly on Mondays** — new disclosures trickle in daily, so weekly is enough to catch the batch. Set `$CONGRESS_LEDGER` to a persistent path on your deployment so the dedup carries across runs.
