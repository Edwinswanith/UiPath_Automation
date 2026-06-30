# Devpost submission checklist — InvoiceShield Case

Everything below is ready except the two things only you can do: record the
video and click Submit. Work top to bottom.

## Hard requirements (Completeness criterion)
- [x] Public GitHub repo with README + setup: https://github.com/Edwinswanith/UiPath_Automation
- [x] Functional prototype that runs (one command: `cd invoiceshield && bash run_all.sh`)
- [ ] Demo video, <= 5 minutes, public or unlisted (record with `docs/demo-script.md`)
- [ ] Submitted on Devpost before the deadline (Mon Jun 29, 11:45pm PDT)

## Record the video
1. Before recording, launch the live app: in Studio Web open SimpleApprovalApp,
   click **Debug on cloud**, then **Save & Debug**. It opens at the Apps runtime
   URL in a new tab. Keep that tab open. This is your "functioning on Automation
   Cloud" footage.
2. Follow `docs/demo-script.md` exactly. Keep it under 5:00.
3. Upload to YouTube (Unlisted is fine) or Vimeo. Copy the link.
4. Test the link in an incognito window so judges can actually open it.

## Devpost form — what to paste in each field
- **Project name:** InvoiceShield Case
- **Tagline:** Governing the risky invoice exceptions humans must own.
- **Track:** Track 1 — UiPath Maestro Case
- **What it does:** Maestro orchestrates AI agents, automation, and people across
  long-running processes; InvoiceShield applies the **Case** side of that to the
  exceptions humans must own. It turns risky AP invoice exceptions (bank-account
  mismatch, duplicates, PO variance, missing goods receipts) into governed cases.
  Agents investigate and recommend, deterministic Maestro rules route, a human
  owns the money decision, a mock ERP write is blocked until that human signs off,
  and a non-linear re-entry loop handles vendor verification.
- **How we built it:** Maestro Case (Studio Web) for orchestration and the
  human-in-the-loop; a real Finance Escalation Action App; deterministic policy
  + tools in Python, plus a **weak-signal fusion model** that catches structured
  fraud passing every hard rule, with a confidence score that abstains to deeper
  investigation when low; two low-code agent specs (Agent Builder) and one coded
  LangGraph agent (external framework, governed by UiPath); a 39-case eval
  harness with an LLM-as-judge and an **accuracy scoreboard** (100% recall, 0%
  false positives, +23% recall from signal fusion over hard rules alone);
  defense-in-depth guardrails. Built in part with a coding agent (Claude Code).
- **Challenges:** Maestro Case is in early preview. Native Data Fabric case
  entities are "Coming Soon," so case fields are defined as task outputs. The
  solution publishes and deploys to Automation Cloud (a real Case Decision agent
  built in Agent Builder and the human Action App are both live), but the "Debug
  on cloud" path for the Case fails at packaging with `No solution tool factory is
  registered`, a known UiPath-acknowledged bug
  (https://forum.uipath.com/t/studio-web-solution-that-contains-maestro-flow-has-a-deploy-bug/5754068),
  so a fully-automated end-to-end Case run was not exercised through that path. We
  built and deployed the agent, ran the human action live, and made the agentic
  decision logic fully runnable and measured in the repo.
- **Built with (tags):** uipath, uipath-maestro, agent-builder, langgraph,
  python, claude-code
- **Repo link:** https://github.com/Edwinswanith/UiPath_Automation
- **Video link:** (paste after upload)

## Coding-agent bonus (free points)
Mention in the video and the write-up that the coded agent, the eval harness,
the deterministic logic, and the docs were built with a coding agent (Claude
Code). That earns extra Platform Usage points in both phases.

## Final 60-second pre-submit check
- [ ] Repo opens public; README renders; `run_all.sh` is present.
- [ ] Video link opens in incognito and is <= 5:00.
- [ ] Devpost project is attached to Track 1 and to your team.
- [ ] Hit Submit. Keep Tuesday morning (your time) as upload buffer only.
