#!/usr/bin/env bun
import { addJob, loadJobs, removeJob, isActive, VALID_CONDITIONS, type AlertJob, type Cond } from "./store.ts";

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
    reasoning: reasons,
    channel: flag("channel") ?? "stdout",
    ...(flag("expiry") ? { expiry: flag("expiry") } : {}),
    ...(flag("cooldown") ? { cooldownSec: parseInt(flag("cooldown")!) } : {}),
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
    const reason = j.reasoning.slice(0, 40) + (j.reasoning.length > 40 ? "…" : "");
    console.log(
      j.id.padEnd(36) + " " +
      j.symbol.padEnd(10) + " " +
      conds.padEnd(32) + " " +
      j.channel.padEnd(20) + " " +
      status.padEnd(8) + " " +
      reason
    );
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
  --desk       <desk>        default: crypto
  --channel    <channel>     default: stdout  (telegram:@handle | ntfy:topic | stdout)
  --period     <int>         optional; per-condition indicator period
  --match      all|any|sequence  default: all (when >1 condition)
  --expiry     <ISO date>    optional
  --cooldown   <seconds>     optional; 0/omit = one-shot

remove:
  --id <id>

list: (no flags)

valid conditions: ${VALID_CONDITIONS.join(", ")}`);
  process.exit(1);
}
