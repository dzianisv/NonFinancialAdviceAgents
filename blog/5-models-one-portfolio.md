# I gave 5 AI models my portfolio. The winner wasn't the smartest model — it was the one with tools.

I have ~70 positions and a recurring question: what do I buy, what do I drop. Every few weeks I paste the portfolio into a chat model and get a confident answer. The answers sound good. I have no way to tell if they're right.

So I ran a test. Same prompt, same portfolio, five models: Gemini, Grok, ChatGPT, Claude Opus in a chat box, and Claude Code running a skill I wrote. Then a sixth model — a separate Opus agent — scored all five against live market data. This is an educational write-up of a personal experiment, not financial advice.

## What the chat models gave me

Four of the five wrote a clean macro story and a buy/sell table. Gemini's was representative and well-reasoned:

- Buy AI-infrastructure chips (AVGO, QCOM, ASML, MRVL) — cashing the AI capex checks
- Buy VXUS / VWO — cheaper than US, catching the chip tailwind
- Buy energy (XLE, CVX, XOM)
- Sell NKE, CVNA, LYFT, ARE, PYPL, ACN

Nothing wrong with the logic. It maps a plausible macro regime onto the book. The other three said almost the same thing — buy cheap international, hold the chips, trim the laggards.

The problem isn't the reasoning. It's that none of it was checked against today's numbers.

## What the skill did differently

The skill is not a smarter prompt. It's the same model wired to data:

- `fundamentals.py` pulls live valuations per ticker from Yahoo Finance — price vs moving averages, P/E, free-cash-flow yield, growth.
- A news step reads Financial Times and Wall Street Journal feeds and quotes them with URLs.
- A smart-money step fetches disclosed insider buys and 13F institutional filings per name (both are public).

Same question, but now the answer has to survive contact with live data. Four calls flipped:

| Call | Chat models | Skill, with data |
|---|---|---|
| VXUS | "cheap, buy" | +8.7% **above** its 200-day average — not cheap, and facing a fresh dollar and tariff headwind |
| NVDA / chips | "buy / hold" | insiders sold $1.8B with zero open-market buys; chips just went late-cycle. The cheap screen is a de-rating trap |
| NKE | "sell" | insiders bought the dip hard — the CEO plus five directors. Trim, don't dump |
| ADBE | "sell / trim" | 7x earnings, 63% return on equity, still growing. Selling locks the loss at the bottom of an AI-fear selloff |

The skill also surfaced one name nobody else mentioned: CRM, at 10x earnings with a 13% free-cash-flow yield and three directors buying $25M of stock.

None of these are exotic. They're just facts you can only act on if you pull them. The chat models couldn't, so they reasoned around them.

## The scoring

I didn't grade my own homework. A separate Opus agent read all five reports off a Notion page and scored them on a rubric: data-groundedness, factual accuracy, actionability, honesty, insight.

| Rank | Model | Score |
|---|---|---|
| 1 | Claude Code + skill | 93 |
| 2 | Gemini | 53 |
| 2 | Claude Opus (chat) | 53 |
| 4 | ChatGPT | 51 |
| 5 | Grok | 47 |

An independent scorer paid off twice. It caught that the Gemini and chat-Opus entries were byte-for-byte identical — a copy-paste error in my test harness I hadn't noticed. And it argued with one of my own reference facts: I claimed the Fed's rate projection wasn't pointing up; it checked and found the median did move up one hike, so the chat models' real error was the size of the move, not the direction. A scorer that pushes back is doing its job.

## The lesson

The winner wasn't the smartest model. Four of the five are frontier models, and they gave competent macro takes. The gap was tooling: live valuations, sourced news, and insider flows. The same Opus model scored 53 in a chat box and 93 wired to data.

This matches a boring truth about agents: for most real tasks, grounding beats raw IQ. The model that reads the actual number beats the model reasoning elegantly about a number it's guessing.

Two trade-offs worth naming:

- **Cost.** The skill run spawns subagents and makes dozens of fetch calls. A chat answer is one call. For a weekly review that's fine; for a throwaway question it's overkill.
- **Dead tools fail loud, not silent.** My charting tool was down during the run. The skill said so and dropped to moving-average-only — "degraded mode, no live triggers" — instead of inventing entry signals. A chat model has no tool to be down, so it never tells you what it couldn't see. That silence is the dangerous part.

## If you want to copy this

You don't need my skill. You need three things bolted onto whatever model you use: a script that pulls current fundamentals, a news reader that returns URLs you can open, and a source for who is actually buying. Then make the model cite all of it. The citation requirement is the point — it's what stops a confident guess from passing as analysis. (I just changed the skill to always print the full source list at the end of every run, for exactly this reason.)

That's the pattern I keep returning to with Claude Code skills: the model is rarely the bottleneck. The data path is.

*Educational write-up of a personal experiment. Not financial advice.*
