# Demo script (<= 5 minutes) — recording-ready

Record at 1080p. Have three things open: (1) Studio Web on the Maestro Case plan,
(2) the SimpleApprovalApp running live on Automation Cloud (the `apps_` runtime
tab), (3) a terminal in the `invoiceshield` folder. Narrate risk reduction, not
features. Times are targets, not rules.

## 0:00–0:30 — The problem
Say: "Accounts-payable invoice exceptions are messy, non-linear, and expensive.
Bank-account mismatches, duplicates, PO variance, missing goods receipts. They
eat 30 to 40 percent of AP time, and a wrong call moves real money. UiPath's
template processes clean invoices. InvoiceShield governs the exceptions."

## 0:30–1:00 — The architecture (one breath)
Show the architecture diagram (README ASCII or the image). Say: "UiPath builds
Maestro to orchestrate AI agents, robots, and people across long-running
processes. InvoiceShield uses the **Case** side of Maestro, where the process is
not linear. Maestro is the governance backbone: deterministic rules route,
agents only judge, and a human owns every risky money decision. A re-entry loop
makes this a real Case, not a disguised workflow. One agent is a coded LangGraph
agent, governed by UiPath."

## 1:00–2:00 — The Maestro Case in Studio (modeled solution)
Screen-share Studio Web on the Case plan. Point to, in order:
- The four stages: Investigate, Human Decision, Resolve & Close, and the
  **Vendor Clarification secondary stage**.
- Click **Human Decision, then Finance Escalation**: show it is a **real human
  action** bound to a published Action App (SimpleApprovalApp), with a
  `financeDecision` output.
- Open the **Rules** tab: show the entry/exit/completion rules, and the
  **Human Decision exit rule** that routes to Vendor Clarification, then back
  via **return-to-origin**. That is the re-entry loop on screen.
Say: "This is the orchestration and the human-in-the-loop, modeled and validated
in Studio."

## 2:00–2:40 — The human action running LIVE on Automation Cloud
Switch to the running Action App tab (the `apps_/.../run/...` URL on
`staging.uipath.com`). The **Finance Escalation** approval form is live: a
"Content for Review" panel, a Comment box, and **Approve / Reject** buttons.
Type a one-line finance note in the Comment box, for example "Bank-account change
unverified, hold payment and request a vendor callback," then click **Reject**.
Say: "This is not a mockup. This is the human-in-the-loop Action App running on
UiPath Automation Cloud. The finance reviewer owns the money decision right here,
and that decision is what the Case routes on."

How to bring it up before recording: open **SimpleApprovalApp** in Studio Web,
click **Debug on cloud**, then **Save & Debug**. The app launches at the Apps
runtime URL in a new browser tab. Leave that tab open for the recording.

## 2:40–4:10 — Run the prototype LIVE (the strongest 90 seconds)
Switch to the terminal. Run:
```bash
bash run_all.sh
```
As it scrolls, call out:
- "Unit tests, the routing brain and the signal-fusion model: 14 of 14."
- "Thirty-nine labeled cases: success, edge, prompt-injection, composite, and
  calibration. Thirty-nine of thirty-nine."
- "And the scoreboard: 100 percent recall, zero false positives. Hard rules
  alone catch 77 percent; signal fusion adds 23 percent, the structured fraud no
  single rule can see."
- "Fuzzing: every malformed invoice routes safely to review, zero crashes."
- "Consistency: code, schema, prompt and data all agree."
- "And the end-to-end stress, six scenarios." Pause on scenario six (structured
  fraud): point at the signals line ("amountJustUnderThreshold, newVendor,
  firstInvoice") while every evidence row reads clean, then the guardrail line
  and the summary ("distinct cash protected: 275,000").
Say: "Bank mismatch held a 225k payment, the duplicate stopped a 50k double-pay,
the prompt-injection attack changed nothing, the clean invoice opened no case,
and scenario six is the one that wins it: every hard rule passed, yet signal
fusion still caught structured fraud. The agent recommends, the human owns the
money, the guardrail blocks the ERP write until a human signs off."

## 4:10–4:40 — Honesty + platform note (do not skip)
Say: "Two honest notes. First, this is live on Automation Cloud: the solution
publishes and deploys, a real Case Decision agent built in Agent Builder is
deployed and bound to the case, and the human approval app runs live. Second, the
one thing that still fails is the Debug-on-cloud path for the Case, with 'no
solution tool factory is registered', so I did not run the Case fully end to end
through that path. UiPath has acknowledged that bug on the forum." Briefly show
the thread. "So the agent and the human action are deployed and live, the Case is
modeled in Studio, and the decision logic runs and is measured here."

## 4:40–5:00 — Close
Say: "Agents investigate, humans decide, UiPath governs. Thirty evals, a fuzz
suite, defense-in-depth guardrails, a live human action on Automation Cloud, and
a coded LangGraph agent, all built in part with a coding agent. InvoiceShield:
governing the exceptions that processing cannot safely automate."

## One-liner to title the video
InvoiceShield Case: governing the risky invoice exceptions humans must own (UiPath AgentHack 2026, Track 1).
