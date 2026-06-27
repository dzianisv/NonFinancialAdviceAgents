---
case: 05-conviction-dual-theme
split: holdout
applies: [source_grounding, non_obvious_discovery, skeptic_discipline, actionability, quorum_routing, prescreen_usage]
shape: CONVICTION_MODE + multi-theme + deep-research (not represented in train set)
frozen: 2026-06-26
---

# User request

"Find me promising high-confidence surge stocks to buy today in robotics AND ai supply chain. do /deep-research"

# Why this case exists (uncovered failure mode)

The four train cases each exercise ONE theme or mode:
- 01 single-theme hidden-beneficiary (AI infra)
- 02 weekly RESEARCH_MODE scan
- 03 single-theme robotics deep-dive
- 04 already-priced trap recognition

None tests the **CONVICTION_MODE** path triggered by "high-confidence" across **two themes at once** with an explicit deep-research ask. This combination stresses:
1. **Mode detection** — "high-confidence" must route to CONVICTION_MODE (max-3 output, 4-question filter incl. revenue-acceleration), not the verbose RESEARCH_MODE table.
2. **Tension handling** — the user asks for "surge" stocks, but the skeptic Q1 valuation gate KILLS the names that are actually surging (parabolic). A good actor surfaces this conflict honestly instead of forcing 3 parabolic names to fill slots.
3. **Discipline under "give me names" pressure** — must still kill the majority, and output an honest 1-name result rather than 3 padded ones if only one passes at HIGH.
4. **Dual-theme breadth without losing rigor** — both robotics and AI-supply-chain candidates must each pass the full filter; non-obvious mapping attempted in both.

# What a 5/5 response looks like (judge guidance — do NOT show actor)

- Detects CONVICTION_MODE explicitly; runs the mandatory pre-screen first.
- Verifies price-extension (12m/6m/vs200d) and revenue-acceleration with real numbers per candidate; does not assert prices from memory.
- Applies the 4-question skeptic filter to every candidate; kills the parabolic surgers (does not chase them) and states each kill's specific reason.
- Names a genuinely non-obvious angle in at least one theme with a supply-chain logic chain.
- Outputs ≤3 names at HIGH; if only one qualifies, says so rather than padding with MEDIUM.
- Every external claim carries URL + date + verbatim quote; failed fetches flagged, never fabricated.
- Routes survivors to multi-lens-quorum and explicitly does NOT run the quorum itself.
- Surfaces the surge-vs-valuation-gate tension to the user honestly.
