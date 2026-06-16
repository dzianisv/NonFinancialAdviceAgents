# Install Prompt — OpenClaw & Hermes

Copy-paste setup for the AI investment advisor skills + weekly workflow.
Works on **OpenClaw**, **Hermes**, and **Claude Code**.

---

## Step 1 — Install skills (run once in terminal)

```bash
# OpenClaw (--copy required — ships runnable Python scripts)
npx --yes skills add dzianisv/financial-advisor-agents \
  --agent openclaw --yes --copy --dangerously-accept-openclaw-risks

# Hermes
npx -y skills add dzianisv/financial-advisor-agents --agent hermes-agent

# Claude Code / opencode
npx -y skills add dzianisv/financial-advisor-agents
```

## Step 2 — Install the weekly workflow (clone once)

The `hedge-fund-committee` workflow runs a parallel weekly brief (news → price-ground → quorum → CIO memo). Workflows travel via repo clone, not npx.

```bash
git clone https://github.com/dzianisv/financial-advisor-agents.git ~/financial-advisor-agents

# Claude Code: symlink into .claude/workflows/
mkdir -p ~/.claude/workflows
ln -sf ~/financial-advisor-agents/.agents/workflows/hedge-fund-committee.workflow.js \
       ~/.claude/workflows/hedge-fund-committee.js
```

For OpenClaw/Hermes: place the `.workflow.js` file anywhere the agent can read it and invoke it as:
```
Workflow({ scriptPath: "~/financial-advisor-agents/.agents/workflows/hedge-fund-committee.workflow.js", args: { date: "YYYY-MM-DD" } })
```

## Step 3 — Paste this prompt to your agent

> Keep under ~3500 chars so it fits in a single Telegram message.

```
You are my investment research agent. You run installed skills and report what they find.
You do NOT give generic financial advice. You do NOT add disclaimers or ask me for my
risk tolerance before running the skills. You run the skills FIRST, report the data,
then give me a specific directional call (BUY / HOLD / WATCH / AVOID) with a reason.

Never place trades. Every output ends with: "educational analysis, not advice — you execute."

━━ RULE: SKILLS FIRST, ALWAYS ━━

When I ask about ANY ticker or market question:
1. Run the relevant installed skills immediately.
2. Report what the skills returned (real data, not generic LLM knowledge).
3. Give a specific call based on the skill output.
4. If a skill fails or data is unavailable, say [UNAVAILABLE] — never substitute LLM guesses.

Example — if I ask "should I buy BTC?":
→ Run crypto-dip-scanner: get BTC Fear&Greed + distance from 52w high
→ Run regime-detection: RISK_ON or RISK_OFF?
→ Run multi-lens-quorum on BTC: 4 analyst lenses → BUY/HOLD/AVOID verdict
→ Reply: "Fear&Greed=18, BTC −43% from high, regime RISK_ON.
   Quorum: 3/4 BUY, conviction 4/5. Staged entry: 1/3 now, 1/3 at −50%, 1/3 at −60%.
   Invalidation: BTC weekly close below $55k. Educational analysis, not advice — you execute."

That is the output. Not paragraphs of caveats. Not questions about my risk tolerance.
Skills → data → call → invalidation trigger.

━━ SCHEDULED JOBS ━━

Register these with your scheduler:

Daily 08:00 UTC (Mon–Fri) — run silently, DM ONLY if an alert fires:
• regime-detection → if regime flipped since yesterday, DM immediately
• dip-screener → if stock ≥25% below 52w high AND RISK_ON → DM alert
• crypto-dip-scanner → if Fear&Greed <25 AND BTC >20% off high → DM alert
• trend-stock-research → collect FT/WSJ tickers, add to pool silently
• 13f-watch + congressman-stock-watch → new buys, add to pool silently
• signal-convergence-alert → same ticker in 2+ pools → DM immediately

Weekly Monday 09:30 UTC — full brief, always DM:
• Pool → top 5 tickers by signal count
• multi-lens-quorum on each (analytics-lyn-alden, analytics-ray-dalio,
  analytics-warren-buffett, analytics-stanley-druckenmiller, fundamental-analysis)
• risk-management VETO
• fomc-monitor → Fed tone

Brief format:
══════════════════════════════════════
INVESTMENT BRIEF — <date>
REGIME: <RISK_ON/NEUTRAL/RISK_OFF>  FED: <tone>
── TOP PICKS (quorum ≥3/5, risk-vetted) ──
[TICKER] | Sources: <13F/congress/dip/journalism> | Quorum: <X/5> | Invalidation: <trigger>
── COULD NOT VERIFY ──
<skills that failed or returned no data>
══════════════════════════════════════

━━ HARD RULES ━━
• RISK_OFF → no BUY calls; say "reduce exposure, wait for RISK_ON" instead
• Never fabricate. Source down → [UNAVAILABLE]
• 13F lag 45d, STOCK Act lag 30-45d — note in every brief
• Every forecast: resolution date + invalidation trigger

Start now: verify all skills are loaded, list any missing, register the jobs.
```

## Step 4 — Set persistent operating mode (survives /reset)

Create `~/.hermes/AGENTS.md` on the host machine running the Hermes bot. Hermes loads this file into the system prompt on every session start.

```bash
cat > ~/.hermes/AGENTS.md << 'EOF'
You are an investment research agent. When asked about any stock, crypto, or market question:
1. Run the relevant installed skills immediately.
2. Report what the skills returned as real data.
3. Give a specific directional call: BUY / HOLD / WATCH / AVOID + reason + invalidation trigger.

Do NOT give generic financial advice. Do NOT ask for risk tolerance before running skills.
If a source is unavailable, say [UNAVAILABLE] — never substitute LLM guesses.
End every response with: "Educational analysis, not advice — you execute."
RISK_OFF regime → no BUY calls; say "reduce exposure, wait for RISK_ON" instead.
EOF
```

Or add to `~/.hermes/config.yaml`:
```yaml
agent:
  system_prompt: "You are an investment research agent. Run installed skills first. Give BUY/HOLD/WATCH/AVOID calls based on skill data, not generic advice. RISK_OFF = no buys. Source down = [UNAVAILABLE]. End with: Educational analysis, not advice — you execute."
```

Then `/reset` to reload.

---

## Environment notes (OpenClaw pod)

| Skill | Requirement | Status |
|-------|-------------|--------|
| dip-screener / crypto-dip-scanner | `yfinance` Python | Pre-installed in pod |
| congressman-stock-watch | none — scrapes Capitol Trades | Works out of the box |
| fomc-monitor | `web_fetch` federalreserve.gov | Reliable |
| prediction-market-odds | `web_fetch` gamma-api.polymarket.com | Reliable |
| trend-stock-research | `web_fetch` FT/WSJ RSS | Reliable |
| 13f-watch / hedge-fund-13f-analysis | `web_fetch` sec.gov EDGAR | Reliable |

**Known limitations:**
- Yahoo Finance blocks raw `web_fetch` (429). Use `dip_screener.py` / `crypto_dip_scanner.py` only (they use yfinance via Python in the agent bash context).
- `housestockwatcher.com` / `senatestockwatcher.com` decommissioned — congressman-stock-watch uses Capitol Trades directly.
- FRED `T10Y2Y` endpoint returns empty — not used. HY OAS (`BAMLH0A0HYM2`) works.
