---
name: update-fidelity-recuring
description: Pull recurring transactions from Fidelity accounts to track monthly auto-invest amounts
---

Pull recurring transactions from Fidelity accounts https://digital.fidelity.com/ftgw/digital/recurring-activity/ and log them into a Google Sheet's "Recurring activity" tab https://docs.google.com/spreadsheets/d/1aunLbpNGo85WqrMHiIsy6nFUija4Lnjot-rIhE-pGU8/edit?gid=881284498#gid=881284498 to track monthly auto-invest amounts. Since this requires browser interaction with Fidelity, I should use a subagent with chrome-use to handle the data collection, then write the results to the sheet. I'll start by checking the sheet's Recurring activity tab to understand its structure, then launch a subagent to handle the Fidelity browser extraction in parallel while I inspect what's already there.