# Publish drafts — crypto-portfolio-2026-07-24 (corrected)

Prepared 2026-07-27 by the analyse-defi seat. Notion leg already shipped:
https://app.notion.com/p/2026-07-24-fear-aave-buy-3aaac25eb49f8190929ae903415d97ba

The two drafts below are **ready to paste** once auth is restored. Nothing here was posted.

---

## 1. Telegram → @CryptoAiInvestor

**Blocker:** `AuthKeyDuplicatedError` — session file used from two IPs, permanently invalidated.
**Fix:** `python3 ~/.agents/skills/telegram-cli/telegram-cli.py login` (interactive, needs phone code).
**Then:** `python3 ~/.agents/skills/telegram-cli/telegram-cli.py send @CryptoAiInvestor "$(cat <<'EOF' ... EOF)"`

```
📊 Crypto desk — 2026-07-24 (revised 07-27)

Regime: BEARISH. F&G 28 (Fear). BTC $63,922, death cross active, −49% from ATH.

We re-verified every protocol's tokenomics live this week instead of trusting last month's notes. Three things had changed:

🔴 AAVE — buybacks have been OFF since Apr 19, 2026. Governance-confirmed after the Kelp/rsETH bridge exploit; holders revenue is $0 over 30d, and no restart condition has been defined. AAVE is still cheap ($14.7B TVL, 0.10 MC/TVL, GHO $648M) but the token captures none of it today. Downgraded BUY ZONE → ACCUMULATE-WITH-CAVEAT.

🟡 UNI — the "fee switch catalyst" is not pending. It went live Dec 28 and now runs on 11 chains. Realised capture is only 3.49% of fees (v4 contributes zero), ≈1.65% of supply/yr burned. The catalyst already fired and repriced nothing.

🟢 PUMP — accrual is NOT unproven. $14.3M bought back per 30d, printing every single day = 20.6% of market cap per year, the cheapest verified cashflow in the book. Still AVOID, but on cyclicality risk, not on absent accrual.

⚠️ The whole book's revenue is contracting vs trailing-1y: AAVE −61%, AERO −58%, JUP −54%, HYPE −44%, PUMP −26%. Cheap multiples here are falling numerators, not bargains.

Also corrected: LINK spot $8.80 → $8.60 (5 venues), WTI Jul-27 $84.75 → $81.64 (re-verified 2026-07-27; an earlier fix to $83.28 was itself wrong), and AERO's "only 2 weeks of history" (it has 2+ years; 52w range $0.30–$1.49).

Educational only. Not financial advice.
```

---

## 2. X.com

**Blocker:** Chrome reachable but x.com signed out (`LOGGED_OUT`).
**Fix:** sign in to X in the real Chrome profile, then post.

```
Re-verified crypto protocol tokenomics from source today. 3 things had gone stale:

• AAVE buybacks OFF since Apr 19 (gov-confirmed, $0/30d)
• UNI's fee switch isn't pending — live 7 months, realised capture 3.49%
• PUMP buys back 20.6% of mcap/yr, daily

Tokenomics rot fast. Re-fetch, don't remember.
```

(272 chars.)

---

## Verification notes for whoever posts

Every number above traces to a live fetch logged in `research/defi-brief-2026-07-27.md`:

- AAVE pause → `governance.aave.com/t/24686` + DeFiLlama `aave holdersRevenue 30d= 0`
- UNI 3.49% → `gov.uniswap.org/t/26162` + `fees 30d= 93,240,408.55` vs `revenue 30d= 3,255,483`
- PUMP 20.6% → `holdersRevenue 30d= 14,301,309` ÷ mcap `844,686,746` × 12.17
- LINK $8.60 → CoinGecko 8.60 / Coinbase 8.597 / Kraken 8.6051 / OKX 8.611 / CoinPaprika 8.6037
- WTI $81.64 → Yahoo `CL=F` Jul-27 intraday (NOT settled; `regularMarketPrice` 81.64, Jul-24 close 89.31). Brent `BZ=F` $87.50 intraday, Jul-24 close $96.78.
- AERO history → CoinGecko `market_chart` 365 daily points, range $0.3018–$1.4907
