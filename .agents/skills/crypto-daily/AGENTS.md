# crypto-daily — Agent Contract

This file is read automatically by any agent that edits this skill.
Read it fully before changing SKILL.md.

---

## What this skill does

Publishes the daily crypto-advisor run to three channels:
1. **Notion** — full analyst report (Block 1 + Block 2 with researcher recaps + Block 3 sources)
2. **Telegram** (@CryptoAiInvestor) — per-token recap with 5 researcher lines each
3. **X.com** — ≤280 char tweet summary

---

## Telegram format contract — DO NOT simplify without explicit user approval

The Telegram output is the primary user-facing product. The format was deliberately designed after several regressions. **Do not collapse, shorten, or remove researcher lines.**

### Per-token block (mandatory, all 5 lines always present)

```
{SIGNAL_EMOJI} {TICKER} ${PRICE} — {SIGNAL}
  📈 Technical:   {1 sentence — key chart indicator (plain explanation in parens)}
  ⛓ On-Chain:    {1 sentence — on-chain metric (plain explanation in parens)}
  🏛 DeFi:        {1 sentence — protocol revenue/TVL (plain explanation in parens); or "n/a — base layer asset"}
  🌍 Macro:       {1 sentence — macro driver (plain explanation in parens)}
  🐋 Smart Money: {1 sentence — exchange flows/whale activity (plain explanation in parens)}
```

### Signal emoji rules (hard)

| Signal | Emoji | Notes |
|---|---|---|
| BUY / BUY(small) | 🟢 | |
| HOLD / WATCH / gov-downgraded | 🟡 | **Never use 🔴 for HOLD** |
| SELL | 🔴 | Red is SELL only |

### Language rules (hard)

- **Keep technical terms** (RSI, death cross, MACD, EMA, TVL, etc.) — do not rename them
- **Every jargon term must be followed by a plain-English explanation in `()`** — write for someone who doesn't know crypto
- **No internal code words** in Telegram output: `DEEP_VALUE`, `FAIR_VALUE`, `BULLISH`, `BEARISH`, `UNCERTAIN`, `seats_bull`, `quorum_verdict`, etc. — translate to plain English
- Use concrete numbers ($, %, timeframes) over adjectives

### Multi-part message split

11 tokens × 5 researcher lines exceeds 4096 bytes. Split order:
- **Part 1**: header + BUY/BUY(small) active tokens (highest conviction first)
- **Part 2**: HOLD gov-cap tokens (downgraded BUYs)
- **Part 3**: remaining HOLDs + group summary + governor note + Notion link + disclaimer

Each part must be ≤ 4096 bytes. Verify: `echo -n "$PART" | wc -c`

---

## Notion format contract

The Notion page is the full report. It must include:
1. Signal table (all 11 tokens, one row each)
2. Block 2 per token: verdict narrative + Research Desk recap (5 researcher lines) + panel votes (5 investor lines) + bull/bear cases
3. Block 3: all research sources with T1/T2/T3 ranking

---

## Key design decisions (do not revert)

| Decision | Reason |
|---|---|
| 5 researcher lines per token in Telegram | Users need to see WHY, not just the signal. A bare "HOLD BTC" with no reasoning is useless. |
| 🟡 for HOLD | Red signals danger/sell. HOLD is neutral. Yellow avoids false alarm. |
| Jargon + `(plain explanation)` | Keeps the precision of the technical term while making it accessible. Fully plain English loses credibility; fully jargon loses audience. |
| Multi-part messages | Telegram 4096-byte limit. BUY tokens sent first because readers act on those. |
| Researcher names kept (Technical/On-Chain/DeFi/Macro/Smart Money) | These map to the 5 Research Desk agents. Renaming them (e.g. to "Chart"/"Flows") breaks the correspondence and confuses readers who look up the full Notion report. |
| Notion link at end of final message only | One URL, one place. Prevents link spam. |

---

## Regression history (do not repeat)

- **2026-06-28**: `b1cd3e9` refactor decoupled Research Desk from output. Investment Panel votes appeared in Block 2 but researcher briefs were silently dropped. Telegram had zero reasoning. Fixed in `3bf7760` + `bd26185`.
- **Single-message rule** was removed because 11 tokens × 5 researcher lines cannot fit in 4096 bytes. Do not reinstate it.
- Researcher line labels were briefly renamed to "Chart/Value/Protocol/Market/Flows" — reverted. Keep original names.

---

## Files owned by this skill

| Path | Purpose |
|---|---|
| `.agents/skills/crypto-daily/SKILL.md` | Agent instructions |
| `.cache/crypto-daily/notion.yaml` | Notion target page (runtime config, never hardcode) |
| `.cache/crypto-daily/portfolio.csv` | Optional token universe override |
