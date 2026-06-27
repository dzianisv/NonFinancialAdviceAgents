#!/usr/bin/env bun
/**
 * boundary_pnl.ts — Wallet-boundary PnL accounting on yield_trace normalized ledger.
 * Usage: bun boundary_pnl.ts <ledger.json> [--window 1y] [--out file]
 */

import {
  CHAIN_CONFIG as _CHAIN_CONFIG,
  ethCall,
  pad32,
  llamaBlock,
  llamaPriceHistorical,
  SEL_BALANCEOF,
  SEL_TOTAL_ASSETS,
  SEL_TOTAL_SUPPLY,
  SEL_CONVERT_ASSETS,
  SEL_PRICE_PER_SHARE,
} from "./yield_trace.ts";

// Additional selectors not in yield_trace (Curve stable LP and Aave aToken)
const SEL_VIRTUAL_PRICE = "0xbb7b8b80"; // Curve/Aero/Velo: get_virtual_price()
const SEL_AAVE_UNDERLYING = "0xb16a19c1"; // Aave V3: UNDERLYING_ASSET_ADDRESS()

/** Known stable token addresses for Aave aToken underlying detection. */
const KNOWN_STABLE_ADDRS: Set<string> = new Set([
  // USDC
  "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913", // Base
  "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", // Ethereum
  "0xaf88d065e77c8cc2239327c5edb3a432268e5831", // Arbitrum
  "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8", // Arbitrum USDC.e
  // USDT
  "0xdac17f958d2ee523a2206206994597c13d831ec7", // Ethereum
  "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9", // Arbitrum
  // DAI
  "0x6b175474e89094c44da98b954eedeac495271d0f", // Ethereum
  "0x50c5725949a6f0c72e6c4a641f24049a917db0cb", // Base
  // USDbC (bridged USDC on Base)
  "0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca",
  // USDe (Ethena)
  "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34", // Arbitrum
  "0x4c9edd5852cd905f086c759e8383e09bff1e68b3", // Ethereum
  // EUSD (Reserve, Base)
  "0xcfa3ef56d303ae4faaba0592388f19d7c3399fb4",
].map((a) => a.toLowerCase()));
import type { LedgerRow } from "./yield_trace.ts";

// Override CHAIN_CONFIG with multiple verified-working endpoints per chain.
// base-rpc.publicnode.com is REMOVED: it consistently returns malformed JSON ("Failed to
// parse JSON" ×1765 in one cluster run), and being first it wasted retries and starved the
// working endpoints under the cluster's concurrency — silently zeroing identified ERC-4626
// vault valuations (e.g. avUSDC) and swinging the "hard-measured" anchor by ~$1k.
// Endpoints below were each verified live serving eth_call/convertToAssets (2026-06-27).
const CHAIN_CONFIG = {
  ..._CHAIN_CONFIG,
  base: {
    ..._CHAIN_CONFIG.base,
    rpcs: [
      "https://mainnet.base.org",
      "https://base-mainnet.public.blastapi.io",
      "https://base.gateway.tenderly.co",
      "https://base-pokt.nodies.app",
    ],
  },
  ethereum: {
    ..._CHAIN_CONFIG.ethereum,
    rpcs: [
      "https://ethereum-rpc.publicnode.com",
      "https://ethereum.publicnode.com",
      "https://eth.drpc.org",
    ],
  },
  arbitrum: {
    ..._CHAIN_CONFIG.arbitrum,
    rpcs: [
      "https://arb1.arbitrum.io/rpc",
      "https://arbitrum-one-rpc.publicnode.com",
      "https://arbitrum.drpc.org",
    ],
  },
  optimism: {
    ..._CHAIN_CONFIG.optimism,
    rpcs: [
      "https://mainnet.optimism.io",
      "https://optimism-rpc.publicnode.com",
      "https://optimism.drpc.org",
    ],
  },
};

// ── Constants ─────────────────────────────────────────────────────────────────

export const OWNED_WALLETS: Set<string> = new Set([
  "0x5c1b7a3ab7797e237cc9ec1e30a18048c364174a",
  "0x5d039ece117073323ade5057a516864f4c40e653",
  "0x9945ba0a781200b90b4c28528cced309abb90871",
  "0xd6b5587944a2bf537ef9cf04695ed093f4805e75",
  "0xaefdc2b58f5a15b6e5e3d6d7ac707c76967ab4ae",
].map((a) => a.toLowerCase()));

export const EXTERNAL_CEX = "0x10fc069bd3cd4a0734139b292fa64d76f98fd25b";

export const KNOWN_BRIDGES: Set<string> = new Set([
  "0x2df1c51e09aecf9cacb7bc98cb1742757f163df7",
  "0xf7e96217347667064dee8f20db747b1c7df45dde",
  "0x9e36cb86a159d479ced94fa05036f235ac40e1d5",
].map((a) => a.toLowerCase()));

export const BRIDGE_NAME_REGEX =
  /bridge|metarouter|stargate|across\b|hop|cctp|synapse|celer|debridge|wormhole|hyperliquid|socket|squid/i;

export const SPAM_REGEX =
  /https?:|t\.me|\.xyz|\.com|claim|redeem|reward|airdrop|visit|[Ѐ-ӿ]|\$[A-Z]+ -/i;

export const DIRECTIONAL_TOKENS: Set<string> = new Set([
  "stETH", "wstETH", "cbETH", "WETH", "ETH",
]);

export const DIRECTIONAL_ADDRS: Set<string> = new Set([
  "0xae7ab96520de3a18e5e111b5eaab095312d7fe84",
  "0xbe9895146f7af43049ca1c1ae358b0541ea49704",
].map((a) => a.toLowerCase()));

// ZkLighter on-chain perps/derivatives exchange (net +$2,220 in cluster; excluded from DeFi yield).
// 0x244ecc = deposit proxy on Base; 0x3b4d79 = settlement proxy on Ethereum (confirmed via Blockscout).
export const ZKLIGHTER_ADDRS: Set<string> = new Set([
  "0x244ecc908cbb13bf2d033bdcfe7a804b495aa128", // ZkLighter deposit proxy (Base)
  "0x3b4d794a66304f130a4db8f2551b0070dfcf5ca7", // ZkLighter settlement proxy (Ethereum, Blockscout-confirmed)
].map((a) => a.toLowerCase()));

// Cross-chain bridge / routing addresses (capital movements, not yield; excluded from DeFi yield).
// LiFiDiamond = confirmed well-known address; others identified by counterparty pattern + chain.
export const MISC_BRIDGE_ADDRS: Set<string> = new Set([
  "0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae", // LiFiDiamond (confirmed)
  "0x89c6340b1a1f4b25d36cd8b063d49045caf3f818", // Permit2Proxy paired with LiFiDiamond in same tx
  "0xce8cca271ebc0533920c83d39f417ed6a0abb7d0", // WooCrossChainRouterV2 (Optimism)
  "0x5961f116f5aa784bd9dcfa55d3e8203dddb82bc4", // Stargate Pool USDC (Arbitrum, likely)
].map((a) => a.toLowerCase()));

// Unverified contract — 4byte selector unknown, deployer is plain EOA, no name on Blockscout.
// Cannot positively tie to stablecoin/LP yield source → excluded from DeFi yield headline.
export const UNIDENTIFIED_MISC_ADDRS: Set<string> = new Set([
  "0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43", // Ethereum unverified contract (selector 0xca350aa6 = no 4byte match)
].map((a) => a.toLowerCase()));

// EOA addresses that the ledger builder incorrectly tagged counterpartyIsContract=true.
// Skipping them in computeMiscFlows prevents them from leaking into the protocol yield bucket.
export const KNOWN_EOAS: Set<string> = new Set([
  "0xbb968a2c8855226389893d0b00c1f4b3f77bf0bb", // Base EOA, ledger has counterpartyIsContract=true (bug)
].map((a) => a.toLowerCase()));

// Named Misc protocol addresses — each gets its own ProtocolRow with individual windowBasis.
// This makes per-address window correction (TASK 2) visible and verifiable in the output table.
//
//  CLPool   0x988702 — LP deposit/withdraw cycle; ~-$1 window after basis correction
//  CLPoolFees 0x27a16dc — fee distributions; all in-window; real DeFi yield ~+$2,253
//  AlgebraPool 0xa17afcab — Algebra V2 pool; ~+$12.90 window after basis correction
//  WooPPV2  0xed9e — WooFi pool yield; all in-window; real DeFi yield ~+$5,151
//  LPExit   0xd5d1f85e — LP exit capital return; ~$0 window after basis correction
export const NAMED_MISC_PROTOS: Map<string, string> = new Map(
  ([
    ["0x988702fe529a3461ec7fd09eea3f962856709fd9", "CLPool"],
    ["0x27a16dc786820b16e5c9028b75b99f6f604b5d26", "CLPoolFees"],
    ["0xa17afcab059f3c6751f5b64347b5a503c3291868", "AlgebraPool"],
    ["0xed9e3f98bbed560e66b89aac922e29d4596a9642", "WooPPV2"],
    ["0xd5d1f85e65ce58a4782852f4a845b1d6ca71f1a2", "LPExit"],
  ] as [string, string][]).map(([k, v]) => [k.toLowerCase(), v]),
);

export const CURRENT_VALUES = {
  idle_usdc_base: 44637.08,
  stable_vault: 28727.99,
  // directional: not computed per-wallet — requires ETH price feed + per-wallet RPC balance.
  // Was hardcoded to L3's stETH/cbETH value ($2,427.93), which leaked into every other wallet.
  directional: 0,
  total: 75793.00,
};

export const WINDOW_1Y_TS = 1750896000;

/** Deterministic "now" for apportionment — hardcoded 2026-06-26. Never use Date.now(). */
export const NOW = 1782432000;

/**
 * computeApportionFraction — pure, time-based linear accrual model.
 * Returns the fraction of a position's lifetime PnL attributable to the trailing window.
 * NOTE: apportioned 1Y PnL is a LINEAR-ACCRUAL MODEL estimate; lifetime PnL is hard-measured.
 */
export function computeApportionFraction(
  firstEntryTs: number,
  endTs: number,
  windowStart: number,
  _now: number,
): number {
  const totalHold = Math.max(1, endTs - firstEntryTs);
  const inWindowOverlap = Math.max(0, endTs - Math.max(firstEntryTs, windowStart));
  return Math.min(1, inWindowOverlap / totalHold);
}

// EUSD (Reserve eUSD, Base, USD-pegged ~$1) is NOT flagged isStable by the ledger builder
// but is economically a stablecoin. Treat it as stable for all PnL accounting.
export const EUSD_ADDR = "0xcfa3ef56d303ae4faaba0592388f19d7c3399fb4";
export const STABLE_OVERRIDE_ADDRS: Set<string> = new Set([EUSD_ADDR]);
export function isStableRow(r: LedgerRow): boolean {
  return r.isStable || (r.tokenAddr != null && STABLE_OVERRIDE_ADDRS.has(r.tokenAddr.toLowerCase()));
}

// ── Types ─────────────────────────────────────────────────────────────────────

export type CounterpartyClass =
  | "owned"
  | "bridge"
  | "external_cex"
  | "external_eoa"
  | "internal";

export interface ProtocolRow {
  protocol: string;
  /** present only in per-LP cluster mode: the owning wallet this row is attributed to */
  wallet?: string;
  costIn: number;
  proceedsOut: number;
  curVal: number;
  lifePnL: number;
  /** headline: time-apportioned linear-accrual model estimate */
  pnl1y: number;
  /** upper bound: face-value window-start basis (pre-apportionment) */
  pnl1y_facebasis: number;
  flags: string;
  windowCostIn: number;
  windowProceedsOut: number;
  windowBasis: number;
}

export interface BoundaryOutput {
  anchor: number;
  delta_vs_anchor: number;
  protocols: ProtocolRow[];
  trailing_1y: {
    window_start_value: number;
    /** headline: sum of time-apportioned pnl1y across protocols */
    pnl_1y: number;
    /** upper bound: sum of face-value pnl1y_facebasis across protocols */
    pnl_1y_facebasis: number;
    pnl_1y_anchor: number;
    /** conservation check: face-basis attribution vs independent anchor */
    delta_1y: number;
  };
  idle_rpc: number;
  idle_flow: number;
  /** present only in cluster mode: addresses of all wallets merged */
  cluster_wallets?: string[];
}

export type BalanceProvider = (
  rpcs: string[],
  tokenAddr: string,
  walletAddr: string,
  blockHex: string,
) => Promise<bigint>;

export interface BoundaryPnLOpts {
  /** Optional balance provider. Defaults to live RPC with exponential-backoff retry. */
  balanceProvider?: BalanceProvider;
  /**
   * Override the nowBlockMap (used for block-at-time RPC calls).
   * When provided, skips llamaBlock() calls to DefiLlama. Pass any non-null block value
   * per chain to make all RPC calls offline (stubs ignore the blockHex argument).
   */
  nowBlockMap?: Map<string, string | null>;
  /**
   * Optional probe used ONLY by the vault-RPC sanity guard to classify a $0-valued position.
   * Defaults to a live fetch-based ERC-4626 redemption probe; tests inject it for determinism.
   */
  ethReachProbe?: EthReachProbe;
}

/**
 * Independently re-reads a held token for the vault guard (own balanceOf + ERC-4626 redemption):
 *  - reachable: did the chain authoritatively answer balanceOf (a `result`/`0x`, or an
 *    execution-revert)? false only on transport failure / node-availability error → can't read.
 *  - heldRaw: wallet's current balance (raw), or null if unreachable. 0n → not held / exited.
 *  - redeemPerShare: assets per 1 share from convertToAssets when it parses to a sane stable
 *    band [0.5, 2.0]; null if it reverted (→ not an ERC-4626 stable vault) or wasn't queried.
 * The guard throws only when a token is held with > $1 of redeemable value yet the main pass
 * valued it $0, or when a deployed position is unreachable — never on exited (heldRaw 0) or
 * held-but-non-redeemable (LINEA/PAXG) tokens.
 */
export type EthReachProbe = (
  rpcs: string[], tokenAddr: string, walletAddr: string, decimals: number,
) => Promise<{ reachable: boolean; heldRaw: bigint | null; redeemPerShare: number | null }>;

// ── Pure helpers ──────────────────────────────────────────────────────────────

/**
 * classifyCounterparty — pure, no network.
 * Rules (first match wins):
 *   1. addr in ownedSet → "owned"
 *   2. addr in KNOWN_BRIDGES → "bridge"
 *   3. blockscoutCache.get(addr) name matches BRIDGE_NAME_REGEX → "bridge"
 *   4. same-tx-no-return: stable goes OUT to addr and no non-stable receipt token returns
 *      in the same txHash → "bridge" (covers cross-chain bridges & external withdrawals)
 *   5. counterpartyIsContract=true → "internal"
 *   6. counterpartyIsContract=false → "external_eoa" (data-driven; covers CEX + external EOAs)
 *   default: "internal"
 *
 * NOTE: EXTERNAL_CEX is no longer hardcoded here — external-EOA classification is driven
 * by the ledger's counterpartyIsContract field, so the function generalises across wallets.
 */
export function classifyCounterparty(
  addr: string,
  ownedSet: Set<string>,
  txRows: LedgerRow[],
  blockscoutCache: Map<string, string>,
): CounterpartyClass {
  const a = addr.toLowerCase();
  if (ownedSet.has(a)) return "owned";
  if (KNOWN_BRIDGES.has(a)) return "bridge";
  const name = blockscoutCache.get(a);
  if (name && BRIDGE_NAME_REGEX.test(name)) return "bridge";
  // Same-tx-no-return: stable goes OUT to this address and no non-stable, non-spam receipt
  // token returns in the same tx → bridge / external withdrawal (cross-chain or CEX-like).
  const addrRows = txRows.filter((r) => r.counterparty === a);
  if (addrRows.some((r) => isStableRow(r) && r.direction === "out" && (r.amountFloat ?? 0) > 0)) {
    const anyReceiptIn = txRows.some(
      (r) =>
        r.direction === "in" &&
        !isStableRow(r) &&
        !SPAM_REGEX.test(r.symbol) &&
        (r.amountFloat ?? 0) > 0,
    );
    if (!anyReceiptIn) return "bridge";
  }
  // Data-driven: classify by counterpartyIsContract field from the ledger row.
  if (addrRows.length > 0) {
    const isContract = addrRows[0].counterpartyIsContract;
    if (isContract === true) return "internal";
    if (isContract === false) return "external_eoa";
  }
  return "internal";
}

/**
 * detectProtocol — pure, no network.
 * Maps a receipt token symbol (and optional counterparty name) to a protocol name.
 */
export function detectProtocol(symbol: string, counterpartyName?: string): string {
  const s = symbol.toLowerCase();
  const n = (counterpartyName ?? "").toLowerCase();
  if (s === "meusd") return "Morpho";  // MEUSD is a Morpho vault receipt token
  if (s.includes("exm") || n.includes("extrafi") || n.includes("extra")) return "ExtraFi";
  if (s.includes("syrup") || n.includes("maple")) return "Maple";
  if (s === "susde" || s.startsWith("susde")) return "Ethena";
  if (s === "smusdc" || s.includes("morpho") || n.includes("morpho")) return "Morpho";
  if (s.startsWith("moo")) return "Beefy";
  if (s.includes("pendle") || s.startsWith("pt-")) return "Pendle";
  if (s.includes("aero") || s.includes("crv") || s.includes("curve")) return "CurveAero";
  const dirL = new Set(["steth", "wsteth", "cbeth", "weth", "eth"]);
  if (dirL.has(s)) return "Directional";
  return "Other";
}

// ── Misc (standalone) flow capture ────────────────────────────────────────────

/** Per-category stable-flow totals for a Misc sub-bucket. */
interface MiscFlowBucket {
  costIn: number;
  proceedsOut: number;
  windowCostIn: number;
  windowProceedsOut: number;
}
function emptyBucket(): MiscFlowBucket {
  return { costIn: 0, proceedsOut: 0, windowCostIn: 0, windowProceedsOut: 0 };
}

/**
 * Compute stable flows in transactions that have NO non-stable, non-spam receipt
 * token AND whose counterparty is not a known capital source (CEX/owned/bridge).
 *
 * Returns total flows plus four sub-buckets for reclassification:
 *   perps       — ZkLighter on-chain perps/trading (excluded from DeFi yield headline)
 *   bridge      — LiFiDiamond / Stargate / WooCrossChainRouterV2 (capital movements)
 *   unidentified — 0xa9d1e0 (unverified contract, cannot be positively tied to yield)
 *   regular     — remaining DeFi protocol flows (CLPool fees, WooPP, AlgebraPool, etc.)
 *
 * These flows represent protocol interactions (stable swaps, partial liquidations,
 * yield distributions) where no receipt token co-occurred in the same txHash.
 * They must be included for the per-protocol sum to conserve with the anchor.
 */
export function computeMiscFlows(rows: LedgerRow[]): {
  costIn: number;
  proceedsOut: number;
  windowCostIn: number;
  windowProceedsOut: number;
  perps: MiscFlowBucket;
  bridge: MiscFlowBucket;
  unidentified: MiscFlowBucket;
  regular: MiscFlowBucket;
  /** Named protocol sub-buckets keyed by protocol name from NAMED_MISC_PROTOS. */
  named: Map<string, MiscFlowBucket>;
} {
  const byTx = new Map<string, LedgerRow[]>();
  for (const row of rows) {
    const h = row.txHash;
    if (!byTx.has(h)) byTx.set(h, []);
    byTx.get(h)!.push(row);
  }

  let costIn = 0, proceedsOut = 0, windowCostIn = 0, windowProceedsOut = 0;
  const perps = emptyBucket();
  const bridge = emptyBucket();
  const unidentified = emptyBucket();
  const regular = emptyBucket();
  // Pre-initialise one bucket per unique named protocol name so the caller can iterate.
  const named = new Map<string, MiscFlowBucket>();
  for (const protoName of new Set(NAMED_MISC_PROTOS.values())) {
    named.set(protoName, emptyBucket());
  }

  for (const [, txRows] of byTx) {
    // Only process txs WITHOUT a non-stable, non-spam, non-directional receipt token
    const hasReceipt = txRows.some(
      (r) =>
        !isStableRow(r) &&
        !SPAM_REGEX.test(r.symbol) &&
        r.amountFloat > 0 &&
        detectProtocol(r.symbol) !== "Directional",
    );
    if (hasReceipt) continue;

    const txTs = txRows[0]?.ts ?? 0;
    const inWindow = txTs >= WINDOW_1Y_TS;

    for (const r of txRows) {
      if (!isStableRow(r)) continue;
      const cp = r.counterparty.toLowerCase();
      // Skip capital flows — already captured in anchor formula.
      // Data-driven: external EOAs (counterpartyIsContract === false) are capital flows;
      // only stable flows to contracts (protocols) belong in Misc.
      if (OWNED_WALLETS.has(cp) || KNOWN_BRIDGES.has(cp) || r.counterpartyIsContract === false) continue;
      // Skip EOAs misclassified as contracts in the ledger builder.
      if (KNOWN_EOAS.has(cp)) continue;

      const usd = r.usd ?? 0;
      const isOut = r.direction === "out";

      // Grand total (used for conservation invariant)
      if (isOut) { costIn += usd; if (inWindow) windowCostIn += usd; }
      else { proceedsOut += usd; if (inWindow) windowProceedsOut += usd; }

      // Sub-bucket classification (first match wins)
      const _namedProto = NAMED_MISC_PROTOS.get(cp);
      const bucket: MiscFlowBucket =
        ZKLIGHTER_ADDRS.has(cp) ? perps :
        MISC_BRIDGE_ADDRS.has(cp) ? bridge :
        UNIDENTIFIED_MISC_ADDRS.has(cp) ? unidentified :
        _namedProto ? named.get(_namedProto)! :
        regular;

      if (isOut) {
        bucket.costIn += usd;
        if (inWindow) bucket.windowCostIn += usd;
      } else {
        bucket.proceedsOut += usd;
        if (inWindow) bucket.windowProceedsOut += usd;
      }
    }
  }

  return { costIn, proceedsOut, windowCostIn, windowProceedsOut, perps, bridge, unidentified, regular, named };
}

// ── Note: EXTERNAL_CEX is kept as an exported constant for documentation / test use,
// but is no longer used in computation — classification is data-driven via counterpartyIsContract.

// ── Misc window-basis and row builder ─────────────────────────────────────────

/**
 * Compute windowBasis for a Misc-style bucket (no receipt tokens, curVal always 0).
 *
 * Applies the same pre-window capital-return correction used for named receipt-token
 * protocols: any pre-window net investment (costIn > proceedsOut before window start)
 * must be subtracted from in-window proceeds before reporting as window yield.
 *
 * Conservation note: including this windowBasis in the ProtocolRow causes sumWindowBasis
 * to increase by the same amount that pnl1y_facebasis decreases, so delta_1y is unchanged.
 * This is identical to the named-protocol case and preserves the 1Y conservation invariant.
 */
function calcMiscWindowBasis(m: MiscFlowBucket): number {
  const preWinCostIn = m.costIn - m.windowCostIn;
  const preWinProceeds = m.proceedsOut - m.windowProceedsOut;
  const contributesToWindow = m.windowCostIn > 0.01 || m.windowProceedsOut > 0.01;
  return contributesToWindow ? Math.max(0, preWinCostIn - preWinProceeds) : 0;
}

/** Build a ProtocolRow for one Misc sub-bucket with correct windowBasis applied. */
function buildMiscRow(
  protocol: string,
  m: MiscFlowBucket,
  flags: string,
): ProtocolRow {
  const lifePnL = m.proceedsOut - m.costIn;
  const wBasis = calcMiscWindowBasis(m);
  const pnl = m.windowProceedsOut - m.windowCostIn - wBasis;
  return {
    protocol,
    costIn: m.costIn,
    proceedsOut: m.proceedsOut,
    curVal: 0,
    lifePnL,
    pnl1y: pnl,
    pnl1y_facebasis: pnl,
    flags,
    windowCostIn: m.windowCostIn,
    windowProceedsOut: m.windowProceedsOut,
    windowBasis: wBasis,
  };
}

// ── Capital flow accounting (computed from ledger) ────────────────────────────

export interface CapitalFlows {
  cexIn: number;
  ownedIn: number;
  ownedOut: number;
  bridgeOut: number;
  capitalIn: number;
  capitalOut: number;
  wCexIn: number;
  wOwnedIn: number;
  wOwnedOut: number;
  wBridgeOut: number;
  wCapitalIn: number;
  wCapitalOut: number;
}

/**
 * computeCapitalFlows — pure, ledger-derived.
 * Walks all isStableRow rows and classifies by counterparty into CEX, owned, bridge flows.
 * windowTs: unix timestamp marking the start of the 1Y window.
 */
export function computeCapitalFlows(rows: LedgerRow[], windowTs: number): CapitalFlows {
  let cexIn = 0, ownedIn = 0, ownedOut = 0, bridgeOut = 0;
  let wCexIn = 0, wOwnedIn = 0, wOwnedOut = 0, wBridgeOut = 0;

  for (const r of rows) {
    if (!isStableRow(r)) continue;
    const cp = r.counterparty.toLowerCase();
    const usd = r.usd ?? 0;
    const inW = r.ts >= windowTs;

    if (r.direction === "in") {
      // Owned-wallet inflows first (owned wallets can be EOAs, so must check before EOA branch)
      if (OWNED_WALLETS.has(cp)) { ownedIn += usd; if (inW) wOwnedIn += usd; }
      // Data-driven external-EOA detection: not owned + not a contract → external capital in
      else if (r.counterpartyIsContract === false) { cexIn += usd; if (inW) wCexIn += usd; }
    } else {
      if (OWNED_WALLETS.has(cp)) { ownedOut += usd; if (inW) wOwnedOut += usd; }
      else if (KNOWN_BRIDGES.has(cp)) { bridgeOut += usd; if (inW) wBridgeOut += usd; }
    }
  }

  const capitalIn = cexIn + ownedIn;
  const capitalOut = ownedOut + bridgeOut;
  const wCapitalIn = wCexIn + wOwnedIn;
  const wCapitalOut = wOwnedOut + wBridgeOut;

  return { cexIn, ownedIn, ownedOut, bridgeOut, capitalIn, capitalOut, wCexIn, wOwnedIn, wOwnedOut, wBridgeOut, wCapitalIn, wCapitalOut };
}

/**
 * computeClusterCapitalFlows — cluster (multi-wallet) mode.
 *
 * Inter-wallet flows (between any two owned wallets) are INTERNAL → both sides cancelled.
 * External-EOA outflows count as capital-out, fixing the per-wallet silent-drop bug where
 * stable outflows to non-bridge, non-owned EOAs were missing from the anchor formula.
 *
 * Per-wallet bug root cause: computeCapitalFlows only counts ownedOut + bridgeOut as
 * capital-out. Stable flows to external EOAs (e.g. CEX withdrawals) were silently dropped,
 * leaving the anchor too low by exactly the external-out amount.
 */
export function computeClusterCapitalFlows(
  rows: LedgerRow[],
  windowTs: number,
  ownedSet: Set<string>,
): CapitalFlows {
  let cexIn = 0, ownedIn = 0, ownedOut = 0, bridgeOut = 0;
  let wCexIn = 0, wOwnedIn = 0, wOwnedOut = 0, wBridgeOut = 0;

  for (const r of rows) {
    if (!isStableRow(r)) continue;
    const cp = r.counterparty.toLowerCase();
    const usd = r.usd ?? 0;
    const inW = r.ts >= windowTs;

    if (r.direction === "in") {
      if (ownedSet.has(cp)) {
        // Inter-wallet transfer: internal, skip (cancel with mirror row from the other ledger)
      } else if (r.counterpartyIsContract === false) {
        // External EOA inflow: genuine capital entering the cluster
        cexIn += usd; if (inW) wCexIn += usd;
      }
    } else { // out
      if (ownedSet.has(cp)) {
        // Inter-wallet transfer: internal, skip
      } else if (KNOWN_BRIDGES.has(cp)) {
        bridgeOut += usd; if (inW) wBridgeOut += usd;
      } else if (r.counterpartyIsContract === false) {
        // External EOA outflow: capital leaving the cluster boundary.
        // Counted in bridgeOut bucket (capital-out) — absent in per-wallet mode.
        bridgeOut += usd; if (inW) wBridgeOut += usd;
      }
    }
  }

  const capitalIn = cexIn + ownedIn;
  const capitalOut = ownedOut + bridgeOut;
  const wCapitalIn = wCexIn + wOwnedIn;
  const wCapitalOut = wOwnedOut + wBridgeOut;

  return { cexIn, ownedIn, ownedOut, bridgeOut, capitalIn, capitalOut,
           wCexIn, wOwnedIn, wOwnedOut, wBridgeOut, wCapitalIn, wCapitalOut };
}

/**
 * idleStableFlowDerived — pure, ledger-derived.
 * Computes the net stable balance in the wallet (total and at window start)
 * by summing all isStableRow in/out flows.
 */
export function idleStableFlowDerived(
  rows: LedgerRow[],
  windowTs: number,
): { now: number; atStart: number } {
  let now = 0, atStart = 0;
  for (const r of rows) {
    if (!isStableRow(r)) continue;
    const s = r.direction === "in" ? (r.usd ?? 0) : -(r.usd ?? 0);
    now += s;
    if (r.ts < windowTs) atStart += s;
  }
  return { now, atStart };
}

// ── Per-protocol attribution ───────────────────────────────────────────────────

interface ProtoAccum {
  costIn: number;
  proceedsOut: number;
  windowCostIn: number;
  windowProceedsOut: number;
  /** receipt tokens seen: symbol → {addr, chain, decimals} */
  receiptTokens: Map<string, { addr: string; chain: string; decimals: number }>;
}

function ensure(map: Map<string, ProtoAccum>, key: string): ProtoAccum {
  if (!map.has(key)) {
    map.set(key, {
      costIn: 0,
      proceedsOut: 0,
      windowCostIn: 0,
      windowProceedsOut: 0,
      receiptTokens: new Map(),
    });
  }
  return map.get(key)!;
}

export function attributeProtocols(rows: LedgerRow[]): Map<string, ProtoAccum> {
  // Group rows by txHash
  const byTx = new Map<string, LedgerRow[]>();
  for (const row of rows) {
    const h = row.txHash;
    if (!byTx.has(h)) byTx.set(h, []);
    byTx.get(h)!.push(row);
  }

  const result = new Map<string, ProtoAccum>();

  // Stable-symbol names that sometimes appear as non-stable (different contract address)
  const stableSymNames = new Set([
    "usdc", "usdt", "dai", "usde", "usdbc", "usdc.e", "usdt0",
  ]);

  for (const [, txRows] of byTx) {
    // Step 1: Find non-stable, non-spam, non-directional-dust candidates
    const candidates = txRows.filter((r) => {
      if (isStableRow(r)) return false;
      if (SPAM_REGEX.test(r.symbol)) return false;
      if (r.amountFloat <= 0) return false;
      // Skip Directional tokens (WETH dust in Beefy txes, etc.) — handled separately
      if (detectProtocol(r.symbol) === "Directional") return false;
      // Skip tokens with stable-sounding names at non-standard addresses (fake stablecoins)
      if (stableSymNames.has(r.symbol.toLowerCase())) return false;
      return true;
    });

    // Step 2: No candidates → standalone stable flow → skip
    if (candidates.length === 0) continue;

    // Step 3: Apply EUSD pass-through rule
    // When Beefy token OR MEUSD appears in same tx as EUSD, Beefy/MEUSD is primary
    const eusd_addr = "0xcfa3ef56d303ae4faaba0592388f19d7c3399fb4";
    const filteredCandidates = candidates.filter((r) => {
      if (r.tokenAddr === eusd_addr || r.symbol.toLowerCase() === "eusd") {
        const hasOtherPrimary = candidates.some(
          (c) =>
            c !== r &&
            (detectProtocol(c.symbol) === "Beefy" ||
              c.symbol.toLowerCase() === "meusd"),
        );
        return !hasOtherPrimary;
      }
      return true;
    });

    if (filteredCandidates.length === 0) continue;

    // Step 4: Detect protocols for each filtered candidate
    const protocolsInTx = new Map<string, { addr: string; chain: string }>();
    for (const r of filteredCandidates) {
      const proto = detectProtocol(r.symbol);
      if (!protocolsInTx.has(proto)) {
        protocolsInTx.set(proto, { addr: r.tokenAddr, chain: r.chain });
      }
    }

    if (protocolsInTx.size === 0) continue;

    // Step 5: Compute stable flows in this tx
    // Count genuine stablecoins (isStable=true) plus EUSD (stable override)
    let stableOutTotal = 0;
    let stableInTotal = 0;
    for (const r of txRows) {
      if (!isStableRow(r)) continue;
      if (r.direction === "out") stableOutTotal += r.usd ?? 0;
      else stableInTotal += r.usd ?? 0;
    }

    // Step 6: Split equally among detected protocols
    const n = protocolsInTx.size;
    const txTs = txRows[0]?.ts ?? 0;
    const inWindow = txTs >= WINDOW_1Y_TS;

    for (const [proto, { addr, chain }] of protocolsInTx) {
      const acc = ensure(result, proto);
      acc.costIn += stableOutTotal / n;
      acc.proceedsOut += stableInTotal / n;
      if (inWindow) {
        acc.windowCostIn += stableOutTotal / n;
        acc.windowProceedsOut += stableInTotal / n;
      }
      // Track receipt token addresses and decimals
      for (const r of filteredCandidates) {
        if (detectProtocol(r.symbol) === proto && !acc.receiptTokens.has(r.symbol)) {
          acc.receiptTokens.set(r.symbol, { addr: r.tokenAddr, chain: r.chain, decimals: r.decimals });
        }
      }
    }
  }

  return result;
}

// ── Live RPC helpers ───────────────────────────────────────────────────────────

/** Default BalanceProvider: wraps ethCall with 3-attempt exponential-backoff retry.
 *  Retries on: HTTP error (rpcPost handles), null result, empty result, 0 value.
 *  Delays: 500ms / 1000ms / 2000ms between attempts.
 */
async function rpcGetBalance(
  rpcs: string[],
  tokenAddr: string,
  wallet: string,
  blockHex: string,
): Promise<bigint> {
  const delays = [500, 1000, 2000];
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const raw = await ethCall(rpcs, tokenAddr, SEL_BALANCEOF + pad32(wallet), blockHex);
      if (raw && raw !== "0x" && raw !== "0x0" && raw !== "") {
        const val = BigInt(raw);
        if (val > 0n) return val;
      }
    } catch {}
    if (attempt < 2) await Bun.sleep(delays[attempt]);
  }
  return 0n;
}

async function getBalanceOf(
  rpcs: string[],
  tokenAddr: string,
  wallet: string,
  blockHex: string,
  provider: BalanceProvider = rpcGetBalance,
): Promise<bigint> {
  return provider(rpcs, tokenAddr, wallet, blockHex);
}

/**
 * valueNonStableHeld — tries per-protocol on-chain methods in priority order to value a
 * held non-stable token at its current USD redemption value.
 *
 * Order: ERC-4626 convertToAssets → ERC-4626 totalAssets/totalSupply →
 *        Beefy getPricePerFullShare → Curve/Aero stable LP get_virtual_price →
 *        Aave aToken UNDERLYING_ASSET_ADDRESS → unpriced ($0).
 *
 * GUARDRAIL: returns $0 for any token where all RPC calls fail or return 0.
 * Conservative under-value > fictional inflation. Governance tokens, market tokens,
 * and spam all stay $0 — only tokens with provable on-chain redemption paths are valued.
 *
 * @param rpcs       - RPC endpoints for the token's chain
 * @param tokenAddr  - ERC-20 token contract address
 * @param walletAddr - wallet address (lowercase)
 * @param decimals   - token decimals from ledger (used for Beefy/Curve/Aave paths)
 * @param blockHex   - hex block number for RPC calls (current block)
 */
export async function valueNonStableHeld(
  rpcs: string[],
  tokenAddr: string,
  walletAddr: string,
  decimals: number,
  blockHex: string,
  provider: BalanceProvider = rpcGetBalance,
): Promise<{ value: number; method: string }> {
  const balance = await getBalanceOf(rpcs, tokenAddr, walletAddr, blockHex, provider);
  if (balance === 0n) return { value: 0, method: "balance=0" };

  // ── 1. ERC-4626 convertToAssets(balance) ──────────────────────────────────
  const sharesHex = balance.toString(16).padStart(64, "0");
  const rawConvert = await ethCall(rpcs, tokenAddr, SEL_CONVERT_ASSETS + sharesHex, blockHex);
  if (rawConvert) {
    try {
      const assets = BigInt(rawConvert);
      if (assets > 0n) {
        // Try ledger decimals first, then [6, 18] as fallback
        for (const d of [decimals, 6, 18]) {
          const v = Number(assets) / 10 ** d;
          if (v >= 1e-2 && v <= 1e9) return { value: v, method: `erc4626-convertToAssets/${d}dec` };
        }
      }
    } catch {}
  }

  // ── 2. ERC-4626 totalAssets/totalSupply × balance ─────────────────────────
  const taRaw = await ethCall(rpcs, tokenAddr, SEL_TOTAL_ASSETS, blockHex);
  const tsRaw = await ethCall(rpcs, tokenAddr, SEL_TOTAL_SUPPLY, blockHex);
  if (taRaw && tsRaw) {
    try {
      const totalAssets = BigInt(taRaw);
      const totalSupply = BigInt(tsRaw);
      if (totalSupply > 0n) {
        const assetValue = (totalAssets * balance) / totalSupply;
        for (const d of [decimals, 6, 18]) {
          const v = Number(assetValue) / 10 ** d;
          if (v >= 1e-2 && v <= 1e9) return { value: v, method: `erc4626-ta-ts/${d}dec` };
        }
      }
    } catch {}
  }

  // ── 3. Beefy getPricePerFullShare ─────────────────────────────────────────
  // Identifies Beefy mooTokens: only Beefy implements this selector.
  // PPFS is always in 1e18 scale: underlyingRaw = balance × PPFS / 1e18
  // (mooToken decimals == underlying decimals, so using ledger decimals is correct)
  const ppfsRaw = await ethCall(rpcs, tokenAddr, SEL_PRICE_PER_SHARE, blockHex);
  if (ppfsRaw) {
    try {
      const ppfs = BigInt(ppfsRaw);
      if (ppfs > 0n) {
        const underlyingRaw = (balance * ppfs) / (10n ** 18n);
        for (const d of [decimals, 6, 18]) {
          const v = Number(underlyingRaw) / 10 ** d;
          if (v >= 1e-2 && v <= 1e9) return { value: v, method: `beefy-ppfs/${d}dec` };
        }
      }
    } catch {}
  }

  // ── 4. Curve/Aerodrome/Velodrome stable LP get_virtual_price ──────────────
  // Identifies stable pool LP tokens: virtual_price ∈ [0.80, 1.30] USD.
  // ONLY apply for stable pools (rejects tricrypto/volatile: VP > 1.3).
  // LP tokens are typically 18 decimals.
  const vpRaw = await ethCall(rpcs, tokenAddr, SEL_VIRTUAL_PRICE, blockHex);
  if (vpRaw) {
    try {
      const virtualPrice = BigInt(vpRaw);
      if (virtualPrice > 0n) {
        const vp = Number(virtualPrice) / 1e18;
        if (vp >= 0.8 && vp <= 1.3) {
          // LP tokens are almost always 18-decimal; try ledger decimals too
          for (const d of [18, decimals]) {
            const v = Number(balance) / 10 ** d * vp;
            if (v >= 1e-2 && v <= 1e9) return { value: v, method: `curve-stable-vp/${d}dec` };
          }
        }
      }
    } catch {}
  }

  // ── 5. Aave V3 aToken: UNDERLYING_ASSET_ADDRESS → if stable, 1:1 value ───
  // Aave aTokens rebase — balanceOf already equals principal+interest.
  // Only applies when underlying is a known stable address.
  const underlyingRaw = await ethCall(rpcs, tokenAddr, SEL_AAVE_UNDERLYING, blockHex);
  if (underlyingRaw && underlyingRaw.length >= 66) {
    const underlying = ("0x" + underlyingRaw.slice(-40)).toLowerCase();
    if (KNOWN_STABLE_ADDRS.has(underlying)) {
      for (const d of [decimals, 6, 18]) {
        const v = Number(balance) / 10 ** d;
        if (v >= 1e-2 && v <= 1e9) return { value: v, method: `aave-atoken-1to1/${d}dec` };
      }
    }
  }

  // ── Unpriced: token does not expose on-chain redemption value ─────────────
  // NOTE: LlamaFi market-price fallback is intentionally absent.
  // Pricing governance/market tokens via external feeds fabricates fictional values.
  // Unpriced tokens are tracked in the protocol row's flags as "unvalued:N(SYM1,SYM2…)".
  return { value: 0, method: "unpriced" };
}

/**
 * computeIdleStableRpc — async, uses live RPC.
 * For each unique (chain, tokenAddr) among isStableRow rows, fetches the wallet's
 * current on-chain balance and converts to USD at face value ($1 per token).
 * This is the independent current-value term for stables, distinct from flow accounting.
 */
async function computeIdleStableRpc(
  rows: LedgerRow[],
  walletLower: string,
  nowBlockMap: Map<string, string | null>,
  provider: BalanceProvider = rpcGetBalance,
): Promise<number> {
  // Unique (chain, tokenAddr) → decimals
  const stableTokens = new Map<string, { chain: string; decimals: number }>();
  for (const r of rows) {
    if (!isStableRow(r)) continue;
    const key = `${r.chain}:${r.tokenAddr.toLowerCase()}`;
    if (!stableTokens.has(key)) {
      stableTokens.set(key, { chain: r.chain, decimals: r.decimals });
    }
  }

  const results = await Promise.all(
    [...stableTokens.entries()].map(async ([key, { chain, decimals }]) => {
      const tokenAddr = key.split(":")[1];
      const cfg = CHAIN_CONFIG[chain];
      if (!cfg) return 0;
      const nowBlockHex = nowBlockMap.get(chain);
      if (!nowBlockHex) return 0;
      const bal = await getBalanceOf(cfg.rpcs, tokenAddr, walletLower, nowBlockHex, provider);
      const usd = Number(bal) / 10 ** decimals;
      if (usd >= 0 && usd <= 1e9) return usd;
      return 0;
    }),
  );

  return results.reduce((s, v) => s + v, 0);
}

/**
 * computeIdleStableRpcMultiWallet — async, cluster mode.
 * Sums on-chain stable balances across ALL provided wallets.
 */
async function computeIdleStableRpcMultiWallet(
  rows: LedgerRow[],
  wallets: string[],
  nowBlockMap: Map<string, string | null>,
  provider: BalanceProvider = rpcGetBalance,
): Promise<number> {
  const stableTokens = new Map<string, { chain: string; decimals: number }>();
  for (const r of rows) {
    if (!isStableRow(r)) continue;
    const key = `${r.chain}:${r.tokenAddr.toLowerCase()}`;
    if (!stableTokens.has(key)) {
      stableTokens.set(key, { chain: r.chain, decimals: r.decimals });
    }
  }

  const results = await Promise.all(
    [...stableTokens.entries()].flatMap(([key, { chain, decimals }]) =>
      wallets.map(async (walletAddr) => {
        const tokenAddr = key.split(":")[1];
        const cfg = CHAIN_CONFIG[chain];
        if (!cfg) return 0;
        const nowBlockHex = nowBlockMap.get(chain);
        if (!nowBlockHex) return 0;
        const bal = await getBalanceOf(cfg.rpcs, tokenAddr, walletAddr, nowBlockHex, provider);
        const usd = Number(bal) / 10 ** decimals;
        if (usd >= 0 && usd <= 1e9) return usd;
        return 0;
      }),
    ),
  );

  return results.reduce((s, v) => s + v, 0);
}

// ── Open position detector ─────────────────────────────────────────────────────

/**
 * Determine if a position was open at the window start (provably open).
 * A position is provably open if it has entries before the window AND
 * (no exits before window OR exits at/after window).
 */
function isProvablyOpenAtWindow(
  rows: LedgerRow[],
  tokenSymbol: string,
  windowTs: number,
): boolean {
  const tokenRows = rows.filter((r) => r.symbol === tokenSymbol);
  const entriesBefore = tokenRows.filter((r) => r.direction === "in" && r.ts < windowTs);
  if (entriesBefore.length === 0) return false;
  const exitsBefore = tokenRows.filter((r) => r.direction === "out" && r.ts < windowTs);
  const exitsAtOrAfter = tokenRows.filter((r) => r.direction === "out" && r.ts >= windowTs);
  return exitsBefore.length === 0 || exitsAtOrAfter.length > 0;
}

/**
 * Sanity guard: compares live-RPC idle_rpc value against ledger-derived idle_flow.
 * Throws if divergence exceeds max($500, 3% of idle_flow) — this prevents the skill from
 * emitting a PnL table when the RPC balanceOf reads are returning garbage values.
 */
export function assertIdleRpcSanity(idle_rpc: number, idle_flow: number): void {
  const tolerance = Math.max(500, Math.abs(idle_flow) * 0.03);
  const diff = Math.abs(idle_rpc - idle_flow);
  if (diff > tolerance) {
    throw new Error(
      `RPC current-value read failed: idle_rpc=$${idle_rpc.toFixed(2)} vs idle_flow=$${idle_flow.toFixed(2)} ` +
      `(diff $${diff.toFixed(2)} exceeds tolerance $${tolerance.toFixed(2)}) ` +
      `— refusing to emit a PnL number`
    );
  }
}

/** True for a JSON-RPC error that is a genuine EVM execution revert (the chain answered,
 *  the token simply doesn't implement the method) — as opposed to a node-availability error
 *  (rate-limit / internal / auth) which means the endpoint did NOT give an authoritative answer. */
function isExecutionRevert(err: unknown): boolean {
  const e = err as { code?: number; message?: string } | null;
  const code = e?.code;
  const msg = String(e?.message ?? "").toLowerCase();
  return code === 3 || code === -32015 || msg.includes("revert") || msg.includes("execution");
}

/**
 * authoritativeEthCall — one eth_call across the endpoint list with retries, reporting whether
 * the chain gave an AUTHORITATIVE answer. ok=true on a `result` (incl `0x`) or an execution
 * revert (chain reached + contract queried); ok=false only on transport failure / node-
 * availability error (rate-limit / internal / auth) where no endpoint answered.
 */
async function authoritativeEthCall(
  rpcs: string[], to: string, data: string,
): Promise<{ ok: boolean; result: string | null }> {
  for (const rpc of rpcs) {
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), 15_000);
        try {
          const res = await fetch(rpc, {
            method: "POST",
            headers: { "Content-Type": "application/json", "User-Agent": "boundary-pnl/1.0" },
            body: JSON.stringify({ jsonrpc: "2.0", method: "eth_call", params: [{ to, data }, "latest"], id: 1 }),
            signal: ctrl.signal,
          });
          const j = (await res.json()) as { result?: unknown; error?: unknown };
          if (j && typeof j.result === "string") return { ok: true, result: j.result };
          if (j && j.error && isExecutionRevert(j.error)) return { ok: true, result: null }; // clean revert
          // else node-availability error → not authoritative; try next endpoint
        } finally {
          clearTimeout(t);
        }
      } catch {
        // transport failure — retry / fall through
      }
      if (attempt < 2) await Bun.sleep(400 * (attempt + 1));
    }
  }
  return { ok: false, result: null };
}

/**
 * defaultReachProbe — live re-read of a held token for the vault guard.
 * Reads the wallet's own balanceOf first (so an EXITED token, balanceOf 0, is never flagged);
 * only if held does it probe convertToAssets(1 share) to tell an ERC-4626 stable vault from a
 * non-redeemable holding (LINEA/PAXG). reachable=false (transport failure) → caller throws.
 */
const defaultReachProbe: EthReachProbe = async (rpcs, tokenAddr, walletAddr, decimals) => {
  const bal = await authoritativeEthCall(rpcs, tokenAddr, SEL_BALANCEOF + pad32(walletAddr));
  if (!bal.ok) return { reachable: false, heldRaw: null, redeemPerShare: null };
  let heldRaw = 0n;
  if (bal.result && bal.result !== "0x" && bal.result !== "0x0" && bal.result !== "") {
    try { heldRaw = BigInt(bal.result); } catch { /* unparseable → treat as 0 */ }
  }
  if (heldRaw === 0n) return { reachable: true, heldRaw: 0n, redeemPerShare: null }; // not held → $0 correct

  const ca = await authoritativeEthCall(rpcs, tokenAddr, SEL_CONVERT_ASSETS + (10n ** BigInt(decimals)).toString(16).padStart(64, "0"));
  let redeemPerShare: number | null = null;
  if (ca.ok && ca.result && ca.result !== "0x" && ca.result !== "0x0" && ca.result !== "") {
    try {
      const perShare = Number(BigInt(ca.result)) / 10 ** decimals;
      if (perShare >= 0.5 && perShare <= 2.0) redeemPerShare = perShare;
    } catch { /* unparseable → non-vault */ }
  }
  return { reachable: true, heldRaw, redeemPerShare };
};

// ── Main computation ───────────────────────────────────────────────────────────

/** One receipt-token current-value read, retained for the vault-RPC sanity guard. */
interface TokenValuation {
  wallet: string;
  proto: string;
  sym: string;
  tokenAddr: string;
  chain: string;
  decimals: number;
  /** USD value the main pass resolved for this token at this wallet ($0 if unvalued). */
  value: number;
  /** net ledger basis (costIn − proceedsOut) of the owning (wallet, protocol) — proxy for capital still deployed. */
  protoNetBasis: number;
}

/** Protocols whose $0 curVal is structural (no receipt token / excluded), never RPC-failure. */
const VAULT_GUARD_EXCLUDE = new Set<string>(["Directional", "Misc", "Perps", "Bridge", "Unidentified", ...NAMED_MISC_PROTOS.values()]);

/**
 * assertVaultRpcSanity — the safety net for SILENT vault under-valuation (the avUSDC bug).
 *
 * assertIdleRpcSanity only covers idle STABLE balances; it cannot see a vault position the
 * RPC zeroed. This guard closes that gap. A token is a "suspect" when the main pass valued it
 * ~$0 while its owning (wallet,protocol) still has net capital deployed (positive ledger
 * basis) and is a real-protocol position (not Misc/Perps/Bridge/Unidentified/Directional).
 * For each suspect it independently re-reads the wallet's own balanceOf, then:
 *   • chain unreachable after retries → cannot confirm a deployed position → THROW;
 *   • not held (balanceOf 0 → exited) → $0 is correct → OK;
 *   • held with > $1 of ERC-4626-redeemable value → a vault the main pass zeroed
 *     (e.g. avUSDC after an RPC flake) → THROW;
 *   • held but non-redeemable (convertToAssets reverts → spam / LINEA / PAXG) → OK.
 *
 * MUST NOT trip on: fully-exited positions, or held-but-non-redeemable holdings. Probes run in
 * parallel and only for $0 suspects, so a healthy run pays ~0 extra cost (valued vaults aren't
 * suspects), and balanceOf 0 short-circuits before any convertToAssets call.
 */
export async function assertVaultRpcSanity(
  tokenValuations: TokenValuation[],
  opts?: BoundaryPnLOpts,
): Promise<void> {
  const GUARD_BASIS = 100;  // $ net basis above which the bucket has capital still deployed
  const GUARD_VALUE = 1;    // $ below which a position is "valued ~zero" / "held ~nothing"
  const reachProbe = opts?.ethReachProbe ?? defaultReachProbe;

  const suspects = tokenValuations.filter(
    (tv) => !VAULT_GUARD_EXCLUDE.has(tv.proto) &&
      tv.value <= GUARD_VALUE &&
      tv.protoNetBasis > GUARD_BASIS &&
      tv.chain in CHAIN_CONFIG,
  );

  const verdicts = await Promise.all(
    suspects.map(async (tv) => {
      const cfg = CHAIN_CONFIG[tv.chain];
      const { reachable, heldRaw, redeemPerShare } = await reachProbe(cfg.rpcs, tv.tokenAddr, tv.wallet, tv.decimals);
      if (!reachable) {
        return `refusing to emit a PnL number: ${tv.sym} (${tv.wallet.slice(0, 8)}…) sits in a position ` +
          `with ~$${tv.protoNetBasis.toFixed(0)} net basis deployed but its chain (${tv.chain}) is unreachable ` +
          `after retries — cannot confirm it is genuinely $0`;
      }
      if (heldRaw === null || heldRaw === 0n) return null; // exited / not held → $0 is correct
      if (redeemPerShare !== null) {
        const heldUsd = (Number(heldRaw) / 10 ** tv.decimals) * redeemPerShare;
        if (heldUsd > GUARD_VALUE) {
          return `refusing to emit a PnL number: vault ${tv.sym} (${tv.wallet.slice(0, 8)}…) still holds ` +
            `$${heldUsd.toFixed(2)} (redeems ${redeemPerShare.toFixed(3)} assets/share) but the main pass ` +
            `valued it $0 — RPC was flaky during valuation`;
        }
      }
      return null; // held but non-redeemable (revert) or sub-$1 → genuine $0 → OK
    }),
  );

  const tripped = verdicts.find((v) => v !== null);
  if (tripped) throw new Error(tripped);
}

/**
 * Max concurrent receipt-token valuations. The cluster used to fire ALL (token × wallet)
 * valuations at once — a burst of ~150+ eth_calls that rate-limited the public Base/Ethereum
 * endpoints, silently zeroing a real vault (avUSDC) and swinging the anchor by ~$1k. Bounding
 * concurrency keeps every endpoint responsive so identified vaults value deterministically.
 */
const RPC_VALUATION_CONCURRENCY = 5;

/** Run `fn` over `items` with at most `limit` in-flight at once; preserves input order. */
async function mapLimit<T, R>(items: T[], limit: number, fn: (item: T) => Promise<R>): Promise<R[]> {
  const results = new Array<R>(items.length);
  let next = 0;
  const worker = async () => {
    while (true) {
      const i = next++;
      if (i >= items.length) return;
      results[i] = await fn(items[i]);
    }
  };
  await Promise.all(Array.from({ length: Math.min(Math.max(1, limit), items.length || 1) }, worker));
  return results;
}

interface ComputeResult {
  protocolRows: ProtocolRow[];
  sumPnL: number;
  nowBlockMap: Map<string, string | null>;
}

export async function compute(
  rows: LedgerRow[],
  wallet: string,
  windowTs: number,
  opts?: BoundaryPnLOpts,
): Promise<ComputeResult> {
  const walletLower = wallet.toLowerCase();

  // Attribute stable flows per protocol
  const protoAccum = attributeProtocols(rows);

  // Get current block heights per chain (no window block needed — archive RPC removed)
  const chains = [...new Set(rows.map((r) => r.chain))].filter(
    (c) => c in CHAIN_CONFIG,
  );

  const nowBlockMap: Map<string, string | null> = opts?.nowBlockMap ?? new Map<string, string | null>();

  if (!opts?.nowBlockMap) {
    // Read current chain-head state via the "latest" block tag. NOT Date.now()+llamaBlock:
    // wall-clock is banned, and a hung DefiLlama connection (httpGet has no timeout) would stall
    // the entire run before any valuation. "latest" reads live state with no DefiLlama/archive
    // dependency, exactly as the per-LP path does.
    for (const chain of chains) nowBlockMap.set(chain, "latest");
  }

  // Build per-protocol rows with live current values
  const protocolRows: ProtocolRow[] = [];

  for (const [proto, acc] of protoAccum) {
    let curVal = 0;
    const flags: string[] = [];

    if (proto === "Directional") {
      // Directional (stETH/cbETH) current value not computed per-wallet.
      // Requires ETH price feed + per-wallet on-chain balance query — omitted to avoid
      // cross-wallet value leakage.  curVal = $0.
      curVal = 0;
    } else {
      // Compute current value via live RPC for each receipt token.
      // valueNonStableHeld tries ERC-4626 → Beefy PPFS → Curve stable VP → Aave aToken.
      // Tokens that cannot be identified as a real protocol receipt stay $0.
      const unpricedSymbols: string[] = [];
      for (const [sym, { addr, chain, decimals }] of acc.receiptTokens) {
        const cfg = CHAIN_CONFIG[chain];
        if (!cfg) continue;

        const nowBlockHex = nowBlockMap.get(chain);
        if (!nowBlockHex) continue;

        const { value: val, method } = await valueNonStableHeld(
          cfg.rpcs, addr, walletLower, decimals, nowBlockHex, opts?.balanceProvider,
        );
        curVal += val;
        if (val > 0) {
          console.log(`  [valued] ${sym} (${chain}): $${val.toFixed(2)} via ${method}`);
        }
        if (method === "unpriced") unpricedSymbols.push(sym);
      }
      if (unpricedSymbols.length > 0) {
        flags.push(`unvalued:${unpricedSymbols.length}(${unpricedSymbols.join(",")})`);
      }
    }

    const lifePnL = acc.proceedsOut + curVal - acc.costIn;

    // Ledger-derived window-start basis (eliminates archive RPC dependency):
    //   preWinCostIn  = total cost in BEFORE window
    //   preWinProceeds = total proceeds BEFORE window
    //   windowBasis = pre-window net investment still at stake at window start
    //                 (clamped to 0 — can't be negative if we entered and haven't fully exited)
    // A protocol "contributes to the window" if it has current value OR in-window flows.
    const preWinCostIn = acc.costIn - acc.windowCostIn;
    const preWinProceeds = acc.proceedsOut - acc.windowProceedsOut;
    const contributesToWindow =
      curVal > 0.01 || acc.windowCostIn > 0.01 || acc.windowProceedsOut > 0.01;
    const windowBasis = contributesToWindow ? Math.max(0, preWinCostIn - preWinProceeds) : 0;

    // 1Y PnL (stable protocols only):
    //   pnl_1y = in-window proceeds + current value - in-window cost - window-start basis
    // Directional is excluded from stable yield — report separately, set pnl1y = 0.
    const pnl1y =
      proto === "Directional"
        ? 0
        : acc.windowProceedsOut + curVal - acc.windowCostIn - windowBasis;

    protocolRows.push({
      protocol: proto,
      costIn: acc.costIn,
      proceedsOut: acc.proceedsOut,
      curVal,
      lifePnL,
      pnl1y,           // will be overwritten by apportionment pass below
      pnl1y_facebasis: pnl1y, // set now; serves as upper bound
      flags: flags.join(","),
      windowCostIn: acc.windowCostIn,
      windowProceedsOut: acc.windowProceedsOut,
      windowBasis,
    });
  }

  // ── Time-apportion pnl1y per protocol (linear-accrual model estimate)
  // For each open/closed protocol position, weight lifetime PnL by the fraction of
  // the holding period that falls inside the trailing window.
  // NOTE: apportioned 1Y is a MODEL — lifetime PnL is hard-measured. pnl1y_facebasis is upper bound.
  // Misc-like protocols have no receipt tokens — skip apportionment, their pnl1y is set by buildMiscRow.
  // NAMED_MISC_PROTOS values are also misc-like (individual address buckets with no receipt tokens).
  const MISC_LIKE = new Set(["Directional", "Misc", "Perps", "Bridge", "Unidentified", ...NAMED_MISC_PROTOS.values()]);
  for (const pr of protocolRows) {
    if (MISC_LIKE.has(pr.protocol)) continue;

    const acc = protoAccum.get(pr.protocol);
    if (!acc) continue;

    const receiptSymbols = new Set(acc.receiptTokens.keys());
    const receiptRows = rows.filter((r) => receiptSymbols.has(r.symbol));

    const entryRows = receiptRows.filter((r) => r.direction === "in");
    const exitRows  = receiptRows.filter((r) => r.direction === "out");

    if (entryRows.length === 0) continue; // no entry ts — keep face-basis

    const firstEntryTs = Math.min(...entryRows.map((r) => r.ts));
    const lastExitTs   = exitRows.length > 0 ? Math.max(...exitRows.map((r) => r.ts)) : null;

    // "fully closed" = curVal < $1 AND there was at least one exit
    const isClosed = pr.curVal < 1 && lastExitTs !== null;
    const endTs = isClosed ? lastExitTs! : NOW;

    const fraction = computeApportionFraction(firstEntryTs, endTs, windowTs, NOW);
    pr.pnl1y = pr.lifePnL * fraction;
  }

  // Misc reconciliation — standalone stable flows split into named sub-buckets.
  // windowBasis fix: each sub-bucket applies the pre-window capital-return correction
  // (same logic as named protocols) so capital returns are not counted as window yield.
  // Conservation invariant: Σ lifePnL and Σ pnl1y_facebasis are unchanged; each bucket's
  // windowBasis reduces pnl1y_facebasis by the same amount it increases sumWindowBasis.
  const misc = computeMiscFlows(rows);
  if (misc.costIn > 0 || misc.proceedsOut > 0) {
    // Regular DeFi yield (CLPool fees, WooPP, AlgebraPool, uncategorized protocol flows)
    if (misc.regular.costIn > 0 || misc.regular.proceedsOut > 0) {
      protocolRows.push(buildMiscRow("Misc", misc.regular, "standalone-flows"));
    }
    // ZkLighter on-chain perps/trading P&L — separate from DeFi yield
    if (misc.perps.costIn > 0 || misc.perps.proceedsOut > 0) {
      protocolRows.push(buildMiscRow("Perps", misc.perps, "zklighter:perps-trading:excluded-from-yield"));
    }
    // Cross-chain bridge flows (capital movements, not yield)
    if (misc.bridge.costIn > 0 || misc.bridge.proceedsOut > 0) {
      protocolRows.push(buildMiscRow("Bridge", misc.bridge, "lifi/stargate/woo:bridge-flows:excluded-from-yield"));
    }
    // Unidentified inflows — excluded pending positive ID as DeFi yield source
    if (misc.unidentified.costIn > 0 || misc.unidentified.proceedsOut > 0) {
      protocolRows.push(buildMiscRow("Unidentified", misc.unidentified, "0xa9d1e0:unverified-contract:excluded-from-yield"));
    }
    // Per-address named protocol sub-buckets (CLPool, CLPoolFees, AlgebraPool, WooPPV2, LPExit).
    // Each gets individual windowBasis so the pre-window capital-return correction is per-address.
    for (const [protoName, bucket] of misc.named) {
      if (bucket.costIn > 0 || bucket.proceedsOut > 0) {
        protocolRows.push(buildMiscRow(protoName, bucket, "misc-named-defi-yield"));
      }
    }
  }

  // Synthetic Directional row — STETH/CBETH tracked separately, costIn=0 per spec.
  // curVal=$0: computing ETH/stETH current value requires an ETH price feed + per-wallet
  // on-chain balance query.  Without that, we report $0 to avoid cross-wallet value leakage.
  if (!protocolRows.some((r) => r.protocol === "Directional")) {
    protocolRows.push({
      protocol: "Directional",
      costIn: 0,
      proceedsOut: 0,
      curVal: 0,
      lifePnL: 0,
      pnl1y: 0, // excluded from stable yield — reported separately
      pnl1y_facebasis: 0,
      flags: "directional: not computed per-wallet",
      windowCostIn: 0,
      windowProceedsOut: 0,
      windowBasis: 0,
    });
  }

  const sumPnL = protocolRows.reduce((s, p) => s + p.lifePnL, 0);

  return { protocolRows, sumPnL, nowBlockMap };
}

// ── Cluster computation ────────────────────────────────────────────────────────

/**
 * computeCluster — async, multi-wallet cluster mode.
 *
 * Identical algorithm to compute() with two differences:
 *   1. RPC balance checks iterate over ALL wallets in the cluster (sum across wallets).
 *   2. Capital flows use computeClusterCapitalFlows (inter-wallet flows are internal → $0).
 *
 * When rows from all N ledgers are merged and passed here:
 *   - Inter-wallet transfers appear as paired rows (out from A, in to B) which cancel in
 *     computeClusterCapitalFlows and also in idleStableFlowDerived (symmetric net = $0).
 *   - Protocol attribution via attributeProtocols() still works correctly because
 *     inter-wallet txHashes have only stable rows (no receipt tokens) and are skipped.
 */
export async function computeCluster(
  rows: LedgerRow[],
  wallets: string[],
  windowTs: number,
  opts?: BoundaryPnLOpts,
  /** Optional `${chain}:${tokenAddr}` → owning wallets, to value each token only where it lives. */
  tokenOwners?: Map<string, Set<string>>,
): Promise<ComputeResult & { tokenValuations: TokenValuation[] }> {
  const protoAccum = attributeProtocols(rows);

  const chains = [...new Set(rows.map((r) => r.chain))].filter((c) => c in CHAIN_CONFIG);

  const nowBlockMap: Map<string, string | null> = opts?.nowBlockMap ?? new Map<string, string | null>();

  if (!opts?.nowBlockMap) {
    // Read current chain-head state via the "latest" block tag. NOT Date.now()+llamaBlock:
    // wall-clock is banned, and a hung DefiLlama connection (httpGet has no timeout) would stall
    // the entire run before any valuation. "latest" reads live state with no DefiLlama/archive
    // dependency, exactly as the per-LP path does.
    for (const chain of chains) nowBlockMap.set(chain, "latest");
  }

  const protocolRows: ProtocolRow[] = [];
  const tokenValuations: TokenValuation[] = [];

  for (const [proto, acc] of protoAccum) {
    let curVal = 0;
    const flags: string[] = [];

    if (proto !== "Directional") {
      const unpricedSymbols: string[] = [];
      // Value (token × wallet) at bounded concurrency. A receipt token lives in exactly the
      // wallet(s) whose ledger references it, so when tokenOwners is provided we check only
      // those wallets instead of all N — this cut "Other" from 158×5=790 valuations (most
      // guaranteed-$0) down to ~158, the difference between a 1-min run and a stalled one.
      const tokenWalletPairs = [...acc.receiptTokens.entries()].flatMap(
        ([sym, { addr, chain, decimals }]) => {
          const owners = tokenOwners?.get(`${chain}:${addr.toLowerCase()}`);
          const ws = owners ? wallets.filter((w) => owners.has(w.toLowerCase())) : wallets;
          return ws.map((walletAddr) => ({ sym, addr, chain, decimals, walletAddr }));
        },
      );
      const tokenWalletResults = await mapLimit(
        tokenWalletPairs, RPC_VALUATION_CONCURRENCY,
        async ({ sym, addr, chain, decimals, walletAddr }) => {
          const cfg = CHAIN_CONFIG[chain];
          if (!cfg) return { sym, addr, chain, decimals, walletAddr, val: 0, method: "no-chain-config" };
          const nowBlockHex = nowBlockMap.get(chain);
          if (!nowBlockHex) return { sym, addr, chain, decimals, walletAddr, val: 0, method: "no-block" };
          const { value: val, method } = await valueNonStableHeld(
            cfg.rpcs, addr, walletAddr, decimals, nowBlockHex, opts?.balanceProvider,
          );
          return { sym, addr, chain, decimals, walletAddr, val, method };
        },
      );
      const protoNetBasis = acc.costIn - acc.proceedsOut;
      for (const { sym, addr, chain, decimals, walletAddr, val, method } of tokenWalletResults) {
        curVal += val;
        if (val > 0) {
          console.log(`  [valued] ${sym} (${walletAddr.slice(0, 8)}…): $${val.toFixed(2)} via ${method}`);
        }
        if (method === "unpriced" && !unpricedSymbols.includes(sym)) {
          unpricedSymbols.push(sym);
        }
        // Retained for the vault-RPC sanity guard (cluster mode has no per-row visibility otherwise).
        tokenValuations.push({ wallet: walletAddr, proto, sym, tokenAddr: addr, chain, decimals, value: val, protoNetBasis });
      }
      if (unpricedSymbols.length > 0) {
        flags.push(`unvalued:${unpricedSymbols.length}(${unpricedSymbols.join(",")})`);
      }
    }

    const lifePnL = acc.proceedsOut + curVal - acc.costIn;
    const preWinCostIn = acc.costIn - acc.windowCostIn;
    const preWinProceeds = acc.proceedsOut - acc.windowProceedsOut;
    const contributesToWindow = curVal > 0.01 || acc.windowCostIn > 0.01 || acc.windowProceedsOut > 0.01;
    const windowBasis = contributesToWindow ? Math.max(0, preWinCostIn - preWinProceeds) : 0;

    const pnl1y = proto === "Directional"
      ? 0
      : acc.windowProceedsOut + curVal - acc.windowCostIn - windowBasis;

    protocolRows.push({
      protocol: proto,
      costIn: acc.costIn,
      proceedsOut: acc.proceedsOut,
      curVal,
      lifePnL,
      pnl1y,
      pnl1y_facebasis: pnl1y,
      flags: flags.join(","),
      windowCostIn: acc.windowCostIn,
      windowProceedsOut: acc.windowProceedsOut,
      windowBasis,
    });
  }

  // Time-apportion pnl1y (identical to per-wallet logic)
  // Misc-like protocols have no receipt tokens — skip; their pnl1y is set by buildMiscRow.
  const MISC_LIKE_CLUSTER = new Set(["Directional", "Misc", "Perps", "Bridge", "Unidentified", ...NAMED_MISC_PROTOS.values()]);
  for (const pr of protocolRows) {
    if (MISC_LIKE_CLUSTER.has(pr.protocol)) continue;
    const acc = protoAccum.get(pr.protocol);
    if (!acc) continue;
    const receiptSymbols = new Set(acc.receiptTokens.keys());
    const receiptRows = rows.filter((r) => receiptSymbols.has(r.symbol));
    const entryRows = receiptRows.filter((r) => r.direction === "in");
    const exitRows  = receiptRows.filter((r) => r.direction === "out");
    if (entryRows.length === 0) continue;
    const firstEntryTs = Math.min(...entryRows.map((r) => r.ts));
    const lastExitTs   = exitRows.length > 0 ? Math.max(...exitRows.map((r) => r.ts)) : null;
    const isClosed = pr.curVal < 1 && lastExitTs !== null;
    const endTs = isClosed ? lastExitTs! : NOW;
    const fraction = computeApportionFraction(firstEntryTs, endTs, windowTs, NOW);
    pr.pnl1y = pr.lifePnL * fraction;
  }

  // Misc reconciliation — split into sub-buckets with windowBasis correction (same as compute()).
  const misc = computeMiscFlows(rows);
  if (misc.costIn > 0 || misc.proceedsOut > 0) {
    if (misc.regular.costIn > 0 || misc.regular.proceedsOut > 0) {
      protocolRows.push(buildMiscRow("Misc", misc.regular, "standalone-flows"));
    }
    if (misc.perps.costIn > 0 || misc.perps.proceedsOut > 0) {
      protocolRows.push(buildMiscRow("Perps", misc.perps, "zklighter:perps-trading:excluded-from-yield"));
    }
    if (misc.bridge.costIn > 0 || misc.bridge.proceedsOut > 0) {
      protocolRows.push(buildMiscRow("Bridge", misc.bridge, "lifi/stargate/woo:bridge-flows:excluded-from-yield"));
    }
    if (misc.unidentified.costIn > 0 || misc.unidentified.proceedsOut > 0) {
      protocolRows.push(buildMiscRow("Unidentified", misc.unidentified, "0xa9d1e0:unverified-contract:excluded-from-yield"));
    }
    for (const [protoName, bucket] of misc.named) {
      if (bucket.costIn > 0 || bucket.proceedsOut > 0) {
        protocolRows.push(buildMiscRow(protoName, bucket, "misc-named-defi-yield"));
      }
    }
  }

  if (!protocolRows.some((r) => r.protocol === "Directional")) {
    protocolRows.push({
      protocol: "Directional",
      costIn: 0, proceedsOut: 0, curVal: 0, lifePnL: 0, pnl1y: 0, pnl1y_facebasis: 0,
      flags: "directional: not computed per-wallet",
      windowCostIn: 0, windowProceedsOut: 0, windowBasis: 0,
    });
  }

  const sumPnL = protocolRows.reduce((s, p) => s + p.lifePnL, 0);
  return { protocolRows, sumPnL, nowBlockMap, tokenValuations };
}

// ── Per-wallet per-LP cluster computation ───────────────────────────────────────

/**
 * computeClusterPerLp — multi-wallet cluster mode, but attribution is keyed by
 * (owning-wallet, protocol/LP) instead of (protocol) alone.
 *
 * Each ledger's rows are pre-partitioned by their owning wallet (rowsByWallet).
 * For each wallet we run the SAME attribution + valuation pipeline as compute(),
 * but:
 *   - stable flows are attributed only from that wallet's own ledger rows, and
 *   - each receipt token's current value is read at THAT wallet only.
 * Because each LP receipt token lives in exactly one wallet, Σ over wallets of a
 * protocol's (costIn, proceedsOut, curVal) equals the merged-cluster total — so
 * the cluster anchor and the single cluster-level "Unattributed / Idle" residual
 * are unchanged. The only structural difference is that a protocol held by two
 * wallets (e.g. Maple in L3 and B3) now produces one row per wallet.
 *
 * Block lookups use the deterministic NOW constant (never wall-clock time).
 */
export async function computeClusterPerLp(
  rowsByWallet: Map<string, LedgerRow[]>,
  windowTs: number,
  opts?: BoundaryPnLOpts,
): Promise<ComputeResult & { tokenValuations: TokenValuation[] }> {
  const allRows = [...rowsByWallet.values()].flat();
  const chains = [...new Set(allRows.map((r) => r.chain))].filter((c) => c in CHAIN_CONFIG);

  const nowBlockMap: Map<string, string | null> = opts?.nowBlockMap ?? new Map<string, string | null>();
  if (!opts?.nowBlockMap) {
    // Read current chain-head state via the "latest" block tag.
    // NOT Date.now() (banned), and NOT a pinned historical block: public RPCs lack
    // archive state, so balanceOf at an old block reverts to 0 and trips the idle
    // sanity guard. "latest" reads live state (no archive needed) and is not wall-clock.
    for (const chain of chains) nowBlockMap.set(chain, "latest");
  }

  const MISC_LIKE = new Set(["Directional", "Misc", "Perps", "Bridge", "Unidentified", ...NAMED_MISC_PROTOS.values()]);
  const protocolRows: ProtocolRow[] = [];
  const tokenValuations: TokenValuation[] = [];

  for (const [wallet, wRows] of rowsByWallet) {
    const protoAccum = attributeProtocols(wRows);
    const localRows: ProtocolRow[] = [];

    // ── Receipt-token protocol rows — current value read at THIS wallet only ──
    for (const [proto, acc] of protoAccum) {
      let curVal = 0;
      const flags: string[] = [];

      if (proto !== "Directional") {
        const unpricedSymbols: string[] = [];
        const tokenResults = await mapLimit(
          [...acc.receiptTokens.entries()], RPC_VALUATION_CONCURRENCY,
          async ([sym, { addr, chain, decimals }]) => {
            const cfg = CHAIN_CONFIG[chain];
            if (!cfg) return { sym, addr, chain, decimals, val: 0, method: "no-chain-config" };
            const nowBlockHex = nowBlockMap.get(chain);
            if (!nowBlockHex) return { sym, addr, chain, decimals, val: 0, method: "no-block" };
            const { value: val, method } = await valueNonStableHeld(
              cfg.rpcs, addr, wallet, decimals, nowBlockHex, opts?.balanceProvider,
            );
            return { sym, addr, chain, decimals, val, method };
          },
        );
        const protoNetBasis = acc.costIn - acc.proceedsOut;
        for (const { sym, addr, chain, decimals, val, method } of tokenResults) {
          curVal += val;
          if (val > 0) {
            console.log(`  [valued] ${sym} (${wallet.slice(0, 8)}…): $${val.toFixed(2)} via ${method}`);
          }
          if (method === "unpriced" && !unpricedSymbols.includes(sym)) unpricedSymbols.push(sym);
          // Retained for the vault-RPC sanity guard (catches a deployed position silently $0'd by a flaky RPC).
          tokenValuations.push({ wallet, proto, sym, tokenAddr: addr, chain, decimals, value: val, protoNetBasis });
        }
        if (unpricedSymbols.length > 0) {
          flags.push(`unvalued:${unpricedSymbols.length}(${unpricedSymbols.join(",")})`);
        }
      }

      const lifePnL = acc.proceedsOut + curVal - acc.costIn;
      const preWinCostIn = acc.costIn - acc.windowCostIn;
      const preWinProceeds = acc.proceedsOut - acc.windowProceedsOut;
      const contributesToWindow = curVal > 0.01 || acc.windowCostIn > 0.01 || acc.windowProceedsOut > 0.01;
      const windowBasis = contributesToWindow ? Math.max(0, preWinCostIn - preWinProceeds) : 0;
      const pnl1y = proto === "Directional" ? 0 : acc.windowProceedsOut + curVal - acc.windowCostIn - windowBasis;

      localRows.push({
        protocol: proto, wallet,
        costIn: acc.costIn, proceedsOut: acc.proceedsOut, curVal, lifePnL,
        pnl1y, pnl1y_facebasis: pnl1y, flags: flags.join(","),
        windowCostIn: acc.windowCostIn, windowProceedsOut: acc.windowProceedsOut, windowBasis,
      });
    }

    // ── Time-apportion pnl1y per (wallet, proto) — linear-accrual on this wallet's rows ──
    for (const pr of localRows) {
      if (MISC_LIKE.has(pr.protocol)) continue;
      const acc = protoAccum.get(pr.protocol);
      if (!acc) continue;
      const receiptSymbols = new Set(acc.receiptTokens.keys());
      const receiptRows = wRows.filter((r) => receiptSymbols.has(r.symbol));
      const entryRows = receiptRows.filter((r) => r.direction === "in");
      const exitRows = receiptRows.filter((r) => r.direction === "out");
      if (entryRows.length === 0) continue;
      const firstEntryTs = Math.min(...entryRows.map((r) => r.ts));
      const lastExitTs = exitRows.length > 0 ? Math.max(...exitRows.map((r) => r.ts)) : null;
      const isClosed = pr.curVal < 1 && lastExitTs !== null;
      const endTs = isClosed ? lastExitTs! : NOW;
      const fraction = computeApportionFraction(firstEntryTs, endTs, windowTs, NOW);
      pr.pnl1y = pr.lifePnL * fraction;
    }

    // ── Misc reconciliation per wallet — standalone stable flows split into sub-buckets ──
    const misc = computeMiscFlows(wRows);
    if (misc.costIn > 0 || misc.proceedsOut > 0) {
      const pushMisc = (name: string, bucket: typeof misc.regular, flag: string) => {
        if (bucket.costIn > 0 || bucket.proceedsOut > 0) {
          const row = buildMiscRow(name, bucket, flag);
          row.wallet = wallet;
          localRows.push(row);
        }
      };
      pushMisc("Misc", misc.regular, "standalone-flows");
      pushMisc("Perps", misc.perps, "zklighter:perps-trading:excluded-from-yield");
      pushMisc("Bridge", misc.bridge, "lifi/stargate/woo:bridge-flows:excluded-from-yield");
      pushMisc("Unidentified", misc.unidentified, "0xa9d1e0:unverified-contract:excluded-from-yield");
      for (const [protoName, bucket] of misc.named) pushMisc(protoName, bucket, "misc-named-defi-yield");
    }

    protocolRows.push(...localRows);
  }

  const sumPnL = protocolRows.reduce((s, p) => s + p.lifePnL, 0);
  return { protocolRows, sumPnL, nowBlockMap, tokenValuations };
}

/**
 * aggregateSumWindowBasis — the cluster-wide window-start basis, computed from the
 * WHOLE-CLUSTER attribution accumulators (identical to what --cluster mode derives from
 * its merged protocol rows).
 *
 * Why this exists: windowBasis = max(0, preWinCostIn − preWinProceeds). The max(0,…) clamp
 * is non-linear, so summing windowBasis over per-(wallet,protocol) sub-positions does NOT
 * equal the aggregate windowBasis of the merged protocol. The trailing-1Y cluster boundary
 * (currentStable + wCapitalOut − (windowStartStable + wCapitalIn)) is an economic boundary
 * that must be invariant to how attribution is partitioned by wallet — so the per-LP path
 * must use THIS aggregate, exactly as --cluster does, rather than a per-wallet sum.
 *
 * curValByProto: aggregate current value per protocol (Σ over wallets), driving the
 * `contributesToWindow` flag exactly as the live cluster valuation does.
 */
export function aggregateSumWindowBasis(
  allRows: LedgerRow[],
  curValByProto: Map<string, number>,
): number {
  let sum = 0;
  // Receipt-token protocols (aggregate accumulators). Directional is excluded from basis.
  const acc = attributeProtocols(allRows);
  for (const [proto, a] of acc) {
    if (proto === "Directional") continue;
    const curVal = curValByProto.get(proto) ?? 0;
    const preWinCostIn = a.costIn - a.windowCostIn;
    const preWinProceeds = a.proceedsOut - a.windowProceedsOut;
    const contributesToWindow = curVal > 0.01 || a.windowCostIn > 0.01 || a.windowProceedsOut > 0.01;
    sum += contributesToWindow ? Math.max(0, preWinCostIn - preWinProceeds) : 0;
  }
  // Misc sub-buckets (curVal always 0) — same calcMiscWindowBasis used by buildMiscRow.
  const misc = computeMiscFlows(allRows);
  for (const m of [misc.regular, misc.perps, misc.bridge, misc.unidentified, ...misc.named.values()]) {
    sum += calcMiscWindowBasis(m);
  }
  return sum;
}

export interface ClusterPerLpResult {
  /** per-(wallet, protocol) rows PLUS one cluster-level "Unattributed / Idle" residual */
  protocolRows: ProtocolRow[];
  anchorLife: number;
  pnl1yAnchor: number;
  /** Σ row pnl1y_facebasis incl residual — equals pnl1yAnchor by construction */
  pnl1yFacebasis: number;
  /** Σ row pnl1y (apportioned headline) incl residual */
  pnl1yApportioned: number;
  windowStartStable: number;
  sumVaultCurVal: number;
  idleRpc: number;
  idleFlow: number;
  cf: CapitalFlows;
  /** Σ row lifePnL − anchorLife (must be ~0) */
  gap: number;
}

/**
 * computeClusterPerLpBoundary — full per-(wallet,LP) pipeline, testable without subprocess.
 *
 * The lifetime AND trailing-1Y anchors are the cluster-wide economic boundaries — computed
 * identically to --cluster mode (capital flows + idle RPC + aggregate windowBasis). The
 * per-(wallet,LP) rows attribute within that single boundary; one explicit cluster-level
 * "Unattributed / Idle" residual row closes any gap (idle stable, cross-wallet routing, the
 * windowBasis aggregation granularity, and RPC rounding) to $0.
 *
 * Applies the idle_rpc sanity guard (throws on divergence > max($500, 3%)).
 */
export async function computeClusterPerLpBoundary(
  rowsByWallet: Map<string, LedgerRow[]>,
  windowTs: number,
  opts?: BoundaryPnLOpts,
): Promise<ClusterPerLpResult> {
  const allRows = [...rowsByWallet.values()].flat();
  const wallets = [...rowsByWallet.keys()];

  const result = await computeClusterPerLp(rowsByWallet, windowTs, opts);

  // Vault-RPC sanity guard — BEFORE any anchor/number is derived. Catches a deployed vault
  // position silently valued $0 by a flaky RPC (the avUSDC bug); throws rather than emit a
  // silently-low anchor. (assertIdleRpcSanity below only covers idle stables, not vaults.)
  await assertVaultRpcSanity(result.tokenValuations, opts);

  const cf = computeClusterCapitalFlows(allRows, windowTs, OWNED_WALLETS);
  const idleFlow = idleStableFlowDerived(allRows, windowTs);

  let idleRpc = await computeIdleStableRpcMultiWallet(allRows, wallets, result.nowBlockMap, opts?.balanceProvider);
  if (Math.abs(idleRpc - idleFlow.now) > Math.max(500, Math.abs(idleFlow.now) * 0.03)) {
    const retry = await computeIdleStableRpcMultiWallet(allRows, wallets, result.nowBlockMap, opts?.balanceProvider);
    assertIdleRpcSanity(retry, idleFlow.now);
    idleRpc = retry;
  }

  const NO_CURVEVAL = new Set(["Directional", "Misc", "Perps", "Bridge", "Unidentified", "Unattributed", "Unattributed / Idle", ...NAMED_MISC_PROTOS.values()]);
  // Aggregate current value per protocol (Σ over wallets) — used for both sumVaultCurVal
  // and the contributesToWindow flag inside aggregateSumWindowBasis.
  const curValByProto = new Map<string, number>();
  for (const r of result.protocolRows) curValByProto.set(r.protocol, (curValByProto.get(r.protocol) ?? 0) + r.curVal);
  const sumVaultCurVal = result.protocolRows
    .filter((r) => !NO_CURVEVAL.has(r.protocol))
    .reduce((s, r) => s + r.curVal, 0);

  const currentStable = idleRpc + sumVaultCurVal;
  const anchorLife = currentStable + cf.capitalOut - cf.capitalIn;

  // Cluster-aggregate window-start basis (partition-invariant — matches --cluster exactly).
  const sumWindowBasis = aggregateSumWindowBasis(allRows, curValByProto);
  const windowStartStable = idleFlow.atStart + sumWindowBasis;
  const pnl1yAnchor = currentStable + cf.wCapitalOut - (windowStartStable + cf.wCapitalIn);

  // ── Single explicit cluster-level residual closes both lifetime and 1Y to the anchor ──
  const sumLife_pre = result.protocolRows.reduce((s, p) => s + p.lifePnL, 0);
  const lifeResidual = anchorLife - sumLife_pre;
  const sumFace_pre = result.protocolRows
    .filter((r) => r.protocol !== "Directional")
    .reduce((s, r) => s + r.pnl1y_facebasis, 0);
  const y1Residual = pnl1yAnchor - sumFace_pre;

  result.protocolRows.push({
    protocol: "Unattributed / Idle",
    costIn: 0, proceedsOut: 0, curVal: 0,
    lifePnL: lifeResidual, pnl1y: y1Residual, pnl1y_facebasis: y1Residual,
    flags: "cluster-level: idle stable + cross-wallet routing + windowBasis-aggregation + rpc rounding (not per-wallet)",
    windowCostIn: 0, windowProceedsOut: 0, windowBasis: 0,
  });

  const sumLife = result.protocolRows.reduce((s, p) => s + p.lifePnL, 0);
  const gap = sumLife - anchorLife;
  const pnl1yFacebasis = result.protocolRows
    .filter((r) => r.protocol !== "Directional")
    .reduce((s, r) => s + r.pnl1y_facebasis, 0);
  const pnl1yApportioned = result.protocolRows
    .filter((r) => r.protocol !== "Directional")
    .reduce((s, r) => s + r.pnl1y, 0);

  return {
    protocolRows: result.protocolRows, anchorLife, pnl1yAnchor, pnl1yFacebasis,
    pnl1yApportioned, windowStartStable, sumVaultCurVal, idleRpc, idleFlow: idleFlow.now, cf, gap,
  };
}

// ── Output formatting ──────────────────────────────────────────────────────────

function fmt(n: number, decimals = 0): string {
  const s = Math.abs(n).toFixed(decimals);
  const parts = s.split(".");
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  const formatted = parts.join(".");
  return (n < 0 ? "-$" : "+$") + formatted;
}

function fmtCost(n: number): string {
  const s = n.toFixed(0);
  return "$" + s.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function pad(s: string, w: number): string {
  return s.padEnd(w);
}

function rpad(s: string, w: number): string {
  return s.padStart(w);
}

function printTable(rows: ProtocolRow[]): void {
  const cols = {
    proto: 13,
    cost: 11,
    proc: 11,
    cur: 10,
    life: 10,
    y1fb: 13, // face-basis (upper bound)
    y1ap: 13, // apportioned (headline)
    flags: 12,
  };
  const header =
    pad("Protocol", cols.proto) + " | " +
    rpad("costIn", cols.cost) + " | " +
    rpad("proceeds", cols.proc) + " | " +
    rpad("curVal", cols.cur) + " | " +
    rpad("lifePnL", cols.life) + " | " +
    rpad("1Y facebasis", cols.y1fb) + " | " +
    rpad("1Y apportion", cols.y1ap) + " | " +
    "flags";
  const sep = "─".repeat(header.length);

  console.log("\n" + header);
  console.log(sep);

  let totCost = 0, totProc = 0, totCur = 0, totLife = 0, totY1fb = 0, totY1ap = 0;

  for (const r of rows.sort((a, b) => b.lifePnL - a.lifePnL)) {
    const line =
      pad(r.protocol, cols.proto) + " | " +
      rpad(fmtCost(r.costIn), cols.cost) + " | " +
      rpad(fmtCost(r.proceedsOut), cols.proc) + " | " +
      rpad(fmtCost(r.curVal), cols.cur) + " | " +
      rpad(fmt(r.lifePnL), cols.life) + " | " +
      rpad(fmt(r.pnl1y_facebasis), cols.y1fb) + " | " +
      rpad(fmt(r.pnl1y), cols.y1ap) + " | " +
      r.flags;
    console.log(line);
    totCost += r.costIn;
    totProc += r.proceedsOut;
    totCur += r.curVal;
    totLife += r.lifePnL;
    totY1fb += r.pnl1y_facebasis;
    totY1ap += r.pnl1y;
  }

  console.log(sep);
  const total =
    pad("TOTAL", cols.proto) + " | " +
    rpad(fmtCost(totCost), cols.cost) + " | " +
    rpad(fmtCost(totProc), cols.proc) + " | " +
    rpad(fmtCost(totCur), cols.cur) + " | " +
    rpad(fmt(totLife), cols.life) + " | " +
    rpad(fmt(totY1fb), cols.y1fb) + " | " +
    rpad(fmt(totY1ap), cols.y1ap) + " | ";
  console.log(total);
}

/**
 * printPerLpTable — per-(wallet, protocol/LP) table.
 * Columns: Wallet (short=addr) | Protocol/LP | Lifetime PnL | Trailing-1Y PnL.
 * Sorted by wallet (in clusterWallets order), then by |pnl1y| descending.
 * The single cluster-level "Unattributed / Idle" residual (wallet undefined) is
 * printed last in its own section.
 */
function printPerLpTable(rows: ProtocolRow[], walletShort: Map<string, string>): void {
  const cols = { wallet: 22, proto: 14, life: 14, y1: 14 };
  const header =
    pad("Wallet", cols.wallet) + " | " +
    pad("Protocol/LP", cols.proto) + " | " +
    rpad("Lifetime PnL", cols.life) + " | " +
    rpad("Trailing-1Y PnL", cols.y1) + " | flags";
  const sep = "─".repeat(header.length);
  console.log("\n" + header);
  console.log(sep);

  const walletOrder = [...walletShort.keys()];
  const perWallet = rows.filter((r) => r.wallet !== undefined);
  perWallet.sort((a, b) => {
    const wa = walletOrder.indexOf(a.wallet!);
    const wb = walletOrder.indexOf(b.wallet!);
    if (wa !== wb) return wa - wb;
    return Math.abs(b.pnl1y) - Math.abs(a.pnl1y);
  });

  let lastWallet = "";
  for (const r of perWallet) {
    if (r.wallet !== lastWallet && lastWallet !== "") console.log(sep);
    lastWallet = r.wallet!;
    const short = walletShort.get(r.wallet!) ?? "?";
    const label = `${short}=${r.wallet!.slice(0, 10)}…`;
    console.log(
      pad(label, cols.wallet) + " | " +
      pad(r.protocol, cols.proto) + " | " +
      rpad(fmt(r.lifePnL), cols.life) + " | " +
      rpad(fmt(r.pnl1y), cols.y1) + " | " + r.flags,
    );
  }

  // Cluster-level residual (no owning wallet)
  const residual = rows.filter((r) => r.wallet === undefined);
  if (residual.length > 0) {
    console.log(sep);
    for (const r of residual) {
      console.log(
        pad("CLUSTER (all)", cols.wallet) + " | " +
        pad(r.protocol, cols.proto) + " | " +
        rpad(fmt(r.lifePnL), cols.life) + " | " +
        rpad(fmt(r.pnl1y), cols.y1) + " | " + r.flags,
      );
    }
  }

  console.log(sep);
  const totLife = rows.reduce((s, r) => s + r.lifePnL, 0);
  const totY1 = rows.filter((r) => r.protocol !== "Directional").reduce((s, r) => s + r.pnl1y, 0);
  console.log(
    pad("TOTAL", cols.wallet) + " | " +
    pad("", cols.proto) + " | " +
    rpad(fmt(totLife), cols.life) + " | " +
    rpad(fmt(totY1), cols.y1) + " |",
  );
}

/**
 * computeBoundaryPnL — full per-wallet pipeline, testable without subprocess.
 *
 * If opts.balanceProvider is provided, all balanceOf/RPC calls use it (offline-safe).
 * If opts.nowBlockMap is provided, llamaBlock() calls are skipped.
 *
 * Applies idle_rpc sanity guard: divergence from idle_flow > max($500, 3%) throws.
 */
export async function computeBoundaryPnL(
  rows: LedgerRow[],
  wallet: string,
  windowTs: number,
  opts?: BoundaryPnLOpts,
): Promise<BoundaryOutput> {
  const result = await compute(rows, wallet, windowTs, opts);
  const cf = computeCapitalFlows(rows, windowTs);
  const idleFlow = idleStableFlowDerived(rows, windowTs);

  // First attempt at idle_rpc
  let idleRpc = await computeIdleStableRpc(rows, wallet.toLowerCase(), result.nowBlockMap, opts?.balanceProvider);

  // Sanity guard with one retry pass before throwing
  const tolerance = Math.max(500, Math.abs(idleFlow.now) * 0.03);
  if (Math.abs(idleRpc - idleFlow.now) > tolerance) {
    // Retry all stable balances once before declaring failure
    idleRpc = await computeIdleStableRpc(rows, wallet.toLowerCase(), result.nowBlockMap, opts?.balanceProvider);
    assertIdleRpcSanity(idleRpc, idleFlow.now);
  }

  // Held-position warning: protocols with open ledger positions but zero curVal
  for (const pr of result.protocolRows) {
    if (pr.curVal === 0 && pr.lifePnL < -100 && !["Misc", "Perps", "Bridge", "Unidentified", "Directional", "Unattributed", ...NAMED_MISC_PROTOS.values()].includes(pr.protocol)) {
      console.warn(`  [WARN] ${pr.protocol}: ledger shows open position (lifePnL=$${pr.lifePnL.toFixed(2)}) but curVal=$0 — possible RPC balance read failure`);
    }
  }

  const NO_CURVEVAL = new Set(["Directional", "Misc", "Perps", "Bridge", "Unidentified", "Unattributed", ...NAMED_MISC_PROTOS.values()]);
  const sumVaultCurVal = result.protocolRows.filter((r) => !NO_CURVEVAL.has(r.protocol)).reduce((s, r) => s + r.curVal, 0);
  const directionalCurVal = result.protocolRows.find((r) => r.protocol === "Directional")?.curVal ?? 0;
  const currentValueTotal = idleRpc + sumVaultCurVal + directionalCurVal;
  const anchorComputed = currentValueTotal + cf.capitalOut - cf.capitalIn;

  const sumWindowBasis = result.protocolRows.filter((r) => r.protocol !== "Directional" && r.protocol !== "Unattributed").reduce((s, r) => s + r.windowBasis, 0);
  const windowStartStable = idleFlow.atStart + sumWindowBasis;
  const currentStable = idleRpc + sumVaultCurVal;
  const pnl1yAnchor = currentStable + cf.wCapitalOut - (windowStartStable + cf.wCapitalIn);

  const sumPnL_preResidual = result.protocolRows.reduce((s, p) => s + p.lifePnL, 0);
  const lifeResidual = anchorComputed - sumPnL_preResidual;
  const sumFaceBasis_preResidual = result.protocolRows.filter((r) => r.protocol !== "Directional").reduce((s, r) => s + r.pnl1y_facebasis, 0);
  const y1Residual = pnl1yAnchor - sumFaceBasis_preResidual;

  if (Math.abs(lifeResidual) > 0.01 || Math.abs(y1Residual) > 0.01) {
    result.protocolRows.push({
      protocol: "Unattributed", costIn: 0, proceedsOut: 0, curVal: 0,
      lifePnL: lifeResidual, pnl1y: y1Residual, pnl1y_facebasis: y1Residual,
      flags: "rpc-rounding-residual", windowCostIn: 0, windowProceedsOut: 0, windowBasis: 0,
    });
  }

  const sumPnL = result.protocolRows.reduce((s, p) => s + p.lifePnL, 0);
  const delta = sumPnL - anchorComputed;
  const pnl1yAttrib = result.protocolRows.filter((r) => r.protocol !== "Directional").reduce((s, r) => s + r.pnl1y_facebasis, 0);
  const pnl1yApportioned = result.protocolRows.filter((r) => r.protocol !== "Directional").reduce((s, r) => s + r.pnl1y, 0);
  const delta1y = pnl1yAttrib - pnl1yAnchor;

  return {
    anchor: anchorComputed,
    delta_vs_anchor: delta,
    protocols: result.protocolRows,
    trailing_1y: {
      window_start_value: windowStartStable,
      pnl_1y: pnl1yApportioned,
      pnl_1y_facebasis: pnl1yAttrib,
      pnl_1y_anchor: pnl1yAnchor,
      delta_1y: delta1y,
    },
    idle_rpc: idleRpc,
    idle_flow: idleFlow.now,
  };
}

// ── main() ────────────────────────────────────────────────────────────────────

async function main() {
  const argv = process.argv.slice(2);
  const windowArg = argv.includes("--window") ? argv[argv.indexOf("--window") + 1] : "1y";
  const outPath = argv.includes("--out") ? argv[argv.indexOf("--out") + 1] : undefined;
  const windowTs = windowArg === "1y" ? WINDOW_1Y_TS : WINDOW_1Y_TS; // only 1y supported here
  const isCluster = argv.includes("--cluster");
  const isPerLp = argv.includes("--per-lp");

  // ── Per-wallet per-LP cluster mode ──────────────────────────────────────────────
  // Same cluster boundary anchor as --cluster, but attribution is keyed by
  // (owning-wallet, protocol/LP). One explicit cluster-level "Unattributed / Idle"
  // residual row closes conservation to $0.
  if (isPerLp) {
    const ledgerPaths: string[] = [];
    const seenPaths = new Set<string>();
    for (let i = 0; i < argv.length; i++) {
      const a = argv[i];
      if (a === "--cluster" || a === "--per-lp") continue;
      if (a === "--window" || a === "--out") { i++; continue; }
      if (a.startsWith("--")) continue;
      if (!seenPaths.has(a)) { seenPaths.add(a); ledgerPaths.push(a); }
    }
    if (ledgerPaths.length === 0) {
      console.error("per-lp mode requires at least one ledger path");
      process.exit(1);
    }

    // Partition rows by owning wallet (the source ledger's `wallet` field).
    const rowsByWallet = new Map<string, LedgerRow[]>();
    const walletShort = new Map<string, string>();
    const wallets: string[] = [];
    for (const p of ledgerPaths) {
      const raw = JSON.parse(require("fs").readFileSync(p, "utf8"));
      const rows: LedgerRow[] = raw.rows ?? raw;
      const w = ((raw.wallet as string | undefined) ?? "").toLowerCase();
      if (!w) { console.error(`ledger ${p} has no wallet field`); process.exit(1); }
      if (!rowsByWallet.has(w)) { rowsByWallet.set(w, []); wallets.push(w); }
      rowsByWallet.get(w)!.push(...rows);
      // Short label from ledger filename prefix (e.g. /tmp/B5_ledger.json → "B5").
      const base = p.split("/").pop() ?? p;
      walletShort.set(w, base.split("_")[0] || w.slice(0, 6));
    }

    console.log(`\nCluster Per-LP Boundary PnL — window=${windowArg} — NOW=${NOW} windowStart=${windowTs}`);
    console.log(`Cluster wallets (${wallets.length}):`);
    for (const w of wallets) console.log(`  ${walletShort.get(w)} = ${w}`);
    console.log("=".repeat(78));

    // Boundary is the cluster-wide economic anchor (lifetime + 1Y), computed identically to
    // --cluster mode; per-(wallet,LP) rows attribute within it, with ONE explicit
    // cluster-level "Unattributed / Idle" residual closing any gap to $0.
    const r = await computeClusterPerLpBoundary(rowsByWallet, windowTs);

    printPerLpTable(r.protocolRows, walletShort);

    console.log(`\nCluster capital flows (external boundary only):`);
    console.log(`  capitalIn  (lifetime): $${r.cf.capitalIn.toFixed(2)}   capitalOut: $${r.cf.capitalOut.toFixed(2)}`);

    console.log(`\nConservation (lifetime):`);
    console.log(`  Σ rows (incl Unattributed/Idle): ${fmt(r.protocolRows.reduce((s, p) => s + p.lifePnL, 0))}`);
    console.log(`  cluster anchor:                  ${fmt(r.anchorLife)}`);
    console.log(`  gap:                             $${r.gap.toFixed(2)}  (must be 0.00)`);

    console.log(`\nRPC sanity guard:`);
    console.log(`  idle_rpc  (sum across ${wallets.length} wallets): $${r.idleRpc.toFixed(2)}`);
    console.log(`  idle_flow (ledger-net):              $${r.idleFlow.toFixed(2)}`);
    console.log(`  |rpc − flow|: $${Math.abs(r.idleRpc - r.idleFlow).toFixed(2)}  → PASS`);

    console.log(`\nTrailing 1Y (Directional EXCLUDED):`);
    console.log(`  pnl_1y facebasis (= cluster 1Y anchor): ${fmt(r.pnl1yFacebasis)}`);
    console.log(`  pnl_1y apportioned (headline):          ${fmt(r.pnl1yApportioned)}`);
    console.log(`  pnl_1y anchor:                          ${fmt(r.pnl1yAnchor)}`);

    const output: BoundaryOutput = {
      anchor: r.anchorLife,
      delta_vs_anchor: r.gap,
      protocols: r.protocolRows,
      trailing_1y: {
        window_start_value: r.windowStartStable,
        pnl_1y: r.pnl1yApportioned,
        pnl_1y_facebasis: r.pnl1yFacebasis,
        pnl_1y_anchor: r.pnl1yAnchor,
        delta_1y: r.pnl1yFacebasis - r.pnl1yAnchor,
      },
      idle_rpc: r.idleRpc,
      idle_flow: r.idleFlow,
      cluster_wallets: wallets,
    };

    if (outPath) {
      require("fs").writeFileSync(outPath, JSON.stringify(output, null, 2));
      console.log(`\nWrote output → ${outPath}`);
    } else {
      console.log("\nJSON output:");
      console.log(JSON.stringify(output, null, 2));
    }
    return;
  }

  // ── Cluster mode ──────────────────────────────────────────────────────────────
  if (isCluster) {
    // Collect all non-flag, non-flag-value args as ledger paths
    const ledgerPaths: string[] = [];
    const seenPaths = new Set<string>();
    for (let i = 0; i < argv.length; i++) {
      const a = argv[i];
      if (a === "--cluster") continue;
      if (a === "--window" || a === "--out") { i++; continue; }
      if (a.startsWith("--")) continue;
      if (!seenPaths.has(a)) { seenPaths.add(a); ledgerPaths.push(a); }
    }

    if (ledgerPaths.length === 0) {
      console.error("cluster mode requires at least one ledger path");
      process.exit(1);
    }

    const allRows: LedgerRow[] = [];
    const wallets: string[] = [];
    // tokenOwners: `${chain}:${tokenAddr}` → wallets whose ledger references that receipt token,
    // so computeCluster values each token only where it lives (not × all wallets).
    const tokenOwners = new Map<string, Set<string>>();
    for (const p of ledgerPaths) {
      const raw = JSON.parse(require("fs").readFileSync(p, "utf8"));
      const rows: LedgerRow[] = raw.rows ?? raw;
      const w = ((raw.wallet as string | undefined) ?? "").toLowerCase();
      if (w && !wallets.includes(w)) wallets.push(w);
      for (const r of rows) {
        if (r.tokenAddr == null) continue;
        const key = `${r.chain}:${r.tokenAddr.toLowerCase()}`;
        (tokenOwners.get(key) ?? tokenOwners.set(key, new Set()).get(key)!).add(w);
      }
      allRows.push(...rows);
    }

    console.log(`\nCluster Boundary PnL — window=${windowArg} — NOW=${NOW} windowStart=${windowTs}`);
    console.log(`Cluster wallets (${wallets.length}):`);
    for (const w of wallets) console.log(`  ${w}`);
    console.log("=".repeat(78));

    const result = await computeCluster(allRows, wallets, windowTs, undefined, tokenOwners);

    // Vault-RPC sanity guard — BEFORE any anchor/number. Refuses to emit a silently-low anchor
    // when a deployed vault (e.g. avUSDC) was zeroed by a flaky RPC. (Same guard as --per-lp.)
    await assertVaultRpcSanity(result.tokenValuations);

    const cf = computeClusterCapitalFlows(allRows, windowTs, OWNED_WALLETS);
    const idleFlow = idleStableFlowDerived(allRows, windowTs);
    let idleRpc = await computeIdleStableRpcMultiWallet(allRows, wallets, result.nowBlockMap);
    // Sanity guard with one retry before throwing
    if (Math.abs(idleRpc - idleFlow.now) > Math.max(500, Math.abs(idleFlow.now) * 0.03)) {
      const idleRpcRetry = await computeIdleStableRpcMultiWallet(allRows, wallets, result.nowBlockMap);
      assertIdleRpcSanity(idleRpcRetry, idleFlow.now);
      idleRpc = idleRpcRetry;
    }

    const NO_CURVEVAL = new Set(["Directional", "Misc", "Perps", "Bridge", "Unidentified", "Unattributed", ...NAMED_MISC_PROTOS.values()]);
    const sumVaultCurVal = result.protocolRows
      .filter((r) => !NO_CURVEVAL.has(r.protocol))
      .reduce((s, r) => s + r.curVal, 0);
    const directionalCurVal =
      result.protocolRows.find((r) => r.protocol === "Directional")?.curVal ?? 0;
    const currentValueTotal = idleRpc + sumVaultCurVal + directionalCurVal;
    const anchorComputed = currentValueTotal + cf.capitalOut - cf.capitalIn;

    const sumWindowBasis = result.protocolRows
      .filter((r) => r.protocol !== "Directional" && r.protocol !== "Unattributed")
      .reduce((s, r) => s + r.windowBasis, 0);
    const windowStartStable = idleFlow.atStart + sumWindowBasis;
    const currentStable = idleRpc + sumVaultCurVal;
    const pnl1yAnchor = currentStable + cf.wCapitalOut - (windowStartStable + cf.wCapitalIn);

    const sumPnL_preResidual = result.protocolRows.reduce((s, p) => s + p.lifePnL, 0);
    const lifeResidual = anchorComputed - sumPnL_preResidual;
    const sumFaceBasis_preResidual = result.protocolRows
      .filter((r) => r.protocol !== "Directional")
      .reduce((s, r) => s + r.pnl1y_facebasis, 0);
    const y1Residual = pnl1yAnchor - sumFaceBasis_preResidual;

    if (Math.abs(lifeResidual) > 0.01 || Math.abs(y1Residual) > 0.01) {
      result.protocolRows.push({
        protocol: "Unattributed",
        costIn: 0, proceedsOut: 0, curVal: 0,
        lifePnL: lifeResidual,
        pnl1y: y1Residual,
        pnl1y_facebasis: y1Residual,
        flags: "cluster-residual",
        windowCostIn: 0, windowProceedsOut: 0, windowBasis: 0,
      });
    }

    printTable(result.protocolRows);

    const sumPnL = result.protocolRows.reduce((s, p) => s + p.lifePnL, 0);
    const delta = sumPnL - anchorComputed;
    const pnl1yAttrib = result.protocolRows
      .filter((r) => r.protocol !== "Directional")
      .reduce((s, r) => s + r.pnl1y_facebasis, 0);
    const pnl1yApportioned = result.protocolRows
      .filter((r) => r.protocol !== "Directional")
      .reduce((s, r) => s + r.pnl1y, 0);
    const delta1y = pnl1yAttrib - pnl1yAnchor;

    console.log(`\nCluster capital flows (external boundary only):`);
    console.log(`  externalIn  (non-owned EOA inflows):  $${cf.cexIn.toFixed(2)}`);
    console.log(`  externalOut (bridge + non-owned EOA): $${cf.bridgeOut.toFixed(2)}`);
    console.log(`  capitalIn  (lifetime):                $${cf.capitalIn.toFixed(2)}`);
    console.log(`  capitalOut (lifetime):                $${cf.capitalOut.toFixed(2)}`);

    console.log(`\nIdle stable cross-check (cluster):`);
    console.log(`  idleRpc (sum across ${wallets.length} wallets): $${idleRpc.toFixed(2)}`);
    console.log(`  idleFlow (ledger-net, inter-wallet cancels): $${idleFlow.now.toFixed(2)}`);
    console.log(`  |rpc − flow|: $${Math.abs(idleRpc - idleFlow.now).toFixed(2)}`);

    console.log(`\nLifetime conservation (cluster):`);
    console.log(`  sumVaultCurVal:    $${sumVaultCurVal.toFixed(2)}`);
    console.log(`  directionalCurVal: $${directionalCurVal.toFixed(2)}`);
    console.log(`  currentValueTotal: $${currentValueTotal.toFixed(2)}`);
    console.log(`  anchorComputed:    $${anchorComputed.toFixed(2)}`);
    console.log(`  sumPnL (attrib):   ${fmt(sumPnL)}  (includes Unattributed row)`);
    console.log(`  Δ vs anchor:       ${fmt(delta)}  (should be ≈$0 after residual)`);

    console.log(`\nTrailing 1Y (cluster, stable protocols, Directional EXCLUDED):`);
    console.log(`  window capital in:  $${cf.wCapitalIn.toFixed(2)}`);
    console.log(`  window capital out: $${cf.wCapitalOut.toFixed(2)}`);
    console.log(`  window_start_value: $${windowStartStable.toFixed(2)}`);
    console.log(`  current_stable:     $${currentStable.toFixed(2)}`);
    console.log(`  pnl_1y facebasis:   ${fmt(pnl1yAttrib)}  (upper bound)`);
    console.log(`  pnl_1y apportioned: ${fmt(pnl1yApportioned)}  (headline — linear-accrual)`);
    console.log(`  pnl_1y (anchor):    ${fmt(pnl1yAnchor)}`);
    console.log(`  delta_1y:           ${fmt(delta1y)}  (should be ≈$0 after residual)`);

    const output: BoundaryOutput = {
      anchor: anchorComputed,
      delta_vs_anchor: delta,
      protocols: result.protocolRows,
      trailing_1y: {
        window_start_value: windowStartStable,
        pnl_1y: pnl1yApportioned,
        pnl_1y_facebasis: pnl1yAttrib,
        pnl_1y_anchor: pnl1yAnchor,
        delta_1y: delta1y,
      },
      idle_rpc: idleRpc,
      idle_flow: idleFlow.now,
      cluster_wallets: wallets,
    };

    if (outPath) {
      require("fs").writeFileSync(outPath, JSON.stringify(output, null, 2));
      console.log(`\nWrote output → ${outPath}`);
    } else {
      console.log("\nJSON output:");
      console.log(JSON.stringify(output, null, 2));
    }
    return;
  }

  // ── Per-wallet mode (original) ────────────────────────────────────────────────
  if (!argv[0] || argv[0].startsWith("--")) {
    console.error("usage: bun boundary_pnl.ts <ledger.json> [--window 1y] [--out file]");
    console.error("       bun boundary_pnl.ts --cluster <l1.json> <l2.json> ... [--window 1y] [--out file]");
    process.exit(1);
  }

  const ledgerPath = argv[0];

  // Load ledger
  const raw = JSON.parse(require("fs").readFileSync(ledgerPath, "utf8"));
  const rows: LedgerRow[] = raw.rows ?? raw;

  // Read wallet from ledger's top-level "wallet" field; fall back to known active wallet.
  const wallet: string = (
    (raw.wallet as string | undefined) ?? "0x5d039ece117073323ade5057a516864f4c40e653"
  ).toLowerCase();

  console.log(`\nBoundary PnL — window=${windowArg} — NOW=${NOW} windowStart=${windowTs}`);
  console.log("=".repeat(78));

  const result = await compute(rows, wallet, windowTs);

  // ── Capital flows — computed from ledger (replaces hardcoded LIFETIME_CAPITAL / WINDOW_CAPITAL)
  const cf = computeCapitalFlows(rows, windowTs);

  // ── Idle stable: RPC (independent) vs flow-derived (ledger)
  const idleFlow = idleStableFlowDerived(rows, windowTs);
  let idleRpc = await computeIdleStableRpc(rows, wallet, result.nowBlockMap);
  // Sanity guard with one retry before throwing
  if (Math.abs(idleRpc - idleFlow.now) > Math.max(500, Math.abs(idleFlow.now) * 0.03)) {
    const idleRpcRetry = await computeIdleStableRpc(rows, wallet, result.nowBlockMap);
    assertIdleRpcSanity(idleRpcRetry, idleFlow.now);
    idleRpc = idleRpcRetry;
  }

  // ── Lifetime conservation anchor (independent cash-flow path)
  //   current_value_total = idleRpc + Σ vault curVal + directional curVal
  // Misc/Perps/Bridge/Unidentified all have curVal=0; filter is explicit for safety.
  const NO_CURVEVAL_SINGLE = new Set(["Directional", "Misc", "Perps", "Bridge", "Unidentified", "Unattributed", ...NAMED_MISC_PROTOS.values()]);
  const sumVaultCurVal = result.protocolRows
    .filter((r) => !NO_CURVEVAL_SINGLE.has(r.protocol))
    .reduce((s, r) => s + r.curVal, 0);
  const directionalCurVal =
    result.protocolRows.find((r) => r.protocol === "Directional")?.curVal ?? 0;
  const currentValueTotal = idleRpc + sumVaultCurVal + directionalCurVal;
  const anchorComputed = currentValueTotal + cf.capitalOut - cf.capitalIn;

  // ── Trailing 1Y anchor (computed before residual so window basis excludes Unattributed)
  const sumWindowBasis = result.protocolRows
    .filter((r) => r.protocol !== "Directional" && r.protocol !== "Unattributed")
    .reduce((s, r) => s + r.windowBasis, 0);
  const windowStartStable = idleFlow.atStart + sumWindowBasis;
  const currentStable = idleRpc + sumVaultCurVal;
  // Independent 1Y anchor:
  //   pnl_1y_anchor = (current_stable + wCapitalOut) - (window_start_stable + wCapitalIn)
  const pnl1yAnchor =
    currentStable + cf.wCapitalOut - (windowStartStable + cf.wCapitalIn);

  // ── Reconciliation: make attribution self-reconciling by adding an explicit "Unattributed"
  // row that closes the gap between ledger-flow attribution and the RPC-anchored value.
  // The gap originates from rounding differences between on-chain RPC balance and ledger-flow
  // derived balance (idleRpc vs idleFlow.now).  Making it explicit (named row) means the printed
  // table total always equals the anchor — no silent hidden bucket.
  const sumPnL_preResidual = result.protocolRows.reduce((s, p) => s + p.lifePnL, 0);
  const lifeResidual = anchorComputed - sumPnL_preResidual;

  const sumFaceBasis_preResidual = result.protocolRows
    .filter((r) => r.protocol !== "Directional")
    .reduce((s, r) => s + r.pnl1y_facebasis, 0);
  const y1Residual = pnl1yAnchor - sumFaceBasis_preResidual;

  if (Math.abs(lifeResidual) > 0.01 || Math.abs(y1Residual) > 0.01) {
    result.protocolRows.push({
      protocol: "Unattributed",
      costIn: 0,
      proceedsOut: 0,
      curVal: 0,
      lifePnL: lifeResidual,
      pnl1y: y1Residual,          // unknown timing → no apportionment discount
      pnl1y_facebasis: y1Residual,
      flags: "rpc-rounding-residual",
      windowCostIn: 0,
      windowProceedsOut: 0,
      windowBasis: 0,
    });
  }

  // ── Print table (now with Unattributed row if residual was significant)
  printTable(result.protocolRows);

  // Recompute sums after residual row — these should now satisfy Σ rows ≈ anchor
  const sumPnL = result.protocolRows.reduce((s, p) => s + p.lifePnL, 0);
  const delta = sumPnL - anchorComputed;

  // face-basis (upper bound, used for conservation delta_1y; should now ≈ pnl1yAnchor)
  const pnl1yAttrib = result.protocolRows
    .filter((r) => r.protocol !== "Directional")
    .reduce((s, r) => s + r.pnl1y_facebasis, 0);

  // apportioned headline (time-weighted linear-accrual model)
  const pnl1yApportioned = result.protocolRows
    .filter((r) => r.protocol !== "Directional")
    .reduce((s, r) => s + r.pnl1y, 0);

  const delta1y = pnl1yAttrib - pnl1yAnchor;

  const directional1y = result.protocolRows.find((r) => r.protocol === "Directional")?.lifePnL ?? 0;

  console.log(`\nCapital flows (ledger-derived):`);
  console.log(`  cexIn:    $${cf.cexIn.toFixed(2)}  ownedIn: $${cf.ownedIn.toFixed(2)}`);
  console.log(`  ownedOut: $${cf.ownedOut.toFixed(2)}  bridgeOut: $${cf.bridgeOut.toFixed(2)}`);
  console.log(`  capitalIn (lifetime): $${cf.capitalIn.toFixed(2)}  capitalOut: $${cf.capitalOut.toFixed(2)}`);

  console.log(`\nIdle stable cross-check:`);
  console.log(`  idleRpc (on-chain):      $${idleRpc.toFixed(2)}`);
  console.log(`  idleFlow (ledger-net):   $${idleFlow.now.toFixed(2)}`);
  console.log(`  |rpc − flow|:            $${Math.abs(idleRpc - idleFlow.now).toFixed(2)}`);

  console.log(`\nLifetime conservation:`);
  console.log(`  sumVaultCurVal:          $${sumVaultCurVal.toFixed(2)}`);
  console.log(`  directionalCurVal:       $${directionalCurVal.toFixed(2)}`);
  console.log(`  currentValueTotal:       $${currentValueTotal.toFixed(2)}`);
  console.log(`  anchorComputed:          $${anchorComputed.toFixed(2)}`);
  console.log(`  sumPnL (attribution):    ${fmt(sumPnL)}  (includes Unattributed row)`);
  console.log(`  Δ vs anchor:             ${fmt(delta)}  (should be ≈$0 after residual)`);

  console.log(`\nTrailing 1Y (stable protocols, Directional EXCLUDED):`);
  console.log(`  window capital in:       $${cf.wCapitalIn.toFixed(2)}`);
  console.log(`  window capital out:      $${cf.wCapitalOut.toFixed(2)}`);
  console.log(`  window_start_value:      $${windowStartStable.toFixed(2)}`);
  console.log(`  current_stable:          $${currentStable.toFixed(2)}`);
  console.log(`  pnl_1y facebasis:        ${fmt(pnl1yAttrib)}  (upper bound; ≈ anchor after residual)`);
  console.log(`  pnl_1y apportioned:      ${fmt(pnl1yApportioned)}  (headline — linear-accrual model)`);
  console.log(`  pnl_1y (anchor):         ${fmt(pnl1yAnchor)}`);
  console.log(`  delta_1y (face vs anch): ${fmt(delta1y)}  (should be ≈$0 after residual)`);
  console.log(`  Directional (EXCLUDED):  ${fmt(directional1y)} lifetime`);

  // JSON output
  const output: BoundaryOutput = {
    anchor: anchorComputed,
    delta_vs_anchor: delta,
    protocols: result.protocolRows,
    trailing_1y: {
      window_start_value: windowStartStable,
      pnl_1y: pnl1yApportioned,         // headline: apportioned
      pnl_1y_facebasis: pnl1yAttrib,    // upper bound: face-basis (≈ anchor after residual)
      pnl_1y_anchor: pnl1yAnchor,
      delta_1y: delta1y,                 // face-basis vs anchor (should be ≈0 after residual)
    },
    idle_rpc: idleRpc,
    idle_flow: idleFlow.now,
  };

  if (outPath) {
    require("fs").writeFileSync(outPath, JSON.stringify(output, null, 2));
    console.log(`\nWrote output → ${outPath}`);
  } else {
    console.log("\nJSON output:");
    console.log(JSON.stringify(output, null, 2));
  }
}

if (import.meta.main) main();
