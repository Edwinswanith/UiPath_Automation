#!/usr/bin/env python3
"""
InvoiceShield - Decision Console (local demo UI).

A tiny, dependency-free web UI for DEMOING the workflow on screen instead of in
a terminal. It imports the REAL decision engine (logic/checks.py) - the same code
covered by the 30-case eval harness and the stress test - so what you see here is
exactly what the Maestro agents route on. Nothing is faked.

Run:
    python3 demo_ui.py
then open http://localhost:8000

What it shows, mirroring the Maestro Case:
  1. INVESTIGATE      - deterministic evidence + the agent's risk verdict
  2. HUMAN DECISION   - the money is locked; the ERP write is blocked until a
                        human signs off (try it before and after)
  3. RESOLVE & CLOSE  - ERP write allowed, final outcome, money impact, audit
"""
from __future__ import annotations

import json
import os
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "logic"))
import checks  # noqa: E402  (the real engine - single source of truth)
import re  # noqa: E402

PORT = int(os.environ.get("PORT", "8000"))


def extract_invoice(text: str) -> dict:
    """Stand-in for UiPath Document Understanding / IXP: pull the structured
    fields out of raw invoice text. In production a PDF or scan goes through
    Document Understanding; here a regex reads these text files. The extracted
    fields are exactly what the case runs on."""
    def grab(*patterns: str) -> str:
        for p in patterns:
            m = re.search(p, text or "", re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return ""
    amount = grab(
        r"(?:invoice\s*)?amount\s*[:\-]?\s*\$?\s*([\d,]+(?:\.\d+)?)",
        r"total\s*[:\-]?\s*\$?\s*([\d,]+)",
    ).replace(",", "")
    return {
        "invoiceNumber": grab(r"invoice\s*number\s*[:\-]?\s*(INV-?\w+)", r"\b(INV-\d+)\b"),
        "vendorId": grab(r"vendor\s*id\s*[:\-]?\s*(VEN-?\w+)", r"\b(VEN-\d+)\b"),
        "poNumber": grab(r"po\s*number\s*[:\-]?\s*(PO-?\w+)", r"\b(PO-\d+)\b"),
        "invoiceAmount": amount,
        "invoiceBankAccount": grab(
            r"bank\s*account\s*[:\-]?\s*[X\*x ]*(\d{4})",
            r"account\s*(?:ending|no|#)?\s*[:\-]?\s*[X\*x ]*(\d{4})",
        ),
    }

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>InvoiceShield - Decision Console</title>
<style>
  :root{
    --bg:#0b0e14; --panel:#131722; --panel2:#0f131c; --bd:#232838;
    --tx:#e6e9ef; --mut:#8b93a7; --accent:#3b82f6; --accent2:#60a5fa;
    --red:#ef4444; --green:#22c55e; --amber:#f59e0b;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--tx);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
  header{padding:18px 24px;border-bottom:1px solid var(--bd);display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
  header h1{font-size:18px;margin:0;letter-spacing:.2px}
  header .sub{color:var(--mut);font-size:12.5px}
  .badge{margin-left:auto;font-size:11px;color:var(--accent2);border:1px solid var(--accent);
    border-radius:999px;padding:3px 10px;white-space:nowrap}
  .wrap{padding:20px 24px;max-width:1180px;margin:0 auto}
  .controls{background:var(--panel);border:1px solid var(--bd);border-radius:14px;padding:16px;margin-bottom:18px}
  .chips{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
  .chip{background:var(--panel2);border:1px solid var(--bd);color:var(--tx);border-radius:10px;
    padding:8px 12px;font-size:12.5px;cursor:pointer;transition:.12s}
  .chip:hover{border-color:var(--accent)}
  .chip b{color:var(--accent2)}
  .grid-in{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
  .grid-in label{display:block;font-size:11px;color:var(--mut);margin-bottom:4px}
  .grid-in input{width:100%;background:var(--panel2);border:1px solid var(--bd);border-radius:8px;
    color:var(--tx);padding:8px;font-size:13px}
  .row2{display:flex;align-items:center;gap:16px;margin-top:14px;flex-wrap:wrap}
  .tog{display:flex;align-items:center;gap:8px;color:var(--mut);font-size:12.5px;cursor:pointer;user-select:none}
  .tog input{accent-color:var(--red)}
  .go{margin-left:auto;background:var(--accent);color:#fff;border:0;border-radius:10px;
    padding:11px 22px;font-size:14px;font-weight:600;cursor:pointer}
  .go:hover{background:#2f6fe0}
  .reset{background:transparent;border:1px solid var(--bd);color:var(--mut);border-radius:10px;padding:11px 16px;cursor:pointer}
  .stages{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}
  .stage{background:var(--panel);border:1px solid var(--bd);border-radius:14px;padding:16px;min-height:280px;opacity:.5;transition:.18s}
  .stage.on{opacity:1}
  .stage h2{font-size:12px;letter-spacing:1.2px;color:var(--mut);margin:0 0 12px;font-weight:700}
  .stage h2 .n{color:var(--accent2)}
  .ev{font-size:12.5px;line-height:1.9}
  .ev .k{color:var(--mut)}
  .ev .v{color:var(--tx);font-weight:600}
  .ev .bad{color:var(--red);font-weight:700}
  .ev .ok{color:var(--green);font-weight:700}
  .verdict{margin-top:12px;border-top:1px solid var(--bd);padding-top:12px}
  .issue{display:inline-block;font-weight:700;font-size:13px;padding:4px 10px;border-radius:8px;
    background:rgba(239,68,68,.12);color:#fda4a4;border:1px solid rgba(239,68,68,.4)}
  .issue.clean{background:rgba(34,197,94,.12);color:#86efac;border-color:rgba(34,197,94,.4)}
  .score{display:flex;align-items:center;gap:10px;margin:12px 0 6px}
  .score .num{font-size:30px;font-weight:800;line-height:1}
  .bar{height:8px;border-radius:6px;background:#22283a;flex:1;overflow:hidden}
  .bar > i{display:block;height:100%;background:var(--red)}
  .meta{font-size:12px;color:var(--mut);line-height:1.8;margin-top:6px}
  .meta b{color:var(--tx)}
  .lock{display:flex;align-items:center;gap:10px;font-weight:700;font-size:13px;margin-bottom:12px}
  .lock .dot{width:11px;height:11px;border-radius:50%}
  .lock.locked .dot{background:var(--red)} .lock.locked{color:#fda4a4}
  .lock.open .dot{background:var(--green)} .lock.open{color:#86efac}
  select,.signrole{width:100%;background:var(--panel2);border:1px solid var(--bd);color:var(--tx);
    border-radius:8px;padding:9px;font-size:13px;margin-top:8px}
  .btn{width:100%;margin-top:10px;border-radius:9px;padding:10px;font-size:13px;font-weight:600;cursor:pointer;border:1px solid var(--bd)}
  .btn.try{background:transparent;color:var(--mut)}
  .btn.sign{background:var(--accent);color:#fff;border:0}
  .note{font-size:12px;border-radius:8px;padding:9px 11px;margin-top:10px;line-height:1.5}
  .note.block{background:rgba(239,68,68,.1);color:#fca5a5;border:1px solid rgba(239,68,68,.35)}
  .note.allow{background:rgba(34,197,94,.1);color:#86efac;border:1px solid rgba(34,197,94,.35)}
  .note.inj{background:rgba(245,158,11,.1);color:#fcd34d;border:1px solid rgba(245,158,11,.35)}
  .impact{font-size:13px;font-weight:600;margin-top:12px;line-height:1.5}
  .muted{color:var(--mut);font-size:12.5px;line-height:1.7}
  footer{color:var(--mut);font-size:11.5px;text-align:center;padding:16px}
  .batch{background:var(--panel);border:1px solid var(--bd);border-radius:14px;padding:16px;margin-bottom:6px}
  .bhd{font-size:14px;font-weight:700}
  .bhd span{color:var(--mut);font-weight:400;font-size:11.5px}
  .drop{margin-top:10px;border:1.5px dashed var(--bd);border-radius:12px;padding:22px;text-align:center;color:var(--mut);font-size:13px;cursor:pointer;transition:.15s;line-height:1.7}
  .drop.over{border-color:var(--accent);color:var(--tx);background:var(--panel2)}
  .drop .pick{color:var(--accent2);text-decoration:underline;cursor:pointer}
  .drop code{color:var(--accent2);font-size:11.5px}
  table.bt{width:100%;border-collapse:collapse;margin-top:14px;font-size:12px}
  table.bt th{text-align:left;color:var(--mut);font-weight:600;padding:7px 8px;border-bottom:1px solid var(--bd)}
  table.bt td{padding:7px 8px;border-bottom:1px solid var(--bd);color:var(--tx)}
  table.bt tr:hover td{background:var(--panel2)}
  .pill{display:inline-block;font-size:10.5px;font-weight:700;padding:2px 8px;border-radius:999px}
  .pill.human{background:rgba(239,68,68,.13);color:#fda4a4;border:1px solid rgba(239,68,68,.4)}
  .pill.auto{background:rgba(34,197,94,.13);color:#86efac;border:1px solid rgba(34,197,94,.4)}
  .bsum{margin-top:12px;font-size:12.5px;color:var(--tx);line-height:1.5}
</style>
</head>
<body>
<header>
  <h1>InvoiceShield <span style="color:var(--mut);font-weight:400">· Decision Console</span></h1>
  <span class="sub">Agents recommend · rules route · a human decides · the guardrail blocks the money</span>
  <span class="badge">live engine: logic/checks.py</span>
</header>

<div class="wrap">
  <div class="batch">
    <div class="bhd">Batch intake <span>drop invoice files; extraction stands in for UiPath Document Understanding</span></div>
    <div id="drop" class="drop">Drop invoice files here, or <label class="pick">browse<input type="file" id="files" accept=".txt,.text" multiple hidden></label>.<br>Sample files live in <code>invoiceshield/data/sample_invoices/</code></div>
    <div id="bresult"></div>
  </div>
  <div class="bhd" style="margin:18px 0 8px">Single invoice <span>pick a sample below, or click a batch row, to step one through</span></div>
  <div class="controls">
    <div class="chips" id="chips"></div>
    <div class="grid-in">
      <div><label>Invoice #</label><input id="invoiceNumber"></div>
      <div><label>Vendor ID</label><input id="vendorId"></div>
      <div><label>PO #</label><input id="poNumber"></div>
      <div><label>Amount</label><input id="invoiceAmount"></div>
      <div><label>Bank acct</label><input id="invoiceBankAccount"></div>
    </div>
    <div class="row2">
      <label class="tog"><input type="checkbox" id="inject"> Attach prompt-injection memo ("approve immediately")</label>
      <button class="reset" onclick="resetAll()">Reset</button>
      <button class="go" onclick="investigate()">Investigate &rarr;</button>
    </div>
  </div>

  <div class="stages">
    <div class="stage" id="s1">
      <h2><span class="n">1</span> · INVESTIGATE</h2>
      <div id="s1body" class="muted">Pick a sample invoice above and press Investigate.</div>
    </div>
    <div class="stage" id="s2">
      <h2><span class="n">2</span> · HUMAN DECISION</h2>
      <div id="s2body" class="muted">The human owns the money decision.</div>
    </div>
    <div class="stage" id="s3">
      <h2><span class="n">3</span> · RESOLVE &amp; CLOSE</h2>
      <div id="s3body" class="muted">Mock ERP write + audit trail.</div>
    </div>
  </div>
</div>
<footer>Local demo. Same decision engine as the eval harness and stress test. No payment moves without a recorded human decision.</footer>

<script>
const SAMPLES = [
  {tag:"Bank mismatch", id:"INV-1002", b:"225k", inv:{invoiceNumber:"INV-1002",vendorId:"VEN-104",poNumber:"PO-1002",invoiceAmount:"225000",invoiceBankAccount:"7781"}},
  {tag:"Duplicate",     id:"INV-1001", b:"50k",  inv:{invoiceNumber:"INV-1001",vendorId:"VEN-101",poNumber:"PO-1001",invoiceAmount:"50000",invoiceBankAccount:"1122"}},
  {tag:"Amount variance",id:"INV-1003",b:"108k", inv:{invoiceNumber:"INV-1003",vendorId:"VEN-103",poNumber:"PO-1003",invoiceAmount:"108000",invoiceBankAccount:"5566"}},
  {tag:"Structured fraud",id:"INV-1005",b:"49.5k",inv:{invoiceNumber:"INV-1005",vendorId:"VEN-105",poNumber:"PO-1005",invoiceAmount:"49500",invoiceBankAccount:"4407"}},
  {tag:"Clean invoice", id:"INV-2001", b:"100k", inv:{invoiceNumber:"INV-2001",vendorId:"VEN-103",poNumber:"PO-1003",invoiceAmount:"100000",invoiceBankAccount:"5566"}},
];
const DECISIONS = {
  BANK_MISMATCH:["Payment Hold","Rejected Suspected Fraud"],
  DUPLICATE:["Rejected Duplicate"],
  AMOUNT_VARIANCE:["Approved With Exception","Rejected"],
  MISSING_GOODS_RECEIPT:["Pending Vendor Clarification","Rejected"],
  COMPOSITE_RISK:["Rejected Suspected Fraud","Payment Hold","Pending Vendor Clarification"],
  MISSING_EVIDENCE:["Pending Vendor Clarification"],
  NO_EXCEPTION:[],
};
let STATE = null;

const $=id=>document.getElementById(id);
function fields(){return ["invoiceNumber","vendorId","poNumber","invoiceAmount","invoiceBankAccount"]}
function setForm(inv){fields().forEach(f=>$(f).value=inv[f]||"")}
function getForm(){const o={};fields().forEach(f=>o[f]=$(f).value);return o}

function renderChips(){
  $("chips").innerHTML = SAMPLES.map((s,i)=>
    `<div class="chip" onclick="pick(${i})">${s.tag} <b>${s.id} · ${s.b}</b></div>`).join("");
}
function pick(i){setForm(SAMPLES[i].inv); $("inject").checked=false; investigate();}
function resetAll(){fields().forEach(f=>$(f).value="");$("inject").checked=false;
  ["s1","s2","s3"].forEach(s=>$(s).classList.remove("on"));
  $("s1body").innerHTML='<span class="muted">Pick a sample invoice above and press Investigate.</span>';
  $("s2body").innerHTML='<span class="muted">The human owns the money decision.</span>';
  $("s3body").innerHTML='<span class="muted">Mock ERP write + audit trail.</span>';STATE=null;}

async function post(url,body){const r=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});return r.json();}

async function investigate(){
  const inv=getForm(); const injected=$("inject").checked;
  const res=await post("/api/decide",{invoice:inv,injected});
  STATE={inv,res,injected};
  const ev=res.evidence, d=res.decision;
  const clean = d.issueType==="NO_EXCEPTION";
  const bankRow = (ev.approvedBankAccount!=null)
     ? `inv <b>${(inv.invoiceBankAccount||"").slice(-4)}</b> vs approved <b>${ev.approvedBankAccount}</b> ${(""+(inv.invoiceBankAccount||"")).slice(-4)===(""+ev.approvedBankAccount)?'<span class="ok">match</span>':'<span class="bad">MISMATCH</span>'}`
     : '<span class="bad">vendor not found</span>';
  $("s1").classList.add("on");
  $("s1body").innerHTML = `
    <div class="ev">
      <div><span class="k">vendor:</span> <span class="v">${ev.vendorFound?'found':'<span class=bad>not found</span>'}</span></div>
      <div><span class="k">bank:</span> ${bankRow}</div>
      <div><span class="k">PO amount:</span> <span class="v">${ev.poAmount!=null?ev.poAmount:'-'}</span> · variance <span class="v">${ev.amountVariancePercent}%</span></div>
      <div><span class="k">duplicate:</span> <span class="v">${ev.duplicateFound?'<span class=bad>YES '+(ev.matchedInvoiceNumber||'')+'</span>':'no'}</span></div>
      <div><span class="k">goods receipt:</span> <span class="v">${ev.goodsReceiptRequired?(ev.goodsReceiptFound?'received':'<span class=bad>missing</span>'):'n/a'}</span></div>
      <div><span class="k">evidence:</span> <span class="v">${ev.evidenceCompleteness}</span></div>
    </div>
    <div class="verdict">
      <span class="issue ${clean?'clean':''}">${d.issueType.replace(/_/g,' ')}</span>
      <div class="score"><span class="num">${d.riskScore}</span><div class="bar"><i style="width:${d.riskScore}%;background:${clean?'var(--green)':d.riskScore>=80?'var(--red)':'var(--amber)'}"></i></div></div>
      <div class="meta">action <b>${d.recommendedAction.replace(/_/g,' ')}</b> · route <b>${d.recommendedStage}</b><br>confidence <b>${d.confidence}</b> · human review required: <b>${d.humanReviewRequired}</b></div>
      ${(d.signals&&d.signals.length)?`<div class="meta" style="margin-top:6px">signals fired: <b>${d.signals.map(s=>s.replace(/([A-Z])/g,' $1').toLowerCase().trim()).join(', ')}</b> · composite ${d.signalScore}</div>`:''}
      ${d.issueType==='COMPOSITE_RISK'?'<div class="note inj">No single rule fired. The weak signals combined cross the threshold: structured fraud a flat rules engine misses.</div>':''}
      ${injected?'<div class="note inj">Prompt-injection memo attached. Routing is computed from data, not memo text, so the verdict is unchanged.</div>':''}
    </div>`;

  // stage 2
  $("s2").classList.add("on");
  if(!d.humanReviewRequired){
    $("s2body").innerHTML='<div class="lock open"><span class="dot"></span>No exception</div><div class="muted">Clean invoice. Straight-through. No case opened, no human time spent.</div>';
    $("s3").classList.add("on");
    $("s3body").innerHTML=`<div class="muted">Nothing to resolve. Invoice cleared for normal payment.</div>`;
    return;
  }
  const opts=(DECISIONS[d.issueType]||["Rejected"]).map(x=>`<option>${x}</option>`).join("");
  $("s2body").innerHTML=`
    <div class="lock locked" id="lock"><span class="dot"></span>Money locked · payment held</div>
    <div class="muted">The agent recommended; a human must own the decision.</div>
    <label class="muted" style="display:block;margin-top:12px">Human decision</label>
    <select id="finalDecision">${opts}</select>
    <input class="signrole" id="role" placeholder="Reviewer (e.g. Finance Analyst)" value="Finance Analyst">
    <button class="btn try" onclick="tryEarly()">Try ERP write now (before sign-off)</button>
    <button class="btn sign" onclick="signoff()">Sign off &amp; write ERP &rarr;</button>
    <div id="s2note"></div>`;
  $("s3body").innerHTML='<div class="muted">Waiting for a recorded human decision before any ERP write.</div>';
}

async function tryEarly(){
  const d=STATE.res.decision;
  const r=await post("/api/resolve",{finalDecision:$("finalDecision").value,humanDecision:null,riskScore:d.riskScore});
  $("s2note").innerHTML=`<div class="note ${r.allowed?'allow':'block'}">ERP write attempted with no human: <b>${r.allowed?'ALLOWED':'BLOCKED'}</b><br>${r.reason}</div>`;
}

async function signoff(){
  const d=STATE.res.decision; const inv=STATE.inv;
  const final=$("finalDecision").value, role=$("role").value||"Reviewer";
  const r=await post("/api/resolve",{finalDecision:final,humanDecision:role+": "+final,riskScore:d.riskScore});
  $("lock").className="lock open"; $("lock").innerHTML='<span class="dot"></span>Unlocked by '+role;
  $("s2note").innerHTML=`<div class="note allow">Human signed off. ERP write now permitted.</div>`;
  $("s3").classList.add("on");
  const amt=Number(inv.invoiceAmount||0).toLocaleString();
  const impact={
    BANK_MISMATCH:`Blocked a ${amt} payment to an unverified bank account.`,
    DUPLICATE:`Prevented a ${amt} double payment.`,
    AMOUNT_VARIANCE:`Held ${amt} until the ${STATE.res.evidence.amountVariancePercent}% overbilling was signed off.`,
    COMPOSITE_RISK:`Held ${amt}. Structured fraud no single rule caught, flagged by signal fusion.`,
    MISSING_GOODS_RECEIPT:`Held ${amt} until goods receipt was confirmed.`,
    MISSING_EVIDENCE:`Held ${amt} pending vendor clarification.`,
  }[d.issueType]||`Recorded decision for ${amt}.`;
  $("s3body").innerHTML=`
    <div class="lock open"><span class="dot"></span>ERP write ALLOWED</div>
    <div class="ev">
      <div><span class="k">final decision:</span> <span class="v">${final}</span></div>
      <div><span class="k">signed off by:</span> <span class="v">${role}</span></div>
      <div><span class="k">mock ERP:</span> <span class="ok">written</span></div>
    </div>
    <div class="impact">${impact}</div>
    <div class="muted" style="margin-top:8px">Audit Summary Agent logs the case: evidence, recommendation, who decided, and why.</div>`;
}
// --- batch intake: drop multiple invoice files, extract, fan out ---
let BATCH=[];
const drop=$("drop"), filesEl=$("files");
drop.onclick=()=>filesEl.click();
filesEl.onchange=e=>handleFiles([...e.target.files]);
["dragenter","dragover"].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.add("over")}));
["dragleave","drop"].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.remove("over")}));
drop.addEventListener("drop",e=>{e.preventDefault();drop.classList.remove("over");handleFiles([...e.dataTransfer.files])});
function readText(file){return new Promise(res=>{const r=new FileReader();r.onload=()=>res(r.result);r.onerror=()=>res("");r.readAsText(file)})}
async function handleFiles(files){
  if(!files.length) return;
  $("bresult").innerHTML='<div class="muted" style="margin-top:12px">Extracting and routing '+files.length+' file(s)...</div>';
  const rows=[]; let human=0, auto=0;
  for(const f of files){
    const text=await readText(f);
    const r=await post("/api/extract",{text});
    const flagged=r.decision.humanReviewRequired;
    flagged?human++:auto++;
    rows.push({f:f.name,inv:r.invoice,d:r.decision,flagged});
  }
  BATCH=rows;
  const body=rows.map((x,i)=>`<tr style="cursor:pointer" onclick="openOne(${i})">
    <td>${x.f}</td><td><b>${x.inv.invoiceNumber||'?'}</b></td><td>${x.inv.vendorId||'?'}</td>
    <td>${Number(x.inv.invoiceAmount||0).toLocaleString()}</td>
    <td>${x.d.issueType==='NO_EXCEPTION'?'<span class="ok">clean</span>':'<span class="bad">'+x.d.issueType.replace(/_/g,' ')+'</span> · risk '+x.d.riskScore}</td>
    <td>${x.flagged?'<span class="pill human">to a human</span>':'<span class="pill auto">auto-close</span>'}</td></tr>`).join("");
  $("bresult").innerHTML=`<table class="bt"><thead><tr><th>file</th><th>invoice</th><th>vendor</th><th>amount</th><th>verdict</th><th>outcome</th></tr></thead><tbody>${body}</tbody></table>
    <div class="bsum"><b>${files.length}</b> invoices in &rarr; <b>${auto}</b> auto-closed, <b>${human}</b> routed to a human. Each file becomes its own case; only the risky ones reach a person. Click any row to step it through below.</div>`;
}
function openOne(i){const x=BATCH[i];if(!x)return;setForm(x.inv);$("inject").checked=false;investigate();window.scrollTo({top:document.body.scrollHeight,behavior:'smooth'});}
renderChips();
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split("?")[0] in ("/", "/index.html"):
            body = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            data = {}
        if self.path == "/api/decide":
            invoice = data.get("invoice", {})
            res = checks.decide(invoice)
            self._json(200, {"evidence": res["evidence"], "decision": res["decision"]})
        elif self.path == "/api/extract":
            invoice = extract_invoice(data.get("text", ""))
            res = checks.decide(invoice)
            self._json(200, {"invoice": invoice, "evidence": res["evidence"], "decision": res["decision"]})
        elif self.path == "/api/resolve":
            allowed, reason = checks.can_update_mock_erp(
                data.get("finalDecision", ""),
                data.get("humanDecision") or None,
                int(data.get("riskScore", 0)),
            )
            self._json(200, {"allowed": allowed, "reason": reason})
        else:
            self._json(404, {"error": "not found"})


def main():
    url = f"http://localhost:{PORT}"
    print("InvoiceShield Decision Console")
    print("  open:", url)
    print("  (Ctrl+C to stop)")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
