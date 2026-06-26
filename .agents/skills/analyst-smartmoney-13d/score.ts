#!/usr/bin/env -S node --experimental-strip-types
/**
 * 13D Watch — Composite Scoring Engine
 *
 * Reads a candidate JSON from stdin, computes a 0-100 composite score,
 * and outputs the scored candidate JSON to stdout.
 *
 * Score dimensions (weights configurable via env):
 *   conviction  (35%) — stake size, repeat filer, multiple filers
 *   catalyst    (25%) — intent clarity, board/M&A/restructuring signals
 *   timing      (20%) — filing recency, earnings proximity, sector momentum
 *   technical   (10%) — price vs 52w range, volume confirmation
 *   risk        (10%) — market cap floor, liquidity, concentration
 *
 * Usage:
 *   echo '{"ticker":"XYZ",...}' | node --experimental-strip-types score.ts
 *   node --experimental-strip-types score.ts --explain  # show weight breakdown
 */

import { readFileSync } from "node:fs";
import { parseArgs } from "node:util";

// --- Types ---

interface CandidateInput {
  ticker: string;
  filing_type: "13D" | "13G" | "13F" | "STOCK_ACT";
  filer: string;

  // Conviction signals
  stake_pct?: number;         // Reported stake %
  is_repeat_filer?: boolean;  // Filer has filed 13D before on other targets
  num_filers?: number;        // Number of distinct filers on same ticker (convergence)
  is_new_position?: boolean;  // New vs. amendment to existing

  // Catalyst signals
  intent?: string;            // From filing: "influence", "acquisition", "restructuring", "passive"
  has_board_seats?: boolean;  // Seeking/obtained board representation
  has_letter?: boolean;       // Published activist letter

  // Timing signals
  filing_age_days?: number;   // Days since filing date
  days_to_earnings?: number;  // Days until next earnings
  sector_momentum?: number;   // Sector relative strength (-1 to 1)

  // Technical signals
  pct_from_52w_high?: number; // Negative = below high (e.g. -0.25 = 25% below)
  pct_from_52w_low?: number;  // Positive = above low
  volume_ratio?: number;      // Current vol / 20d avg vol

  // Risk signals
  market_cap_m?: number;      // Market cap in millions
  avg_daily_volume?: number;  // Average daily dollar volume
  portfolio_pct?: number;     // Would-be portfolio weight if added
}

interface ScoredCandidate extends CandidateInput {
  score: number;
  conviction_score: number;
  catalyst_score: number;
  timing_score: number;
  technical_score: number;
  risk_score: number;
  flags: string[];
}

// --- Weights (override via env) ---

const WEIGHTS = {
  conviction: parseFloat(process.env.W_CONVICTION || "0.35"),
  catalyst:   parseFloat(process.env.W_CATALYST   || "0.25"),
  timing:     parseFloat(process.env.W_TIMING      || "0.20"),
  technical:  parseFloat(process.env.W_TECHNICAL   || "0.10"),
  risk:       parseFloat(process.env.W_RISK        || "0.10"),
};

// --- Scoring Functions ---

function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}

function scoreConviction(c: CandidateInput): { score: number; flags: string[] } {
  let score = 50; // baseline
  const flags: string[] = [];

  // Stake size — higher is stronger conviction
  if (c.stake_pct != null) {
    if (c.stake_pct >= 15) { score += 30; flags.push("stake>=15%"); }
    else if (c.stake_pct >= 10) { score += 22; flags.push("stake>=10%"); }
    else if (c.stake_pct >= 5)  { score += 12; flags.push("stake>=5%"); }
    else { score += 5; }
  }

  // Filing type — 13D signals active intent
  if (c.filing_type === "13D") { score += 10; flags.push("13D-active"); }
  else if (c.filing_type === "13G") { score -= 5; } // passive

  // Repeat filer (experienced activist)
  if (c.is_repeat_filer) { score += 8; flags.push("repeat-activist"); }

  // Multiple filers converging
  if (c.num_filers != null && c.num_filers >= 2) {
    score += Math.min(15, (c.num_filers - 1) * 8);
    flags.push(`${c.num_filers}-filers`);
  }

  // New position vs amendment
  if (c.is_new_position) { score += 5; flags.push("new-position"); }

  return { score: clamp(score, 0, 100), flags };
}

function scoreCatalyst(c: CandidateInput): { score: number; flags: string[] } {
  let score = 30;
  const flags: string[] = [];

  const intent = (c.intent || "").toLowerCase();
  if (intent.includes("acqui") || intent.includes("merger") || intent.includes("takeover")) {
    score += 35; flags.push("M&A-intent");
  } else if (intent.includes("restructur") || intent.includes("spin") || intent.includes("break")) {
    score += 30; flags.push("restructuring");
  } else if (intent.includes("influence") || intent.includes("change") || intent.includes("board")) {
    score += 20; flags.push("influence-intent");
  } else if (intent.includes("passive")) {
    score -= 10; flags.push("passive-intent");
  }

  if (c.has_board_seats) { score += 15; flags.push("board-seats"); }
  if (c.has_letter)      { score += 10; flags.push("activist-letter"); }

  return { score: clamp(score, 0, 100), flags };
}

function scoreTiming(c: CandidateInput): { score: number; flags: string[] } {
  let score = 50;
  const flags: string[] = [];

  // Filing recency — fresher is better
  if (c.filing_age_days != null) {
    if (c.filing_age_days <= 3)  { score += 25; flags.push("filed-<3d"); }
    else if (c.filing_age_days <= 7)  { score += 18; }
    else if (c.filing_age_days <= 14) { score += 10; }
    else if (c.filing_age_days <= 30) { score += 0; }
    else { score -= 15; flags.push("stale-filing"); }
  }

  // Earnings proximity — near-earnings activist filing is higher catalyst
  if (c.days_to_earnings != null && c.days_to_earnings <= 30) {
    score += 10; flags.push("near-earnings");
  }

  // Sector momentum tailwind
  if (c.sector_momentum != null) {
    score += Math.round(c.sector_momentum * 15);
    if (c.sector_momentum >= 0.5) flags.push("sector-tailwind");
    if (c.sector_momentum <= -0.5) flags.push("sector-headwind");
  }

  return { score: clamp(score, 0, 100), flags };
}

function scoreTechnical(c: CandidateInput): { score: number; flags: string[] } {
  let score = 50;
  const flags: string[] = [];

  // Price vs 52w high — deeper discount is more interesting for value activists
  if (c.pct_from_52w_high != null) {
    const discount = Math.abs(c.pct_from_52w_high);
    if (discount >= 0.30) { score += 20; flags.push("deep-discount"); }
    else if (discount >= 0.15) { score += 10; }
    else if (discount <= 0.05) { score -= 5; flags.push("near-high"); }
  }

  // Volume confirmation — abnormal volume on filing
  if (c.volume_ratio != null) {
    if (c.volume_ratio >= 3.0) { score += 15; flags.push("volume-spike"); }
    else if (c.volume_ratio >= 1.5) { score += 8; }
  }

  return { score: clamp(score, 0, 100), flags };
}

function scoreRisk(c: CandidateInput): { score: number; flags: string[] } {
  let score = 70; // start favorable, penalize for risks
  const flags: string[] = [];

  // Market cap floor — micro/nano caps are risky
  if (c.market_cap_m != null) {
    if (c.market_cap_m < 100)       { score -= 30; flags.push("nano-cap-risk"); }
    else if (c.market_cap_m < 500)  { score -= 15; flags.push("micro-cap"); }
    else if (c.market_cap_m < 2000) { score -= 5; }
  }

  // Liquidity — thin names are hard to exit
  if (c.avg_daily_volume != null && c.avg_daily_volume < 1_000_000) {
    score -= 20; flags.push("illiquid");
  }

  // Portfolio concentration check
  if (c.portfolio_pct != null && c.portfolio_pct > 0.10) {
    score -= 15; flags.push("concentration-risk");
  }

  return { score: clamp(score, 0, 100), flags };
}

// --- Main Scoring ---

function scoreCandidate(input: CandidateInput): ScoredCandidate {
  const conv = scoreConviction(input);
  const cat  = scoreCatalyst(input);
  const tim  = scoreTiming(input);
  const tech = scoreTechnical(input);
  const risk = scoreRisk(input);

  const composite = Math.round(
    conv.score * WEIGHTS.conviction +
    cat.score  * WEIGHTS.catalyst +
    tim.score  * WEIGHTS.timing +
    tech.score * WEIGHTS.technical +
    risk.score * WEIGHTS.risk
  );

  return {
    ...input,
    score: clamp(composite, 0, 100),
    conviction_score: conv.score,
    catalyst_score:   cat.score,
    timing_score:     tim.score,
    technical_score:  tech.score,
    risk_score:       risk.score,
    flags: [...conv.flags, ...cat.flags, ...tim.flags, ...tech.flags, ...risk.flags],
  };
}

// --- CLI ---

const { values } = parseArgs({
  options: {
    explain: { type: "boolean", default: false },
    help:    { type: "boolean", short: "h", default: false },
  },
});

if (values.help) {
  console.log(`Usage: echo '{"ticker":"XYZ",...}' | score.ts [--explain]

Reads a candidate JSON from stdin, computes a 0-100 composite score.
Outputs the scored JSON to stdout.

Dimensions (override weights via env W_CONVICTION, W_CATALYST, etc.):
  conviction (${WEIGHTS.conviction * 100}%) — stake size, repeat filer, multi-filer convergence
  catalyst   (${WEIGHTS.catalyst * 100}%) — intent clarity, board seats, activist letter
  timing     (${WEIGHTS.timing * 100}%) — filing recency, earnings proximity, sector momentum
  technical  (${WEIGHTS.technical * 100}%) — price vs 52w range, volume confirmation
  risk       (${WEIGHTS.risk * 100}%) — market cap, liquidity, concentration

  --explain  Show weight breakdown table`);
  process.exit(0);
}

if (values.explain) {
  console.log("Score weights:");
  for (const [dim, w] of Object.entries(WEIGHTS)) {
    console.log(`  ${dim.padEnd(12)} ${(w * 100).toFixed(0)}%`);
  }
  const total = Object.values(WEIGHTS).reduce((a, b) => a + b, 0);
  console.log(`  ${"TOTAL".padEnd(12)} ${(total * 100).toFixed(0)}%`);
  process.exit(0);
}

// Read from stdin
let input = "";
try {
  input = readFileSync("/dev/stdin", "utf-8");
} catch {
  console.error("Error reading stdin. Pipe a candidate JSON.");
  process.exit(2);
}

let candidate: CandidateInput;
try {
  candidate = JSON.parse(input) as CandidateInput;
} catch {
  console.error("Invalid JSON on stdin.");
  process.exit(2);
}

if (!candidate.ticker) {
  console.error("Missing required field: ticker");
  process.exit(2);
}

const scored = scoreCandidate(candidate);
console.log(JSON.stringify(scored, null, 2));
