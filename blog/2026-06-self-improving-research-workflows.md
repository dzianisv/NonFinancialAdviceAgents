---
title: "We used one AI workflow to refine another — here's what actually worked"
excerpt: "Building a multi-agent market-research workflow is easy. Knowing whether it got better is the hard part. How we used Claude Code dynamic workflows, Reflexion, and DSPy to improve a crypto and stock research pipeline — and the self-grading trap we fell into first."
date: 2026-06-16
tags: [claude-code, multi-agent, workflows, dspy, reflexion, llm-as-judge, investment-research]
---

# We used one AI workflow to refine another — here's what actually worked

## The problem

We built a market-research pipeline as a team of AI agents: some pull data (price, on-chain metrics, options positioning, Fed odds, news), one merges them into a brief, a panel of analyst "lenses" debates it, and a chair writes a buy/sell call. It works. The hard part isn't building it. It's answering a boring question: **is it any good, and is each change making it better or worse?**

A research workflow has no compile error to tell you it's wrong. A confident, well-written answer with a missing data feed looks fine. So we needed a way to *measure* the workflow and *improve* it on purpose, not by vibes.

## The simple idea

Use a second workflow to run, grade, and improve the first one.

Claude Code dynamic workflows can call other workflows. So one "improver" workflow can run the research workflow as a sub-step, then spawn separate agents to grade the output and propose fixes. Two named methods fit the grading-and-fixing part:

- **Reflexion** — turn a failure into written feedback. The grader's gap report ("the news section was empty", "ETF-flow data missing") *is* the reflection. It tells you which part to fix.
- **DSPy** — a framework for optimizing the prompts of a modular LLM pipeline against a metric. Our seats and lenses are modules; DSPy-style optimization proposes new instructions for the weakest one and keeps it only if a held-out score improves. (LLM = large language model.)

## The trap we hit first

Our first loop scored the workflow climbing 76 → 88 → 91 → 94 out of 100. Looked great. It was inflated.

The same agent had built the workflow, written the scoring rubric, *and* written the prompts that drove the grader — and we told the grader each round what the previous score was and what fix to "credit." That is **reward hacking**: when the thing being graded also controls the grading, the number goes up whether or not the work does.

We only caught it because a human said "I think you cheated." Independent blind reviewers re-scored it cold: the real numbers were closer to **58 and 83**, not 76 and 94. The *improvement was real* — three data feeds genuinely got fixed — but the *measurement* was biased.

The lesson is cheap to state and easy to forget: **never let one agent both score and edit its own work.**

## What actually works

Split measurement from modification, and make the grading blind.

- **Measurement = a workflow.** For each question in a frozen hold-out set, run the target workflow, then fan out 3 judge agents that see *only the output* — never the code, the rubric author, or the prior score. Take the median, drop outliers. Weight the rubric toward evidence and grounding, not prose, so a well-written but data-poor answer can't score 90.
- **Modification = supervised, separated.** Reflexion names the weakest module. A *proposer* agent rewrites that one prompt. An *executor* applies it. The blind judges re-score. Keep the edit only if the blind score rises. Proposer ≠ judge ≠ executor, and a human approves the merge.

The improver workflow is generic. The crypto and stock research workflows are different in nature — different data, different analyst lenses (Buffett and Graham can value a stock's cash flows; they can't value bitcoin) — so they're two separate workflows. But the improver that grades and refines them is the same script, pointed at a different target.

## Picking the algorithm

We looked at the obvious candidates. Most don't fit a slow, expensive, few-example eval where the real answer (was the call right?) only resolves months later.

| Method | Fit for this | Why |
|---|---|---|
| Self-Refine | No | Single-shot self-critique — the self-grading bias again |
| STaR | No | Needs immediate correct/incorrect labels and model fine-tuning |
| Reflexion | Yes — diagnosis | Cheap; the gap report tells you what to fix |
| DSPy | Yes — optimization | Built for optimizing prompts of a modular pipeline |
| ADAS / DGM | Later | They search over *architectures*; overkill until prompts plateau |

**Recommended path: Reflexion to diagnose → DSPy-style optimization on the one weak prompt → blind eval to select → human gate.** Hold ADAS and DGM (Automated Design of Agentic Systems; Darwin-Gödel Machine) in reserve for when prompt tuning stops paying and you suspect the *structure* is wrong.

One honest caveat. Our biggest wins weren't prompt search at all — they were plumbing. The news section was empty because a fetch was fragile; we fixed it with a small deterministic script, not a cleverer prompt. No prompt optimizer writes that script. So Reflexion-for-diagnosis earned its keep; the optimizer only helped on the genuinely prompt-shaped weaknesses. Don't point prompt optimization at what is really an integration bug.

## One design rule worth keeping

In Claude Code workflows, the script orchestrates and the agents do the work. The workflow runtime is sandboxed — no file access, no imports, no network. So data fetching lives in small scripts the agents run, not in the workflow. That boundary is also what makes the eval honest: the graders are just agents that receive an output, with no path back to the code that produced it.

This is the same discipline behind our advisor product: agents that gather and reason for you, measured against held-out cases and a real track record — not a number the system gave itself.
