#!/usr/bin/env bun
import { addJob, loadJobs, removeJob, isActive, normalizeReasoning, VALID_CONDITIONS, type AlertJob, type Cond } from "./store.ts";

const args = process.argv.slice(2);
const sub = args[0];

function flag(name: string): string | undefined {
  const i = args.indexOf(`--${name}`);
  return i !== -1 ? args[i + 1] : undefined;
}

function flagAll(name: string): string[] {
  const results: string[] = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === `--${name}` && i + 1 < args.length) results.push(args[i + 1]);
  }
  return results;
}

function die(msg: string): never {
  console.error(`error: ${msg}`);
  process.exit(1);
}

if (sub === "add") {
  const symbol = flag("symbol") ?? die("--symbol required");
  const reasons = flag("reason") ?? die("--reason required and must be non-empty");
  if (!reasons.trim()) die("--reason must be non-empty");

  const conditionFlags = flagAll("condition");
  const valueFlags = flagAll("value");

  if (conditionFlags.length === 0) die("--condition required");
  if (conditionFlags.length !== valueFlags.length)
    die("each --condition must have a matching --value");

  for (const c of conditionFlags) {
    if (!(VALID_CONDITIONS as readonly string[]).includes(c)) {
      die(`invalid condition "${c}". Valid: ${VALID_CONDITIONS.join(", ")}`);
    }
  }

  // Hard gate: price-level alerts (above/below) require --data-source
  // to prevent fabricated support/resistance levels.
  // RSI, MACD, and other indicator conditions are exempt.
  const priceConditions = conditionFlags.filter(c => c === "above" || c === "below");
  if (priceConditions.length > 0) {
    const dataSource = flag("data-source");
    if (!dataSource || !dataSource.trim()) {
      die(
        `--data-source required for price conditions (above/below).\n` +
        `Pull OHLCV data first, then cite the evidence.\n` +
        `Example: --data-source "14 weekly closes in $60k-$65k bucket from 210w TradingView OHLCV"\n` +
        `Example: --data-source "200wMA $62,640 from TradingView 210 weekly bars"\n` +
        `No data source = no alert. Do not fabricate support levels.`
      );
    }
    // Embed data-source into the reason so it's visible in the alert
    reasons.trim(); // already validated above
  }

  const periodFlags = flagAll("period");
  const conditions: Cond[] = conditionFlags.map((c, i) => {
    const cond: Cond = { condition: c, value: parseFloat(valueFlags[i]) };
    if (isNaN(cond.value)) die(`--value for condition "${c}" must be numeric`);
    if (periodFlags[i]) cond.period = parseInt(periodFlags[i]);
    return cond;
  });

  const matchRaw = flag("match");
  const match = (matchRaw as AlertJob["match"]) ?? (conditions.length > 1 ? "all" : undefined);

  const job = addJob({
    desk: flag("desk") ?? "crypto",
    symbol: symbol.toUpperCase(),
    conditions,
    ...(match ? { match } : {}),
    reasoning: priceConditions.length > 0
      ? `${reasons} [data: ${flag("data-source")}]`
      : reasons,
    channel: flag("channel") ?? "stdout",
    ...(flag("expiry") ? { expiry: flag("expiry") } : {}),
    ...(flag("cooldown") ? { cooldownSec: parseInt(flag("cooldown")!) } : {}),
    ...(flag("link") ? { analysisLink: flag("link") } : {}),
  });

  console.log(JSON.stringify(job, null, 2));
  console.log(`\nadded job id: ${job.id}`);

} else if (sub === "list") {
  const jobs = loadJobs();
  if (!jobs.length) { console.log("no jobs"); process.exit(0); }

  const now = new Date();
  console.log(
    "ID".padEnd(36) + " " +
    "SYMBOL".padEnd(10) + " " +
    "CONDITIONS".padEnd(32) + " " +
    "CHANNEL".padEnd(20) + " " +
    "STATUS".padEnd(8) + " " +
    "REASON"
  );
  console.log("─".repeat(140));
  for (const j of jobs) {
    const conds = j.conditions.map(c => `${c.condition}@${c.value}`).join(",");
    const status = isActive(j, now) ? "active" : "inactive";
    // Normalize at display time so a stale legacy job (created before this
    // rule, or edited outside addJob()) still shows "WHY SET:" in `list`.
    const normalizedReasoning = normalizeReasoning(j.reasoning);
    const reason = normalizedReasoning.slice(0, 40) + (normalizedReasoning.length > 40 ? "…" : "");
    console.log(
      j.id.padEnd(36) + " " +
      j.symbol.padEnd(10) + " " +
      conds.padEnd(32) + " " +
      j.channel.padEnd(20) + " " +
      status.padEnd(8) + " " +
      reason
    );
    if (j.analysisLink) {
      console.log(" ".repeat(37) + "📊 " + j.analysisLink);
    }
  }

} else if (sub === "remove") {
  const id = flag("id") ?? die("--id required");
  removeJob(id);
  console.log(`removed ${id}`);

} else {
  console.log(`usage: mkt-alert.ts <add|list|remove> [flags]

add:
  --symbol     <SYM>         required
  --condition  <cond>        required; repeat for compound rules
  --value      <num>         required; one per --condition
  --reason     <text>        required
  --data-source <text>       REQUIRED for above/below price conditions — cite the OHLCV/on-chain evidence for the level (e.g. "14 weekly closes at $60-65k from 210w TV OHLCV"). Omitting this causes a hard failure. Indicator conditions (rsi_above etc.) are exempt.
  --desk       <desk>        default: crypto
  --channel    <channel>     default: stdout  (telegram:@handle | ntfy:topic | email:to@addr | stdout)
  --period     <int>         optional; per-condition indicator period
  --match      all|any|sequence  default: all (when >1 condition)
  --expiry     <ISO date>    optional
  --cooldown   <seconds>     optional; 0/omit = one-shot
  --link       <url>         optional; attach analysis report URL to the notification

remove:
  --id <id>

list: (no flags)

valid conditions: ${VALID_CONDITIONS.join(", ")}`);
  process.exit(1);
}
