# Versioned git hooks

Enable once per clone/worktree:

```
git config core.hooksPath hooks
```

## pre-push
Runs the hedge-fund-committee-workflow invariant tests and **blocks the push** if they fail:
- `test_gate_contract.mjs` — a single-source narrative name (SNDK-class) must reach the panel (the SanDisk regression guard, bound to the real workflow source).
- `apply_score_caps.mjs --selftest` — the deterministic eval hard-caps (flagship-exclusion → 35, all-PASS → 45) are intact.

Naturally scoped: no-ops on any branch/worktree whose working tree lacks these files, and when `node` is unavailable. Override (discouraged): `git push --no-verify`.
