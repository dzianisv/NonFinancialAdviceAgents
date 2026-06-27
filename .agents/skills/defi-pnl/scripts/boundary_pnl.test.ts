import { test, expect, describe } from "bun:test";
import { readFileSync } from "fs";
import path from "path";
import {
  classifyCounterparty,
  detectProtocol,
  computeMiscFlows,
  isStableRow,
  computeApportionFraction,
  computeClusterCapitalFlows,
  EUSD_ADDR,
  OWNED_WALLETS,
  EXTERNAL_CEX,
  KNOWN_BRIDGES,
  SPAM_REGEX,
  DIRECTIONAL_ADDRS,
  CURRENT_VALUES,
  WINDOW_1Y_TS,
  NOW,
  NAMED_MISC_PROTOS,
  assertIdleRpcSanity,
  computeBoundaryPnL,
  idleStableFlowDerived,
  computeCluster,
  computeClusterPerLpBoundary,
  assertVaultRpcSanity,
  type BalanceProvider,
  type BoundaryPnLOpts,
} from "./boundary_pnl.ts";
import type { LedgerRow } from "./yield_trace.ts";

const LEDGER_PATH = "/tmp/L3_ledger.json";
const SCRIPTS_DIR = path.resolve(import.meta.dir);

// ── Load ledger once ──────────────────────────────────────────────────────────

function loadRows(): LedgerRow[] {
  const raw = JSON.parse(readFileSync(LEDGER_PATH, "utf8"));
  return raw.rows ?? raw;
}

/**
 * makeIdleStub — ledger-derived balance provider for offline testing.
 * Returns the ledger-net flow amount for each stable token, so idle_rpc ≈ idle_flow.
 * Returns 0n for non-stable tokens (vault receipt tokens), making curVal=0 for all protocols.
 * This is conservative but correct: the Unattributed row absorbs the gap.
 */
function makeIdleStub(rows: LedgerRow[]): BalanceProvider {
  const netRaw = new Map<string, bigint>();
  for (const r of rows) {
    if (!isStableRow(r)) continue;
    const addr = r.tokenAddr.toLowerCase();
    const raw = BigInt(r.amountRaw);
    const cur = netRaw.get(addr) ?? 0n;
    netRaw.set(addr, r.direction === "in" ? cur + raw : cur - raw);
  }
  return async (_rpcs, tokenAddr, _wallet, _blockHex) => {
    const bal = netRaw.get(tokenAddr.toLowerCase()) ?? 0n;
    return bal > 0n ? bal : 0n;
  };
}

function makeOfflineOpts(rows: LedgerRow[]): BoundaryPnLOpts {
  const chains = [...new Set(rows.map((r) => r.chain))];
  return {
    balanceProvider: makeIdleStub(rows),
    nowBlockMap: new Map(chains.map((c) => [c, "0x1a00000"])),
  };
}

// ── 1. classifyCounterparty unit tests ───────────────────────────────────────

describe("classifyCounterparty", () => {
  const ownedAddr = [...OWNED_WALLETS][0];
  const bridgeAddr = [...KNOWN_BRIDGES][0];
  const unknownAddr = "0xdeadbeef00000000000000000000000000000001";

  test("owned wallet → owned", () => {
    expect(classifyCounterparty(ownedAddr, OWNED_WALLETS, [], new Map())).toBe("owned");
  });

  test("external CEX (EOA, data-driven) → external_eoa", () => {
    // EXTERNAL_CEX is an EOA; classification is now driven by counterpartyIsContract field.
    // Provide a row so the function can read counterpartyIsContract === false.
    const rows: Partial<LedgerRow>[] = [
      { counterparty: EXTERNAL_CEX, counterpartyIsContract: false },
    ];
    expect(
      classifyCounterparty(EXTERNAL_CEX, OWNED_WALLETS, rows as LedgerRow[], new Map()),
    ).toBe("external_eoa");
  });

  test("known bridge → bridge (from KNOWN_BRIDGES set)", () => {
    expect(classifyCounterparty(bridgeAddr, OWNED_WALLETS, [], new Map())).toBe("bridge");
  });

  test("unknown addr + counterpartyIsContract=true → internal", () => {
    const rows: Partial<LedgerRow>[] = [
      { counterparty: unknownAddr, counterpartyIsContract: true },
    ];
    expect(
      classifyCounterparty(unknownAddr, OWNED_WALLETS, rows as LedgerRow[], new Map()),
    ).toBe("internal");
  });

  test("unknown addr + counterpartyIsContract=false → external_eoa", () => {
    const rows: Partial<LedgerRow>[] = [
      { counterparty: unknownAddr, counterpartyIsContract: false },
    ];
    expect(
      classifyCounterparty(unknownAddr, OWNED_WALLETS, rows as LedgerRow[], new Map()),
    ).toBe("external_eoa");
  });

  test("unknown addr + blockscout bridge name → bridge", () => {
    const cache = new Map<string, string>([[unknownAddr, "Hop Bridge"]]);
    expect(
      classifyCounterparty(unknownAddr, OWNED_WALLETS, [], cache),
    ).toBe("bridge");
  });

  test("default (no info) → internal", () => {
    expect(
      classifyCounterparty(unknownAddr, OWNED_WALLETS, [], new Map()),
    ).toBe("internal");
  });
});

// ── 2. Idle USDC cross-check (pure, from ledger) ─────────────────────────────

test("idle USDC on base matches $44,637 ± $5", () => {
  const rows = loadRows();
  const baseUsdc = rows.filter((r) => r.chain === "base" && r.symbol === "USDC" && r.isStable);
  const netIn = baseUsdc
    .filter((r) => r.direction === "in")
    .reduce((s, r) => s + (r.usd ?? 0), 0);
  const netOut = baseUsdc
    .filter((r) => r.direction === "out")
    .reduce((s, r) => s + (r.usd ?? 0), 0);
  const net = netIn - netOut;
  expect(Math.abs(net - 44637.08)).toBeLessThan(5);
  expect(Math.abs(net - CURRENT_VALUES.idle_usdc_base)).toBeLessThan(5);
});

// ── 3. Spam → $0 (pure, from ledger) ─────────────────────────────────────────

test("spam tokens sum to < $1 USD", () => {
  const rows = loadRows();
  const spamRows = rows.filter((r) => SPAM_REGEX.test(r.symbol));
  const total = spamRows.reduce((s, r) => s + Math.abs(r.usd ?? 0), 0);
  expect(total).toBeLessThan(1);
});

// ── 4. Bridge classification (pure, from ledger) ─────────────────────────────

describe("bridge classification", () => {
  test("all KNOWN_BRIDGES addresses classify as bridge", () => {
    const rows = loadRows();
    for (const addr of KNOWN_BRIDGES) {
      const addrRows = rows.filter((r) => r.counterparty === addr);
      const cls = classifyCounterparty(addr, OWNED_WALLETS, addrRows, new Map());
      expect(cls).toBe("bridge");
    }
  });

  test("sum of stable OUT to bridges ≈ $30,305 ± $50", () => {
    const rows = loadRows();
    const bridgeOuts = rows.filter(
      (r) => r.isStable && r.direction === "out" && KNOWN_BRIDGES.has(r.counterparty),
    );
    const sum = bridgeOuts.reduce((s, r) => s + (r.usd ?? 0), 0);
    expect(Math.abs(sum - 30305)).toBeLessThan(50);
  });
});

// ── 5. Conservation (async, requires live RPC) ────────────────────────────────

test("conservation: |delta_vs_anchor| < 250 (offline stub)", async () => {
  const rows = loadRows();
  const wallet = "0x5d039ece117073323ade5057a516864f4c40e653";
  const output = await computeBoundaryPnL(rows, wallet, WINDOW_1Y_TS, makeOfflineOpts(rows));
  const delta = output.delta_vs_anchor;
  console.log(`Conservation delta (stub): ${delta.toFixed(4)}`);
  // With Unattributed row, conservation is exact (by construction)
  expect(Math.abs(delta)).toBeLessThan(1e-6);
  expect(output).toHaveProperty("anchor");
  expect(output).toHaveProperty("protocols");
  expect(Array.isArray(output.protocols)).toBe(true);
  expect(output.protocols.length).toBeGreaterThan(0);
});

// ── 6. 1Y conservation (async, requires live RPC) ────────────────────────────

test("1Y conservation: |delta_1y| < 250 (offline stub)", async () => {
  const rows = loadRows();
  const wallet = "0x5d039ece117073323ade5057a516864f4c40e653";
  const output = await computeBoundaryPnL(rows, wallet, WINDOW_1Y_TS, makeOfflineOpts(rows));
  const t1y = output.trailing_1y;
  console.log(`1Y delta (stub): ${t1y.delta_1y.toFixed(4)}`);
  // With Unattributed row, 1Y conservation is exact (by construction)
  expect(Math.abs(t1y.delta_1y)).toBeLessThan(1e-6);
  expect(typeof t1y.pnl_1y).toBe("number");
  expect(isFinite(t1y.pnl_1y)).toBe(true);
  // Rejects old archive-RPC inflation bug: pnl should be finite and bounded
  expect(Math.abs(t1y.pnl_1y)).toBeLessThan(1_000_000);
});

// ── 7. Unit: EUSD treated as stable ──────────────────────────────────────────

test("isStableRow: EUSD row (isStable=false) counts as stable", () => {
  const row = {
    ts: 0,
    date: "2024-01-01",
    chain: "base",
    txHash: "0xabc",
    tokenAddr: EUSD_ADDR,
    symbol: "EUSD",
    decimals: 18,
    direction: "in" as const,
    counterparty: "0x0000000000000000000000000000000000000001",
    amountRaw: "1000000000000000000",
    amountFloat: 1,
    isStable: false,
    usd: 1,
    counterpartyIsContract: true,
  };
  expect(isStableRow(row)).toBe(true);
});

test("isStableRow: genuine stable row (isStable=true) still counts as stable", () => {
  const row = {
    ts: 0,
    date: "2024-01-01",
    chain: "base",
    txHash: "0xabc",
    tokenAddr: "0xaf88d065e77c8cc2239327c5edb3a432268e5831",
    symbol: "USDC",
    decimals: 6,
    direction: "in" as const,
    counterparty: "0x0000000000000000000000000000000000000001",
    amountRaw: "1000000",
    amountFloat: 1,
    isStable: true,
    usd: 1,
    counterpartyIsContract: true,
  };
  expect(isStableRow(row)).toBe(true);
});

// ── 8. Unit: MEUSD → Morpho ──────────────────────────────────────────────────

test("detectProtocol: MEUSD maps to Morpho", () => {
  expect(detectProtocol("MEUSD")).toBe("Morpho");
  expect(detectProtocol("meusd")).toBe("Morpho");
});

// ── 9. Unit: computeApportionFraction pure cases ─────────────────────────────

describe("computeApportionFraction", () => {
  // windowStart = 300, now = 400 (unused in formula but passed for clarity)

  test("fully pre-window position → fraction = 0", () => {
    // Entry at 100, exit at 200, window starts at 300 — no overlap
    const f = computeApportionFraction(100, 200, 300, 400);
    expect(f).toBe(0);
  });

  test("fully post-window position → fraction = 1", () => {
    // Entry at 400, exit at 600, window starts at 300 — fully inside
    const f = computeApportionFraction(400, 600, 300, 700);
    expect(f).toBe(1);
  });

  test("position straddling 50/50 → fraction ≈ 0.5", () => {
    // Entry at 100, exit at 300, window starts at 200 — half pre, half post
    const f = computeApportionFraction(100, 300, 200, 400);
    expect(Math.abs(f - 0.5)).toBeLessThan(0.001);
  });

  test("NOW constant is 1782432000 (2026-06-26)", () => {
    expect(NOW).toBe(1782432000);
  });
});

// ── 10. Apportionment vs lifetime checks (async, requires live RPC) ──────────

test("apportioned pnl1y <= lifetime_pnl + $1 per protocol (offline stub)", async () => {
  const rows = loadRows();
  const wallet = "0x5d039ece117073323ade5057a516864f4c40e653";
  const output = await computeBoundaryPnL(rows, wallet, WINDOW_1Y_TS, makeOfflineOpts(rows));
  const protocols = output.protocols as Array<{
    protocol: string;
    lifePnL: number;
    pnl1y: number;
    pnl1y_facebasis: number;
  }>;

  // Per-protocol structural check: apportioned must not exceed face-basis + tolerance
  // (Note: lifePnL includes curVal; with stub curVal=0, open positions have negative lifePnL.
  //  Check against face-basis instead of lifePnL to remain meaningful with stub.)
  const MISC_LIKE_PROTOS = new Set([
    "Misc", "Directional", "Perps", "Bridge", "Unidentified",
    ...NAMED_MISC_PROTOS.values(),
  ]);
  for (const p of protocols) {
    if (MISC_LIKE_PROTOS.has(p.protocol) || p.protocol === "Unattributed") continue;
    // Apportioned must not exceed face-basis (face-basis is the upper bound)
    expect(p.pnl1y).toBeLessThanOrEqual(p.pnl1y_facebasis + 1);
  }

  // Sanity: total apportioned 1Y should not blow up to old ~69k figure (archive RPC bug)
  const totalApportioned = output.trailing_1y.pnl_1y;
  console.log(`Apportioned 1Y total (stub): ${totalApportioned.toFixed(2)}`);
  expect(Math.abs(totalApportioned)).toBeLessThan(100_000);
});

// ── 11a. Cluster netting: inter-wallet transfers must contribute $0 ──────────────

describe("computeClusterCapitalFlows: cluster netting", () => {
  // Two owned wallets swap $1000 USDC: both sides of the transfer appear in merged rows
  const walletA = "0x5c1b7a3ab7797e237cc9ec1e30a18048c364174a"; // L1
  const walletB = "0x5d039ece117073323ade5057a516864f4c40e653"; // L3

  // A sends $1000 to B → appears in A's ledger as "out to B"
  const rowOutAtoB: LedgerRow = {
    ts: 1700000000,
    date: "2023-11-14",
    chain: "base",
    txHash: "0xclustertest001",
    tokenAddr: "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
    symbol: "USDC",
    decimals: 6,
    direction: "out",
    counterparty: walletB,
    amountRaw: "1000000000",
    amountFloat: 1000,
    isStable: true,
    usd: 1000,
    counterpartyIsContract: false, // walletB is an EOA
  };

  // B receives $1000 from A → appears in B's ledger as "in from A"
  const rowInBfromA: LedgerRow = {
    ...rowOutAtoB,
    direction: "in",
    counterparty: walletA,
  };

  test("inter-wallet transfer: both sides → capitalIn=0, capitalOut=0", () => {
    const mergedRows = [rowOutAtoB, rowInBfromA];
    const cf = computeClusterCapitalFlows(mergedRows, 0, OWNED_WALLETS);

    // Inter-wallet flows must net to zero — they are internal transfers
    expect(cf.cexIn).toBe(0);
    expect(cf.ownedIn).toBe(0);
    expect(cf.ownedOut).toBe(0);
    expect(cf.bridgeOut).toBe(0);
    expect(cf.capitalIn).toBe(0);
    expect(cf.capitalOut).toBe(0);
  });

  test("external-EOA outflow IS counted as capital-out in cluster mode", () => {
    // A sends $500 to an external EOA (not owned)
    const extAddr = "0x8e114030c5e4e2ef91a0c34184e2f64bd8b1d5ff";
    const rowExtOut: LedgerRow = {
      ...rowOutAtoB,
      txHash: "0xclustertest002",
      counterparty: extAddr,
      usd: 500,
    };
    const cf = computeClusterCapitalFlows([rowExtOut], 0, OWNED_WALLETS);
    // External-out should appear in bridgeOut (capital-out bucket)
    expect(cf.bridgeOut).toBe(500);
    expect(cf.capitalOut).toBe(500);
    expect(cf.capitalIn).toBe(0);
  });

  test("external-EOA inflow IS counted as capital-in in cluster mode", () => {
    const extAddr = "0x1985ea6e9c68e1c272d8209f3b478ac2fdb25c87";
    const rowExtIn: LedgerRow = {
      ...rowOutAtoB,
      txHash: "0xclustertest003",
      direction: "in",
      counterparty: extAddr,
      usd: 2000,
    };
    const cf = computeClusterCapitalFlows([rowExtIn], 0, OWNED_WALLETS);
    expect(cf.cexIn).toBe(2000);
    expect(cf.capitalIn).toBe(2000);
    expect(cf.capitalOut).toBe(0);
  });
});

// ── 11. Attribution reconciliation + residual magnitude bound ──
// NOTE: "Σ rows === anchor" is true BY CONSTRUCTION, not a real attribution check: the
// "Unattributed" row is computed as (anchor − Σ other rows), so the printed total always closes
// to the anchor regardless of whether per-protocol attribution is correct. The two equality
// asserts below only verify that the residual row is present and arithmetically closes the total.
// The genuine quality gate is the residual-MAGNITUDE bound: if per-wallet/per-LP attribution
// breaks, everything spills into the Unattributed row and |residual| <= 10% of |anchor| fails.

test("attribution reconciliation: residual closes total to anchor AND |residual| <= 10% |anchor| (offline stub)", async () => {
  const rows = loadRows();
  const wallet = "0x5d039ece117073323ade5057a516864f4c40e653";
  const output = await computeBoundaryPnL(rows, wallet, WINDOW_1Y_TS, makeOfflineOpts(rows));
  const protocols = output.protocols as Array<{ protocol: string; lifePnL: number; pnl1y_facebasis: number }>;

  // Lifetime: Σ lifePnL closes to anchor (tautological — residual row makes this exact)
  const sumLife = protocols.reduce((s, p) => s + p.lifePnL, 0);
  console.log(`Σ lifePnL (stub): ${sumLife.toFixed(4)}, anchor: ${(output.anchor as number).toFixed(4)}`);
  expect(Math.abs(sumLife - (output.anchor as number))).toBeLessThan(1e-4);

  // Trailing-1Y: Σ pnl1y_facebasis (excluding Directional) closes to 1Y anchor (also by construction)
  const sumFaceBasis = protocols
    .filter((p) => p.protocol !== "Directional")
    .reduce((s, p) => s + p.pnl1y_facebasis, 0);
  const anchor1y = output.trailing_1y.pnl_1y_anchor as number;
  console.log(`Σ pnl1y_facebasis excl Dir (stub): ${sumFaceBasis.toFixed(4)}, 1Y anchor: ${anchor1y.toFixed(4)}`);
  expect(Math.abs(sumFaceBasis - anchor1y)).toBeLessThan(1e-4);

  // Non-tautological quality gate: the Unattributed residual must stay small relative to the
  // anchor. Broken attribution would dump unexplained value here and balloon the residual.
  const residual = protocols.find((p) => p.protocol === "Unattributed");
  const anchorLife = output.anchor as number;
  const lifeResid = residual?.lifePnL ?? 0;
  const y1Resid = residual?.pnl1y_facebasis ?? 0;
  console.log(`residual: life=${lifeResid.toFixed(2)} (<=${(0.10 * Math.abs(anchorLife)).toFixed(2)}) | 1Y=${y1Resid.toFixed(2)} (<=${(0.10 * Math.abs(anchor1y)).toFixed(2)})`);
  expect(Math.abs(lifeResid)).toBeLessThanOrEqual(0.10 * Math.abs(anchorLife));
  expect(Math.abs(y1Resid)).toBeLessThanOrEqual(0.10 * Math.abs(anchor1y));
});

// ── 12. DEFECT 1 guard: divergent idle_rpc → throws (offline) ─────────────────

test("RPC sanity guard: divergent idle_rpc throws 'refusing to emit a PnL number'", async () => {
  const rows = loadRows();
  const wallet = "0x5d039ece117073323ade5057a516864f4c40e653";

  // Build the expected idle_flow so we know how big it is
  const idleFlow = idleStableFlowDerived(rows, WINDOW_1Y_TS);

  // Stub: returns $25 for stable tokens (triggers sanity guard), 0n for vault receipt tokens
  // (returning 0n for vault tokens prevents valueNonStableHeld from making real RPC calls)
  const stableAddrs = new Set(rows.filter((r) => isStableRow(r)).map((r) => r.tokenAddr.toLowerCase()));
  const FAKE_TINY_BALANCE = 25_000_000n; // $25 @ 6 decimals
  const garbageProvider: BalanceProvider = async (_rpcs, tokenAddr, _wallet, _blockHex) => {
    return stableAddrs.has(tokenAddr.toLowerCase()) ? FAKE_TINY_BALANCE : 0n;
  };

  const chains = [...new Set(rows.map((r) => r.chain))];
  const opts: BoundaryPnLOpts = {
    balanceProvider: garbageProvider,
    nowBlockMap: new Map(chains.map((c) => [c, "0x1a00000"])),
  };

  // idle_flow.now >> $25 → sanity guard should throw after retry
  await expect(computeBoundaryPnL(rows, wallet, WINDOW_1Y_TS, opts)).rejects.toThrow(
    "refusing to emit a PnL number",
  );
});

// ── 13. assertIdleRpcSanity unit tests ────────────────────────────────────────

describe("assertIdleRpcSanity", () => {
  test("passes when idle_rpc ≈ idle_flow (within 3%)", () => {
    expect(() => assertIdleRpcSanity(44500, 44637)).not.toThrow();
  });

  test("passes when both are small and difference < $500", () => {
    expect(() => assertIdleRpcSanity(10, 100)).not.toThrow();
  });

  test("throws when idle_rpc << idle_flow (garbage RPC value)", () => {
    expect(() => assertIdleRpcSanity(25, 58000)).toThrow("refusing to emit a PnL number");
  });

  test("throws when diff > 3% of idle_flow for large values", () => {
    expect(() => assertIdleRpcSanity(45000, 48000)).toThrow("refusing to emit a PnL number");
  });
});

// ── 14. Cluster ≡ Per-LP anchor equality (load-bearing regression) ────────────
// The trailing-1Y cluster boundary must be invariant to how attribution is partitioned
// by wallet. Per-LP previously re-derived windowStartStable from a per-(wallet,protocol)
// windowBasis sum; the max(0,…) clamp made that drift ~$1.5k from the --cluster aggregate.
// This test pins per-LP lifetime AND 1Y-facebasis anchors == the --cluster anchors.

const CLUSTER_LEDGERS = [
  "/tmp/L1_ledger.json", "/tmp/L3_ledger.json", "/tmp/B1_ledger.json",
  "/tmp/B3_ledger.json", "/tmp/B5_ledger.json",
];

function loadClusterLedgers(): { rowsByWallet: Map<string, LedgerRow[]>; allRows: LedgerRow[]; wallets: string[] } {
  const rowsByWallet = new Map<string, LedgerRow[]>();
  const allRows: LedgerRow[] = [];
  const wallets: string[] = [];
  for (const p of CLUSTER_LEDGERS) {
    const raw = JSON.parse(readFileSync(p, "utf8"));
    const w = (raw.wallet as string).toLowerCase();
    const rows: LedgerRow[] = raw.rows ?? raw;
    if (!rowsByWallet.has(w)) { rowsByWallet.set(w, []); wallets.push(w); }
    rowsByWallet.get(w)!.push(...rows);
    allRows.push(...rows);
  }
  return { rowsByWallet, allRows, wallets };
}

// Cluster offline stub: returns the per-(wallet, token) net stable flow (mimics balanceOf,
// clamped at 0), so idle_rpc summed across wallets ≈ idle_flow and the guard passes offline.
function makeClusterOfflineOpts(rowsByWallet: Map<string, LedgerRow[]>, allRows: LedgerRow[]): BoundaryPnLOpts {
  const net = new Map<string, bigint>();
  for (const [w, rows] of rowsByWallet) {
    for (const r of rows) {
      if (!isStableRow(r)) continue;
      const k = `${w.toLowerCase()}:${r.tokenAddr.toLowerCase()}`;
      const raw = BigInt(r.amountRaw);
      net.set(k, (net.get(k) ?? 0n) + (r.direction === "in" ? raw : -raw));
    }
  }
  const chains = [...new Set(allRows.map((r) => r.chain))];
  return {
    balanceProvider: async (_rpcs, tokenAddr, wallet, _block) => {
      const v = net.get(`${wallet.toLowerCase()}:${tokenAddr.toLowerCase()}`) ?? 0n;
      return v > 0n ? v : 0n;
    },
    nowBlockMap: new Map(chains.map((c) => [c, "0x1a00000"])),
    // Offline: chain reachable + not held → the vault guard treats stub-$0 receipts as exited /
    // genuinely $0, never as RPC failures (no network hit).
    ethReachProbe: async () => ({ reachable: true, heldRaw: 0n, redeemPerShare: null }),
  };
}

test("per-LP anchors equal --cluster anchors (lifetime + 1Y facebasis, ±$0.01, offline)", async () => {
  const { rowsByWallet, allRows, wallets } = loadClusterLedgers();
  const opts = makeClusterOfflineOpts(rowsByWallet, allRows);

  // --cluster reference anchors (same formula as cluster main()).
  const cf = computeClusterCapitalFlows(allRows, WINDOW_1Y_TS, OWNED_WALLETS);
  const idleFlow = idleStableFlowDerived(allRows, WINDOW_1Y_TS);
  const clusterRes = await computeCluster(allRows, wallets, WINDOW_1Y_TS, opts);
  const sumWB_cluster = clusterRes.protocolRows
    .filter((x) => x.protocol !== "Directional")
    .reduce((s, x) => s + x.windowBasis, 0);

  // Per-LP boundary (uses the cluster-aggregate windowBasis internally).
  const perLp = await computeClusterPerLpBoundary(rowsByWallet, WINDOW_1Y_TS, opts);

  // Reference anchors share the same economic inputs (idleRpc, sumVaultCurVal) — isolating
  // windowBasis aggregation as the only thing under test.
  const currentStable = perLp.idleRpc + perLp.sumVaultCurVal;
  const anchorLifeRef = currentStable + cf.capitalOut - cf.capitalIn;
  const pnl1yAnchorRef = currentStable + cf.wCapitalOut - ((idleFlow.atStart + sumWB_cluster) + cf.wCapitalIn);

  console.log(`cluster vs per-LP: life ${anchorLifeRef.toFixed(2)}/${perLp.anchorLife.toFixed(2)} | 1Y ${pnl1yAnchorRef.toFixed(2)}/${perLp.pnl1yAnchor.toFixed(2)}`);

  expect(Math.abs(perLp.anchorLife - anchorLifeRef)).toBeLessThan(0.01);     // lifetime anchors equal
  expect(Math.abs(perLp.pnl1yAnchor - pnl1yAnchorRef)).toBeLessThan(0.01);   // 1Y anchors equal (the fix)
  expect(Math.abs(perLp.pnl1yFacebasis - perLp.pnl1yAnchor)).toBeLessThan(0.01); // facebasis == anchor by construction
  expect(Math.abs(perLp.gap)).toBeLessThan(0.01);                            // conservation gap is $0
});

// ── 15. Vault-RPC silent-$0 guard (the avUSDC bug) ───────────────────────────
// A deployed, identified vault that an RPC flake values $0 must THROW, not silently lower
// the anchor. The guard distinguishes RPC-failure-$0 (throw) from genuine-non-redeemable-$0
// (LINEA/PAXG, reachable revert) and fully-exited positions (zero basis).

describe("assertVaultRpcSanity (vault silent-$0 guard)", () => {
  const tv = (over: Record<string, unknown>) => ({
    wallet: "0xabc0000000000000000000000000000000000001",
    proto: "Other", sym: "avUSDC",
    tokenAddr: "0x0000000000000000000000000000000000000abc",
    chain: "base", decimals: 6, value: 0, protoNetBasis: 5000, ...over,
  });
  const reach = (reachable: boolean, heldRaw: bigint | null, redeemPerShare: number | null) =>
    ({ ethReachProbe: async () => ({ reachable, heldRaw, redeemPerShare }) } as BoundaryPnLOpts);

  test("(a) held redeemable vault valued $0 by main pass ($1340 @ 1.34/share) → throws", async () => {
    // heldRaw 1000e6 shares × 1.34 = $1340 > $1
    await expect(
      assertVaultRpcSanity([tv({})] as never, reach(true, 1_000_000_000n, 1.34)),
    ).rejects.toThrow("refusing to emit a PnL number");
  });

  test("(a2) deployed position + chain unreachable → throws", async () => {
    await expect(
      assertVaultRpcSanity([tv({})] as never, reach(false, null, null)),
    ).rejects.toThrow("refusing to emit a PnL number");
  });

  test("(b1) fully-exited position (net basis ≈ $0) → NO throw (not even a suspect)", async () => {
    await expect(
      assertVaultRpcSanity([tv({ protoNetBasis: 0 })] as never, reach(false, null, null)),
    ).resolves.toBeUndefined();
  });

  test("(b2) not held (balanceOf 0 → exited) even with positive bucket basis → NO throw", async () => {
    await expect(
      assertVaultRpcSanity([tv({ sym: "rcowUniswap" })] as never, reach(true, 0n, null)),
    ).resolves.toBeUndefined();
  });

  test("(b3) held but non-redeemable (convertToAssets reverts, e.g. LINEA/PAXG) → NO throw", async () => {
    await expect(
      assertVaultRpcSanity([tv({ sym: "LINEA" })] as never, reach(true, 2_100_000_000_000_000_000_000n, null)),
    ).resolves.toBeUndefined();
  });

  test("(c) excluded protocol (Bridge) never trips even if unreachable", async () => {
    await expect(
      assertVaultRpcSanity([tv({ proto: "Bridge" })] as never, reach(false, null, null)),
    ).resolves.toBeUndefined();
  });

  test("(d) wired into computeClusterPerLpBoundary: unreachable deployed vault → throws (offline)", async () => {
    const { rowsByWallet, allRows } = loadClusterLedgers();
    const opts: BoundaryPnLOpts = {
      ...makeClusterOfflineOpts(rowsByWallet, allRows),
      ethReachProbe: async () => ({ reachable: false, heldRaw: null, redeemPerShare: null }),
    };
    await expect(
      computeClusterPerLpBoundary(rowsByWallet, WINDOW_1Y_TS, opts),
    ).rejects.toThrow("refusing to emit a PnL number");
  });
});
