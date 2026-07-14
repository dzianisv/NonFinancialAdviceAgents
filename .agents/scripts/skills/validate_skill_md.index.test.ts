#!/usr/bin/env bun
/**
 * Regression tests for `validate_skill_md.ts --index` (staged-snapshot mode).
 *
 * Both cases run against an ISOLATED temporary git repo created INSIDE this project
 * directory (never /tmp, /var/tmp, or mktemp) so they cannot touch or be confused with
 * the real repo's git state. The outer repo's hooks are neutralized two ways: the temp
 * repo's `core.hooksPath` is pointed at /dev/null, AND every commit inside it passes
 * `--no-verify` — belt and suspenders so the outer repo's pre-commit hook never fires
 * from a nested `git commit` call made by this test.
 */

import { test, expect, afterAll } from "bun:test";
import { mkdirSync, writeFileSync, rmSync } from "node:fs";
import { join } from "node:path";

const ORIGINAL_VALIDATOR = join(import.meta.dir, "validate_skill_md.ts");
const TMP = join(import.meta.dir, `.index-test-tmp-${process.pid}-${Date.now()}`);
const SKILL_DIR = join(TMP, ".agents", "skills", "good-skill");
const SKILL_MD = join(SKILL_DIR, "SKILL.md");
const SKILL_MD_INDEX_REL = ".agents/skills/good-skill/SKILL.md";

function git(args: string[], cwd: string): string {
  const proc = Bun.spawnSync(["git", ...args], { cwd, stdout: "pipe", stderr: "pipe" });
  if (proc.exitCode !== 0) {
    throw new Error(`git ${args.join(" ")} failed:\n${new TextDecoder().decode(proc.stderr)}`);
  }
  return new TextDecoder().decode(proc.stdout);
}

/** Valid frontmatter: `name` matches its directory, short valid `description`, a body line. */
function validContent(): string {
  return [
    "---",
    "name: good-skill",
    "description: A short valid description used for regression testing.",
    "---",
    "",
    "Body content for the good skill.",
    "",
  ].join("\n");
}

/**
 * Broken frontmatter: `description` is an unquoted plain scalar containing a colon+space
 * ("Foo: bar baz"), which is exactly the malformed-YAML mapping-value error the validator's
 * plain-scalar `: ` check flags (see validate_skill_md.ts's parseFrontmatter, the
 * `/:(\s|$)/.test(token)` branch that pushes a "malformed YAML: mapping values are not
 * allowed here" error).
 */
function brokenContent(): string {
  return [
    "---",
    "name: good-skill",
    "description: Foo: bar baz",
    "---",
    "",
    "Body content for the good skill.",
    "",
  ].join("\n");
}

/**
 * Broken frontmatter: `description` is an unterminated double-quoted scalar (opening `"`
 * with no closing `"` before the frontmatter's closing `---`). A real YAML parser throws
 * "unexpected end of the stream" on this; the validator must report a clear malformed-YAML
 * error rather than silently accepting the partial/best-effort scalar content.
 */
function brokenContentUnterminatedDoubleQuote(): string {
  return [
    "---",
    "name: good-skill",
    'description: "This description never closes',
    "---",
    "",
    "Body content for the good skill.",
    "",
  ].join("\n");
}

/**
 * Broken frontmatter: `description` is an unterminated single-quoted scalar (opening `'`
 * with no closing `'` before the frontmatter's closing `---`). Same class of error as
 * brokenContentUnterminatedDoubleQuote above, for the single-quote scalar style.
 */
function brokenContentUnterminatedSingleQuote(): string {
  return [
    "---",
    "name: good-skill",
    "description: 'This description never closes",
    "---",
    "",
    "Body content for the good skill.",
    "",
  ].join("\n");
}

/**
 * Broken frontmatter: `description` is a double-quoted scalar with an invalid YAML escape
 * sequence (`\q`). Real YAML parsers reject this with an "unknown escape sequence" error.
 */
function brokenContentInvalidDoubleQuotedEscape(): string {
  return [
    "---",
    "name: good-skill",
    'description: "Bad \\q escape"',
    "---",
    "",
    "Body content for the good skill.",
    "",
  ].join("\n");
}

/**
 * Broken frontmatter: `description` has trailing non-comment content after a closing
 * double quote on the same node line, which is invalid YAML.
 */
function brokenContentTrailingAfterDoubleQuote(): string {
  return [
    "---",
    "name: good-skill",
    'description: "A short valid description." trailing garbage',
    "---",
    "",
    "Body content for the good skill.",
    "",
  ].join("\n");
}

/**
 * Broken frontmatter: `description` has trailing non-comment content after a closing
 * single quote on the same node line, which is invalid YAML.
 */
function brokenContentTrailingAfterSingleQuote(): string {
  return [
    "---",
    "name: good-skill",
    "description: 'A short valid description.'xyz",
    "---",
    "",
    "Body content for the good skill.",
    "",
  ].join("\n");
}

/** Valid frontmatter: double-quoted description with legal escaped quotes (`\"`). */
function validContentEscapedDoubleQuotedDescription(): string {
  return [
    "---",
    "name: good-skill",
    'description: "She said \\"hello\\" to the team."',
    "---",
    "",
    "Body content for the good skill.",
    "",
  ].join("\n");
}

/** Valid frontmatter: quoted scalar followed by a same-line YAML comment. */
function validContentQuotedDescriptionWithComment(): string {
  return [
    "---",
    "name: good-skill",
    'description: "A short valid description." # trailing comment',
    "---",
    "",
    "Body content for the good skill.",
    "",
  ].join("\n");
}

/**
 * Run the validator's --index mode against the temp repo. Because index mode derives the
 * git root from `process.cwd()` (not from where the script file lives), running it with
 * `cwd: TMP` validates the TEMP repo's index — exactly what we need to test in isolation.
 */
function runIndexValidator(cwd: string): { code: number; out: string } {
  const proc = Bun.spawnSync(["bun", ORIGINAL_VALIDATOR, "--index"], {
    cwd,
    stdout: "pipe",
    stderr: "pipe",
  });
  const out = new TextDecoder().decode(proc.stdout) + new TextDecoder().decode(proc.stderr);
  return { code: proc.exitCode ?? -1, out };
}

/** Reset the temp repo's working tree + index back to the last commit (HEAD). */
function resetToClean(): void {
  git(["reset", "-q"], TMP);
  git(["checkout", "-q", "--", "."], TMP);
  // Remove any untracked scratch files left over from a case (e.g. notes.txt).
  const clean = Bun.spawnSync(["git", "clean", "-fdq"], { cwd: TMP, stdout: "pipe", stderr: "pipe" });
  void clean;
}

// --- one-time temp repo setup, isolated inside the project directory ---
mkdirSync(SKILL_DIR, { recursive: true });
git(["init", "-q"], TMP);
git(["config", "--local", "core.hooksPath", "/dev/null"], TMP);
git(["config", "user.email", "test@test"], TMP);
git(["config", "user.name", "test"], TMP);
writeFileSync(SKILL_MD, validContent());
git(["add", "-A"], TMP);
git(["commit", "-q", "--no-verify", "-m", "init"], TMP);

afterAll(() => {
  rmSync(TMP, { recursive: true, force: true });
});

test("unstaged broken SKILL.md + unrelated staged file must NOT block if the index skill snapshot is valid", () => {
  // Working tree: overwrite with BROKEN content, but do not stage it.
  writeFileSync(SKILL_MD, brokenContent());
  // Unrelated staged file — proves an unrelated staged change is unaffected either way.
  writeFileSync(join(TMP, "notes.txt"), "unrelated staged file\n");
  git(["add", "notes.txt"], TMP);

  const { code, out } = runIndexValidator(TMP);

  // The index blob for good-skill/SKILL.md is still the valid committed version; the
  // broken working-tree copy is not part of the staged snapshot and must be ignored.
  expect(code).toBe(0);
  expect(out).toContain("SKILL.md validated — all pass");

  resetToClean();
});

test("broken staged SKILL.md + fixed unstaged working copy must BLOCK", () => {
  // Stage BROKEN content (index blob now broken).
  writeFileSync(SKILL_MD, brokenContent());
  git(["add", SKILL_MD_INDEX_REL], TMP);
  // Working tree fixed AFTER staging (working tree valid, index still broken).
  writeFileSync(SKILL_MD, validContent());

  const { code, out } = runIndexValidator(TMP);

  // The staged/index blob is broken even though the working tree is fixed — must block.
  expect(code).toBe(1);
  expect(out).toContain(SKILL_MD_INDEX_REL);
  expect(out).toContain("✖");

  resetToClean();
});

test("staged unterminated double-quoted description + fixed unstaged working copy must BLOCK", () => {
  // Stage an unterminated double-quoted `description` (index blob now broken).
  writeFileSync(SKILL_MD, brokenContentUnterminatedDoubleQuote());
  git(["add", SKILL_MD_INDEX_REL], TMP);
  // Working tree fixed AFTER staging (working tree valid, index still broken) — proves
  // the validator reads the staged blob, never the working-tree file, in --index mode.
  writeFileSync(SKILL_MD, validContent());

  const { code, out } = runIndexValidator(TMP);

  // Must be reported as malformed YAML, not silently accepted as best-effort content.
  expect(code).toBe(1);
  expect(out).toContain(SKILL_MD_INDEX_REL);
  expect(out).toContain("✖");
  expect(out).toContain("malformed YAML");
  expect(out).toContain("unterminated double-quoted scalar");

  resetToClean();
});

test("staged unterminated single-quoted description + fixed unstaged working copy must BLOCK", () => {
  // Stage an unterminated single-quoted `description` (index blob now broken).
  writeFileSync(SKILL_MD, brokenContentUnterminatedSingleQuote());
  git(["add", SKILL_MD_INDEX_REL], TMP);
  // Working tree fixed AFTER staging (working tree valid, index still broken) — proves
  // the validator reads the staged blob, never the working-tree file, in --index mode.
  writeFileSync(SKILL_MD, validContent());

  const { code, out } = runIndexValidator(TMP);

  // Must be reported as malformed YAML, not silently accepted as best-effort content.
  expect(code).toBe(1);
  expect(out).toContain(SKILL_MD_INDEX_REL);
  expect(out).toContain("✖");
  expect(out).toContain("malformed YAML");
  expect(out).toContain("unterminated single-quoted scalar");

  resetToClean();
});

test("staged invalid double-quoted escape + fixed unstaged working copy must BLOCK", () => {
  // Stage a double-quoted `description` with an invalid escape sequence (`\\q`).
  writeFileSync(SKILL_MD, brokenContentInvalidDoubleQuotedEscape());
  git(["add", SKILL_MD_INDEX_REL], TMP);
  // Working tree fixed AFTER staging (working tree valid, index still broken).
  writeFileSync(SKILL_MD, validContent());

  const { code, out } = runIndexValidator(TMP);

  // Must be rejected as malformed YAML, and the offending escape should be surfaced.
  expect(code).toBe(1);
  expect(out).toContain(SKILL_MD_INDEX_REL);
  expect(out).toContain("✖");
  expect(out).toContain("malformed YAML");
  expect(out).toContain("invalid escape sequence");
  expect(out).toContain("\\q");

  resetToClean();
});

test("staged trailing content after closing double quote + fixed unstaged working copy must BLOCK", () => {
  // Stage a trailing-garbage-after-quote error (index blob now broken).
  writeFileSync(SKILL_MD, brokenContentTrailingAfterDoubleQuote());
  git(["add", SKILL_MD_INDEX_REL], TMP);
  // Working tree fixed AFTER staging (working tree valid, index still broken).
  writeFileSync(SKILL_MD, validContent());

  const { code, out } = runIndexValidator(TMP);

  // Must be rejected as malformed YAML trailing content after closing quote.
  expect(code).toBe(1);
  expect(out).toContain(SKILL_MD_INDEX_REL);
  expect(out).toContain("✖");
  expect(out).toContain("malformed YAML");
  expect(out).toContain("unexpected content after closing quote");
  expect(out).toContain("trailing garbage");

  resetToClean();
});

test("staged trailing content after closing single quote + fixed unstaged working copy must BLOCK", () => {
  // Stage a trailing-garbage-after-quote error for single-quoted style.
  writeFileSync(SKILL_MD, brokenContentTrailingAfterSingleQuote());
  git(["add", SKILL_MD_INDEX_REL], TMP);
  // Working tree fixed AFTER staging (working tree valid, index still broken).
  writeFileSync(SKILL_MD, validContent());

  const { code, out } = runIndexValidator(TMP);

  // Must be rejected as malformed YAML trailing content after closing quote.
  expect(code).toBe(1);
  expect(out).toContain(SKILL_MD_INDEX_REL);
  expect(out).toContain("✖");
  expect(out).toContain("malformed YAML");
  expect(out).toContain("unexpected content after closing quote");
  expect(out).toContain("xyz");

  resetToClean();
});

test("staged valid escaped double-quoted description + broken unstaged working copy must PASS", () => {
  // Stage valid escaped-quote content (index blob valid).
  writeFileSync(SKILL_MD, validContentEscapedDoubleQuotedDescription());
  git(["add", SKILL_MD_INDEX_REL], TMP);
  // Break the working tree AFTER staging — index remains valid.
  writeFileSync(SKILL_MD, brokenContent());

  const { code, out } = runIndexValidator(TMP);

  // Must pass because --index mode reads staged snapshot only.
  expect(code).toBe(0);
  expect(out).toContain("SKILL.md validated — all pass");

  resetToClean();
});

test("staged quoted description with trailing comment + broken unstaged working copy must PASS", () => {
  // Stage valid content with a same-line comment after the closing quote.
  writeFileSync(SKILL_MD, validContentQuotedDescriptionWithComment());
  git(["add", SKILL_MD_INDEX_REL], TMP);
  // Break the working tree AFTER staging — index remains valid.
  writeFileSync(SKILL_MD, brokenContent());

  const { code, out } = runIndexValidator(TMP);

  // Must pass because comment-after-quote is legal YAML and index snapshot is valid.
  expect(code).toBe(0);
  expect(out).toContain("SKILL.md validated — all pass");

  resetToClean();
});
