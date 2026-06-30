#!/usr/bin/env bash
# InvoiceShield - run the whole verifiable prototype in one command.
# Use this on camera for the demo: it proves the agentic decision logic,
# guardrails, exception handling and evals all run end to end.
set -e
cd "$(dirname "$0")"

echo "============================================================"
echo " 1/5  Unit tests  (deterministic routing brain)"
echo "============================================================"
python3 logic/test_checks.py

echo; echo "============================================================"
echo " 2/5  Eval harness  (30 golden cases: success/edge/adversarial)"
echo "============================================================"
python3 evals/run_evals.py

echo; echo "============================================================"
echo " 3/5  Robustness / fuzz  (malformed + extreme inputs)"
echo "============================================================"
python3 logic/robustness_test.py

echo; echo "============================================================"
echo " 4/5  Consistency / drift  (code == schema == prompt == data)"
echo "============================================================"
python3 evals/consistency_check.py

echo; echo "============================================================"
echo " 5/5  End-to-end stress  (5 scenarios, guardrail + injection)"
echo "============================================================"
python3 stress_test.py

echo; echo "============================================================"
echo " ALL GREEN - InvoiceShield prototype verified."
echo "============================================================"
