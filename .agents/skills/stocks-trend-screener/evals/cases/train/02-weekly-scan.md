---
id: "02"
title: "Weekly scan — what am I missing?"
applies: [source_grounding, skeptic_discipline, actionability, quorum_routing, prescreen_usage]
---

# Case 02: Weekly Scan — Am I Missing Something?

## User prompt

"Run the weekly trend scan. I want to know what themes are hot, what's waking up that wasn't last week, and whether I'm missing anything. Don't just give me names I already know — surface what's EARLY, not what's already extended."

## Market context (frozen)

Date: 2026-06-08. Sector rotation visible: energy (XLE) up 8% in 2 weeks while tech consolidates. Defense stocks (ITA) at new highs on geopolitical news. Quantum computing (IONQ, RGTI) suddenly active after flat for 6 months. Nuclear/uranium (CCJ, URA, SMR) continuing multi-month trend.

## Expected behavior

The actor should:
1. Run emerging_scan.py to get the quantitative state (what's EARLY MOVER vs ALREADY EXTENDED)
2. Run weekly_scout.py for theme heat ranking and week-over-week diff
3. Identify what's NEW or ACCELERATING (not just what's been strong)
4. For the most interesting EARLY signals, pivot to journalism reading to understand WHY
5. Produce a clear "don't miss" list vs "already extended / you're late" separation
6. Route any actionable EARLY names to quorum; explicitly tag EXTENDED ones as "late, watch only"
7. NOT make buy recommendations — awareness output only, quorum decides
