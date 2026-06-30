# Support / forum report: Maestro Case solution fails to publish (AgentHack staging)

Post this as a reply on the existing thread
"Studio Web Solution that Contains Maestro Flow has a Deploy Bug"
(https://forum.uipath.com/t/studio-web-solution-that-contains-maestro-flow-has-a-deploy-bug/5754068),
or as a new topic in the AgentHack category. Text is ready to paste.

---

**Adding a Maestro *Case* data point to this publish/deploy issue, in case it helps engineering.**

**Environment**
- UiPath AgentHack 2026 staging tenant (`staging.uipath.com`, org `hackathon26_1022`)
- Studio Web, a Maestro **Case** project ("Maestro Case" inside "Solution 1", alongside an Action App)

**Symptom**
"Debug on cloud" (and Publish) fails at the packaging step, before any stage executes. Reproduced three times, identically.

**Exact errors**
- Output log: `Failed to pack from snapshot: Solution pack failed: No solution tool factory is registered`
- Dialog: `Solution publish failed — Failed to queue publish for one or more projects. Please try again.`

**What works (the failure is isolated to the Case project)**
The case plan itself validates. The Health analyzer shows only one info-level item (a secondary-stage note); there are no errors on the stages, tasks, or rules. Critically, the **Action App in the very same solution** runs cleanly: "Debug on cloud" on the app provisions the solution successfully ("Provisioning solution completed") and launches the app live at the Apps runtime URL (`apps_/.../run/...`), where it renders and accepts input. So the failure is **isolated to the Maestro Case project's pack/publish step**, not the tenant, the account, or the solution as a whole. It looks like the same unified-vs-legacy solution-package-format incompatibility described earlier in this thread, just on the pack side rather than the upload side, and specific to the Case project.

**Ask**
Could you confirm whether the same server-side fix (enabling unified solution-package support on the tenant solution feed) also covers Maestro **Case** solutions, and whether it can be enabled for the AgentHack staging tenant? Right now no client-side path (Studio Web or CLI) can publish a Maestro Case solution to this tenant, so live debug/deploy is blocked for Track 1 Case submissions.

Thanks.
