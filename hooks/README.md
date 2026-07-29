# Versioned git hooks

Enable once per clone/worktree:

```
git config core.hooksPath hooks
```

## pre-commit
Runs the dependency-free **SKILL.md frontmatter validator** in `--index` (staged-snapshot)
mode and **blocks the commit** if any staged skill would fail to load in GitHub Copilot CLI
(>=1.0.70). Copilot silently drops a skill whose frontmatter it cannot parse or whose
`description` exceeds 1024 parsed characters — a dropped skill never appears in
`copilot skill list`, so this guard turns a silent degradation into a loud, fixable commit
error.

**Staged-snapshot semantics (why `--index`, not the working tree):** a pre-commit hook must
gate exactly what will be committed — the staged index snapshot — not whatever happens to be
sitting in the working tree. In `--index` mode the validator reads each
`.agents/skills/<name>/SKILL.md` blob straight FROM THE GIT INDEX via `git ls-files -s` +
`git cat-file -p <sha>`, exactly what `git commit` will record: staged additions are included,
staged deletions are excluded, and an unstaged edit to a skill (broken or fixed) is invisible
to the check because it isn't part of the commit. The `copilot skill list` cross-check is
intentionally **skipped** in `--index` mode — it inspects the working tree, which is the wrong
snapshot for a staged gate — the local structural checks (frontmatter parse, name/description
presence+shape, description ≤1024, duplicate names, malformed-YAML colon) are sufficient there.

Checks: delimited YAML frontmatter; non-empty scalar `name` + `description`; `name` a
valid slug ≤64 chars matching its directory; `description` parsed length ≤1024; no
duplicate canonical names; and malformed YAML such as an unquoted `: ` in a plain
scalar. In default (working-tree) mode, when `copilot` is on PATH it additionally
cross-checks `copilot skill list` as the authoritative final gate; when absent, the
local structural checks still apply.

- Working-tree full run (with copilot cross-check): `bun .agents/scripts/skills/validate_skill_md.ts`
- Staged-snapshot run (what the hook does): `bun .agents/scripts/skills/validate_skill_md.ts --index`
- Skip the (slower) authoritative cross-check (working-tree): `bun .agents/scripts/skills/validate_skill_md.ts --no-copilot`
- Validate specific files: `bun .agents/scripts/skills/validate_skill_md.ts path/to/SKILL.md ...`

It ALSO gates staged reports (`research/*.md`, `crypto/*.md`) with the network-free
**drawdown-BASIS** check (`drawdown_basis.ts --basis-only`): a staged report that states a
drawdown without saying whether it is measured from the 52w high or the ATH blocks the
commit. See the drawdown-BASIS section below.

Naturally scoped: no-ops on any worktree that lacks the validator script. But when the
validator IS present and **Bun is missing it fails loudly** rather than skipping — the
load guarantee is the whole point. Override (discouraged): `git commit --no-verify`.

## pre-push
Runs the hedge-fund-committee-workflow invariant tests and **blocks the push** if they fail:
- `test_gate_contract.mjs` — a single-source narrative name (SNDK-class) must reach the panel (the SanDisk regression guard, bound to the real workflow source).
- `apply_score_caps.mjs --selftest` — the deterministic eval hard-caps (flagship-exclusion → 35, all-PASS → 45) are intact.
- `bun test .agents/scripts/validate/drawdown_basis.test.ts` — the **drawdown-BASIS invariant** (see below). Hermetic: the price series is injected, so no network.

Naturally scoped: no-ops on any branch/worktree whose working tree lacks these files, and when `node` is unavailable. Override (discouraged): `git push --no-verify`.

## Drawdown-BASIS validation (`.agents/scripts/validate/drawdown_basis.ts`)

Three real incidents shipped the same bug: a "% from high" figure whose BASIS was
ambiguous, never recomputed from one canonical series.

| Published | Basis actually used | Correct 52w figure |
|---|---|---|
| TON −49.2% "from high" | truncated ~37-week window | −59.1% |
| TON −82.5% "from high" | ATH ($8.25) in a 52w report | −59.1% |
| JUP −87% "from high" | ATH ($2.00) in a 52w report | −65.2% |
| LINK "52w low $7.00" | eyeballed round number | $7.19 |

The validator enforces four rules and exits non-zero on any failure:

1. **BASIS** — every drawdown claim must disambiguate to `52w` or `ATH`. A bare
   "from high"/"from highs" is `BASIS_MISSING`. *(This is the network-free rule the
   pre-commit hook enforces on staged reports.)*
2. **RECOMPUTE** — each claim is recomputed from ONE canonical 366-point daily-close
   series per token (CoinGecko) and fails as `MISMATCH` beyond `--tolerance` (default
   0.5 percentage points). Stated 52w low/high levels are checked against the same
   series (`--price-tolerance-pct`, default 1%).
3. **WINDOW** — a series shorter than 360 daily points is `SHORT_SERIES` and fails
   loudly. That truncated window *is* the TON −49.2% incident.
4. **HONESTY** — a network error is `FETCH_FAILED`, an unmapped/unattributable token is
   `NO_TOKEN`, a missing ATH is `ATH_UNAVAILABLE`. Missing data is `[UNAVAILABLE]` and
   loud (repo invariant #4) — never a silent skip or pass.

Usage:
- Full pre-publish check (network): `bun .agents/scripts/validate/drawdown_basis.ts research/<report>.md`
- Basis-only, no network (what pre-commit runs): `bun .agents/scripts/validate/drawdown_basis.ts research/<report>.md --basis-only`
- Machine-readable: `--json` · Tuning: `--tolerance 0.5 --price-tolerance-pct 1.0`
- Tests: `bun test .agents/scripts/validate/drawdown_basis.test.ts`

Rate limits: CoinGecko's keyless tier 429s aggressively, so requests are serialized with
a 3s inter-request gap and exponential backoff (5s→160s, 7 attempts). Exhausted backoff
is reported as `FETCH_FAILED`, never a pass.
