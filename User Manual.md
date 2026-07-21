# Risk Manager — User Manual

This guide is for the trader using the app day-to-day. It doesn't cover code or setup for developers — see the README for that.

**Important:** Risk Manager never places trades, sends orders, or connects to your broker. It's a read-only dashboard that watches numbers you give it (or that it reads off your screen) and tells you when you're approaching your own pre-defined limits.

---

## 1. Getting Started

1. Launch the application (double-click the executable, or run from source if you're testing a development build).
2. On first launch, the app creates its own local database and fills in default risk limits. Go to **Settings** and adjust these to match your actual rules before your first real session — see §3.
3. Click **Start Session** when you begin trading for the day.

---

## 2. The Dashboard

While a session is active, the dashboard shows:

- **Current P&L** — your running profit/loss for the session.
- **Position Size** — your current position.
- **Trade Count** — trades taken so far, out of your configured daily maximum.
- **Trading Time** — elapsed time since session start.
- **Status Indicator** — a colored panel showing how close you are to your limits, plus plain-language warning messages explaining why.

### Status colors

| Color | Meaning |
|---|---|
| 🟢 Green | You're within all your limits. |
| 🟡 Yellow | You've reached 75% of a limit — a heads-up, not a stop. |
| 🟠 Orange | You've reached 90% of a limit — this triggers a mandatory cooldown. |
| 🔴 Red | You've hit a limit — this also triggers a mandatory cooldown. |
| ⚪ Data Error | The app couldn't get a reliable reading (only relevant if you're using OCR — see §5). It will never guess a number on your behalf; it will tell you it doesn't know rather than show you something wrong. |

**Any limit can trip this** — daily loss, position size, trade count, consecutive losses, or trading past your cutoff time. Whichever one is closest to being breached determines the color you see.

---

## 3. Setting Your Limits

Open **Settings** to configure:

- **Daily loss limit** — the maximum you're willing to lose in a session.
- **Max contract/position size**
- **Max trades per day**
- **Trading cutoff time** — the time of day after which you don't want to be trading.
- **Consecutive loss limit** — how many losing trades in a row before the app flags it.
- **Cooldown period** — how many minutes the app locks you out after an Orange or Red status.
- **Rule severity** — for each rule, mark it as "minor" or "major." This matters for your Discipline Score (§4) — a major rule breach (like trading past your cutoff) counts against you more heavily than a minor one (like slightly oversizing a position).

Changes take effect immediately — you don't need to restart a session for a new setting to apply.

---

## 4. Understanding Your Discipline Score

At the end of every session, your report shows three numbers, not just one:

- **Adherence Score** — how well you followed your own rules, independent of whether you made money.
- **Profitability Score** — how well you protected your capital, capped once you reach breakeven.
- **Discipline Score (blended)** — a combination of the two, weighted **70% toward Adherence and 30% toward Profitability.**

**Why it's weighted this way:** this tool exists to build discipline, not to reward big wins. A profitable day where you broke your own rules is treated as a warning sign, not a success — because that's usually how a good trader eventually blows up an account. A losing day where you followed every rule is a *good* day by this score, because it means the system worked as intended.

**Why Profitability caps at breakeven:** you don't get extra credit for making more money once you're past $0 for the session. The score only asks "did you protect your capital," not "how much did you make" — reaching for a higher score by pushing for bigger wins would defeat the purpose.

### How Adherence is scored
| Rule violations this session | Adherence Score |
|---|---|
| None | 100 |
| One minor violation | 80 |
| One major violation | 50 |
| Two or more violations (any severity) | 0 |

### What a "good" score looks like
- **Perfect day:** no violations, P&L at or above $0 → Discipline Score of 100.
- **Good day:** no violations, but a controlled loss within your limit → still a high score (roughly 75–90), because you followed your rules.
- **Mediocre day:** one minor slip-up → a moderate score.
- **Bad day:** one major violation — **even if you made money that day** — scores low. This is intentional. Breaking a major rule is treated as a bad day regardless of the outcome.

Your report always shows Adherence and Profitability separately, alongside the blended score, so you can tell at a glance whether a low score means "I broke a rule" or "I just had a losing day."

---

## 5. Cooldowns

If your status turns Orange or Red, the app locks new data entry (or pauses OCR capture) for a configured cooldown period and shows a countdown. This is deliberate — it's meant to interrupt you at the moment you're most likely to make an emotional decision.

- The cooldown clears automatically once the timer runs out.
- Changing a setting (e.g. adjusting a limit) re-evaluates your status immediately and can clear a cooldown early if the new setting brings you back under the limit — this is the one way to exit a cooldown before the timer ends.

---

## 6. Ending a Session and Reading Your Report

Click **End Session** to close out the day. Your report shows:

- Final P&L, total trades, max position size reached
- Adherence Score, Profitability Score, Discipline Score (blended)
- **Capital Preservation Score** — 100 if you never hit your loss limit, 0 if you did
- **Session Grade** (A–F) — a simplified letter grade summarizing the above (note: exact grade thresholds may be refined over the first few weeks of real use)
- **Recommendations** — plain-language notes on which specific rules you broke, if any, and what to watch for next time

Every session is saved automatically to your local session history — nothing is sent anywhere else.

---

## 7. Using OCR Data Capture (Optional)

If you'd rather not enter data manually, Risk Manager can read your numbers directly off a mirrored phone screen (e.g. via your PC's built-in screen mirroring or an app like LonelyScreen).

**Setup:**
1. Mirror your phone screen to your PC first, using your existing mirroring tool.
2. In Risk Manager, select the mirrored window.
3. Click and drag to mark the regions of your screen that show P&L, position size, etc., and name each one.

**During a session:** toggle the data source to "OCR" instead of "Simulate Data." The app will read those regions continuously.

**If a reading fails:** the status will show **Data Error**, not a guess. This happens if the screen capture is unclear or the number can't be confidently read. When you see this, glance at your phone directly — don't trust a blank or frozen dashboard as a "you're fine" signal.

**Setup requirement:** OCR requires a small one-time software install (Tesseract) on your machine. If you're using a version of the app that includes OCR, this will be noted separately with install instructions.

---

## 8. Troubleshooting

| Problem | What to check |
|---|---|
| Status seems wrong / stuck | Check Settings — a recent change may not match what you expect. Changing any setting re-evaluates immediately. |
| Can't click Simulate Data or see numbers update | You may be in a cooldown — check for the countdown timer. |
| Data Error showing constantly (OCR mode) | Your mirrored window may have moved, resized, or your ROI regions may need re-marking. |
| App won't launch | Confirm you're running the correct executable for your operating system; contact whoever set up the app for you if the issue persists. |

Your session history and settings are stored locally on your machine — they are not affected by app updates unless you're told otherwise.
