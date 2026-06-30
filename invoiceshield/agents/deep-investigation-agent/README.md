# Deep Investigation Agent (coded, LangGraph)

The external-framework, coded agent in InvoiceShield. It exists for one reason
that is both architecturally honest and rubric-aligned.

**Rubric alignment.** AgentHack Platform Usage scores "external agent frameworks
(LangChain, CrewAI, AutoGen) within a governed UiPath orchestration layer"
higher than low-code-only solutions. This agent is built on LangGraph and is
wrapped as a UiPath coded agent: Maestro keeps governance (guardrails, human
gates, traces), the open-ended reasoning runs here.

**Why an agent and not a workflow.** Per Anthropic's "Building effective
agents", agents fit open-ended problems where the steps cannot be predicted.
Evidence reconciliation is exactly that: a clean invoice is a near-passthrough,
but a vendor-not-found / PO-owned-by-another-vendor / partial-goods-receipt case
needs the agent to decide which tools to call and how to reconcile. The
deterministic tools stay the ground truth, so math and lookups are never trusted
to the LLM.

## Files
- `agent.py` — the LangGraph ReAct agent + `investigate()` and the
  `uipath_entrypoint()` contract for the coded-agent wrapper.
- `tools.py` — the deterministic tools (wrap `logic/checks.py`).
- `requirements.txt` — LangGraph + LangChain + Anthropic.

## Run locally
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...            # your key
export INVOICESHIELD_MODEL=claude-sonnet-4-6   # pin the version (eval hygiene)
python agent.py
```
Without a key, `agent.py` prints the deterministic evidence baseline so you can
verify wiring with zero spend.

## How Maestro governs it
The agent runs as a coded-agent task inside the **Investigate** stage. Its
output (`normalizedEvidence`) feeds the deterministic Case Decision policy, which
sets the case fields Maestro routes on. The agent never writes to the mock ERP
and never bypasses the human gate; those are enforced structurally by the stage
rules and the `can_update_mock_erp` guardrail.

Built with Claude Code (coding-agent bonus). Show ~15s of that in the demo.
