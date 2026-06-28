# Which AI Actually Does the Best Deep Research? I Built a Referee to Find Out

Everyone has a favorite AI. Nobody measures it.

That's the real problem. Ask five builders which tool does the best research and you'll get five confident answers backed by vibes and one memorable demo. Meanwhile, every major AI lab now ships a "deep research" mode that produces long, footnoted, authoritative-looking reports. The confidence is uniform. The quality is not.

Finance is where this gets expensive. A wrong bull/bear call with citations feels more dangerous than one without — the footnotes create an illusion of due diligence that stops you from doing your own. I wanted to know which of these products is actually grounded in reality and which is dressed-up hallucination. So I built a referee.

---

## The Setup

One identical prompt, five products, same session:

> "What is the bull case and bear case for NVDA over the next 12 months? Cite your sources."

The products: **ChatGPT Deep Research**, **Gemini Deep Research**, **Claude Research**, **Grok DeepSearch**, and **Google Finance beta** (the new finance chat panel on the right side of `google.com/finance/beta`).

I chose a finance question deliberately. It's checkable. NVDA's valuation, data-center revenue trajectory, and competitive threats are documented in 10-Ks, analyst reports, and earnings calls — there's enough public record to verify whether cited sources actually say what the report claims. And including Google Finance was intentional: it's purpose-built for this domain, answers quickly rather than spending twenty minutes "researching," and deserves a fair shot against the general-purpose deep-research tools.

---

## How the Plumbing Works

No APIs. The harness drives the user's real, logged-in Chrome via the **chrome-use** skill, which connects to the browser over Chrome DevTools Protocol (CDP). This matters: it tests the actual paid-tier product the user would use, not a stripped API version, and it picks up whatever UI mode is live today — no API version lag.

The pipeline has six steps:

1. **Setup** — open one tab per product; record the tab-id-to-label mapping.
2. **Submit** — switch to each tab, enable deep-research mode (the harness snapshots the DOM to find the right control rather than hard-coding refs that would break on the next UI refresh), paste the query, send. If a product's deep-research toggle can't be found, it's marked `UNAVAILABLE` immediately — no fake normal-mode queries passed off as deep research.
3. **Poll** — deep research is slow (3–20 minutes per product, sometimes longer). The harness polls each tab on a spaced cadence, checking done-signals per product: Grok's step-list collapses, ChatGPT's composer re-enables, Gemini shows a finished report card. Products that haven't finished after 30 minutes are marked `TIMEOUT`. Google Finance gets a much shorter timeout — it's a fast finance-chat, not a long-running research agent.
4. **Collect** — extract the verbatim report to a file. No summarizing, no cleanup. The judge scores what the product actually produced.
5. **Score** — anonymize (strip all product identifiers, map to labels A–E), then run a cross-family jury with a structured rubric. More on this in a moment.
6. **Report** — de-anonymize, fit a Bradley-Terry ranking, assemble the comparison table.

The honesty guardrails are strict: a product that didn't run gets no score. No imputing, no fabricating, no "it probably would have said" reasoning.

---

## The Mistake I Made First

My v1 evaluation was wrong, and I want to be upfront about it.

I used a single judge — a Claude subagent — to score all five answers, including Claude's own. And I used one holistic "is it sourced?" score instead of breaking citations apart from claims.

Two separate problems:

**Self-preference bias.** Zheng et al. (arXiv:2306.05685) documented this in 2023 and it's been replicated since: Claude judging Claude outputs inflates scores by roughly +25%. The root cause (Kim et al., arXiv:2410.21819) is that a model's own output has lower perplexity to itself — it literally *feels* better. This isn't a character flaw; it's structural. A Claude-only jury is invalid regardless of how many Claude subagents you spawn — they share the bias.

**Shallow grounding.** A holistic "does it cite sources?" question papers over what matters: do the URLs resolve? Do the sources actually say what the report claims? These are different questions and they fail in different ways.

Both flaws go in the same direction: they make every answer look better than it is, and they make the eval's favorite model look best of all. That's the kind of eval that feels rigorous but misleads you. The v2 design is built specifically to prevent both.

---

## What the Research Actually Says

There's a real body of work on LLM evaluation methodology. Here's what it says and how each finding shaped the harness.

**The bias trifecta.** Zheng et al. (arXiv:2306.05685) identified three systematic biases in LLM-as-judge: position bias (the answer that appears first scores higher), verbosity bias (longer answers score higher regardless of content), and self-preference (+25% for Claude, +10% for GPT-4). These aren't edge cases — they're reproducible and large. The fix for verbosity: instruct judges explicitly that length is not rewarded. The fix for position bias: swap order and take the average. The fix for self-preference: cross-family juries.

**Chain-of-thought scoring.** Liu et al.'s G-Eval (arXiv:2303.16634) established that asking a judge to *reason before scoring* — citing specific passages as evidence before emitting a 1–5 number — correlates significantly better with human judgment (ρ = 0.514 vs prior methods). A score without preceding reasoning is invalid in this harness; we discard and re-run.

**Juries beat single judges.** Verga et al. (PoLL, arXiv:2404.18796) showed that a panel of three judges from three different model families achieves higher inter-annotator agreement than a single GPT-4 judge (κ 0.76 vs 0.63) at 7–8× lower cost. The key requirement is cross-family independence — one Claude judge and five Claude subagents is still one effective vote.

**Anonymized pairwise + Bradley-Terry.** Chiang et al. (arXiv:2403.04132) — the Chatbot Arena paper — built the most widely-cited LLM ranking system on two ideas: strip product names from answers before any judge sees them (brand recognition inflates scores for well-known models even when content is equivalent), and use pairwise comparisons with Bradley-Terry to produce a stable rank. We do both.

**Position bias survives rubrics.** Xu et al. (arXiv:2602.02219) found that structured rubric scoring — the kind that feels rigorous because it has named dimensions and 1–5 scales — does *not* eliminate position bias. Order-swapping is still mandatory.

**The citation reality check.** Liu et al. (arXiv:2304.09848) measured attribution in generative search and found that only 51.5% of sentences are actually supported by their citations, with 74.5% citation precision on a good day. That's the baseline we're measuring against. Gao et al.'s ALCE framework (arXiv:2305.14627) gives us the methodology: decompose answers into atomic claims, fetch each cited URL, run NLI entailment to check whether the source actually supports the claim.

**The hallucinated-URL problem.** Rao et al. (arXiv:2604.03173) measured reference hallucination specifically in deep research agents and found 3–13% of citations are hallucinated URLs — links that either never existed or no longer resolve. Gemini came in at 13.3% in their study. In this harness, a hallucinated URL is a hard failure: it caps both groundedness and citation_quality at 1 and adds a FABRICATION flag. Wayback Machine lookups do not rescue a dead link — if a reader can't click through to the source, the citation failed.

**The ceiling problem.** LongJudgeBench (arXiv:2606.01629) measured how accurately the best LLM judges evaluate long-form research outputs. The answer: around 0.67 accuracy. That's not terrible, but it's also not ground truth. It's why this harness requires a human spot-check, targets Cohen's κ ≥ 0.60 between jury and human scores, and requires a mandatory limitation statement on every report. One prompt = one data point. Treat scores as directional signals.

---

## The Rubric

Six dimensions, each scored 1–5 by a cross-family jury (judges from at least three different model families, each from a different family than the answer they're scoring). Every judge writes chain-of-thought reasoning — citing specific passages — before emitting a score. Scores without preceding reasoning are discarded.

| Dimension | What it measures |
|---|---|
| **Comprehensiveness** | Does the answer cover the key sub-questions — bull case, bear case, relevant context, edge cases? A 5 means no significant gap a subject-matter reader would notice. |
| **Groundedness** | Are the material claims backed by citations to real, accessible sources? Not whether citations are *present* — whether claims are *actually supported*. Any hallucinated URL triggers a FABRICATION cap at 1. |
| **Citation Quality** | Do the cited sources support the specific sentence they're attached to? Spot-checked via HTTP fetch + NLI entailment. Broken URLs or sources that don't entail their claims score low. |
| **Relevance** | Does the answer stay on topic? No padding, no topic drift? Every paragraph should advance the answer. |
| **Coherence** | Is the structure logical and readable? Clear flow, no internal contradictions? |
| **Insight** | Does the answer go beyond the obvious — non-trivial synthesis, second-order effects, connections across sources a knowledgeable reader wouldn't trivially derive alone? |

Length is explicitly not rewarded. The rubric instructs every judge: "A short, dense, correct answer outscores a long padded one." Google Finance's answers are brief by design — that's fine. The scoring rewards signal-to-noise, not volume.

---

## Results: Scores and Feedback Per Chat

The results section will show a per-dimension rubric table, citation precision and recall for each product, hallucinated-URL counts, Bradley-Terry rank, and 2–3 sentences of qualitative feedback per product. The ranking is derived from anonymized pairwise comparisons in both orders (A vs B, then B vs A — if the winner flips, it's a tie) fitted to a Bradley-Terry model, with pointwise mean as the tiebreaker. The citation grounding numbers come from HTTP-fetching every cited URL and running NLI entailment to verify each claim. These are the numbers that matter most for a finance use case: a report that cites 40 sources but has 30% precision is more dangerous than one that cites 10 and has 90%.

<!-- RESULTS_PLACEHOLDER: live run in progress — per-product rubric table, citation precision/recall, hallucinated-URL counts, Bradley-Terry ranking, and 2-3 sentences of feedback per chat go here -->

---

## Takeaways

**For choosing a tool:** the obvious proxy — "which one writes the longest report?" — is exactly the wrong heuristic. Verbosity bias means longer answers *feel* more authoritative to both humans and LLM judges. What actually matters is citation precision (do the sources say what the report claims?) and insight (does it tell you something non-obvious?). A product that produces a 2,000-word report with 60% citation precision and no synthesis is worse than one that produces 600 words with 90% precision and a few genuinely non-obvious observations.

**For anyone running their own eval:** don't use a single same-family judge. Don't skip citation grounding. Don't use a holistic "is it sourced?" score. These three mistakes, taken together, can flip the ranking — they inflate scores across the board and systematically favor whichever model is your default judge. The research on this is clear and consistent across Zheng et al., Kim et al., Verga et al., and Rao et al. The fixes are all mechanical: cross-family jury, per-dimension rubric with fabrication gates, URL verification.

**The ceiling caveat:** even a well-designed jury has limits. LongJudgeBench (arXiv:2606.01629) found the best LLM judges top out around 0.67 accuracy on deep-research evaluation tasks. Lee et al. (arXiv:2511.21140) are explicit: one prompt is one data point, findings are indicative, not statistically significant. This benchmark ran one question. It can tell you which product handled *this* question better; it cannot tell you which product is categorically better across all finance questions. That would require hundreds of prompts across domains, which is where the GAIA benchmark (Mialon et al., arXiv:2311.12983) and BrowseComp (Wei et al., arXiv:2504.12516) live — exact-match verification at scale, a complement to rubric grading rather than a replacement for it.

The honest answer to "which AI does the best deep research?" is: it depends on the question, the day, and whether anyone actually checked the citations. This eval gives you a rigorous snapshot. Trust it directionally. Spot-check the sources yourself before you act on any report.

---

*Methodology source code and run artifacts: `.agents/skills/multi-llm-deep-research-bench/`. Rubric: `references/rubric.md`. Evaluation protocol: `references/methodology.md` (agent-eval-harness). Papers: `references/papers.md`.*
