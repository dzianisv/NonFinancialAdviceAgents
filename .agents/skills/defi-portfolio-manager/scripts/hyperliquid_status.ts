#!/usr/bin/env bun
/**
 * hyperliquid_status.ts — ground-truth a wallet's Hyperliquid book from HL's OWN public API (no key).
 *
 * WHY (same lesson as morpho_vault_status.ts, different blind spot): DeBank/DefiLlama are an aggregator
 * read. For Hyperliquid that misses two things and a real review tripped on both:
 *   1) it can't tell you the HLP/vault equity or that the perp account is empty — only HL's API is
 *      authoritative for those USD figures;
 *   2) it (and the naive fix of "use the protocol's own spot mid") MISPRICES illiquid native dust — HL's
 *      own spot mid quotes MAX/USDC at $6.57, valuing a 1.3M-unit dust bag at $8.65M; the realizable
 *      value is ~$0. A thin last-trade spot mid is NOT a realizable price.
 * So this helper pulls HL's authoritative numbers and prices spot balances ONLY off the canonical
 * oracle HL exposes — the PERP MARK price — never the spot mid. Any spot token with no perp oracle and
 * not a known stable is flagged as illiquid dust valued $0 (the anti-MAX guard), not silently priced.
 *
 * Authoritative for: perp account value (marginSummary.accountValue), open perp positions, and vault
 * deposits incl. HLP (userVaultEquities.equity). HLP is a perp-LP vault — the defi-portfolio-manager
 * skill REJECTS perp-DEX LP ("you're the house"), so held HLP is flagged.
 *
 * Endpoint: POST https://api.hyperliquid.xyz/info  (public, no key).
 *
 * Usage:
 *   bun hyperliquid_status.ts <walletAddress> [--json]
 *   bun hyperliquid_status.ts 0x5D039ECe117073323ADE5057a516864F4c40e653
 *
 * Exit: 2 if anything is flagged (HLP/perp-LP held, or illiquid dust), 1 on API error, else 0.
 */

const ENDPOINT = "https://api.hyperliquid.xyz/info";

// Stable spot tokens priced at $1 (tight allowlist — unknowns must be flagged, not assumed).
export const STABLES = new Set(["USDC", "USDT", "USDT0"]);
// Spot token -> perp coin whose MARK price is its canonical USD oracle. Unit-bridged majors trade on
// HL spot as U<asset>; their value tracks the underlying perp mark.
export const PERP_ALIAS: Record<string, string> = {
  HYPE: "HYPE", USOL: "SOL", UBTC: "BTC", UETH: "ETH", UAVAX: "AVAX", USUI: "SUI", UFART: "FARTCOIN",
};
// Canonical HLP vault(s). HLP = perp liquidity provider — the skill rejects perp-DEX LP.
export const HLP_VAULTS = new Set(["0xdfc24b077bc1425ad1dea75bcb6f8158e10df303"]);

export type SpotValue = { usd: number; basis: string; flagged: boolean };

/**
 * Price one spot balance off the canonical oracle, NEVER the spot mid. Stable -> $1; a token with a
 * perp mark -> amount*mark; otherwise it is illiquid/unoracled dust -> $0 and FLAGGED (the MAX guard).
 */
export function valueSpotToken(
  symbol: string,
  amount: number,
  perpMarks: Record<string, number>,
): SpotValue {
  if (STABLES.has(symbol)) return { usd: amount * 1, basis: "stable=$1", flagged: false };
  const coin = PERP_ALIAS[symbol] ?? (perpMarks[symbol] != null ? symbol : undefined);
  if (coin && perpMarks[coin] != null) {
    return { usd: amount * perpMarks[coin], basis: `perp-mark:${coin}`, flagged: false };
  }
  return { usd: 0, basis: "illiquid/no-perp-oracle", flagged: true };
}

export function isHlpVault(vaultAddress: string | null | undefined): boolean {
  return !!vaultAddress && HLP_VAULTS.has(vaultAddress.toLowerCase());
}

async function info(body: unknown): Promise<any> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 30_000);
  try {
    const res = await fetch(ENDPOINT, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    return await res.json();
  } finally {
    clearTimeout(t);
  }
}

async function perpMarks(): Promise<Record<string, number>> {
  const [meta, ctxs] = await info({ type: "metaAndAssetCtxs" });
  const marks: Record<string, number> = {};
  meta.universe.forEach((a: any, i: number) => {
    const px = Number(ctxs[i]?.oraclePx ?? ctxs[i]?.markPx);
    if (px) marks[a.name] = px;
  });
  return marks;
}

async function main() {
  const argv = process.argv.slice(2);
  const address = argv.find((a) => /^0x[0-9a-fA-F]{40}$/.test(a));
  const asJson = argv.includes("--json");
  if (!address) {
    console.error("usage: bun hyperliquid_status.ts <0x-wallet> [--json]");
    process.exit(1);
  }

  let marks: Record<string, number>, perp: any, spot: any, vaults: any;
  try {
    [marks, perp, spot, vaults] = await Promise.all([
      perpMarks(),
      info({ type: "clearinghouseState", user: address }),
      info({ type: "spotClearinghouseState", user: address }),
      info({ type: "userVaultEquities", user: address }),
    ]);
  } catch (e) {
    console.error(`Hyperliquid API error: ${(e as Error).message}`);
    process.exit(1);
  }

  const perpAcct = Number(perp?.marginSummary?.accountValue ?? 0) || 0;
  const openPerps = (perp?.assetPositions ?? [])
    .map((p: any) => p.position)
    .filter((p: any) => Number(p?.szi ?? 0) !== 0)
    .map((p: any) => ({ coin: p.coin, szi: p.szi, uPnl: Number(p.unrealizedPnl ?? 0), value: Number(p.positionValue ?? 0) }));

  const spotRows = (spot?.balances ?? [])
    .map((b: any) => {
      const amt = Number(b.total ?? 0) || 0;
      const v = valueSpotToken(b.coin, amt, marks);
      return { coin: b.coin, amount: amt, ...v };
    })
    .filter((r: any) => r.amount > 0)
    .sort((a: any, b: any) => b.usd - a.usd);

  const vaultRows = (vaults ?? []).map((v: any) => ({
    vaultAddress: v.vaultAddress, equity: Number(v.equity ?? 0) || 0,
    hlp: isHlpVault(v.vaultAddress),
  }));

  const flaggedSpot = spotRows.filter((r: any) => r.flagged);
  const flaggedVaults = vaultRows.filter((v: any) => v.hlp);
  const anyFlag = flaggedSpot.length > 0 || flaggedVaults.length > 0;

  if (asJson) {
    console.log(JSON.stringify({ address, perpAccountUsd: perpAcct, openPerps, spot: spotRows, vaults: vaultRows, flaggedCount: flaggedSpot.length + flaggedVaults.length }, null, 2));
  } else {
    console.log(`Hyperliquid book — ${address}  (priced off PERP MARKS, not spot mids)`);
    console.log(`  perp account: $${perpAcct.toLocaleString("en-US", { maximumFractionDigits: 2 })}` +
      (openPerps.length ? "" : " (no open positions)"));
    for (const p of openPerps) console.log(`    perp ${p.coin} szi=${p.szi} value=$${p.value.toLocaleString("en-US")} uPnl=$${p.uPnl.toLocaleString("en-US")}`);
    console.log("  spot:");
    for (const r of spotRows) {
      const usd = `$${r.usd.toLocaleString("en-US", { maximumFractionDigits: 2 })}`.padStart(12);
      const flag = r.flagged ? "  DUST/ILLIQUID — verify, not realizable" : "";
      console.log(`    ${String(r.coin).padEnd(8)} ${r.amount.toLocaleString("en-US", { maximumFractionDigits: 4 }).padStart(16)}  ${usd}  [${r.basis}]${flag}`);
    }
    console.log("  vaults:");
    for (const v of vaultRows) {
      console.log(`    ${v.vaultAddress}  equity=$${v.equity.toLocaleString("en-US", { maximumFractionDigits: 2 })}` +
        (v.hlp ? "  HLP perp-LP — skill REJECT (you're the house)" : ""));
    }
    const realizableSpot = spotRows.filter((r: any) => !r.flagged).reduce((s: number, r: any) => s + r.usd, 0);
    console.log(`\n  realizable spot ≈ $${realizableSpot.toLocaleString("en-US", { maximumFractionDigits: 0 })} ` +
      `(excludes ${flaggedSpot.length} dust token(s)); perp $${perpAcct.toLocaleString("en-US", { maximumFractionDigits: 0 })}; ` +
      `vault equity $${vaultRows.reduce((s: number, v: any) => s + v.equity, 0).toLocaleString("en-US", { maximumFractionDigits: 0 })}`);
    if (anyFlag) console.log(`  FLAGGED: ${flaggedSpot.map((r: any) => r.coin).join(", ") || "—"} dust; ${flaggedVaults.length} HLP perp-LP vault(s).`);
  }
  process.exit(anyFlag ? 2 : 0);
}

if (import.meta.main) main();
