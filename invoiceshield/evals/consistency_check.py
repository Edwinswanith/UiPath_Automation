"""
Consistency / drift check. The fastest way to embarrass yourself in a demo is to
have the agent schema, the code, the golden set and the prompt disagree. This
asserts they are in lock-step, that all JSON parses, and that the three demo
invoices still produce the headline outcomes.

Run:  python consistency_check.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "logic"))
import checks  # noqa: E402

errors: list[str] = []


def load(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return json.load(fh)


# 1. agent output-schema enums == code enums (no drift)
schema = load("agents", "case-decision-agent", "output-schema.json")
props = schema["properties"]
for field, code_set in [
    ("issueType", checks.ISSUE_TYPES),
    ("recommendedAction", checks.RECOMMENDED_ACTIONS),
    ("recommendedStage", checks.RECOMMENDED_STAGES),
]:
    schema_set = set(props[field]["enum"])
    if schema_set != code_set:
        errors.append(f"enum drift on {field}: schema={schema_set} code={code_set}")
    else:
        print(f"  OK enum {field}: schema == code ({len(code_set)} values)")

# 2. audit schema is valid JSON
load("agents", "audit-summary-agent", "output-schema.json")
print("  OK audit-summary output schema parses")

# 3. golden set parses and uses only valid enums
golden = load("evals", "golden_cases.json")
for c in golden:
    e = c["expected"]
    if e["issueType"] not in checks.ISSUE_TYPES:
        errors.append(f"{c['id']}: invalid issueType {e['issueType']}")
    if e["recommendedStage"] not in checks.RECOMMENDED_STAGES:
        errors.append(f"{c['id']}: invalid stage {e['recommendedStage']}")
print(f"  OK {len(golden)} golden cases parse and use valid enums")

# 4. the three demo invoices still produce the headline outcomes
demo = {
    "INV-1002": ("VEN-104", "PO-1002", 225000, "7781", "BANK_MISMATCH"),
    "INV-1001": ("VEN-101", "PO-1001", 50000, "1122", "DUPLICATE"),
    "INV-1003": ("VEN-103", "PO-1003", 108000, "5566", "AMOUNT_VARIANCE"),
}
for num, (v, p, a, b, expect) in demo.items():
    got = checks.decide(
        {"invoiceNumber": num, "vendorId": v, "poNumber": p, "invoiceAmount": a, "invoiceBankAccount": b}
    )["decision"]["issueType"]
    if got != expect:
        errors.append(f"demo {num}: expected {expect} got {got}")
    else:
        print(f"  OK demo {num} -> {expect}")

# 5. the prompt still references the core enums (catches a renamed value)
prompt = open(os.path.join(ROOT, "agents", "case-decision-agent", "system-prompt.md"), encoding="utf-8").read()
for token in ["BANK_MISMATCH", "HOLD_AND_ESCALATE", "Finance Escalation", "humanReviewRequired"]:
    if token not in prompt:
        errors.append(f"prompt no longer mentions {token}")
print("  OK prompt references the core enums")

if errors:
    print("\nCONSISTENCY ERRORS:")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("\nCONSISTENCY OK")
