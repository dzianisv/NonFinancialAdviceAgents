#!/usr/bin/env bun
/**
 * validate_skill_md.ts — dependency-free structural validator for canonical skills.
 *
 * Why this exists: GitHub Copilot CLI (>=1.0.70) silently drops any skill whose
 * SKILL.md frontmatter it cannot parse, or whose `description` exceeds 1024 parsed
 * characters. A dropped skill is invisible — it never shows in `copilot skill list`
 * and never loads — so a broken frontmatter degrades the agent with no error at
 * call time. This validator makes those failures loud and pre-commit-blockable.
 *
 * What it checks (all Copilot-load-relevant, one pass, reports EVERY failure):
 *   1. Delimited YAML frontmatter present (opening `---`, closing `---`/`...`).
 *   2. Scalar `name` and `description` present and non-empty strings.
 *   3. `name` is a valid slug, <=64 chars, and matches its directory name.
 *   4. `description` parsed length <=1024 characters.
 *   5. No duplicate canonical `name` across skills.
 *   6. Malformed YAML — specifically an unquoted `: ` (mapping indicator) inside a
 *      PLAIN scalar value, which is exactly what makes libyaml/js-yaml (and Copilot)
 *      throw "mapping values are not allowed in this context". Quoted and block
 *      (`>` / `|`) scalars may legally contain `: ` and are NOT flagged.
 *
 * It supports the YAML scalar styles actually used across the repo — plain,
 * single/double-quoted (with escapes + `\uXXXX`), and folded `>` / literal `|`
 * block scalars (with `+`/`-` chomping) — and computes parsed length per style so a
 * legal multiline description is never rejected merely for being multiline.
 *
 * Final authoritative cross-check: when the `copilot` binary is on PATH, it also runs
 * `copilot skill list` and surfaces any repo skill Copilot itself failed to load.
 * When `copilot` is absent this is skipped explicitly (noted, not silently ignored)
 * and the local structural checks still stand on their own.
 *
 * Usage:
 *   bun .agents/scripts/skills/validate_skill_md.ts            # all .agents/skills/<name>/SKILL.md
 *   bun .agents/scripts/skills/validate_skill_md.ts path/to/SKILL.md [more ...]
 *   bun .agents/scripts/skills/validate_skill_md.ts --no-copilot   # skip Copilot cross-check
 *   bun .agents/scripts/skills/validate_skill_md.ts --index        # staged-snapshot mode (see below)
 *
 * --index (staged-snapshot mode):
 *   Validates the git INDEX (what will actually be committed), not the working tree.
 *   This is what `hooks/pre-commit` runs. The repo root is resolved at runtime from
 *   the current working directory via `git rev-parse --show-toplevel` (not from where
 *   this script lives), so it always gates the repo where the commit is happening.
 *   Canonical skills are enumerated from `git ls-files -s -- .agents/skills` (so staged
 *   additions are included and staged deletions are excluded), and each SKILL.md's
 *   content is read from its staged blob via `git cat-file -p <sha>` — never from the
 *   working-tree file. `--no-copilot` and explicit file arguments are irrelevant in this
 *   mode (ignored); the `copilot skill list` cross-check is always skipped in --index
 *   mode by design, because it inspects the working tree, which is the wrong snapshot
 *   for a staged gate — the local structural checks are sufficient there. Zero staged
 *   canonical skills is not an error: it exits 0 with an informational note.
 *
 * Exit code 0 = all valid; 1 = one or more failures; 2 = bad invocation.
 */

import { readdirSync, readFileSync, existsSync, statSync } from "node:fs";
import { join, dirname, basename, resolve, relative } from "node:path";

const MAX_DESCRIPTION = 1024;
const MAX_NAME = 64;
const SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
// Canonical shape for a skill file's repo-relative path (immediate subdirectory only),
// matching the existing discoverSkillFiles() semantics.
const CANONICAL_SKILL_RE = /^\.agents\/skills\/[^/]+\/SKILL\.md$/;

// Repo root: this file lives at <root>/.agents/scripts/skills/validate_skill_md.ts
const REPO_ROOT = resolve(import.meta.dir, "..", "..", "..");
const SKILLS_DIR = join(REPO_ROOT, ".agents", "skills");

type Finding = { path: string; errors: string[] };

interface ParsedFrontmatter {
  ok: boolean;               // frontmatter structurally extractable
  errors: string[];          // structural / YAML errors found while parsing
  name?: string;
  description?: string;
}

interface DoubleQuotedUnescapeResult {
  value: string;
  invalidEscape?: string;
}

interface QuotedScalarReadResult {
  value: string;
  linesConsumed: number;
  terminated: boolean;
  invalidEscape?: string;
  trailingContent?: string;
}

/** Unescape a YAML double-quoted scalar body (between the quotes). */
function unescapeDoubleQuoted(body: string): DoubleQuotedUnescapeResult {
  let out = "";
  for (let i = 0; i < body.length; i++) {
    const c = body[i];
    if (c !== "\\") { out += c; continue; }
    const n = body[++i];
    if (n === undefined) return { value: out, invalidEscape: "\\" };
    switch (n) {
      case "a": out += "\x07"; break;
      case "n": out += "\n"; break;
      case "t": out += "\t"; break;
      case "v": out += "\v"; break;
      case "r": out += "\r"; break;
      case "b": out += "\b"; break;
      case "f": out += "\f"; break;
      case "0": out += "\0"; break;
      case "e": out += "\x1b"; break;
      case '"': out += '"'; break;
      case "\\": out += "\\"; break;
      case "/": out += "/"; break;
      case "N": out += "\u0085"; break;
      case "_": out += "\u00A0"; break;
      case "L": out += "\u2028"; break;
      case "P": out += "\u2029"; break;
      case " ": out += " "; break;
      case "\t": out += "\t"; break;
      case "\n":
      case "\r": {
        if (n === "\r" && body[i + 1] === "\n") i++;
        while (body[i + 1] === " " || body[i + 1] === "\t") i++;
        break;
      }
      case "u": {
        const hex = body.slice(i + 1, i + 5);
        if (!/^[0-9a-fA-F]{4}$/.test(hex)) return { value: out, invalidEscape: `\\u${hex}` };
        out += String.fromCharCode(parseInt(hex, 16));
        i += 4;
        break;
      }
      case "x": {
        const hex = body.slice(i + 1, i + 3);
        if (!/^[0-9a-fA-F]{2}$/.test(hex)) return { value: out, invalidEscape: `\\x${hex}` };
        out += String.fromCharCode(parseInt(hex, 16));
        i += 2;
        break;
      }
      case "U": {
        const hex = body.slice(i + 1, i + 9);
        if (!/^[0-9a-fA-F]{8}$/.test(hex)) return { value: out, invalidEscape: `\\U${hex}` };
        const cp = parseInt(hex, 16);
        if (cp > 0x10FFFF || (cp >= 0xD800 && cp <= 0xDFFF)) {
          return { value: out, invalidEscape: `\\U${hex}` };
        }
        out += String.fromCodePoint(cp);
        i += 8;
        break;
      }
      default: return { value: out, invalidEscape: `\\${n}` };
    }
  }
  return { value: out };
}

/** Detect disallowed trailing content after a quoted scalar's closing quote. */
function getTrailingQuotedGarbage(afterClosingQuote: string): string | undefined {
  const trimmed = afterClosingQuote.trimStart();
  if (trimmed === "" || trimmed.startsWith("#")) return undefined;
  return trimmed;
}

/**
 * Read a double-quoted scalar that may span lines.
 * `terminated` is false when the frontmatter runs out of lines before an unescaped closing
 * quote is found — a real YAML parser throws "unexpected end of the stream" in that case,
 * so the caller must surface it as an error rather than accept the partial content.
 */
function readDoubleQuoted(first: string, rest: string[]): QuotedScalarReadResult {
  // `first` includes the opening quote at index 0.
  let buf = first;
  let consumed = 0;
  while (true) {
    // find closing unescaped quote after the opening one
    let i = 1;
    let closed = -1;
    while (i < buf.length) {
      if (buf[i] === "\\") { i += 2; continue; }
      if (buf[i] === '"') { closed = i; break; }
      i++;
    }
    if (closed >= 0) {
      const unescaped = unescapeDoubleQuoted(buf.slice(1, closed));
      return {
        value: unescaped.value,
        linesConsumed: consumed,
        terminated: true,
        invalidEscape: unescaped.invalidEscape,
        trailingContent: getTrailingQuotedGarbage(buf.slice(closed + 1)),
      };
    }
    if (consumed >= rest.length) return { value: unescapeDoubleQuoted(buf.slice(1)).value, linesConsumed: consumed, terminated: false }; // unterminated
    // A continuation line must be indented (or blank) — a real YAML parser never folds an
    // unindented `key: value` line into a flow scalar. Without this guard an unterminated
    // quote could silently "borrow" a later top-level key's closing quote as its own
    // terminator, masking the very error this function exists to report.
    const next = rest[consumed];
    if (next.trim() !== "" && !/^\s/.test(next)) {
      return { value: unescapeDoubleQuoted(buf.slice(1)).value, linesConsumed: consumed, terminated: false };
    }
    // continuation line: YAML folds a newline in a multiline double-quoted scalar to a space
    buf = buf + " " + next.trim();
    consumed++;
  }
}

/**
 * Read a single-quoted scalar that may span lines.
 * See readDoubleQuoted's doc comment for why `terminated` matters — an unterminated quote is
 * a malformed-YAML condition, not a best-effort value to accept silently.
 */
function readSingleQuoted(first: string, rest: string[]): QuotedScalarReadResult {
  let buf = first;
  let consumed = 0;
  while (true) {
    let i = 1;
    let closed = -1;
    while (i < buf.length) {
      if (buf[i] === "'") {
        if (buf[i + 1] === "'") { i += 2; continue; } // '' escape
        closed = i; break;
      }
      i++;
    }
    if (closed >= 0) {
      return {
        value: buf.slice(1, closed).replace(/''/g, "'"),
        linesConsumed: consumed,
        terminated: true,
        trailingContent: getTrailingQuotedGarbage(buf.slice(closed + 1)),
      };
    }
    if (consumed >= rest.length) return { value: buf.slice(1).replace(/''/g, "'"), linesConsumed: consumed, terminated: false };
    // Same indentation guard as readDoubleQuoted — see its comment for why this matters.
    const next = rest[consumed];
    if (next.trim() !== "" && !/^\s/.test(next)) {
      return { value: buf.slice(1).replace(/''/g, "'"), linesConsumed: consumed, terminated: false };
    }
    buf = buf + " " + next.trim();
    consumed++;
  }
}

/** Fold/collect a block scalar. `header` is the text after the key colon (e.g. ">-", "|"). */
function readBlockScalar(header: string, rest: string[]): [string, number] {
  const style = header[0]; // '>' or '|'
  const chomp = header.includes("-") ? "strip" : header.includes("+") ? "keep" : "clip";
  // collect subsequent lines that are blank or indented (more indented than the key at col 0)
  const block: string[] = [];
  let consumed = 0;
  while (consumed < rest.length) {
    const l = rest[consumed];
    if (l.trim() === "") { block.push(""); consumed++; continue; }
    if (/^\s/.test(l)) { block.push(l); consumed++; continue; }
    break; // next top-level key
  }
  // determine indentation from first non-blank line
  const firstNonBlank = block.find((l) => l.trim() !== "");
  const indent = firstNonBlank ? (firstNonBlank.match(/^\s*/)?.[0].length ?? 0) : 0;
  const stripped = block.map((l) => (l.trim() === "" ? "" : l.slice(indent)));

  let text: string;
  if (style === "|") {
    text = stripped.join("\n");
  } else {
    // folded: consecutive non-empty lines join with a single space; blank line -> newline
    let out = "";
    let prevBlank = true;
    for (const l of stripped) {
      if (l === "") { out += "\n"; prevBlank = true; }
      else { if (!prevBlank) out += " "; out += l; prevBlank = false; }
    }
    text = out;
  }
  // chomping affects trailing newlines
  text = text.replace(/\n+$/, (m) => (chomp === "strip" ? "" : chomp === "keep" ? m : "\n"));
  return [text, consumed];
}

/**
 * Parse the frontmatter for a SKILL.md string. Focused on top-level `name` and
 * `description`, and on detecting the plain-scalar `: ` mapping error that breaks
 * a real YAML parser.
 */
function parseFrontmatter(content: string): ParsedFrontmatter {
  const errors: string[] = [];
  const lines = content.split(/\r?\n/);
  if (lines.length === 0 || lines[0].trim() !== "---") {
    return { ok: false, errors: ["missing or malformed YAML frontmatter (no opening `---`)"] };
  }
  let closeIdx = -1;
  for (let i = 1; i < lines.length; i++) {
    const t = lines[i].trim();
    if (t === "---" || t === "...") { closeIdx = i; break; }
  }
  if (closeIdx < 0) {
    return { ok: false, errors: ["missing or malformed YAML frontmatter (no closing `---`)"] };
  }
  const fm = lines.slice(1, closeIdx);

  const scalars: Record<string, string> = {};
  const seen: Record<string, number> = {};

  let i = 0;
  while (i < fm.length) {
    const line = fm[i];
    if (line.trim() === "") { i++; continue; }
    if (/^\s/.test(line)) { i++; continue; } // nested/continuation of a non-target key

    const m = /^([^\s:][^:]*):(?:[ \t]+(.*)|)\s*$/.exec(line);
    if (!m) { i++; continue; } // not a recognizable top-level key line
    const key = m[1];
    const rawVal = (m[2] ?? "").trim();
    seen[key] = (seen[key] ?? 0) + 1;
    const after = fm.slice(i + 1);

    let value = "";
    let consumed = 0;
    let malformedQuotedScalar = false;

    if (rawVal === "") {
      // empty inline: could be a mapping (e.g. `metadata:`) with indented children,
      // or an explicitly empty scalar. Treat as empty scalar for our target keys.
      value = "";
    } else if (rawVal[0] === '"') {
      const quoted = readDoubleQuoted(rawVal, after);
      value = quoted.value;
      consumed = quoted.linesConsumed;
      if (!quoted.terminated) {
        malformedQuotedScalar = true;
        errors.push(
          `malformed YAML: unterminated double-quoted scalar for "${key}" — no closing " found before the frontmatter ends. Add the closing quote or escape it with \\".`
        );
      } else {
        if (quoted.invalidEscape) {
          malformedQuotedScalar = true;
          errors.push(
            `malformed YAML: invalid escape sequence "${quoted.invalidEscape}" in double-quoted scalar for "${key}" — YAML double-quoted scalars only support \\\\, \\", \\n, \\t, \\r, \\0, \\b, \\f, \\v, \\a, \\e, \\/, \\N, \\_, \\L, \\P, \\xHH, \\uHHHH, \\UHHHHHHHH, \\<space>, and \\<tab> escapes.`
          );
        }
        if (quoted.trailingContent !== undefined) {
          malformedQuotedScalar = true;
          const preview = quoted.trailingContent.slice(0, 60) + (quoted.trailingContent.length > 60 ? "…" : "");
          errors.push(
            `malformed YAML: unexpected content after closing quote for "${key}" — found ${JSON.stringify(preview)} after the closing quote. Quoted scalars cannot have trailing content other than a comment.`
          );
        }
      }
    } else if (rawVal[0] === "'") {
      const quoted = readSingleQuoted(rawVal, after);
      value = quoted.value;
      consumed = quoted.linesConsumed;
      if (!quoted.terminated) {
        malformedQuotedScalar = true;
        errors.push(
          `malformed YAML: unterminated single-quoted scalar for "${key}" — no closing ' found before the frontmatter ends. Add the closing quote (use '' to escape a literal quote).`
        );
      } else if (quoted.trailingContent !== undefined) {
        malformedQuotedScalar = true;
        const preview = quoted.trailingContent.slice(0, 60) + (quoted.trailingContent.length > 60 ? "…" : "");
        errors.push(
          `malformed YAML: unexpected content after closing quote for "${key}" — found ${JSON.stringify(preview)} after the closing quote. Quoted scalars cannot have trailing content other than a comment.`
        );
      }
    } else if (rawVal[0] === ">" || rawVal[0] === "|") {
      [value, consumed] = readBlockScalar(rawVal, after);
    } else {
      // plain scalar (possibly multi-line continuation)
      const parts = [rawVal];
      while (consumed < after.length) {
        const l = after[consumed];
        if (l.trim() === "") break;
        if (!/^\s/.test(l)) break; // next top-level key
        parts.push(l.trim());
        consumed++;
      }
      value = parts.join(" ");
      // Detect the mapping-value error: a plain scalar cannot contain `: ` (colon+space)
      // or a colon at end-of-token. This is exactly Copilot's parse failure.
      for (const token of parts) {
        if (/:(\s|$)/.test(token)) {
          errors.push(
            `malformed YAML: mapping values are not allowed here — unquoted "${key}:" value contains a colon+space ("${token.slice(0, 60)}${token.length > 60 ? "…" : ""}"). Quote the value or use a block scalar.`
          );
          break;
        }
      }
    }

    if ((key === "name" || key === "description") && !malformedQuotedScalar) {
      if (!(key in scalars)) scalars[key] = value;
    }
    i += 1 + consumed;
  }

  for (const [k, n] of Object.entries(seen)) {
    if (n > 1) errors.push(`duplicate top-level key "${k}" in frontmatter`);
  }

  return {
    ok: errors.length === 0,
    errors,
    name: "name" in scalars ? scalars.name : undefined,
    description: "description" in scalars ? scalars.description : undefined,
  };
}

/**
 * Validate the frontmatter/content of one SKILL.md. `path` is used only to derive the
 * expected directory-name match for `name` (via `basename(dirname(path))`) and does NOT
 * need to point at a real file on disk — this is what lets index mode validate a blob
 * read from git (`git cat-file -p <sha>`) using its index-relative path, with identical
 * logic to the working-tree path. Returns list of error strings (empty = valid).
 */
function validateContent(path: string, content: string): { errors: string[]; name?: string } {
  const errors: string[] = [];

  const fm = parseFrontmatter(content);
  errors.push(...fm.errors);

  const dirName = basename(dirname(path));

  // name checks
  if (fm.name === undefined) {
    errors.push("missing `name` in frontmatter");
  } else if (typeof fm.name !== "string" || fm.name.trim() === "") {
    errors.push("`name` must be a non-empty string");
  } else {
    const name = fm.name.trim();
    if (name.length > MAX_NAME) errors.push(`\`name\` exceeds ${MAX_NAME} characters (is ${name.length})`);
    if (!SLUG_RE.test(name)) errors.push(`\`name\` "${name}" is not a valid slug (lowercase letters, digits, single hyphens)`);
    if (name !== dirName) errors.push(`\`name\` "${name}" does not match directory name "${dirName}"`);
  }

  // description checks
  if (fm.description === undefined) {
    errors.push("missing `description` in frontmatter");
  } else if (typeof fm.description !== "string" || fm.description.trim() === "") {
    errors.push("`description` must be a non-empty string");
  } else if (fm.description.length > MAX_DESCRIPTION) {
    errors.push(`\`description\` parsed length ${fm.description.length} exceeds ${MAX_DESCRIPTION} characters`);
  }

  return { errors, name: fm.name?.trim() };
}

/** Validate one SKILL.md file on disk (working tree). Thin wrapper around validateContent. */
function validateFile(path: string): { errors: string[]; name?: string } {
  let content: string;
  try {
    content = readFileSync(path, "utf8");
  } catch (e) {
    return { errors: [`cannot read file: ${(e as Error).message}`] };
  }
  return validateContent(path, content);
}

/** Discover all canonical SKILL.md paths under .agents/skills/. */
function discoverSkillFiles(): string[] {
  if (!existsSync(SKILLS_DIR)) return [];
  const out: string[] = [];
  for (const entry of readdirSync(SKILLS_DIR)) {
    const dir = join(SKILLS_DIR, entry);
    let s;
    try { s = statSync(dir); } catch { continue; }
    if (!s.isDirectory()) continue;
    const md = join(dir, "SKILL.md");
    if (existsSync(md)) out.push(md);
  }
  return out.sort();
}

/**
 * Authoritative cross-check via `copilot skill list`. Returns a map of repo SKILL.md
 * path -> reason for any skill Copilot itself failed to load, or null if copilot is
 * unavailable / cross-check could not run.
 */
function copilotCrossCheck(): Record<string, string> | null {
  const which = Bun.spawnSync(["sh", "-c", "command -v copilot"]);
  if (which.exitCode !== 0) return null;
  const proc = Bun.spawnSync(["copilot", "skill", "list"], { stdout: "pipe", stderr: "pipe" });
  const text = new TextDecoder().decode(proc.stdout) + "\n" + new TextDecoder().decode(proc.stderr);
  const failures: Record<string, string> = {};
  const lines = text.split(/\r?\n/);
  let inFailed = false;
  for (const raw of lines) {
    if (/failed to load/i.test(raw)) { inFailed = true; continue; }
    if (!inFailed) continue;
    // bullet lines look like:  • <path>: <reason>
    const m = /^\s*[\u2022*-]\s*(.+?):\s*(.+)$/.exec(raw);
    if (!m) continue;
    const p = m[1].trim();
    const reason = m[2].trim();
    // scope to repo skills only (relative `.agents/skills/...` or absolute under repo)
    const abs = p.startsWith("/") ? p : join(REPO_ROOT, p);
    if (abs.startsWith(SKILLS_DIR + "/") || p.startsWith(".agents/skills/")) {
      failures[resolve(abs)] = reason;
    }
  }
  return failures;
}

/** Parse `git ls-files -s -z` NUL-delimited output into { sha, path } records. */
function parseIndexEntries(output: string): { sha: string; path: string }[] {
  const out: { sha: string; path: string }[] = [];
  for (const rec of output.split("\0")) {
    if (rec === "") continue;
    // record shape: "<mode> <sha> <stage>\t<path>"
    const tab = rec.indexOf("\t");
    if (tab < 0) continue;
    const left = rec.slice(0, tab);
    const path = rec.slice(tab + 1);
    const fields = left.split(/\s+/).filter(Boolean);
    const sha = fields[1];
    if (!sha) continue;
    out.push({ sha, path });
  }
  return out;
}

/**
 * --index (staged-snapshot) mode: validate exactly what `git commit` would record,
 * reading each canonical SKILL.md's content from its staged blob in the index rather
 * than from the working tree. This is what the pre-commit hook runs, so an unstaged
 * broken edit never blocks an unrelated commit, and a broken staged change can never
 * slip through because a working-tree copy happens to be fixed.
 */
function runIndexMode() {
  const rootProc = Bun.spawnSync(["git", "rev-parse", "--show-toplevel"], {
    cwd: process.cwd(),
    stdout: "pipe",
    stderr: "pipe",
  });
  if (rootProc.exitCode !== 0) {
    console.error("✖ --index: not inside a git repository");
    process.exit(2);
  }
  const gitRoot = new TextDecoder().decode(rootProc.stdout).trim();

  const lsProc = Bun.spawnSync(
    ["git", "-C", gitRoot, "ls-files", "-s", "-z", "--", ".agents/skills"],
    { stdout: "pipe", stderr: "pipe" }
  );
  if (lsProc.exitCode !== 0) {
    console.error(`✖ --index: \`git ls-files\` failed: ${new TextDecoder().decode(lsProc.stderr).trim()}`);
    process.exit(2);
  }

  const entries = parseIndexEntries(new TextDecoder().decode(lsProc.stdout))
    .filter((e) => CANONICAL_SKILL_RE.test(e.path));

  if (entries.length === 0) {
    console.log("ℹ --index: no canonical SKILL.md in the git index — nothing to validate");
    process.exit(0);
  }

  const findings: Finding[] = [];
  const namesToPaths: Record<string, string[]> = {};

  for (const { sha, path } of entries) {
    const catProc = Bun.spawnSync(["git", "-C", gitRoot, "cat-file", "-p", sha], {
      stdout: "pipe",
      stderr: "pipe",
    });
    if (catProc.exitCode !== 0) {
      findings.push({
        path,
        errors: [`cannot read index blob ${sha}: ${new TextDecoder().decode(catProc.stderr).trim()}`],
      });
      continue;
    }
    const content = new TextDecoder().decode(catProc.stdout);
    const { errors, name } = validateContent(path, content);
    if (name) (namesToPaths[name] ??= []).push(path);
    if (errors.length) findings.push({ path, errors });
  }

  // duplicate canonical name across the entire staged canonical set
  for (const [name, paths] of Object.entries(namesToPaths)) {
    if (paths.length > 1) {
      for (const p of paths) {
        let fnd = findings.find((x) => x.path === p);
        if (!fnd) { fnd = { path: p, errors: [] }; findings.push(fnd); }
        fnd.errors.push(`duplicate canonical name "${name}" (also used by: ${paths.filter((x) => x !== p).join(", ")})`);
      }
    }
  }

  const total = entries.length;
  const failed = findings.length;
  const infoNote = `ℹ --index: staged-snapshot mode — validating ${total} canonical SKILL.md from the git index (copilot working-tree cross-check skipped by design)`;

  if (failed === 0) {
    console.log(`✓ ${total} SKILL.md validated — all pass`);
    console.log("  " + infoNote);
    process.exit(0);
  }

  console.error(`✖ ${failed}/${total} SKILL.md failed validation:\n`);
  for (const f of findings.sort((a, b) => a.path.localeCompare(b.path))) {
    console.error(`  ${relative(gitRoot, resolve(gitRoot, f.path))}`);
    for (const e of f.errors) console.error(`     - ${e}`);
  }
  console.error("\n  " + infoNote);
  console.error(`\nFix the frontmatter above. Descriptions must parse as YAML and be <=${MAX_DESCRIPTION} chars.`);
  process.exit(1);
}

function main() {
  const argv = process.argv.slice(2);

  if (argv.includes("--index")) {
    runIndexMode();
    return;
  }

  const noCopilot = argv.includes("--no-copilot");
  const explicit = argv.filter((a) => !a.startsWith("--"));

  const files = explicit.length > 0
    ? explicit.map((p) => resolve(p))
    : discoverSkillFiles();

  if (files.length === 0) {
    console.error("✖ no SKILL.md files found to validate");
    process.exit(2);
  }

  const findings: Finding[] = [];
  const namesToPaths: Record<string, string[]> = {};

  for (const f of files) {
    const { errors, name } = validateFile(f);
    if (name) (namesToPaths[name] ??= []).push(f);
    if (errors.length) findings.push({ path: f, errors });
  }

  // duplicate canonical name across skills
  for (const [name, paths] of Object.entries(namesToPaths)) {
    if (paths.length > 1) {
      for (const p of paths) {
        let fnd = findings.find((x) => x.path === p);
        if (!fnd) { fnd = { path: p, errors: [] }; findings.push(fnd); }
        fnd.errors.push(`duplicate canonical name "${name}" (also used by: ${paths.filter((x) => x !== p).map((x) => relative(REPO_ROOT, x)).join(", ")})`);
      }
    }
  }

  // Copilot authoritative cross-check (only meaningful for a full-repo run)
  let copilotNote = "";
  if (!noCopilot && explicit.length === 0) {
    const cp = copilotCrossCheck();
    if (cp === null) {
      copilotNote = "ℹ copilot not on PATH — skipped authoritative `copilot skill list` cross-check (local structural checks still applied)";
    } else {
      const n = Object.keys(cp).length;
      copilotNote = n === 0
        ? "✓ copilot cross-check: 0 repo skills failed to load"
        : `✖ copilot cross-check: ${n} repo skill(s) failed to load`;
      for (const [p, reason] of Object.entries(cp)) {
        const rp = resolve(p);
        let fnd = findings.find((x) => resolve(x.path) === rp);
        if (!fnd) { fnd = { path: rp, errors: [] }; findings.push(fnd); }
        if (!fnd.errors.some((e) => e.startsWith("copilot:")))
          fnd.errors.push(`copilot: ${reason}`);
      }
    }
  } else if (noCopilot) {
    copilotNote = "ℹ --no-copilot: authoritative `copilot skill list` cross-check disabled";
  }

  const total = files.length;
  const failed = findings.length;

  if (failed === 0) {
    console.log(`✓ ${total} SKILL.md validated — all pass`);
    if (copilotNote) console.log("  " + copilotNote);
    process.exit(0);
  }

  console.error(`✖ ${failed}/${total} SKILL.md failed validation:\n`);
  for (const f of findings.sort((a, b) => a.path.localeCompare(b.path))) {
    console.error(`  ${relative(REPO_ROOT, f.path)}`);
    for (const e of f.errors) console.error(`     - ${e}`);
  }
  if (copilotNote) console.error("\n  " + copilotNote);
  console.error(`\nFix the frontmatter above. Descriptions must parse as YAML and be <=${MAX_DESCRIPTION} chars.`);
  process.exit(1);
}

main();
