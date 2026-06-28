 TradingView MCP vs fundamentals.py — what each does

  They serve completely different data layers:

  ┌───────────────────────────┬────────────────────────────────────────────────────────────────────┬──────────────────────────────┐
  │ Data                      │ TradingView MCP                                                    │ fundamentals.py (yfinance)   │
  ├───────────────────────────┼────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ OHLCV price bars          │ ✅ data_get_ohlcv                                                  │ ✅ (slower)                  │
  ├───────────────────────────┼────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ RSI, MACD, Bollinger      │ ✅ data_get_study_values — pre-computed, correct                   │ ❌ must compute manually     │
  ├───────────────────────────┼────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ Screenshot of chart       │ ✅ capture_screenshot                                              │ ❌                           │
  ├───────────────────────────┼────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ MA50, MA200               │ ⚠️ buggy — chart_manage_indicator ignores the length input         │ ✅ computed from raw closes  │
  ├───────────────────────────┼────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ Forward PE, PEG ratio     │ ❌ not in MCP tools                                                │ ✅                           │
  ├───────────────────────────┼────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ Revenue/earnings growth   │ ❌                                                                 │ ✅                           │
  ├───────────────────────────┼────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ Gross margin, FCF yield   │ ❌                                                                 │ ✅                           │
  ├───────────────────────────┼────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ Short % of float          │ ❌                                                                 │ ✅                           │
  ├───────────────────────────┼────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ Institutional ownership % │ ❌                                                                 │ ✅                           │
  ├───────────────────────────┼────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ Analyst rec mean + count  │ ❌                                                                 │ ✅                           │
  ├───────────────────────────┼────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
  │ ROE, operating margin     │ ❌                                                                 │ ✅                           │
  └───────────────────────────┴────────────────────────────────────────────────────────────────────┴──────────────────────────────┘

  There is a data_get_equity tool in TradingView MCP but nothing in the codebase uses it yet — it may provide some earnings/revenue data from TradingView's "Fundamentals" tab. Worth testing. But even if it does, it almost certainly won't have PEG ratio, FCF yield, short % of float, institutional ownership %, analyst recommendation mean — those come from financial data aggregators (Bloomberg/Reuters/SEC filings) that Yahoo Finance compiles, not from TradingView's charting data.

  Why fundamentals.py won't go away:

   1. TradingView is a charting platform. Its MCP tools expose price data and technical indicators — not financial statement data.
   2. The MA bug is real and documented. chart_manage_indicator ignores the length parameter, so 50d/200d MAs come from yfinance instead (computed from raw closes).
   3. The Fundamental seat needs financial data. FCF yield (the #1 valuation metric in the skill), PEG ratio, revenue growth trend, institutional crowdedness — none of these come from TradingView.

  The only potential consolidation: test data_get_equity to see if it covers PE/revenue/EPS data. If it does, you could skip the TradingView OHLCV pull and just compute RSI/MACD/BB from the yfinance closes directly — eliminating TradingView for everything except the screenshot. But you'd lose the pre-computed indicator accuracy and the visual chart.

  Current split is deliberate:

   TradingView → visual chart + pre-computed indicators (RSI/BB/MACD) + screenshot
   yfinance    → all fundamentals + reliable MA levels (workaround for TV bug)
