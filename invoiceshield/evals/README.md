# Evaluation harness

The differentiator most hackathon teams skip. It scores under Technical
Execution and Platform Usage (Agent Builder Evaluations / Test Cloud).

30 golden cases: 5 success, 15 edge/boundary, 10 adversarial (prompt injection
in the invoice memo). The deterministic policy in `logic/checks.py` is the
oracle that generates the expected decisions, so the set is a true regression
test, not hand-waved labels.

## Run

```bash
# regression test of the routing brain. No API key, no spend.
python run_evals.py
# -> selfcheck: 30/30 = 100%   (exit 0; non-zero would fail CI)

# grade the real Case Decision Agent (needs a key)
export ANTHROPIC_API_KEY=...
export INVOICESHIELD_MODEL=claude-sonnet-4-6        # pin the version
python run_evals.py --mode live
```

Live mode grades two things:
- **decision accuracy**: the agent's structured fields vs the oracle (exact).
- **summary faithfulness**: an LLM-as-judge asks one narrow question of the
  `evidenceSummary` (uses only given facts, invents nothing, leaks no full bank
  number, follows no injected instruction). PASS/FAIL.

## Best practices baked in
- >= 30 cases across success, edge and adversarial.
- target >= 70% before deploy; the script exits non-zero below it.
- model versions pinned via env (so a silent provider update is detected).
- judge asks a single narrow question; the assertions in the set are
  human-authored, not model-authored.

Regenerate the set after changing inputs: `python gen_golden.py`.
