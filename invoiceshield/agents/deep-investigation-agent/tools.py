"""
Deterministic tools exposed to the LangGraph Deep Investigation Agent.

These wrap logic/checks.py (the single source of truth) as LangChain tools.
The agent decides WHICH tools to call and in what order when evidence is
incomplete or conflicting; the tools themselves are pure and deterministic, so
the math and lookups are never left to the LLM (per UiPath + Anthropic guidance).
"""
from __future__ import annotations

import os
import sys

# make logic/checks.py importable regardless of where this is run from
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_REPO_ROOT, "logic"))

import checks  # noqa: E402

from langchain_core.tools import tool  # noqa: E402


@tool
def lookup_vendor(vendor_id: str) -> dict:
    """Return the vendor master record (name, approved bank account last 4, tax id, risk status). Use to verify the vendor exists and to get the approved bank account."""
    return checks.lookup_vendor(vendor_id)


@tool
def lookup_po(po_number: str) -> dict:
    """Return the purchase order (amount, owning vendorId, whether a goods receipt is required). Use to verify PO ownership and amount."""
    return checks.lookup_po(po_number)


@tool
def lookup_goods_receipt(po_number: str) -> dict:
    """Return whether a goods receipt exists for the PO. Use when the PO requires one."""
    return checks.lookup_goods_receipt(po_number)


@tool
def check_duplicate(vendor_id: str, po_number: str, invoice_amount: float) -> dict:
    """Return whether an already-paid invoice matches this vendor+PO+amount. Use to detect duplicate billing."""
    return checks.check_duplicate(vendor_id, po_number, float(invoice_amount))


TOOLS = [lookup_vendor, lookup_po, lookup_goods_receipt, check_duplicate]
