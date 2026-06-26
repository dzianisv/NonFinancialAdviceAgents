#!/usr/bin/env -S node --experimental-strip-types
/**
 * 13D Watch — Tiered Portfolio Construction + Position Sizing
 *
 * Reads scored candidates (JSON array) from stdin, assigns portfolio tiers,
 * computes position sizes, and outputs the tiered portfolio.
 *
 * Tiers:
 *   T1 (80-100) — Full position, high conviction activist plays
 *   T2 (60-79)  — Half position, strong but not peak conviction
 *   T3 (40-59)  — Quarter position, speculative / monitoring
 *   SKIP (<40)  — Below threshold, do not add
 *
 * Constraints:
 *   - Max portfolio allocation to 13D strategy: 15% of total book (configurable)
 *   - Max single position: 5% of total book
 *   - Max T3 allocation: 3% of total book
 *   - Min score to enter: 40
 *
 * Usage:
 *   echo '[{scored1},{scored2}]' | node --experimental-strip-types tier.ts
 *   tier.ts --portfolio-value 1000000   # Set total portfolio value
 *   tier.ts --show-limits               # Show current limits
 *
 * Environment overrides:
 *   PORTFOLIO_VALUE    Total portfolio value in USD (default: 1000000)
 *   MAX_STRATEGY_PCT   Max % of portfolio in 13D strategy (default: 0.15)
 *   MAX_POSITION_PCT   Max single position % (default: 0.05)
 *   MAX_T3_PCT         Max T3 total allocation % (default: 0.03)
 *   MIN_SCORE          Minimum score to enter (default: 40)
 */

import { readFileSync } from "node:fs";
import { parseArgs } from "node:util";

// --- Types ---

interface ScoredCandidate {
  ticker: string;
  filing_type: string;
  filer: string;
  score: number;
  conviction_score: number;
  catalyst_score: number;
  timing_score: number;
  technical_score: number;
  risk_score: number;
  flags: string[];
  stake_pct?: number;
  intent?: string;
  price_at_rec?: number;
  [key: string]: unknown;
}

interface TieredPosition extends ScoredCandidate {
  tier: number;
  tier_label: string;
  position_pct: number;     // % of total portfolio
  position_usd: number;     // USD allocation
  rationale: string;
}

interface PortfolioOutput {
  generated: string;
  portfolio_value: number;
  strategy_budget_usd: number;
  strategy_budget_pct: number;
  positions: TieredPosition[];
  skipped: Array<{ ticker: string; score: number; reason: string }>;
  total_allocated_usd: number;
  total_allocated_pct: number;
  remaining_budget_usd: number;
}

// --- Config ---

const { values: cliValues, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    "portfolio-value": { type: "string", default: "" },
    "show-limits":     { type: "boolean", default: false },
    help:              { type: "boolean", short: "h", default: false },
  },
});

const PORTFOLIO_VALUE = parseFloat(
  (cliValues["portfolio-value"] as string) ||
  process.env.PORTFOLIO_VALUE ||
  "1000000"
);
const MAX_STRATEGY_PCT = parseFloat(process.env.MAX_STRATEGY_PCT || "0.15");
const MAX_POSITION_PCT = parseFloat(process.env.MAX_POSITION_PCT || "0.05");
const MAX_T3_PCT       = parseFloat(process.env.MAX_T3_PCT       || "0.03");
const MIN_SCORE        = parseInt(process.env.MIN_SCORE          || "40", 10);

const STRATEGY_BUDGET = PORTFOLIO_VALUE * MAX_STRATEGY_PCT;

// --- Tier assignment ---

interface TierConfig {
  tier: number;
  label: string;
  min_score: number;
  max_score: number;
  base_pct: number;  // base position size as % of portfolio
}

const TIERS: TierConfig[] = [
  { tier: 1, label: "T1-Full",    min_score: 80, max_score: 100, base_pct: 0.04 },
  { tier: 2, label: "T2-Half",    min_score: 60, max_score: 79,  base_pct: 0.02 },
  { tier: 3, label: "T3-Quarter", min_score: 40, max_score: 59,  base_pct: 0.01 },
];

function assignTier(score: number): TierConfig | null {
  if (score < MIN_SCORE) return null;
  return TIERS.find((t) => score >= t.min_score && score <= t.max_score) || null;
}

// --- Portfolio construction ---

function buildPortfolio(candidates: ScoredCandidate[]): PortfolioOutput {
  // Sort by score descending
  const sorted = [...candidates].sort((a, b) => b.score - a.score);

  const positions: TieredPosition[] = [];
  const skipped: Array<{ ticker: string; score: number; reason: string }> = [];
  let totalAllocated = 0;
  let t3Allocated = 0;

  for (const c of sorted) {
    const tierConfig = assignTier(c.score);

    if (!tierConfig) {
      skipped.push({ ticker: c.ticker, score: c.score, reason: "below-min-score" });
      continue;
    }

    // Position size — base from tier, capped by single-position limit
    let positionPct = Math.min(tierConfig.base_pct, MAX_POSITION_PCT);
    let positionUsd = positionPct * PORTFOLIO_VALUE;

    // T3 cap
    if (tierConfig.tier === 3) {
      const remainingT3 = MAX_T3_PCT * PORTFOLIO_VALUE - t3Allocated;
      if (remainingT3 <= 0) {
        skipped.push({ ticker: c.ticker, score: c.score, reason: "T3-cap-hit" });
        continue;
      }
      positionUsd = Math.min(positionUsd, remainingT3);
      positionPct = positionUsd / PORTFOLIO_VALUE;
    }

    // Strategy budget cap
    const remainingBudget = STRATEGY_BUDGET - totalAllocated;
    if (remainingBudget <= 0) {
      skipped.push({ ticker: c.ticker, score: c.score, reason: "strategy-budget-exhausted" });
      continue;
    }
    positionUsd = Math.min(positionUsd, remainingBudget);
    positionPct = positionUsd / PORTFOLIO_VALUE;

    // Build rationale
    const rationale = [
      `Score ${c.score} → ${tierConfig.label}`,
      c.flags?.length ? `Flags: ${c.flags.join(", ")}` : null,
      c.stake_pct ? `Stake: ${c.stake_pct}%` : null,
      c.intent ? `Intent: ${c.intent}` : null,
    ]
      .filter(Boolean)
      .join(" | ");

    const position: TieredPosition = {
      ...c,
      tier: tierConfig.tier,
      tier_label: tierConfig.label,
      position_pct: Math.round(positionPct * 10000) / 10000,
      position_usd: Math.round(positionUsd),
      rationale,
    };

    positions.push(position);
    totalAllocated += positionUsd;
    if (tierConfig.tier === 3) t3Allocated += positionUsd;
  }

  return {
    generated: new Date().toISOString(),
    portfolio_value: PORTFOLIO_VALUE,
    strategy_budget_usd: STRATEGY_BUDGET,
    strategy_budget_pct: MAX_STRATEGY_PCT,
    positions,
    skipped,
    total_allocated_usd: Math.round(totalAllocated),
    total_allocated_pct: Math.round((totalAllocated / PORTFOLIO_VALUE) * 10000) / 10000,
    remaining_budget_usd: Math.round(STRATEGY_BUDGET - totalAllocated),
  };
}

// --- CLI ---

if (cliValues.help) {
  console.log(`Usage: echo '[{scored1},{scored2}]' | tier.ts [options]

Options:
  --portfolio-value <N>  Total portfolio value in USD (default: ${PORTFOLIO_VALUE})
  --show-limits          Show current portfolio limits
  -h, --help             Show this help

Tiers:
  T1 (80-100) — Full position (${TIERS[0]!.base_pct * 100}% of portfolio)
  T2 (60-79)  — Half position (${TIERS[1]!.base_pct * 100}% of portfolio)
  T3 (40-59)  — Quarter position (${TIERS[2]!.base_pct * 100}% of portfolio)
  SKIP (<${MIN_SCORE})  — Below threshold

Constraints:
  Max strategy allocation: ${MAX_STRATEGY_PCT * 100}% ($${STRATEGY_BUDGET.toLocaleString()})
  Max single position:     ${MAX_POSITION_PCT * 100}% ($${(PORTFOLIO_VALUE * MAX_POSITION_PCT).toLocaleString()})
  Max T3 total:            ${MAX_T3_PCT * 100}% ($${(PORTFOLIO_VALUE * MAX_T3_PCT).toLocaleString()})`);
  process.exit(0);
}

if (cliValues["show-limits"]) {
  console.log(`Portfolio limits (portfolio: $${PORTFOLIO_VALUE.toLocaleString()}):
  Strategy budget:   ${MAX_STRATEGY_PCT * 100}%  = $${STRATEGY_BUDGET.toLocaleString()}
  Max position:      ${MAX_POSITION_PCT * 100}%  = $${(PORTFOLIO_VALUE * MAX_POSITION_PCT).toLocaleString()}
  Max T3 total:      ${MAX_T3_PCT * 100}%  = $${(PORTFOLIO_VALUE * MAX_T3_PCT).toLocaleString()}
  Min score:         ${MIN_SCORE}`);
  process.exit(0);
}

// Read candidates from stdin
let input = "";
try {
  input = readFileSync("/dev/stdin", "utf-8");
} catch {
  console.error("Error reading stdin. Pipe a JSON array of scored candidates.");
  process.exit(2);
}

let candidates: ScoredCandidate[];
try {
  const parsed = JSON.parse(input);
  candidates = Array.isArray(parsed) ? parsed : [parsed];
} catch {
  console.error("Invalid JSON on stdin. Expected array of scored candidates.");
  process.exit(2);
}

const portfolio = buildPortfolio(candidates);
console.log(JSON.stringify(portfolio, null, 2));
