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

Naturally scoped: no-ops on any worktree that lacks the validator script. But when the
validator IS present and **Bun is missing it fails loudly** rather than skipping — the
load guarantee is the whole point. Override (discouraged): `git commit --no-verify`.

## pre-push
Runs the hedge-fund-committee-workflow invariant tests and **blocks the push** if they fail:
- `test_gate_contract.mjs` — a single-source narrative name (SNDK-class) must reach the panel (the SanDisk regression guard, bound to the real workflow source).
- `apply_score_caps.mjs --selftest` — the deterministic eval hard-caps (flagship-exclusion → 35, all-PASS → 45) are intact.

Naturally scoped: no-ops on any branch/worktree whose working tree lacks these files, and when `node` is unavailable. Override (discouraged): `git push --no-verify`.
