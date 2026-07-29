#!/usr/bin/env bash
#
# changed_reports.sh — list the report files a change touches, for the drawdown-BASIS gate.
#
# SINGLE SOURCE OF TRUTH. Both `.github/workflows/gates.yml` and `hooks/pre-commit` call
# this, so the CI gate and the local hook can never drift apart.
#
# WHY `--diff-filter=ACMR` AND NOT `ACM` (the bug this file exists to kill):
#   Git scores "renamed AND substantially edited" as an `R` status (e.g. `R099`, `R062`).
#   `ACM` EXCLUDES `R`. Re-dating a report (`crypto-portfolio-2026-07-24.md` →
#   `crypto-portfolio-2026-07-31.md`) or adding a `-v2` suffix is completely normal here,
#   so the single most common way a report changes was invisible to the gate: rename it,
#   edit a bare "from high" into it, and the gate printed "nothing to gate" and exited 0.
#   That is a silent bypass of the exact rule that exists because TON −49.2%, TON −82.5%
#   and JUP −87% all shipped wrong.
#
# WHY `--name-status ... | awk '{print $NF}'` AND NOT `--name-only`:
#   With rename detection on, `--name-only` can emit BOTH the old and the new path for a
#   single `R` entry. The old path no longer exists on disk, so a naive loop either skips
#   it (fine) or fails on it (spurious). `--name-status` gives `R099<TAB>old<TAB>new`, and
#   the LAST tab-separated field is always the DESTINATION — the file that actually needs
#   validating. `NF>1` drops any malformed line.
#
# Usage:
#   changed_reports.sh --cached          # staged set (pre-commit hook)
#   changed_reports.sh <base> <head>     # commit range (CI)
set -uo pipefail

# Pathspecs below are repo-relative, so anchor to the repo root: a hook or CI step that
# happens to run from a subdirectory would otherwise match nothing and report "nothing to
# gate" — the same silent-bypass failure this script exists to prevent.
cd "$(git rev-parse --show-toplevel)" || exit 1

if [ "${1:-}" = "--cached" ]; then
  git diff --cached --name-status --diff-filter=ACMR -M -- 'research/*.md' 'crypto/*.md'
else
  git diff --name-status --diff-filter=ACMR -M "${1:?base rev required}" "${2:?head rev required}" \
    -- 'research/*.md' 'crypto/*.md'
fi | awk -F'\t' 'NF > 1 { print $NF }'
