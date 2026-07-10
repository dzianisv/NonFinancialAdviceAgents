---
name: stocks-portfolio
description: >
  Refresh the owner's stock/equity book — brokerage positions (IBKR, Fidelity, Chase,
  Schwab, Vanguard, etc.) and private equity (Carta) — in the "Porfolio" Google Sheet
  (`1aunLbpNGo85WqrMHiIsy6nFUija4Lnjot-rIhE-pGU8`). Use when asked to "refresh my
  brokerage positions", "update the stock book", "sync Carta into the sheet", or to
  fix a broken price/ticker/table on any brokerage or Equity tab. Read-only data
  retrieval from brokers and Carta: NEVER sign, accept, exercise, or transact — quantity
  and cert data only. Crypto/DeFi wallets are OUT OF SCOPE (that's the `crypto-portfolio`
  skill) — COIN (Coinbase Global) is a STOCK, never crypto, even though the name suggests
  otherwise.
license: MIT
compatibility: >
  Needs an authenticated browser session (claude-in-chrome / chrome-use) for the broker
  sites and app.carta.com, and the `gws` CLI (Sheets OAuth scope) for all reads/writes to
  the Google Sheet. No brokerage API keys — everything is a logged-in-session scrape.
metadata:
  author: engineer
  version: "1.0"
---

# stocks-portfolio — refresh the stock + private-equity book

Read-only refresh of the owner's tradfi book in the "Porfolio" Google Sheet: brokerage
positions (quantity only — prices are always live `GOOGLEFINANCE` formulas) and private
equity from Carta (options/RSUs/shares valued from each certificate's own detail page,
never its summary-page rollup).

**Scope boundary:** this skill owns stocks + PE. Crypto/DeFi wallets are the
`crypto-portfolio` skill's job — don't let a "Crypto" typed row on any brokerage tab go
unchallenged (COIN is Coinbase the *company*, a NASDAQ stock; MSTR is a stock that holds
BTC on its balance sheet, still a stock). Grep every tab's Type column for "Crypto" before
trusting a stock-side total.

## Workflow

1. **Baseline capture.** Before touching anything, read the current `Totals` tab (FORMULA
   render) so you have a before/after reconciliation number:
   ```bash
   gws sheets spreadsheets values get --params '{"spreadsheetId":"1aunLbpNGo85WqrMHiIsy6nFUija4Lnjot-rIhE-pGU8","range":"Totals!A1:N17","valueRenderOption":"FORMULA"}'
   ```
2. **Brokerage refresh (per broker).** Open the broker's direct all-positions URL (below)
   via claude-in-chrome/chrome-use using the user's existing logged-in session — do not
   attempt credentials yourself; if a login/2FA prompt appears, stop and report, resume
   via SendMessage once the user confirms login. Capture positions to a scratch CSV
   (Position/Quantity/Type/Cost Basis) — do NOT capture the broker's displayed price,
   value, or P&L, those are sheet-side formulas.
3. **Carta refresh (private equity).** Open
   `https://app.carta.com/investors/individual/968826/portfolio/` via browser. The summary
   page is a *lead*, not ground truth — open every security's own certificate/grant
   **detail** page before valuing it (see Carta validation rules below).
4. **Re-read the exact target range immediately before every write** (FORMULA render) —
   row numbers shift on insert/delete; a stale read has caused a multi-row clobber before.
   Write via `gws sheets spreadsheets batchUpdate` (see gws gotchas below), never
   values.update with A1 notation on these tabs.
5. **Verify-reconcile.** Re-read the row you just wrote plus `Equity!L1`, `Totals!C10`,
   `Totals!C11`. Small drift (tens of dollars) is live `GOOGLEFINANCE` price movement
   between reads, not an error — anything larger, stop and investigate before moving on.

## Tab map (numeric sheetIds — required for all API writes)

| Tab | sheetId | Contents |
|---|---|---|
| Brokerages (ex-"Sumary") | `1914937017` | Unmigrated brokers (Schwab, Vanguard, Treasurydirect, Wealthfront, public.com, Shareworks, Robinhood, Webull) + the "Portfolio" named Table (A1:H156) + Vault (Father/Anton) rows |
| IBKR | `663909619` | IBKR positions, same column schema |
| Chase | `2054525237` | Chase brokerage account `ai=1221630014` |
| Fidelity | `2067628127` | 5 accounts: Brokerage, Trad IRA, Roth, HSA, Cash-Mgmt TOD |
| Banks | `777000111` | Bank cash rows (Технобанк/Revolut/Paysera/CapitalOne/МТБанк) + Vault (Father/Anton) |
| Equity | `1787009395` | Private equity from Carta — Company/Security/Type/Shares/Vested/Strike/FMV/Value/Tax est/Notes |
| DeFi | `97679918` | Owned by `crypto-portfolio` skill, not this one — don't write here |
| Totals | `1920653426` | Asset-class Weight/Position/Value/Monthly-Yield breakdown |

Column schema shared by Brokerages/IBKR/Chase/Fidelity: `Position, Quantity, Type, Cost
Basis, Price (=GOOGLEFINANCE), Value, PnL, FMV`.

**Grand net worth = `Totals!C11`** = SUM of Brokerages + `DeFi!I1` + IBKR + Fidelity +
Chase + Banks + `Equity!L1` (plain ranges, not structured refs). Stable cells that Totals
depends on and that row-edits must never move or break: `Equity!L1` (PE total value,
`Equity!K1` label "PE TOTAL:"), `DeFi!I1` (owned by crypto-portfolio).

## gws / Sheets API gotchas (each one caused a real failure this session)

1. **A1-notation writes fail on these tabs** — `values.update` with a range string throws
   "Unable to parse range". All writes go through
   `gws sheets spreadsheets batchUpdate --params '{"spreadsheetId":"..."}' --json '{...}'`
   using `updateCells` / `repeatCell` requests with a `gridRange` (`{sheetId, startRowIndex,
   endRowIndex, startColumnIndex, endColumnIndex}`, 0-based, half-open). Reads still use
   `gws sheets spreadsheets values get --params '{"spreadsheetId":"...","range":"Equity!A1:J20","valueRenderOption":"FORMULA"}'`.
2. **Structured table refs break on write.** A formula containing `Portfolio[Type]`-style
   structured references written via the API returns an instant `#ERROR!` parse error
   (existing cells with that formula keep working until touched). Rewrite any formula you
   touch with plain ranges instead (e.g. `Brokerages!C2:C156`). `Totals!C8` has already been
   converted this way; `Totals!C4/C5/C9` still carry structured refs — leave them alone,
   don't "fix" them into `#ERROR!` by rewriting.
3. **Orphaned Table objects override cell formats.** A leftover named-Table definition
   enforces its own column type over whatever number/date format you write — writes landed
   as "$1,798.00" for a share count and "1/9/1900" for an FMV because the underlying Table
   object still claimed those columns. A `repeatCell` format fix silently doesn't stick
   until the Table object itself is deleted. **`deleteTable` WIPES the cell contents under
   its footprint** — capture the data first, delete the Table, then rewrite both data and
   formats from your capture.
4. **Row numbers shift on insert/delete.** Re-read the exact target range (FORMULA render)
   immediately before EVERY write, not just once at the start of a session — a stale or
   truncated read caused a 5-row clobber once.
5. `gws` prints `Using keyring backend` to stderr on every call — noise, ignore it.

## Pricing rules

Price column is **always** `=GOOGLEFINANCE(ticker)` — never overwrite it with a
brokerage-displayed price. Brokerage refreshes update **quantity only**; cost basis is a
formula (`=<per-share price>*B<row>`), never a hardcoded dollar total. If a price/value
cell errors or looks wrong (e.g. `BRK-B` → `#N/A`), fix it by testing `GOOGLEFINANCE`
ticker-string variants in a scratch cell (`BRK.B` resolves, `BRK-B` and `NYSE:BRK-B` don't)
— do **not** re-check or re-scrape the brokerage site for "the real price"; quantities come
from brokerages, prices never do.

## Broker refresh — direct all-positions URLs

Skip dashboard click-through; these land straight on the positions view given an
authenticated chrome-use session:

| Broker | URL |
|---|---|
| IBKR | `https://portal.interactivebrokers.com/portal/?loginType=1&action=ACCT_MGMT_MAIN&RL=1&locale=en_US#/dashboard/positions/` |
| Fidelity (all accounts) | `https://digital.fidelity.com/ftgw/digital/portfolio/positions` |
| Chase (brokerage, `ai=1221630014`) | `https://secure.chase.com/web/auth/dashboard#/dashboard/oi-portfolio/positions/render;ai=1221630014` |

Fidelity and Chase do not reliably carry a pre-authenticated session (unlike IBKR) — expect
a manual login/2FA step on first use per session; stop and report rather than guessing
credentials, resume via SendMessage once the user confirms they're logged in.

**Fidelity specifics:** the Treasuries row is an aggregate *formula*, not a position
(T-bills + money-market cash − pending) — don't overwrite it with a scraped number. Cash
rows are typed "Cash" (Cash-Mgmt and Trad-IRA cash rows were previously mistyped "Bonds" —
don't reintroduce that). Recurring-buy tickers (GOOG/ROBO/RSP/VXUS) post weekly and need
quantity bumps on refresh.

## Carta validation (Equity tab) — the discipline this skill exists to encode

Source: `https://app.carta.com/investors/individual/968826/portfolio/`, browser session.
**READ-ONLY: never click sign, accept, exercise, or any transaction action.**

**The summary page lies; the certificate/grant DETAIL page is ground truth.** Open every
security's detail page before valuing it. Real discrepancies found this way:
- CS-223 showed cost **$0.00** on the summary but **$2,355.38** basis / **$1.31**
  price-paid on its detail page.
- A grant-total row on summary didn't sum its own listed components (Point Wild showed
  6,968 total where the components summed to 13,936).
- Summary said **"Canceled"**; the detail page said **"Acquisition, 18,229 vested"**
  (Pango ES-124/188 — unresolved conflict, see Known open items).
- ES-98 was labeled **"ISO"** on summary vs **"NSO – ISO Disqualification"** on detail.

**Canceled/expired = $0, excluded from totals — but check *why* before excluding:**
- **Repricing (issuer-side):** a canceled grant replaced by a new one at a lower strike is
  not a loss — it's the same economic position continued (e.g. ES-130 → ES-897 at $1.31).
  Value the replacement, exclude the canceled original.
- **Reorg/exchange:** a canceled cert in the old entity exactly mirrored by a new cert in
  the successor entity (same count, same date) is a rename, not a loss (e.g. Point Wild
  CS-138 ↔ Aura CS-144, both dated 10/22/2025).
- **Partial issuer buyback:** a cert whose detail page says "created from the repurchase
  of CS-X" means the old cert was canceled and the *remainder* reissued as a new cert
  carrying the ORIGINAL cost basis and acquisition date — this is a partial liquidity
  event, not a new or missing position; don't double-count or flag it as a gap.

**Never fabricate a number.** If a company shows no FMV, leave the FMV cell blank and
exclude that row's value from the total — state the gap in Notes. Don't guess a value to
avoid an empty cell.

**Valuation formulas:**
- Options: `(FMV − strike) × vested`, floored at 0.
- RSUs not yet settled/vesting-eligible: Notes only, value = 0 (not realizable yet).
- Shares: `FMV × quantity`.
- Tax-estimate column: 35% of Value.

**Equity tab schema** (columns A–J): `Company, Security, Type, Shares, Vested, Strike,
FMV, Value, Tax est 35%, Notes`. Totals: `K1 = "PE TOTAL:"` (label), `L1 = =SUM(H2:H100)`.

**Before any rebuild of the Equity tab, duplicate it as a dated backup** (e.g. "Equity
BACKUP YYYY-MM-DD") — this tab gets rewritten more than any other and a bad batchUpdate is
otherwise unrecoverable.

**When Carta itself is inconsistent** (e.g. Pango's Acquisition-vs-Canceled conflict),
record it verbatim in Notes ("flagged, not resolved") — don't silently pick a side.

## Known open items

- **IBKR Type tags unconfirmed:** COIN, CRCL, TONX, GSY, GDX are still typed "Stock" but
  probably aren't all correct — needs the owner's call. (PSLV/PHYS already confirmed as
  "Commodity".)
- **Brokerages tab rows 61–71** (a stale cluster inside the old "Portfolio" Table) are
  pending the owner's call on whether to migrate or delete.
- **Pango ES-124/188:** Carta's own summary ("Canceled") and detail page ("Acquisition,
  18,229 vested") disagree; unresolved with the issuer — do not resolve unilaterally,
  keep the Notes flag until the owner or issuer confirms.
