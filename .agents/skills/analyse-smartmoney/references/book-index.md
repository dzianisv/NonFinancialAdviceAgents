# Book Index and Verified Reading List

This file is the source-of-truth for every citation used across the `analyse-smartmoney` skill family. All titles below are **verified** — do not add titles from memory. Honesty flags are stated explicitly where evidence quality is weak, contested, or absent.

---

## COT / Commitments of Traders

| Author | Title | Year | Publisher | Scope | Use in this skill |
|---|---|---|---|---|---|
| Stephen Briese | *The Commitments of Traders Bible* | 2008 | Wiley | **Canonical.** Normalization method (0–100 over 3yr rolling), commercial-as-smart-money logic in commodities, COT Index construction | Primary source for COT methodology in `02-market-implied.md` |
| Floyd Upperman | *Commitments of Traders: Strategies for Trading the Futures Markets* | 2006 | Wiley | Systematic COT trading rules, disaggregated COT | Supplementary COT |
| Jake Bernstein | COT chapter in *30 Days to Market Mastery* | 2007 | Wiley | COT overview chapter only — **no standalone Bernstein COT book exists** | Scope-limited; cite chapter source only |

**FLAG:** No standalone Jake Bernstein COT book exists. Any citation to "Bernstein, COT" without specifying *30 Days to Market Mastery* Chapter reference should be treated as unverified.

---

## Insider Trading / Form 4

| Author | Title | Year | Publisher | Scope | Use in this skill |
|---|---|---|---|---|---|
| H. Nejat Seyhun | *Investment Intelligence from Insider Trading* | 1998 | MIT Press | **Academic canon.** Empirical evidence that insider buying predicts excess returns; buy-side asymmetry; CEO/CFO weighting | Primary academic source for Form 4 methodology |
| George Muzea | *The Vital Few vs. the Trivial Many* | 2004 | Wiley | Practitioner framework for insider tracking; cluster buy concept; distinguishing meaningful from noise | Practitioner complement to Seyhun |
| Jonathan Moreland | *Profit from Legal Insider Trading* | 2000 | Dearborn | Retail-accessible introduction; opportunistic vs. scheduled trades | Background reading |

**Papers (peer-reviewed, load-bearing):**
- Lakonishok, J. and Lee, I. (2001). "Are Insider Trades Informative?" *Review of Financial Studies* 14(1): 79–111. **Finding: insider buying predicts +4–6%/year excess return; insider selling does not predict underperformance.**
- Jeng, L.A., Metrick, A., and Zeckhauser, R. (2003). "Estimating the Returns to Insider Trading." *Review of Economics and Statistics* 85(2): 453–471. Further confirmation of buying alpha.
- Cohen, L., Malloy, C., and Pomorski, L. (2012). "Decoding Inside Information." *Journal of Finance* 67(3): 1009–1043. **Key finding: opportunistic insiders (those who trade outside predictable patterns) generate ~8% alpha; routine insiders (predictable schedule) generate ~1% — the split matters.**

**HONESTY FLAG — unsourced retail figure.** The "8–11% return per insider cluster buy" figure circulating in options-flow and insider-tracking marketing is **unsourced**. Do not assert it. The academic figures (Seyhun, Lakonishok-Lee: ~4–6%/year) are the verifiable claims. The higher retail-circulated figures are not traceable to peer-reviewed research.

---

## Microstructure / Market Structure

| Author | Title | Year | Publisher | Scope | Use in this skill |
|---|---|---|---|---|---|
| Larry Harris | *Trading and Exchanges: Market Microstructure for Practitioners* | 2003 | Oxford | **Canonical.** Informed trader models, market maker behavior, order flow toxicity, dark pool mechanics | Foundation for understanding why dark-pool high short volume ≠ bearish |
| Maureen O'Hara | *Market Microstructure Theory* | 1995 | Blackwell | Academic theory of information asymmetry in markets, adverse selection models | Academic complement |
| Barry Johnson | *Algorithmic Trading and DMA* | 2010 | 4Myeloma Press | Execution algorithms, dark pool routing, TRF reporting mechanics | Practical dark pool mechanics |

---

## Wyckoff / Tape Reading / VSA

| Author | Title | Year | Publisher | Scope | Use in this skill |
|---|---|---|---|---|---|
| Richard D. Wyckoff | *The Richard D. Wyckoff Method of Trading and Investing in Stocks* | 1937 | Stock Market Institute | Original accumulation/distribution schematic, Composite Operator concept | Primary source for `03-wyckoff.md` |
| Richard Wyckoff (as "Rollo Tape") | *Studies in Tape Reading* | 1910 | Ticker Publishing | Foundational tape-reading principles predating modern chart analysis | Historical context |
| Rubén Villahermosa | *The Wyckoff Methodology in Depth* | 2019 | Self-published | Contemporary synthesis; clearest modern treatment of A→E accumulation and distribution schematics | Best modern reference for phase labels |
| David Weis | *Trades About to Happen* | 2013 | Wiley | VSA integration with modern electronic markets; effort vs. result concept | VSA applied |
| Tom Williams | *Master the Markets* | 2005 | Genie Soft | VSA "no supply / no demand" pattern library; stopping volume; absorption signals | VSA canonical source |

---

## Dark Pools

| Author | Title | Year | Publisher | Scope | Use in this skill |
|---|---|---|---|---|---|
| Scott Patterson | *Dark Pools: High Speed Traders, A.I. Bandits, and the Threat to the Global Financial System* | 2012 | Crown | Narrative history of dark pool development, HFT, and off-exchange trading | Background on dark pool mechanics |
| Michael Lewis | *Flash Boys: A Wall Street Revolt* | 2014 | Norton | IEX story; latency arbitrage; dark pool abuse; public awareness | Narrative context |
| Sal Arnuk and Joseph Saluzzi | *Broken Markets: How High Frequency Trading and Predatory Practices on Wall Street Are Destroying Investor Confidence and Your Portfolio* | 2012 | FT Press | Critical perspective on HFT and dark pool practices | Counter-narrative |

**FLAG:** The **Dark Pool Index (DIX)** is a **SqueezeMetrics data product** (https://squeezemetrics.com/monitor/dix), not a concept from any of the above books. The counterintuitive interpretation (high dark-pool short volume = bullish) is SqueezeMetrics' proprietary framing based on their data. It is not independently replicated in peer-reviewed research. Treat as vendor-provided signal with the corresponding uncertainty.

---

## Options Flow

| Author | Title | Year | Publisher | Scope | Use in this skill |
|---|---|---|---|---|---|
| Jon Najarian and Pete Najarian | *Follow The Smart Money — Unusual Option Activity* | 2018 | Self-published / SmartOptions | **FLAG: Promotional.** Only widely available retail book on unusual options activity; lacks rigorous false-positive rate disclosure; qualitative framework is reasonable but performance claims are not peer-reviewed | Background only; do not cite performance claims |
| Sheldon Natenberg | *Option Volatility and Pricing: Advanced Trading Strategies and Techniques* (2nd ed.) | 2014 | McGraw-Hill | Options pricing mechanics, skew interpretation, IV surface | Primary source for put/call skew and IV interpretation |

**Papers (peer-reviewed, load-bearing):**
- Easley, D., O'Hara, M., and Srinivas, P.S. (1998). "Option Volume and Stock Prices: Evidence on Where Informed Traders Trade." *Journal of Finance* 53(2): 431–465. Evidence that options markets contain forward-looking information about stock prices.
- Pan, J. and Poteshman, A.M. (2006). "The Information in Option Volume for Future Stock Prices." *Review of Financial Studies* 19(3): 871–908. **Key finding: aggregate customer put/call volume ratio is a statistically reliable predictor of next-day returns; the signal is in customer-initiated trades, not total volume.**

**HONESTY FLAG on single-print options flow.** The Najarian book and retail options-flow services emphasize single unusual prints. The Pan-Poteshman academic finding is specifically about the **aggregate** ratio, not individual unusual prints. Single prints are low signal-to-noise and frequently represent hedges, market-maker positioning, or algorithmic order-breaking. The aggregate daily ratio is where the academically supported signal lives.

---

## 13F Cloning (no canonical book)

**HONESTY FLAG:** There is **no canonical book** on 13F cloning as an investment strategy. The practice lives in:
- Platform documentation (Dataroma, WhaleWisdom, GuruFocus)
- Academic papers on "Alpha Cloning" (various; search Google Scholar for "13F cloning alpha")
- Conceptual discussion in: Mohnish Pabrai, *The Dhandho Investor* (2007, Wiley) — value-focused position sizing philosophy; Charlie Tian, *Invest Like a Guru* (2017, Wiley) — practical 13F analysis

Neither Pabrai nor Tian focus primarily on 13F cloning; these books address value investing philosophy and have chapters discussing watching institution filings. Any reference to a "definitive 13F cloning book" should be flagged as unverified.

---

## Congressional Trading

**Papers (peer-reviewed):**
- Ziobrowski, A.J., Cheng, P., Boyd, J.W., and Ziobrowski, B.J. (2004). "Abnormal Returns from the Common Stock Investments of the U.S. Senate." *Journal of Financial and Quantitative Analysis* 39(4): 661–676. **Pre-STOCK Act finding: senators earned +6–12%/year excess returns.**
- Ziobrowski, A.J., Boyd, J.W., Cheng, P., and Ziobrowski, B.J. (2011). "Abnormal Returns from the Common Stock Investments of Members of the U.S. House of Representatives." *Business and Politics* 13(1): 1–22. **Pre-STOCK Act: House members +6%/year.**
- Eggers, A.C. and Hainmueller, J. (2013). "Capitol Losses: The Mediocre Performance of Congressional Stock Portfolios." *Journal of Politics* 75(2): 535–551. **Post-STOCK Act counter-evidence: alphas largely disappeared, particularly for Senate.**
- Chen, J. and Sacerdote, B. (NBER Working Paper, 2024). **Post-STOCK Act finding: congressional trades resemble uninformed retail investors; residual alpha concentrated in leadership only.**

**HONESTY FLAG on congressional alpha.** The pre-STOCK Act Ziobrowski findings (+6–12%/year) are real and peer-reviewed. The post-STOCK Act literature (Eggers-Hainmueller, Chen-Sacerdote) substantially weakens the alpha claim. The current evidence is **contested** — do not present congressional PTR as a reliable alpha source. State the pre/post distinction explicitly when citing congressional trading research.

---

## Cross-referenced repo skills

| Skill | Role in smart-money context |
|---|---|
| `analyse-smartmoney-13f` | Disclosed flows spoke — 13F institutional holdings |
| `analyse-smartmoney-13d` | Disclosed flows spoke — activist 13D/13G filings |
| `analyse-smartmoney-form4` | Disclosed flows spoke — SEC Form 4 insider transactions |
| `analyse-smartmoney-ptr` | Disclosed flows spoke — congressional STOCK Act PTRs |
| `analyse-smartmoney-positioning` | Market-implied spoke — COT, funding/OI/basis, skew, IV, gamma |
| `analyse-smartmoney-options` | Market-implied spoke — single-name unusual options flow |
| `analyse-smartmoney-darkpool` | Market-implied spoke — DIX, block prints, off-exchange |
| `analyse-smartmoney-polymarket` | Market-implied spoke — prediction-market event odds |
| `multi-lens-quorum` | Quorum synthesis across multiple analyst lenses; use when cross-skill consensus is needed |
| `superforecasting` | Calibrated probability estimation; applies to prediction-market haircut procedure |
| `signal-convergence-alert` | Alert when multiple signal classes converge on the same direction |

---

## Official data sources (free)

| Signal | Official source |
|---|---|
| Form 4 (SEC EDGAR) | https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=4 |
| 13F filings | https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=13F |
| 13D / 13G filings | https://efts.sec.gov/LATEST/search-index?q=%22SC+13D%22 |
| Congressional PTR — House | https://disclosures.house.gov/ |
| Congressional PTR — Senate | https://efts.senate.gov/ |
| COT reports | https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm |
| FINRA dark pool / TRF | https://www.finra.org/finra-data/browse-catalog/equity-short-interest-data |
| DIX (SqueezeMetrics) | https://squeezemetrics.com/monitor/dix |
| Polymarket | https://polymarket.com |
