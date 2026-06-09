#!/usr/bin/env python3
"""
Stage 0b — does RISK-ADJUSTING / CAPPING EXTENSION beat raw momentum? (the SNDK question)

User caught it: leader_pick = argmax(6m return) grabs the single MOST-extended name (e.g. SNDK
+702%). Stage 0 validated cohort momentum (quintiles), not "buy the biggest winner." Test on the
bias-free Ken French 49 universe, OOS (>=2010), forward 1m:

  T1  raw 6m momentum            : Q5-Q1 spread (baseline, already ~+0.48%/mo OOS)
  T2  risk-adjusted momentum     : rank by 6m return / 6m vol ; Q5-Q1 spread
  T3  single MOST-extended       : each month buy the ONE highest-6m-return industry,
                                    compare its fwd return to the top-quintile mean (the SNDK case)
  T4  extension-capped strong    : within top quintile, least-extended half vs most-extended half

If T2 >= T1 -> risk-adjust helps. If T3 (single max) < cohort -> argmax is worse than the cohort,
confirming the bug. Read SIGN/magnitude; momentum is known, this is about HOW to pick within it.
Educational, not advice.
"""
import numpy as np, pandas as pd
from signal_test import load_french_monthly, t_stat

def run(df, split=2010):
    mom6 = df.rolling(6).apply(lambda x: (1 + x).prod() - 1, raw=True)
    vol6 = df.rolling(6).std()
    ret12 = df.rolling(12).apply(lambda x: (1 + x).prod() - 1, raw=True)
    fwd1 = df.shift(-1)
    radj = mom6 / vol6
    recs = []
    for t in df.index[12:-1]:
        m = mom6.loc[t].dropna()
        if len(m) < 30: continue
        f = fwd1.loc[t]; ra = radj.loc[t].dropna(); ext = (mom6.loc[t] - ret12.loc[t])
        # T1 raw quintiles
        q = pd.qcut(m, 5, labels=False, duplicates="drop")
        q5 = f.reindex(m.index)[q == q.max()].mean(); q1 = f.reindex(m.index)[q == 0].mean()
        # T2 risk-adjusted quintiles
        qa = pd.qcut(ra, 5, labels=False, duplicates="drop")
        a5 = f.reindex(ra.index)[qa == qa.max()].mean(); a1 = f.reindex(ra.index)[qa == 0].mean()
        # T3 single most-extended vs top-quintile cohort mean
        top = m.nlargest(1).index
        single = f.reindex(top).mean(); cohort = f.reindex(m.index)[q == q.max()].mean()
        # T4 within top quintile: least vs most extended
        strong = m[q == q.max()].index; e = ext.reindex(strong).dropna(); half = len(e)//2
        lowext = f.reindex(e.nsmallest(half).index).mean() if half else np.nan
        hiext = f.reindex(e.nlargest(half).index).mean() if half else np.nan
        recs.append({"date": t, "raw": q5-q1, "radj": a5-a1,
                     "single": single, "cohort": cohort, "lowext": lowext, "hiext": hiext})
    R = pd.DataFrame(recs).set_index("date"); te = R[R.index.year >= split]
    p = lambda x: x*100
    print(f"Stage 0b — picking method test (French 49, OOS >={split}, n={len(te)} months, fwd 1m)")
    print("="*70)
    print(f"T1 raw momentum      Q5-Q1: {p(te['raw'].mean()):+.2f}%/mo  t={t_stat(te['raw']):.2f}")
    print(f"T2 risk-adj (ret/vol)Q5-Q1: {p(te['radj'].mean()):+.2f}%/mo  t={t_stat(te['radj']):.2f}")
    print(f"   -> risk-adjust { 'HELPS' if te['radj'].mean()>te['raw'].mean() else 'no better' } vs raw")
    print(f"T3 single MOST-extended:    {p(te['single'].mean()):+.2f}%/mo   "
          f"vs cohort mean {p(te['cohort'].mean()):+.2f}%/mo  "
          f"diff {p((te['single']-te['cohort']).mean()):+.2f}%/mo t={t_stat(te['single']-te['cohort']):.2f}")
    print(f"   -> single argmax { 'WORSE than' if te['single'].mean()<te['cohort'].mean() else 'not worse than' } the cohort")
    print(f"T4 within strong: lowext {p(te['lowext'].mean()):+.2f}  hiext {p(te['hiext'].mean()):+.2f}  "
          f"diff {p((te['lowext']-te['hiext']).mean()):+.2f}%/mo t={t_stat(te['lowext']-te['hiext']):.2f}")
    print("\nFix justified if: T2>=T1 (risk-adjust) OR T3 single<cohort (argmax over-concentrates) OR")
    print("T4 lowext>hiext (extreme extension hurts). Even if weak, argmax->cohort/risk-adj is sounder.")
    return te

if __name__ == "__main__":
    run(load_french_monthly())
