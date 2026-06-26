# References: analyst-smartmoney-options

## Books

**Natenberg, Sheldon. *Option Volatility and Pricing: Advanced Trading Strategies and Techniques*,
2nd ed. McGraw-Hill, 2014.**
The standard practitioner text on options pricing theory. Chapters on volatility skew (Ch. 17–18)
explain why implied vol differs across strikes — essential for interpreting put/call skew steepening
as a demand-for-protection signal rather than a pricing error. Chapter 19 covers volatility trading.
Use for: understanding skew as a signal of directional demand, distinguishing risk-reversal
structures from naked directional plays, and interpreting IV rank.

**Najarian, Jon and Pete Najarian. *Follow The Smart Money: Unusual Option Activity — Finding and
Trading with the Big Boys*. Wiley, 2018.**
FLAG: This is a promotional retail-oriented book from the founders of a paid flow-alert service
(Najarian brothers, Investitute/Market Rebellion). It provides good intuitive descriptions of sweep
mechanics and illustrates how to scan for vol>>OI anomalies. However, it contains weak treatment of
false-positive rates, does not address the hedge-as-signal problem rigorously, lacks out-of-sample
validation, and conflates retail-alert signal quality with institutional OPRA-level data. Read for
the sweep/block taxonomy; do NOT use it as authority for edge or win-rate claims. Treat its
examples as illustrative, not validated.

## Academic Papers

**Easley, David, Maureen O'Hara, and P. S. Srinivas. "Option Volume and Stock Prices: Evidence on
Where Informed Traders Trade." *Journal of Finance* 53, no. 2 (1998): 431–465.**
Foundational paper establishing that options order flow contains information about future stock
prices prior to that information being reflected in the stock market. Key finding: informed traders
use options (leverage + limited downside) to exploit private information. Supports the theoretical
basis for reading options flow as potentially informed. Limitation: this is pre-HFT, pre-algorithmic
market-making, and pre-widespread retail options access; information advantage has likely compressed.

**Pan, Jun, and Allen M. Poteshman. "The Information in Option Volume for Future Stock Prices."
*Review of Financial Studies* 19, no. 3 (2006): 871–908.**
The most-cited empirical paper supporting options-flow-as-signal. Key result: high call/put *volume
ratios* (not single large prints) predict next-week stock returns >1% in the aggregate. Data source:
CBOE proprietary data that separates opening from closing trades and identifies public vs firm
orders. Critical caveat: the edge is in the *aggregate ratio*, not in individual large prints. Pan
and Poteshman explicitly caution that the public (retail) component of options flow has no
predictive power — only the firm (dealer/institutional) component does. This paper is often
misrepresented by retail flow services as validating single-print alerts.

## Note on data availability

Both academic papers used proprietary exchange data (CBOE identifier flags) to separate opening
from closing orders and institutional from retail flow — data that is NOT available to most
practitioners via free or retail-tier feeds. This is the root reason that retail flow alert services
cannot replicate the academic findings: they cannot make the same opening/closing / institutional/
retail distinctions. Vendor backtests that claim to replicate Pan-Poteshman results should be
treated with high skepticism.
