# InvoiceShield: depth and the agentic maturity model

Most "agentic case" submissions stop at detection: spot a duplicate, spot a bank
change, route to a human. That is table stakes, and it is where the field will
cluster. InvoiceShield goes deeper on the axes that actually separate a governed
production system from a demo: the quality of the judgment, the calibration of
the risk, and the governance around it. This document is the ladder.

## What actually makes AP exception handling hard

The toy problem ("detect a duplicate") is a database query. No agent needed. The
real problem, the one that justifies an agent, is judgment under uncertainty:

- **Evidence is incomplete and conflicting.** A changed bank account is either
  fraud or a legitimate vendor update; the data alone cannot tell you which.
- **Fraud is adversarial.** It is engineered to look clean: amounts just under
  approval limits, freshly created payees, lookalike domains, urgency in the memo.
- **Error costs are asymmetric.** A false negative wires money to a criminal; a
  false positive insults a real vendor and burns AP time. The optimal policy is
  calibrated, not "flag everything."
- **The world changes mid-case.** New evidence (a vendor callback, a bank
  confirmation) can flip the right answer. That emergent, non-linear behavior is
  what makes this a Case, not a linear workflow.

Anything built "deep" has to attack those four, or it is decoration.

## The maturity ladder

**Level 1, Detection.** Deterministic rules catch the four named exceptions
(bank mismatch, duplicate, PO variance, missing goods receipt), in priority
order, in `logic/checks.py`. Necessary, and what every competitor will have.

**Level 2, Reasoning over weak and conflicting signals.** The catch no single
rule makes. `compute_signals()` fuses seven real fraud indicators into one
composite score: recent bank change, amount just under an approval threshold,
new vendor, first invoice, vendor risk flag, urgency language, high materiality.
Weights are tuned so that no single signal trips a case, but a realistic
combination does. When every hard rule passes yet the combination crosses the
threshold, the case is flagged `COMPOSITE_RISK`. Worked example: a new vendor's
first invoice priced 0.5% under the 50k approval limit. Bank matches, no
duplicate, no variance, goods receipt present. Every rule says PASS. The agent
flags structured fraud anyway. That single moment proves an agent earns its seat.

**Level 3, Calibrated risk, confidence, and abstention.** Every decision carries
a confidence: High on a hard rule, Medium on a composite, Low on incomplete
evidence. Low confidence **abstains**, routing to deeper investigation instead of
a confident wrong answer. And it is **measured**: `run_evals.py` prints an
accuracy scoreboard over a labeled acceptance set, including the recall the
signal-fusion layer adds over hard rules alone.

**Level 4, Governed adaptive case.** The trust layer: policy-as-code routing (the
AI never routes), a tool-boundary guardrail blocking the mock-ERP write until a
human signs off, prompt-injection resistance (the deterministic engine never
reads memo instructions), PII masking (bank last-4 only), human gates, a full
audit trail, and evals-in-CI. The non-linear re-entry loop (the Vendor
Clarification secondary stage) reopens a case when new evidence arrives.

## The scoreboard (measured, not claimed)

On the 39-case labeled acceptance set (`evals/golden_cases.json`), via
`python3 evals/run_evals.py`:

| metric | value |
| --- | --- |
| recall (exceptions caught) | 100% |
| precision | 100% |
| false-positive rate | 0% |
| hard-rules-only recall | 77% |
| **signal fusion adds** | **+23% recall** (the 7 composite-risk cases no single rule catches) |
| risk separation | 77.6 (flagged) vs 10.0 (clean) |

The +23% is the number that matters: it quantifies the value of the agentic
judgment layer over a flat rules engine.

## The three demo moments that prove depth

1. **The composite catch.** Every evidence row is clean; the agent still flags
   structured fraud from the fused signals.
2. **Calibration.** A new vendor's first invoice at a normal amount is cleared
   (signal score 45); the same vendor at an amount structured under the limit is
   flagged (75). One signal is benign; the combination is fraud.
3. **The scoreboard.** Hard rules alone catch 77%; signal fusion makes it 100%,
   at 0% false positives.

## Honest scope

The composite model and confidence are deterministic, so they stay testable and
calibratable, and they back the agents' judgment rather than replacing it (the
LLM agents narrate, assess novelty, and own the human-readable case). The live
Case publish is blocked by a known UiPath platform bug, so this depth runs in the
engine, the eval harness, and the console, and is modeled in Studio. When the
Case solution feed is enabled, the same plan deploys unchanged.
