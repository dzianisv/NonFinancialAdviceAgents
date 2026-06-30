# How We Built a Multi-Lens Financial-Analyst Agent (and Used It to Ask "Should We Buy Bitcoin Now?")

This is a build log, not a pitch. We wanted a tool that could answer a real money question — *should the live conservative crypto book buy BTC right now?* — without collapsing into a single confident-sounding opinion. The answer we got back was more useful than any one model could have produced, mostly because we forced it to disagree with itself first. Here is how it was built, what broke, and one honest moment where the agent refused to write a tidy story that wasn't true.

Everything below was built with Claude Code subagents and Agent Skills.

## The starting point: books, not prompts

The project began messily, which is worth admitting because most write-ups pretend the inputs were clean. The user dropped a `books/` folder onto the machine and asked, roughly, "which of these are any good for market analysis?" The selection drifted across a few requests — Benjamin Graham value investing came up, then technical analysis, then systematic/quant trading — before it settled. There was no single clean "here are the four canonical books" moment. It converged to:

- Carver, *Systematic Trading*
- Bernstein, *The Ultimate Day Trader*
- Howell, *Capital Wars*
- Housel, *The Psychology of Money*

Important detail: the agent did **not** go download these. The user supplied the EPUBs. The agent's first real job was just to turn them into something it could reason over.

## Step 1: extract the books to text

A small Python script using `ebooklib` and `BeautifulSoup` walked each EPUB, pulled the document items, and stripped HTML to plain text. Nothing clever. The output was large — individual extractions ran from roughly 300k to 640k characters. That number matters for the next decision.

## Step 2: one subagent per book

You cannot usefully dump 1.5M characters of prose into a working context and expect sharp reasoning out the other end. So the main agent spawned **one subagent per book**, each with a single instruction: read your assigned extraction in chunks and return a structured, implementation-ready distillation. Not a book report — a spec. Each subagent returned:

- the core thesis,
- the actual frameworks,
- exact numbers and formulas,
- a "how to apply this" section,
- caveats and failure modes,
- verbatim quotes for grounding.

The payoff here is mechanical but real: the main agent's context never held the raw books. It held five tight distillations. The expensive reading happened in throwaway windows. This is the single most reusable pattern in the whole project — subagents as a context firewall.

## Step 3: distillations become Agent Skills

Each distillation was turned into an Agent Skill: a `SKILL.md` router plus a `references/` directory holding a per-theme knowledge base. The skills follow the open Agent Skills spec — `name` and `description` frontmatter, `compatibility: opencode`. What we ended up with:

- `analyse-systematic-trading` — Carver. Trend filters, volatility targeting, position sizing, Kelly.
- `analyse-technical` — Bernstein. Setups, triggers, the "no trigger, no trade" discipline.
- `analyse-onchain` — Howell-grounded global-liquidity reasoning, plus on-chain, sentiment, and DCA methodology.
- `analyst-benjamin-graham` — the value lens, built from canonical knowledge rather than a supplied book.

### Grounding, and being honest about it

The skills are built from the actual text, with quotes and real numbers, so a verdict can point at where it came from. But grounding cuts both ways, and the interesting cases are the misattribution traps.

Take Howell. The famous "5–6 year global liquidity cycle" and the Bitcoin-as-high-beta-liquidity-asset framing are from his **later** work — not from the 2020 *Capital Wars* the user actually supplied. The lazy move is to let the skill quietly imply it all came from the book in the folder. Instead the skill says so: this part is from the book, this part is from later work, treat it accordingly. A grounded skill that misattributes is worse than an ungrounded one, because it launders a guess into a citation.

Every skill also carries its own blind spot, on purpose. **A lens is not gospel.** A value lens that can't price a non-cash-flowing asset should say that out loud, not pretend gold and Bitcoin are simply "uninvestable."

## Step 4: the quorum

Here is where it gets fun. The main agent launched a **quorum of five subagents**. Each one loaded exactly **one** skill and judged the **same** question on the **same** market facts:

> Should the live ~$177k conservative crypto book buy BTC now?

One lens each. No cross-talk. Identical inputs. Each subagent returned a structured verdict: a call (BUY / ACCUMULATE / WAIT / PASS), a conviction level, a sizing recommendation, grounded reasoning, an explicit "what would change my mind," and the blind spot of its own lens.

The point of a quorum of narrow lenses — instead of one model told to "give a balanced view" — is that **the disagreement is the signal.** A blended view averages a liquidity bear and a debasement bull into a shrug. The quorum keeps both, because each is naming a *different risk*. You want the liquidity guy to scare you about the tide going out at the same time the debasement guy scares you about holding idle cash. Averaging that is how you end up with a recommendation that protects against nothing.

## The honest part: the post that almost lied

When the user first asked for *this* write-up, the agent started to draft it — and caught a problem. Steps 4 and the synthesis below had **not actually been run in that session.** There *had* been a multi-lens panel earlier, but it was a different, prior session on macro economists (Dalio, Druckenmiller, et al.), not these four books.

The clean move, narratively, would have been to describe the quorum as if it had happened. It would have read fine. It would have been false.

So the agent flagged the gap instead of papering over it. The user's response was the right one: "make it real first." The quorum was then actually executed against the live book and current market facts — and only then was this post written.

Frame this as a design principle, because it is the most important thing here: **an honest agent refuses to fabricate its own success story.** Surfacing disconfirming evidence — including "the thing you're about to write about didn't happen" — has to win over producing a satisfying narrative. An agent that will quietly invent its own track record is more dangerous than one that's merely wrong, because you stop being able to trust the parts that *are* right.

## The BTC case study

**Market facts, 2026-06-08:** BTC ~$66k, down ~48% from the $126k October-2025 top. MVRV-Z ~0.34 (cheap-to-fair). Fear & Greed = 11 (Extreme Fear). Price below the 200-day MA. RSI ~21. Long-term holders re-accumulating. Global liquidity cycle rolling over. The book currently holds **zero** spot BTC and has ~$103k sitting idle below 3% APY. A *moderate* plan proposes ~$21k spot BTC (~12%); a *conservative* variant holds none.

Five lenses, same facts:

| Lens | Verdict | Conviction | Sizing | One-line reasoning |
|---|---|---|---|---|
| Howell / global liquidity | WAIT | High | $0 for now | Tide is going out; liquidity leads equities 6–12 months. "Stocks bottom in the Calm regime" — we're in Turbulence. Wait for liquidity to re-cross trend. |
| Carver / systematic | ACCUMULATE-STAGED, small | Medium | ~$5–7k starter, cap ~$15k | Trend filter is DOWN (below 200d), so a pure rule sizes near-zero. Vol-target + Half-Kelly (σ~70%, negative skew) caps the sleeve. The "cheap" story is exactly the narrative bias rules exist to suppress. |
| Bernstein / TA | ACCUMULATE-STAGED via DCA | Low | DCA, not a timed entry | Valid set-up (oversold + extreme fear + forming divergence) but **no trigger yet** — "no trigger, no trade." And TA doesn't even apply to a long-horizon allocator; DCA beats TA timing after costs. |
| Graham / value | PASS as investment | High | ≤3% (~$5k) quarantined, never 12% | No cash flows → no intrinsic value → no margin of safety. A 48% fall isn't "cheap" against an undefined value. Blind spot, conceded: a 1949 cash-flow lens also valued gold at zero. |
| Alden / debasement | ACCUMULATE-STAGED | High (structural) | ~12% self-custody, ~4 tranches | Under fiscal dominance, holding $103k idle cash *is* the risk. "Size for volatility, hold through cycles." Near-term liquidity rollover is a reason to stage, not skip. |

### What the quorum actually agreed on

Read the table for conflict and you miss the consensus, which is sharp:

- **Nobody says lump-sum.** Unanimous. Even the structural bull stages in.
- **Start small.** ~$5–7k first tranche — the overlap of Carver, Graham, and Alden, three lenses that otherwise barely speak the same language.
- **Self-custody.**
- **Gate the remaining tranches on confirmation** — a 200-day reclaim and/or liquidity turning — **not on fear.**

That last point is where the quorum earned its keep. The agent's earlier *solo* answer had said to *accelerate* tranches into extreme fear — buy more as it gets scarier. The liquidity and trend lenses (Howell, Carver) outvoted that directly: extreme fear is not a buy trigger when the tide is still going out and price is below trend. The quorum corrected a real, specific error the single-voice version had made.

And the conservative zero-BTC stance never gets argued away. Graham and Howell both land somewhere a disciplined holder of nothing can stand on. The system produces a defensible "do less," which a hype machine never will.

## What we'd reuse

- **Subagents as a context firewall.** The reasoning agent should almost never hold the raw corpus. Read in disposable windows, return specs.
- **Narrow lenses over blended balance.** Preserve dissent. The spread between verdicts tells you which risks are live.
- **Grounding with honesty flags.** Quote the source, and flag when "the framework" actually comes from somewhere other than the document in hand.
- **Make every lens state its own blind spot.** It costs one sentence and it stops the lens from being treated as gospel.
- **Honesty over narrative.** If the workflow didn't happen, say so and go make it happen — don't write the press release.

---

*Not financial advice. This is an educational write-up about an agent-design methodology; the market figures are illustrative and public, and nothing here is a recommendation to buy or sell anything. Built with Claude Code subagents and Agent Skills.*
