#!/usr/bin/env bun
/**
 * morpho_vault_status.ts — per-held-vault LIFECYCLE / deprecation check for defi-portfolio-manager.
 *
 * WHY: DeBank/DefiLlama grade a position by NAME and TVL, not by the exact on-chain vault the wallet
 * holds. A deprecated / delisted / deposit-disabled Morpho vault still shows a balance on DeBank, and a
 * DefiLlama name-match hands it a healthy *lookalike's* APY — so a wound-down vault earning ~0% reads as
 * a "stable 4.5% core". This is the "deprecated clones silently earn ~0%" trap, realized. This script
 * closes it: for every Morpho v1 + v2 vault the WALLET ACTUALLY HOLDS (keyed by on-chain address, not a
 * name), it pulls the protocol's own truth — `listed`, `warnings`, and the real `netApy` — and flags any
 * position that is delisted, deposit-disabled, not-whitelisted, deprecated, or yielding ~0% as DEAD money
 * to migrate. Run it for each wallet before grading a Morpho-heavy book.
 *
 * Source of truth: Morpho GraphQL `https://api.morpho.org/graphql` (no API key). netApy is a decimal
 * fraction (0.0382 = 3.82%). Holdings come from `userByAddress(address, chainId){ vaultPositions,
 * vaultV2Positions }` so only vaults the wallet holds are checked.
 *
 * Usage:
 *   bun morpho_vault_status.ts <walletAddress> [--chains 1,8453] [--json]
 *   bun morpho_vault_status.ts 0x5D039ECe117073323ADE5057a516864F4c40e653
 *
 * Output (default): one row per held vault — chain · v1/v2 · name · listed · netAPY% · $USD · warnings ·
 * STATUS (DEAD/ok), sorted by USD desc, then a FLAGGED summary ($ and count of dead/0% positions).
 * Exit code 2 if any held vault is flagged (so a caller can gate on it), 1 on a network/API error, else 0.
 */

const ENDPOINT = "https://api.morpho.org/graphql";

// Warnings Morpho raises that mean "this vault is winding down / do not deposit". `invalid_name` is a
// metadata nit and is NOT on its own a deprecation signal, so it is excluded here.
export const DEPRECATION_WARNINGS = new Set([
  "deposit_disabled",
  "not_whitelisted",
  "deprecated",
  "unrecognized_vault",
  "withdraw_only",
]);
// A net APY at/below this (decimal fraction) is treated as effectively dead money.
export const DEAD_APY = 0.0005; // 0.05%

const CHAIN_NAME: Record<number, string> = {
  1: "Ethereum", 8453: "Base", 42161: "Arbitrum", 137: "Polygon",
  10: "Optimism", 130: "Unichain", 81457: "Blast", 100: "Gnosis",
};

export type VaultWarning = { type: string; level?: string | null };
export type VaultInfo = {
  name?: string | null;
  address?: string | null;
  listed?: boolean | null;
  netApy?: number | null; // decimal fraction
  warnings?: VaultWarning[] | null;
};
export type Verdict = { dead: boolean; reasons: string[] };

/**
 * Pure classifier: given a held vault's protocol-truth fields, decide whether it is dead money to
 * migrate, and why. Dead if delisted (listed===false), carrying any deprecation warning, or netApy≈0.
 */
export function classifyVault(v: VaultInfo): Verdict {
  const reasons: string[] = [];
  if (v.listed === false) reasons.push("delisted");
  for (const w of v.warnings ?? []) {
    if (DEPRECATION_WARNINGS.has(w.type)) reasons.push(`warn:${w.type}`);
  }
  const apy = v.netApy ?? 0;
  if (apy <= DEAD_APY) reasons.push(`netApy≈0 (${(apy * 100).toFixed(2)}%)`);
  return { dead: reasons.length > 0, reasons };
}

type Held = {
  chainId: number;
  kind: "v1" | "v2";
  usd: number;
  vault: VaultInfo;
};

async function gql(query: string): Promise<any> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 40_000);
  try {
    const res = await fetch(ENDPOINT, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ query }),
      signal: ctrl.signal,
    });
    const json = await res.json();
    if (json.errors) throw new Error(JSON.stringify(json.errors).slice(0, 400));
    return json.data;
  } finally {
    clearTimeout(t);
  }
}

export async function fetchHeldVaults(address: string, chainId: number): Promise<Held[]> {
  const q = `query{ userByAddress(address:"${address}", chainId:${chainId}){
    vaultPositions{ state{ assetsUsd } vault{ name address listed state{ netApy } warnings{ type level } } }
    vaultV2Positions{ assetsUsd vault{ name address listed netApy warnings{ type level } } }
  } }`;
  const data = await gql(q);
  const u = data?.userByAddress;
  const out: Held[] = [];
  if (!u) return out;
  for (const p of u.vaultPositions ?? []) {
    const v = p.vault ?? {};
    out.push({
      chainId, kind: "v1",
      usd: Number(p.state?.assetsUsd ?? 0) || 0,
      vault: { name: v.name, address: v.address, listed: v.listed, netApy: v.state?.netApy ?? 0, warnings: v.warnings },
    });
  }
  for (const p of u.vaultV2Positions ?? []) {
    const v = p.vault ?? {};
    out.push({
      chainId, kind: "v2",
      usd: Number(p.assetsUsd ?? 0) || 0,
      vault: { name: v.name, address: v.address, listed: v.listed, netApy: v.netApy ?? 0, warnings: v.warnings },
    });
  }
  return out;
}

function fmtRow(h: Held, vd: Verdict): string {
  const chain = CHAIN_NAME[h.chainId] ?? String(h.chainId);
  const name = (h.vault.name ?? "?").slice(0, 26).padEnd(27);
  const listed = String(h.vault.listed).padEnd(5);
  const apy = `${((h.vault.netApy ?? 0) * 100).toFixed(2)}%`.padStart(7);
  const usd = `$${h.usd.toLocaleString("en-US", { maximumFractionDigits: 0 })}`.padStart(11);
  const warns = (h.vault.warnings ?? []).map((w) => w.type).join(",") || "-";
  const status = vd.dead ? `DEAD[${vd.reasons.join(";")}]` : "ok";
  return `${chain.padEnd(9)} ${h.kind} ${name} listed=${listed} ${apy} ${usd}  ${status}  warn=${warns}`;
}

async function main() {
  const argv = process.argv.slice(2);
  const address = argv.find((a) => /^0x[0-9a-fA-F]{40}$/.test(a));
  const asJson = argv.includes("--json");
  const chainsArg = argv[argv.indexOf("--chains") + 1];
  const chains = argv.includes("--chains") && chainsArg
    ? chainsArg.split(",").map((s) => Number(s.trim())).filter(Boolean)
    : [1, 8453]; // Ethereum + Base — where curated Morpho vaults concentrate
  if (!address) {
    console.error("usage: bun morpho_vault_status.ts <0x-wallet> [--chains 1,8453] [--json]");
    process.exit(1);
  }

  let held: Held[] = [];
  try {
    const batches = await Promise.all(chains.map((c) => fetchHeldVaults(address, c)));
    held = batches.flat().filter((h) => h.usd > 0 || h.vault.listed === false);
  } catch (e) {
    console.error(`Morpho API error: ${(e as Error).message}`);
    process.exit(1);
  }

  held.sort((a, b) => b.usd - a.usd);
  const graded = held.map((h) => ({ h, vd: classifyVault(h.vault) }));
  const flagged = graded.filter((g) => g.vd.dead);
  const flaggedUsd = flagged.reduce((s, g) => s + g.h.usd, 0);

  if (asJson) {
    console.log(JSON.stringify({
      address,
      held: graded.map((g) => ({
        chainId: g.h.chainId, chain: CHAIN_NAME[g.h.chainId] ?? String(g.h.chainId),
        kind: g.h.kind, name: g.h.vault.name, vaultAddress: g.h.vault.address,
        listed: g.h.vault.listed, netApyPct: (g.h.vault.netApy ?? 0) * 100, usd: g.h.usd,
        warnings: (g.h.vault.warnings ?? []).map((w) => w.type), dead: g.vd.dead, reasons: g.vd.reasons,
      })),
      flaggedCount: flagged.length, flaggedUsd,
    }, null, 2));
  } else {
    if (graded.length === 0) {
      console.log(`No Morpho vault positions for ${address} on chains ${chains.join(",")}.`);
    } else {
      console.log(`Morpho held-vault lifecycle check — ${address}`);
      for (const g of graded) console.log("  " + fmtRow(g.h, g.vd));
      if (flagged.length) {
        console.log(`\nFLAGGED ${flagged.length} deprecated/0%-APY vault(s) holding ` +
          `$${flaggedUsd.toLocaleString("en-US", { maximumFractionDigits: 0 })} → DEAD money, migrate.`);
      } else {
        console.log(`\nAll held Morpho vaults listed & yielding — no deprecation flags.`);
      }
    }
  }
  process.exit(flagged.length ? 2 : 0);
}

if (import.meta.main) main();
