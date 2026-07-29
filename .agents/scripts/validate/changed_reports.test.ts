#!/usr/bin/env bun
/**
 * Regression test for the drawdown-BASIS gate's CHANGE-DETECTION (finding B1).
 *
 * THE BUG: both `.github/workflows/gates.yml` and `hooks/pre-commit` used
 * `--diff-filter=ACM`, which EXCLUDES `R` (rename). Git scores a rename-plus-substantial
 * -edit as `R` (e.g. `R096`), and re-dating a report (`…-2026-07-24.md` → `…-2026-07-31.md`)
 * or adding a `-v2` suffix is the NORMAL way reports change here. So the single most
 * common change shape was invisible: rename a report, edit a bare "from high" into it,
 * and the gate printed "nothing to gate" and exited 0 — a silent bypass of the rule that
 * exists because TON −49.2%, TON −82.5% and JUP −87% all shipped wrong.
 *
 * Both call sites now delegate to changed_reports.sh, so this one test covers both.
 * These tests use a THROWAWAY git repo in a temp dir — they never touch this repo.
 */

import { test, expect, describe, beforeEach, afterEach } from "bun:test";
import { mkdtempSync, rmSync, mkdirSync, writeFileSync, renameSync, cpSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const SCRIPT_SRC = resolve(import.meta.dir, "changed_reports.sh");

let repo: string;
let script: string;

function git(...args: string[]): string {
  return execFileSync("git", args, {
    cwd: repo,
    encoding: "utf8",
    env: {
      ...process.env,
      GIT_AUTHOR_NAME: "t", GIT_AUTHOR_EMAIL: "t@t",
      GIT_COMMITTER_NAME: "t", GIT_COMMITTER_EMAIL: "t@t",
    },
  });
}

/** Runs the gate's file-selection step exactly as CI and the hook do. */
function changed(...args: string[]): string[] {
  const out = execFileSync("bash", [script, ...args], { cwd: repo, encoding: "utf8" });
  return out.split("\n").filter(Boolean);
}

/** ~60 lines so a 2-line edit still scores as a rename, not add+delete. */
function reportBody(marker: string): string {
  return [
    "# Crypto Portfolio",
    "",
    "### 1. TON — Toncoin",
    "",
    marker,
    ...Array.from({ length: 55 }, (_, i) => `Filler line ${i} — stable content so git scores a rename.`),
    "",
  ].join("\n");
}

describe("B1 — a RENAMED report must still be gated", () => {
  beforeEach(() => {
    repo = mkdtempSync(join(tmpdir(), "ddgate-"));
    script = join(repo, "changed_reports.sh");
    cpSync(SCRIPT_SRC, script);
    git("init", "-q", "-b", "main");
    mkdirSync(join(repo, "research"), { recursive: true });
    writeFileSync(join(repo, "research", "crypto-2026-07-24.md"), reportBody("TON is −59.1% from 52w high."));
    git("add", "-A");
    git("commit", "-qm", "base");
  });

  afterEach(() => rmSync(repo, { recursive: true, force: true }));

  test("rename + substantial edit is scored R by git (the precondition for the bug)", () => {
    renameSync(join(repo, "research", "crypto-2026-07-24.md"), join(repo, "research", "crypto-2026-07-31.md"));
    writeFileSync(join(repo, "research", "crypto-2026-07-31.md"), reportBody("TON is −62.8% from high."));
    git("add", "-A");
    git("commit", "-qm", "redate");

    const status = git("diff", "--name-status", "--diff-filter=ACMR", "-M", "HEAD~1", "HEAD");
    expect(status).toMatch(/^R\d*\t/);
    // Proof of the original bypass: ACM sees NOTHING for this commit.
    expect(git("diff", "--name-only", "--diff-filter=ACM", "HEAD~1", "HEAD").trim()).toBe("");
  });

  test("the gate now lists the renamed report — and lists its DESTINATION path", () => {
    renameSync(join(repo, "research", "crypto-2026-07-24.md"), join(repo, "research", "crypto-2026-07-31.md"));
    writeFileSync(join(repo, "research", "crypto-2026-07-31.md"), reportBody("TON is −62.8% from high."));
    git("add", "-A");
    git("commit", "-qm", "redate");

    // Exactly one path, and it is the NEW one: the old path no longer exists on disk, so
    // emitting it would either be skipped (missing the real file) or fail spuriously.
    expect(changed("HEAD~1", "HEAD")).toEqual(["research/crypto-2026-07-31.md"]);
  });

  test("the STAGED (pre-commit) path also catches a rename", () => {
    renameSync(join(repo, "research", "crypto-2026-07-24.md"), join(repo, "research", "crypto-2026-07-31.md"));
    writeFileSync(join(repo, "research", "crypto-2026-07-31.md"), reportBody("TON is −62.8% from high."));
    git("add", "-A");

    expect(changed("--cached")).toEqual(["research/crypto-2026-07-31.md"]);
  });

  test("a pure rename with no edit is still gated (R100)", () => {
    renameSync(join(repo, "research", "crypto-2026-07-24.md"), join(repo, "research", "crypto-v2.md"));
    git("add", "-A");
    git("commit", "-qm", "rename only");

    expect(changed("HEAD~1", "HEAD")).toEqual(["research/crypto-v2.md"]);
  });

  test("no regression: added and modified reports are still listed, deleted ones are not", () => {
    writeFileSync(join(repo, "research", "crypto-2026-08-01.md"), reportBody("new"));
    writeFileSync(join(repo, "research", "crypto-2026-07-24.md"), reportBody("edited materially, different text entirely"));
    git("add", "-A");
    git("commit", "-qm", "add+modify");
    expect(changed("HEAD~1", "HEAD").sort()).toEqual([
      "research/crypto-2026-07-24.md",
      "research/crypto-2026-08-01.md",
    ]);

    rmSync(join(repo, "research", "crypto-2026-08-01.md"));
    git("add", "-A");
    git("commit", "-qm", "delete");
    // A deleted report has nothing to validate; listing it would fail the loop spuriously.
    expect(changed("HEAD~1", "HEAD")).toEqual([]);
  });

  test("non-report files are never gated", () => {
    writeFileSync(join(repo, "README.md"), "hello");
    git("add", "-A");
    git("commit", "-qm", "readme");
    expect(changed("HEAD~1", "HEAD")).toEqual([]);
  });

  test("it works from a SUBDIRECTORY (repo-relative pathspecs must be anchored)", () => {
    renameSync(join(repo, "research", "crypto-2026-07-24.md"), join(repo, "research", "crypto-2026-07-31.md"));
    git("add", "-A");
    git("commit", "-qm", "redate");

    const out = execFileSync("bash", [script, "HEAD~1", "HEAD"], {
      cwd: join(repo, "research"),
      encoding: "utf8",
    });
    expect(out.split("\n").filter(Boolean)).toEqual(["research/crypto-2026-07-31.md"]);
  });
});

describe("B1 — both call sites delegate to the shared script (no drift)", () => {
  test("gates.yml and pre-commit call changed_reports.sh and no longer use ACM", async () => {
    const root = resolve(import.meta.dir, "../../..");
    const yml = await Bun.file(join(root, ".github/workflows/gates.yml")).text();
    const hook = await Bun.file(join(root, "hooks/pre-commit")).text();

    expect(yml).toContain("changed_reports.sh");
    expect(hook).toContain("changed_reports.sh");

    // Strip comments: both files NAME the old flag when explaining why it was wrong.
    // Only EXECUTABLE lines matter, and none of them may reintroduce the bypass.
    const code = (s: string) =>
      s.split("\n").filter((l) => !l.trim().startsWith("#")).join("\n");
    expect(code(yml)).not.toMatch(/--diff-filter=ACM\b(?!R)/);
    expect(code(hook)).not.toMatch(/--diff-filter=ACM\b(?!R)/);
  });
});
