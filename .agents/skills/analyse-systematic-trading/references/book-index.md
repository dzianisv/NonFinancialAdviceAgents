# Book Index & Provenance — Systematic Trading Lens

> Source: Robert Carver, *Systematic Trading: A unique new method for designing trading and investing systems* (Harriman House, 2015) — the single primary source for this skill, present in this repo's `books/`. Distilled 2026-06-07.

## Primary source (grounded)
- **Robert Carver, *Systematic Trading* (Harriman House, 2015).** Every reference file in this skill is distilled from it. All numbers, formulas, scalars, and quotes are Carver's (preserved verbatim-ish). The book is in `books/` as: *"Robert Carver - Systematic Trading - A unique new method for designing trading and investing systems (2015, Harriman House) - libgen.li.epub"*.

Carver's background: former AHL (Man Group) portfolio manager; the book generalises an institutional managed-futures framework into something an individual can run in a spreadsheet.

## Carver's later open-source implementation (post-book)
- **`pysystemtrade`** — Carver's open-source Python implementation of this exact framework (forecasts, scalars, vol targeting, IDM/FDM, costs). **It postdates the 2015 book**, so treat code specifics as "Carver's later work," not as the book's text. It is the most faithful reference implementation of references 02–07.
- His blog *Investment Idiocy* and the follow-up book *Leveraged Trading* (2019) extend the same ideas — **not distilled here**; cite as pointers only.

## Reference map
| File | Theme |
|---|---|
| `01-systematic-vs-discretionary.md` | Biases, the commitment mechanism, three trader types, the three pitfalls |
| `02-modular-framework.md` | Modular pipeline, the no-account-size invariant, subsystems |
| `03-forecasts-and-trading-rules.md` | Continuous vol-standardised forecasts, EWMAC + carry, scalars |
| `04-volatility-targeting-and-position-sizing.md` | Vol target, volatility scalar, Kelly/Half-Kelly, worked example |
| `05-portfolio-construction-and-risk-allocation.md` | Handcrafting/bootstrapping, IDM/FDM, pessimism factors |
| `06-fitting-overfitting-and-costs.md` | Overfitting discipline, standardised cost, the speed limit |
| `07-automation-and-implementation.md` | Spreadsheet/Python/IB/pysystemtrade, TradingView limits, inertia |

## Adjacent canonical works — NOT yet distilled (cite as pointers, not grounded content)
These are the standard adjacent texts on systematic/algorithmic trading. They are **not** sources for this skill; do not attribute claims to them as if grounded. Flag clearly if a user wants them distilled (a future task).
- **Ernest P. Chan — *Algorithmic Trading* (2013) and *Quantitative Trading* (2009).** Mean-reversion vs momentum, backtest pitfalls, execution; more US-equities/stat-arb flavoured than Carver.
- **Andreas Clenow — *Following the Trend* (2013).** A concrete diversified-futures trend-following system; complements Carver's EWMAC/portfolio chapters with a worked managed-futures program.
- **Perry Kaufman — *Trading Systems and Methods* (6th ed.).** Encyclopaedic catalogue of indicators, systems, and testing methods; breadth reference.

## Cross-references within this repo
- **`trend-following`, `regime-detection`, `risk-management`, `portfolio-construction`** (and a future `backtesting` skill): this skill is their **how-to-build-and-validate** counterpart and shares the vocabulary (vol targeting, diversification, costs).
- **`analyse-technical`:** the *discretionary / chart-pattern* counterpart with a **weak evidence base**; the systematic + backtested path here is the rigorous alternative (or, for a discretionary view, wrap it as a *semi-automatic* forecast, ref 01/03).
- **GOAL.md mandate:** any strategy must be backtested with realistic costs before trading — Carver's **overfitting discipline + cost speed limit (ref 06)** *are* that gate.

## Honesty note
Carver repeatedly stresses humility: realistic Sharpes are modest (~0.3–0.5), sustained SR>1.0 essentially never, and most backtests over-state edge. Carry his caveats and pessimism factors with the numbers; never present a backtested figure as a forward expectation without a haircut.
