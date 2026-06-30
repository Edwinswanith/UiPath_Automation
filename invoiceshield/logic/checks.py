"""
InvoiceShield Case - deterministic check logic (single source of truth).

Design principle (per Anthropic "Building effective agents" and UiPath
"Best practices for building agents"): LLMs are weak at math, comparison and
lookups, so every deterministic decision lives HERE, in code, not in an agent.
The agent's job is judgment and natural-language explanation, not arithmetic
and not routing. Maestro Case rules route on the fields this module produces.

This module backs three things so they can never drift apart:
  1. the deterministic "tools" the agents call (lookup_*, check_duplicate),
  2. the policy classifier used to grade agent output in the eval harness,
  3. the guardrail that blocks the mock-ERP write.

No external dependencies. Pure standard library so it runs anywhere.
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass, asdict, field
from typing import Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# --- enums kept in lock-step with schemas/case-decision-output.schema.json ----
ISSUE_TYPES = {
    "BANK_MISMATCH",
    "DUPLICATE",
    "AMOUNT_VARIANCE",
    "MISSING_GOODS_RECEIPT",
    "MISSING_EVIDENCE",
    "COMPOSITE_RISK",
    "NO_EXCEPTION",
}
CONFIDENCE_LEVELS = {"High", "Medium", "Low"}
RECOMMENDED_ACTIONS = {
    "HOLD_AND_ESCALATE",
    "HUMAN_REVIEW",
    "PROCUREMENT_REVIEW",
    "REQUEST_CLARIFICATION",
    "NONE",
}
# recommendedStage values are the *logical* routing targets. They map onto the
# four stages actually built in Maestro as follows:
#   Finance Escalation, Human Review -> "Human Decision" stage
#   Vendor Clarification             -> "Vendor Clarification" secondary stage
#   Procurement Review               -> future secondary stage
#   Resolution                       -> "Resolve & Close" stage
RECOMMENDED_STAGES = {
    "Human Decision",
    "Finance Escalation",
    "Vendor Clarification",
    "Procurement Review",
    "Resolution",
}
VARIANCE_THRESHOLD_PCT = 5.0
HUMAN_REVIEW_RISK_FLOOR = 60


def _safe_float(value) -> Optional[float]:
    """Coerce to float, or None if it cannot be parsed (malformed input)."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value) -> Optional[int]:
    """Coerce to int, or None if blank/unparseable (e.g. an empty CSV cell)."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# --- tiny CSV-backed data access (stands in for ERP / vendor master) ----------
def _load(name: str) -> list[dict]:
    path = os.path.join(DATA_DIR, name)
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def lookup_vendor(vendor_id: str) -> dict:
    """Tool: return vendor master record. Bank account returned as last 4 only."""
    for row in _load("vendors.csv"):
        if row["vendorId"] == vendor_id:
            return {
                "vendorFound": True,
                "vendorName": row["vendorName"],
                "approvedBankAccount": row["approvedBankAccount"][-4:],
                "taxId": row["taxId"],
                "riskStatus": row["riskStatus"],
                "tenureDays": _safe_int(row.get("tenureDays")),
                "bankChangeDays": _safe_int(row.get("bankChangeDays")),
            }
    return {"vendorFound": False}


def lookup_po(po_number: str) -> dict:
    """Tool: return purchase-order record."""
    for row in _load("purchase_orders.csv"):
        if row["poNumber"] == po_number:
            return {
                "poFound": True,
                "poAmount": float(row["poAmount"]),
                "vendorId": row["vendorId"],
                "goodsReceiptRequired": row["goodsReceiptRequired"].lower() == "true",
            }
    return {"poFound": False}


def lookup_goods_receipt(po_number: str) -> dict:
    """Tool: return goods-receipt record."""
    for row in _load("goods_receipts.csv"):
        if row["poNumber"] == po_number:
            return {
                "goodsReceiptFound": row["goodsReceiptFound"].lower() == "true",
                "receiptId": row["receiptId"],
            }
    return {"goodsReceiptFound": False, "receiptId": None}


def check_duplicate(vendor_id: str, po_number: str, invoice_amount: float) -> dict:
    """Tool: a paid invoice with the same vendor+PO+amount is a duplicate."""
    for row in _load("invoice_history.csv"):
        if (
            row["vendorId"] == vendor_id
            and row["poNumber"] == po_number
            and float(row["amount"]) == float(invoice_amount)
            and row["status"] == "Paid"
        ):
            return {
                "duplicateFound": True,
                "matchedInvoiceNumber": row["invoiceNumber"],
                "duplicateReason": "Same vendor, PO and amount already paid",
            }
    return {"duplicateFound": False, "matchedInvoiceNumber": None}


# --- deterministic evidence + classification ---------------------------------
@dataclass
class Decision:
    issueType: str
    riskScore: int
    recommendedAction: str
    recommendedStage: str
    humanReviewRequired: bool
    confidence: str = "High"
    signalScore: int = 0
    signals: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def amount_variance_pct(invoice_amount: Optional[float], po_amount: Optional[float]) -> float:
    if invoice_amount is None or not po_amount:
        return 0.0
    return round(((invoice_amount - po_amount) / po_amount) * 100, 2)


def gather_evidence(invoice: dict) -> dict:
    """Run the deterministic tools and assemble the evidence package. Defensive
    against missing or malformed fields so a bad payload routes to review,
    never crashes and never silently passes."""
    inv_amount = _safe_float(invoice.get("invoiceAmount"))
    vendor_id = invoice.get("vendorId", "")
    po_number = invoice.get("poNumber", "")
    inv_bank = str(invoice.get("invoiceBankAccount") or "").strip()
    vendor = lookup_vendor(vendor_id)
    po = lookup_po(po_number)
    gr = lookup_goods_receipt(po_number) if po.get("poFound") else {"goodsReceiptFound": False}
    dup = check_duplicate(vendor_id, po_number, inv_amount) if inv_amount is not None else {"duplicateFound": False, "matchedInvoiceNumber": None}
    po_amount = po.get("poAmount")
    complete = bool(vendor.get("vendorFound") and po.get("poFound") and inv_amount is not None and inv_bank)
    return {
        "vendorFound": vendor.get("vendorFound", False),
        "approvedBankAccount": vendor.get("approvedBankAccount"),
        "poFound": po.get("poFound", False),
        "poAmount": po_amount,
        "goodsReceiptRequired": po.get("goodsReceiptRequired", False),
        "goodsReceiptFound": gr.get("goodsReceiptFound", False),
        "duplicateFound": dup.get("duplicateFound", False),
        "matchedInvoiceNumber": dup.get("matchedInvoiceNumber"),
        "amountVariancePercent": amount_variance_pct(inv_amount, po_amount),
        "evidenceCompleteness": "Complete" if complete else "Incomplete",
    }


def classify_and_score(invoice: dict, evidence: dict) -> Decision:
    """
    Policy rules in PRIORITY ORDER. Bank mismatch is highest because an
    unverified bank-account change is the strongest fraud signal and money
    must never move on it without a human. Routing is deterministic; the
    LLM only narrates.
    """
    inv_bank = str(invoice.get("invoiceBankAccount") or "").strip()[-4:]
    approved = str(evidence.get("approvedBankAccount") or "")

    # incomplete evidence first: missing vendor/PO, unparseable amount, or no bank
    if evidence.get("evidenceCompleteness") != "Complete":
        return Decision("MISSING_EVIDENCE", 60, "REQUEST_CLARIFICATION", "Vendor Clarification", True)

    # 1. bank account mismatch (highest priority)
    if approved and inv_bank and inv_bank != approved:
        return Decision("BANK_MISMATCH", 92, "HOLD_AND_ESCALATE", "Finance Escalation", True)

    # 2. duplicate invoice
    if evidence.get("duplicateFound"):
        return Decision("DUPLICATE", 80, "HUMAN_REVIEW", "Human Decision", True)

    # 3. amount variance over threshold
    if abs(evidence.get("amountVariancePercent", 0.0)) > VARIANCE_THRESHOLD_PCT:
        return Decision("AMOUNT_VARIANCE", 70, "HUMAN_REVIEW", "Human Decision", True)

    # 4. missing goods receipt where required
    if evidence.get("goodsReceiptRequired") and not evidence.get("goodsReceiptFound"):
        return Decision("MISSING_GOODS_RECEIPT", 65, "PROCUREMENT_REVIEW", "Procurement Review", True)

    # 5. clean -> no case needed
    return Decision("NO_EXCEPTION", 10, "NONE", "Resolution", False)


# --- Level 2: weak-signal fusion (the catch no single hard rule makes) --------
# Each signal below is a real accounts-payable fraud indicator. The weights are
# tuned so that NO single signal trips a case on its own, but a realistic
# COMBINATION crosses the threshold. That combination is the holistic judgment a
# flat per-rule engine cannot make. The eval set pins the calibration.
APPROVAL_THRESHOLDS = (25000, 50000, 100000, 250000)
NEW_VENDOR_DAYS = 90
RECENT_BANK_CHANGE_DAYS = 30
MATERIALITY_AMOUNT = 150000
RISK_FLAG_STATUSES = {"HighReview", "Watch", "High"}
URGENCY_TERMS = ("urgent", "immediately", "asap", "today", "wire now", "final notice", "right away")
COMPOSITE_RISK_THRESHOLD = 50
SIGNAL_WEIGHTS = {
    "recentBankChange": 40,          # payee bank changed days ago: top BEC indicator
    "amountJustUnderThreshold": 30,  # classic structuring just under an approval limit
    "newVendor": 25,
    "firstInvoice": 20,
    "vendorRiskFlag": 20,
    "urgencyLanguage": 15,
    "highMateriality": 10,
}


def _has_paid_history(vendor_id: str) -> bool:
    return any(r["vendorId"] == vendor_id and r["status"] == "Paid" for r in _load("invoice_history.csv"))


def _amount_just_under_threshold(amount: Optional[float]) -> bool:
    if amount is None:
        return False
    return any(t * 0.97 <= amount < t for t in APPROVAL_THRESHOLDS)


def compute_signals(invoice: dict, evidence: dict) -> dict:
    """Fuse weak signals into one composite risk score. Any single one is benign;
    the right combination is fraud. Deterministic, so it stays testable."""
    amount = _safe_float(invoice.get("invoiceAmount"))
    vendor = lookup_vendor(invoice.get("vendorId", ""))
    fired: list[str] = []
    bank_change = vendor.get("bankChangeDays")
    if bank_change is not None and bank_change < RECENT_BANK_CHANGE_DAYS:
        fired.append("recentBankChange")
    if _amount_just_under_threshold(amount):
        fired.append("amountJustUnderThreshold")
    tenure = vendor.get("tenureDays")
    if tenure is not None and tenure < NEW_VENDOR_DAYS:
        fired.append("newVendor")
    if invoice.get("vendorId") and not _has_paid_history(invoice.get("vendorId", "")):
        fired.append("firstInvoice")
    if vendor.get("riskStatus") in RISK_FLAG_STATUSES:
        fired.append("vendorRiskFlag")
    memo = str(invoice.get("memo") or invoice.get("notes") or "").lower()
    if memo and any(term in memo for term in URGENCY_TERMS):
        fired.append("urgencyLanguage")
    if amount is not None and amount >= MATERIALITY_AMOUNT:
        fired.append("highMateriality")
    score = min(100, sum(SIGNAL_WEIGHTS[s] for s in fired))
    return {"signalScore": score, "signals": fired}


def _composite_risk_score(signal_score: int) -> int:
    return min(88, 45 + signal_score // 2)


def assess(invoice: dict) -> dict:
    """Full assessment: hard rules first, then weak-signal fusion to catch
    structured fraud that passes every rule, plus a confidence the case can
    abstain on (Low -> route to deeper investigation rather than guess)."""
    evidence = gather_evidence(invoice)
    decision = classify_and_score(invoice, evidence)
    sig = compute_signals(invoice, evidence)
    decision.signalScore = sig["signalScore"]
    decision.signals = sig["signals"]
    if decision.issueType == "NO_EXCEPTION" and sig["signalScore"] >= COMPOSITE_RISK_THRESHOLD:
        # no single rule fired, but the combined weak signals indicate structured risk
        decision = Decision(
            "COMPOSITE_RISK",
            _composite_risk_score(sig["signalScore"]),
            "HUMAN_REVIEW",
            "Human Decision",
            True,
            confidence="Medium",
            signalScore=sig["signalScore"],
            signals=sig["signals"],
        )
    elif decision.issueType == "MISSING_EVIDENCE":
        decision.confidence = "Low"  # abstain: not enough to decide, send to clarification
    elif decision.issueType == "NO_EXCEPTION":
        decision.confidence = "Medium" if sig["signalScore"] >= 20 else "High"
    else:
        decision.confidence = "High"  # a hard rule fired: clear-cut
    return {"evidence": evidence, "decision": decision.to_dict(), "signals": sig}


def decide(invoice: dict) -> dict:
    """Convenience: the full assessment for one incoming invoice."""
    return assess(invoice)


# --- guardrail: the structural control, also enforced by Maestro stage gating -
ALLOWED_FINAL_DECISIONS = {
    "Rejected Duplicate",
    "Rejected Suspected Fraud",
    "Approved With Exception",
    "Payment Hold",
    "Pending Vendor Clarification",
    "Rejected",
}


def can_update_mock_erp(final_decision: str, human_decision: Optional[str], risk_score: int) -> tuple[bool, str]:
    """
    Block the ERP write unless a human owns the decision. In Maestro this is
    also enforced structurally: the Update Mock ERP task lives in Resolve &
    Close, whose entry rule requires the human decision field to be set.
    Defence in depth: the same rule is checked here at the tool boundary.
    """
    if final_decision not in ALLOWED_FINAL_DECISIONS:
        return False, f"finalDecision '{final_decision}' is not in the allowed set"
    if risk_score >= HUMAN_REVIEW_RISK_FLOOR and not human_decision:
        return False, "high-risk case requires a recorded human decision before ERP write"
    return True, "ok"


if __name__ == "__main__":
    import json

    for row in _load("incoming_invoices.csv"):
        row["invoiceAmount"] = float(row["invoiceAmount"])
        print(row["invoiceNumber"], json.dumps(decide(row)["decision"]))
