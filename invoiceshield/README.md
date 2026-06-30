# InvoiceShield Case

**UiPath AgentHack 2026 — Track 1 (UiPath Maestro Case)**

UiPath's invoice template processes clean invoices. InvoiceShield governs the
**exceptions** that processing cannot safely automate: bank-account mismatches,
suspected duplicates, PO variance, and missing goods receipts. It turns each
risky invoice into a governed Maestro Case, uses agents to investigate and
explain, routes the money decision to a human, updates a mock ERP under a hard
guardrail, and closes with an audit trail.

The one idea: **Maestro governs and routes with deterministic rules, agents only
judge, and a human owns every risky money decision.** This is the design both
Anthropic and UiPath recommend (simplest system that works; agents are scoped
components inside a workflow, never the router), and it is what scores on a
rubric that grades production-readiness on a live demo.

## Architecture (one line)
`Manual trigger → [Investigate: Case Decision Agent (+ coded Deep Investigation Agent)] → [Human Decision: Finance Escalation] → [Resolve & Close: Update Mock ERP, Audit Summary Agent]` with a **Vendor Clarification** secondary stage that activates when Human Decision exits and **returns to origin** — the non-linear re-entry loop that makes this Track 1, not Track 2.

See `docs/architecture.md` for the full, cited design.

## UiPath platform usage (depth over breadth)
- **Maestro Case** as the governance + orchestration backbone (deterministic CMMN rules route).
- **Agent Builder** low-code agents: Case Decision Agent, Audit Summary Agent.
- **Coded agent on an external framework (LangGraph)**: the Deep Investigation Agent, wrapped as a UiPath coded agent — the rubric scores external frameworks inside a governed UiPath layer higher.
- **Human action / Action App**: Finance Escalation (the human owns the call).
- **AI Trust Layer + tool-level guardrails**, **agent traces**, and an **eval harness** (Agent Builder Evaluations / Test Cloud).
- Built in part with a **coding agent (Claude Code)** for the bonus.

## Case stages
Primary: Investigate → Human Decision → Resolve & Close.
Secondary (exception, self-activating, return-to-origin): **Vendor Clarification** (the re-entry loop). Roadmap secondary: Procurement Review, Rejected.

## Agents
1. **Case Decision Agent** (low-code) — classifies, scores risk, writes the human-readable evidence summary. Recommends; does not route or approve. `agents/case-decision-agent/`.
2. **Audit Summary Agent** (low-code) — closure audit trail. `agents/audit-summary-agent/`.
3. **Deep Investigation Agent** (coded, LangGraph) — reconciles conflicting/incomplete evidence. `agents/deep-investigation-agent/`.

Routing is **not** done by any agent. Deterministic policy (`logic/checks.py`) and Maestro rules decide the path.

## Demo cases
1. **Bank mismatch** (INV-1002) — the flagship: risk 92 → Finance Escalation + payment hold → vendor verification → **re-entry** → Rejected Suspected Fraud → mock ERP → audit.
2. **Duplicate** (INV-1001) — AP review → rejected.
3. **Amount variance** (INV-1003) — approved with exception.

## Guardrails (defense in depth)
- **Structural (shown live):** the Update Mock ERP task lives in Resolve & Close, whose entry rule requires the human decision field. Maestro blocks any payment action until a human signs off. Mirrored at the tool boundary by `can_update_mock_erp`.
- **AI Trust Layer:** prompt-injection guardrail (invoice text is untrusted), PII masking (bank last-4 only), trace retention.
- **Tool-level:** ERP write blocked unless `finalDecision` is in the allowed enum and a human decision exists.

See `docs/security-compliance.md`.

## What's verified in this repo
```bash
# deterministic routing brain: 9/9 unit tests
python logic/test_checks.py
# eval regression over 30 golden cases (success/edge/adversarial): 30/30, no API key
python evals/run_evals.py
# coded agent wiring (prints deterministic baseline without a key)
python agents/deep-investigation-agent/agent.py
```

## Repo layout
```
data/      5 mock CSVs (vendors, POs, goods receipts, invoice history, incoming)
logic/     checks.py  (deterministic tools + policy + ERP guardrail) + tests
agents/    case-decision-agent, audit-summary-agent (prompts + schemas),
           deep-investigation-agent (LangGraph coded agent)
evals/     golden_cases.json + run_evals.py (selfcheck + live LLM-as-judge)
docs/      architecture.md, security-compliance.md, demo-script.md
```

## Setup (to run live agents)
```bash
pip install -r agents/deep-investigation-agent/requirements.txt
export ANTHROPIC_API_KEY=...
export INVOICESHIELD_MODEL=claude-sonnet-4-6
python evals/run_evals.py --mode live
```

## Status
Maestro Case plan (4 stages + tasks + the re-entry loop) is built in the
hackathon tenant. The off-platform kit in this repo (agents, logic, evals, data,
docs) is the content that populates the real Agent Builder agents and the
Action App. Final wiring of rule expressions and a debug run are the last steps;
see `docs/architecture.md` section 13 for the build sequence.
