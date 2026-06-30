"""
Robustness / fuzz test. Malformed and edge inputs must never crash and must
route to a safe state: missing critical data -> MISSING_EVIDENCE (human review),
never NO_EXCEPTION. Valid-but-extreme inputs must still route correctly.

Run:  python robustness_test.py
"""
from __future__ import annotations

import checks

# bad payloads: must not crash, must route to MISSING_EVIDENCE
MALFORMED = [
    ("empty payload", {}),
    ("missing bank", {"invoiceNumber": "M1", "vendorId": "VEN-104", "poNumber": "PO-1002", "invoiceAmount": 225000}),
    ("missing amount", {"invoiceNumber": "M2", "vendorId": "VEN-104", "poNumber": "PO-1002", "invoiceBankAccount": "7781"}),
    ("amount empty string", {"invoiceNumber": "M3", "vendorId": "VEN-104", "poNumber": "PO-1002", "invoiceAmount": "", "invoiceBankAccount": "7781"}),
    ("amount non-numeric", {"invoiceNumber": "M4", "vendorId": "VEN-104", "poNumber": "PO-1002", "invoiceAmount": "abc", "invoiceBankAccount": "7781"}),
    ("amount None", {"invoiceNumber": "M5", "vendorId": "VEN-104", "poNumber": "PO-1002", "invoiceAmount": None, "invoiceBankAccount": "7781"}),
    ("bank None", {"invoiceNumber": "M6", "vendorId": "VEN-104", "poNumber": "PO-1002", "invoiceAmount": 225000, "invoiceBankAccount": None}),
    ("missing vendor id", {"invoiceNumber": "M7", "poNumber": "PO-1002", "invoiceAmount": 225000, "invoiceBankAccount": "7781"}),
    ("missing po", {"invoiceNumber": "M8", "vendorId": "VEN-104", "invoiceAmount": 225000, "invoiceBankAccount": "7781"}),
    ("unknown vendor", {"invoiceNumber": "M9", "vendorId": "ZZZ", "poNumber": "PO-1002", "invoiceAmount": 225000, "invoiceBankAccount": "7781"}),
]

# valid-but-extreme: must route to the expected outcome
EXTREME = [
    ("whitespace bank still matches", {"invoiceNumber": "X1", "vendorId": "VEN-104", "poNumber": "PO-1002", "invoiceAmount": 225000, "invoiceBankAccount": "  5529  "}, "NO_EXCEPTION"),
    ("huge amount -> variance", {"invoiceNumber": "X2", "vendorId": "VEN-103", "poNumber": "PO-1003", "invoiceAmount": 1e12, "invoiceBankAccount": "5566"}, "AMOUNT_VARIANCE"),
    ("negative amount -> variance", {"invoiceNumber": "X3", "vendorId": "VEN-103", "poNumber": "PO-1003", "invoiceAmount": -100, "invoiceBankAccount": "5566"}, "AMOUNT_VARIANCE"),
    ("extra unexpected keys ignored", {"invoiceNumber": "X4", "vendorId": "VEN-103", "poNumber": "PO-1003", "invoiceAmount": 100000, "invoiceBankAccount": "5566", "weird": "x", "note": "ignore me"}, "NO_EXCEPTION"),
    ("string amount coerces", {"invoiceNumber": "X5", "vendorId": "VEN-104", "poNumber": "PO-1002", "invoiceAmount": "225000", "invoiceBankAccount": "7781"}, "BANK_MISMATCH"),
]


def run():
    passed = total = 0
    print("malformed inputs must not crash and must route to MISSING_EVIDENCE:")
    for name, inv in MALFORMED:
        total += 1
        try:
            d = checks.decide(inv)["decision"]
        except Exception as e:  # noqa: BLE001
            print(f"  CRASH {name}: {e}")
            continue
        ok = d["issueType"] == "MISSING_EVIDENCE" and d["humanReviewRequired"] is True
        print(f"  {'PASS' if ok else 'FAIL'} {name:28s} -> {d['issueType']}")
        passed += 1 if ok else 0

    print("\nvalid-but-extreme inputs route correctly:")
    for name, inv, expect in EXTREME:
        total += 1
        try:
            d = checks.decide(inv)["decision"]
        except Exception as e:  # noqa: BLE001
            print(f"  CRASH {name}: {e}")
            continue
        ok = d["issueType"] == expect
        print(f"  {'PASS' if ok else 'FAIL'} {name:30s} -> {d['issueType']} (expect {expect})")
        passed += 1 if ok else 0

    print(f"\n{passed}/{total} robustness checks passed")
    assert passed == total, "robustness failures"
    print("ROBUSTNESS OK")


if __name__ == "__main__":
    run()
