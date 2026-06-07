# Books — knowledge base

Full-text markdown of reference books, converted from EPUB for grep/search and
for grounding skills (per the progressive-disclosure pattern used by the
`analytics-lyn-alden` and macro-panel skills).

Source `.epub` files are kept locally but git-ignored (see `.gitignore`); only
the markdown is committed. Conversion: `pandoc <file>.epub -t gfm-raw_html
--wrap=none`, then strip leftover image/svg lines.

| File | Book | Author | Relevance |
|------|------|--------|-----------|
| [systematic-trading-carver.md](systematic-trading-carver.md) | Systematic Trading | Robert Carver | Vol-targeting, forecast combination, position sizing → `analyst-systematic-trading` |
| [capital-wars-howell.md](capital-wars-howell.md) | Capital Wars: The Rise of Global Liquidity | Michael J. Howell | Global-liquidity cycle, cross-border flows → macro-panel companion |
| [psychology-of-money-housel.md](psychology-of-money-housel.md) | The Psychology of Money | Morgan Housel | Behavioral/temperament, staying-wealthy |
| [ultimate-day-trader-bernstein.md](ultimate-day-trader-bernstein.md) | The Ultimate Day Trader | Jacob Bernstein | Day-trading mechanics (cf. our hold-beats-daytrade finding) |

Note: leftover `[N](#...xhtml...)` footnote/anchor links from the EPUB remain
inline; harmless for search, ignore when reading.
