# Dark Factory Skills — How to use with ruflo

> This file is auto-imported into `CLAUDE.md` via `@CLAUDE.skills.md`
> by the devcontainer's `post-create.sh`. Keeping the guidance here
> (instead of inside `CLAUDE.md`) means `ruflo init` regenerating
> `CLAUDE.md` does not delete it — only the small auto-managed import
> block in `CLAUDE.md` may need to be re-added (post-create does that
> idempotently on next container start).
>
> Edit this file freely. It is checked into the repo and survives
> across `ruflo init`. To regenerate from the bundled template (loses
> your edits), delete it and re-run
> `bash /usr/local/bin/devcontainer-post-create.sh`.

## Cross-cutting institutional memory (apply by default)

| Skill                     | Phase      | Use it when…                                                       |
| ------------------------- | ---------- | ------------------------------------------------------------------ |
| `/engineering-playbook`   | Always-on  | **Apply by default at session start.** Portable engineering rules — TDD ≥90% meaningful coverage, real E2E by default, TLA+/TLC at two gates, measurable assurance (no eyeballing), feature-branch workflow with remote-as-truth, conventional commits with no AI attribution, permissive licenses only, decisive proposals over multiple-choice, continuous knowledge accumulation. Also: `/engineering-playbook bootstrap` copies the full 7-file KB (`engineering-rules`, `best-practices`, `lessons-learned`, `architecture-decisions`, `common-failures`, `debugging-playbook`, `project-playbook`) into `docs/knowledge-base/`. |

> The other skills below tell you *how* to execute each piece (specs, scenarios, validation, UI tests, assurance, pentest). `/engineering-playbook` tells you *what* the cross-cutting rules are. Treat it as load-bearing — don't restate the rules each turn; refer back to it.

## Methodology skills (13 prompt-only)

| Skill                     | Phase      | Use it when…                                                       |
| ------------------------- | ---------- | ------------------------------------------------------------------ |
| `/socratic-interviewer`   | Pre-spec   | Intent is vague; you need scope, non-goals, outputs, and verification explicit. ONE question at a time. NEVER writes code. |
| `/ontology-analyst`       | Pre-spec   | Root cause feels off; need to apply Essence / Root Cause / Prerequisites / Hidden Assumptions with a confidence score. |
| `/nlspec-writer`          | Pre-build  | Produce an 8-section NLSpec (`spec.md`) from a clarified request.  |
| `/scenario-designer`      | Pre-build  | Generate Gherkin holdout scenarios under `scenarios/` (build agents must NOT see them). |
| `/spec-preflight`         | Gate       | Score spec + scenarios across 4 clarity dimensions; go/no-go.      |
| `/validate-design`        | Gate       | Architecture-scale: produce a falsifiable-evidence pack (TLA+, fitness functions, thin-slice, pre-mortem, threat model). |
| `/ui-test`                | Post-build | Translate Gherkin scenarios into headless Playwright tests (Chromium/Firefox/WebKit). Captures screenshot + video + trace evidence; MCP server `playwright` is registered for AI-driven browser control. |
| `/cloakbrowser`           | Post-build | Stealth Chromium (Playwright drop-in) — escalation from `/ui-test` when Cloudflare Turnstile / FingerprintJS / BrowserScan / reCAPTCHA v3 blocks stock Playwright. **Authorization-gated** (`.cloakbrowser/<engagement-id>/authorization.md`); hard-refusal list mirrors the binary license. Default to `/ui-test` first; reach for this only with a documented engagement. |
| `/holdout-validate`       | Post-build | LLM-as-judge against the built artifact; 0–100 per scenario.       |
| `/assure`                 | Post-build | SOC2-grade: coverage + property fuzz + strict typing + CI gates + evidence bundle. |
| `/formal-verify`          | Verification | **TLA+/TLC as first-class discipline** for any distributed/concurrent/state-machine work (provisioning lifecycle, schedulers, locking, retry/recovery, queue/worker, multi-tenant isolation, capacity/quota, async coordination). Spawns an 8-role parallel agent team (architect / spec designer / invariant designer / state-machine modeler / concurrency analyst / coverage engineer / counterexample analyst / spec-code validator). Treats "TLC passes with weak spec" as FAILURE. Mandates sabotage-checks for every invariant. CI gate blocks merge. Wraps the `/specula/*` bundle for the mechanical workflow. |
| `/enterprise-saas-validate` | Pipeline | Full enterprise validation pipeline with two profiles: `backend-only` (exhaustive backend matrix + security/pentest + TLA+ + HTML reports) and `full-stack` (adds Playwright + Storybook + Chromatic + axe-core + UI/UX deep review + frontend code review + UI-state TLA+). Orchestrates a massively parallel agent team — backend impl, integration tests, security review, TLA+ team, perf tests, CI reporting, docs, optionally frontend impl/E2E/visual regression/a11y. Generates per-PR HTML report with suites + coverage + security + TLA+ + perf + trends. **Use when project graduates from prototype → production SaaS.** Speed via parallelism; rigor via every gate still bindings. |
| `/pentest`                | Security   | **Authorized pentesting**. Hard-gates on ROE/SOW. Orchestrates 35 pentest-ai-agents (recon, web-hunter, api-security, cloud-security, ad-attacker, exploit-chainer, poc-validator, report-generator, ...) + optional autonomous tools Shannon (white-box web) and PentAGI (multi-agent platform). Evidence under `.pentest/<engagement-id>/`. If an authorized engagement needs bot-detection bypass on an in-scope target, escalate to `/cloakbrowser` — both skills can reference the SAME authorization file. |

## Specula skills (TLA+ verification pipeline, 9 skills)

For distributed-systems / consensus / concurrent code where invariants
must hold across all interleavings the model captures. Backed by the
Specula MCP servers (`tracedebugger`, `spec_analyzer`,
`inv_checking_tool`) registered at user scope with `SPECULA_ROOT=/opt/specula`.

| Skill                       | Phase           | Use it when…                                                       |
| --------------------------- | --------------- | ------------------------------------------------------------------ |
| `/code-analysis`            | Phase 1         | Investigate a system implementation, do bug archaeology, produce a modeling brief that guides spec generation. |
| `/spec-generation`          | Phase 2         | Turn a modeling brief into TLA+ specs (base + MC + trace validation + instrumentation). |
| `/harness-generation`       | Phase 2.5       | Instrument source code to emit NDJSON traces and write the test scenarios that exercise protocol paths. |
| `/tla-trace-workflow`       | Phase 3 (trace) | Validate that a trace matches a TLA+ spec; debug trace-validation failures; fix spec/trace inconsistencies. |
| `/tla-checking-workflow`    | Phase 3 (MC)    | Run TLC model checking or simulation; analyze invariant-violation counterexamples; classify spec issue vs strong invariant vs real bug. |
| `/validation-workflow`      | Phase 3 (orch.) | Orchestrate the trace ↔ MC loop until both pass — the spec faithfully models the system. |
| `/bug-confirmation`         | Phase 4         | Map a TLC counterexample to a real triggerable scenario; reproduce the bug in the real system; rule out false positives. |
| `/bug-recording`            | Phase 4 (log)   | Log a confirmed bug to the shared Specula bug tracker; update status after filing issues / PRs. |
| `/writing-prompt-extra`     | Setup           | Write target-specific `.prompt-extra.md` (bug-family hypotheses, scope guidance, production-incident context) for a new target system. |

Specula's recommended pipeline:

```
/code-analysis  →  /spec-generation  →  /harness-generation
              →  /validation-workflow  (which iterates
                  /tla-trace-workflow  ↔  /tla-checking-workflow)
              →  /bug-confirmation  →  /bug-recording
```

Background reading: see `specula/workflow-overview.md` in the skills
bundle (also available at
`~/.claude/skills/code-analysis/../workflow-overview.md` via the
symlinked tree).

All skills live in `~/.claude/skills/<name>/`. The post-create symlinker
handles two layouts: top-level leaf skills (with `SKILL.md`) and nested
bundle dirs (like `specula/`, recursed one level deep). Sources are
under `/opt/dark-factory-skills/` (read-only, baked into the image).

## Security testing toolkit (orchestrated via `/pentest`)

For **authorized** pentesting only. `/pentest` is the gate — it refuses
to operate without `.pentest/<engagement-id>/authorization.md` (ROE /
SOW / signed scope) on record.

### pentest-ai-agents (35 spawnable Claude Code agents)

Cloned to `/opt/pentest-ai-agents/`; symlinked into `~/.claude/agents/`
on first start. Spawn with `Agent({subagent_type: "<name>", ...})`.

| Phase             | Agents                                                                                |
|-------------------|---------------------------------------------------------------------------------------|
| Plan / model      | `engagement-planner`, `threat-modeler`, `attack-planner`                              |
| Recon             | `recon-advisor`, `osint-collector`                                                    |
| Active (Tier 2)   | `web-hunter`, `api-security`, `ad-attacker`, `cloud-security`, `container-breakout`, `credential-tester`, `vuln-scanner`, `mobile-pentester`, `wireless-pentester`, `social-engineer`, `phishing-operator`, `llm-redteam`, `cicd-redteam`, `bug-bounty` |
| Exploit / validate| `exploit-chainer`, `payload-crafter`, `poc-validator`, `c2-operator`, `privesc-advisor`, `opsec-anonymizer` |
| Defensive         | `forensics-analyst`, `malware-analyst`, `reverse-engineer`, `detection-engineer`, `stig-analyst` |
| Report / specialty| `report-generator`, `bizlogic-hunter`, `exploit-guide`, `ctf-solver`, `swarm-orchestrator` |

All Tier-2 agents auto-include the `_scope-guard.md` shared block —
per-command scope verification, hard-refusal list (no DoS, no mass
internet scanning, no persistent backdoors, no false-flag ops).

### Heavy autonomous tools (opt-in, source cloned at `/opt/`)

| Tool       | Where        | Launch                       | When to use                                              |
|------------|--------------|------------------------------|----------------------------------------------------------|
| **Shannon**| `/opt/shannon` | `make pentest-shannon-up`  | Autonomous white-box web app / API testing; CI-friendly. |
| **PentAGI**| `/opt/pentagi` | `make pentest-pentagi-up`  | Multi-agent supervised exploitation, knowledge-graph driven. |

Both launch via docker-compose through the dev container's DinD. Each
needs `.env` configured (LLM provider keys, target). The `/pentest`
skill knows when to recommend each.

## Recommended end-to-end pipeline

```
/engineering-playbook  (apply at session start — institutional rules)
   │
   ▼
/socratic-interviewer  →  /ontology-analyst (if root cause is unclear)
                       →  /nlspec-writer  →  /scenario-designer  →  /spec-preflight
                       →  /validate-design  (architecture-scale / Complex / Adversarial)
                       →  ruflo coder/sparc-coder builds — reads spec.md, NOT scenarios/
                       →  /ui-test  (if there's a UI — translate scenarios → Playwright)
                       →  /holdout-validate
                       →  /assure  (SOC2-sensitive paths)
                       →  /formal-verify  (DISTRIBUTED / CONCURRENT / STATE-MACHINE work
                                            — first-class TLA+/TLC with the 8-agent team;
                                            wraps and drives /specula/* underneath)
                       →  /enterprise-saas-validate  (production-SaaS gate — backend matrix
                                            + security/pentest + TLA+ + frontend pipeline
                                            if full-stack + HTML report per CI run)
                       →  /pentest  (security validation — authorized engagements only)
                       →  ruflo reviewer
```

For a fresh project that wants the full 7-file KB structure:

```
/engineering-playbook bootstrap
   │
   ▼
docs/knowledge-base/{project-playbook, engineering-rules, best-practices,
   lessons-learned, architecture-decisions, common-failures, debugging-playbook}.md
```

End of every session: extract → dedupe → generalize → classify → commit (per ER-13).

## Calling these skills with ruflo

Two patterns. **A** = lead session drives. **B** = delegate to a
background ruflo agent so you can keep working.

### Pattern A — Inline (you drive)

Just type the slash-command in the Claude chat with a one-line target:

```
/assure on src/redaction/. 95% line / 90% branch / 100% function for
critical-security; 10k+ Hypothesis cases with shrinking; mypy --strict;
wire CI in .github/workflows/ci.yml. Stop before destructive changes.
```

```
/validate-design on docs/en/proposals/<slug>.md. Scaffold the
evidence pack at docs/en/validation/<slug>/. Stop after the rubric
plan; wait for my OK before invoking executors.
```

### Pattern B — Delegated to a ruflo agent (SendMessage-first)

Use when you want parallel background work. Spawns named agents that
read the skill's `SKILL.md` and follow it; agents coordinate via
`SendMessage` per the project `CLAUDE.md`.

```
ruflo, harden src/redaction with measurable assurance. Spawn:

  • name: "assurance-engineer"
    subagent_type: security-auditor
    run_in_background: true
    prompt: |
      Read /opt/dark-factory-skills/assure/SKILL.md and follow it
      against src/redaction/. 95/90/100 thresholds, 10k+ Hypothesis,
      mypy --strict, fail-on-miss CI. Emit
      .assurance/<run-id>/assurance-report.json.
      SendMessage progress + final report path to "tester".

  • name: "tester"
    subagent_type: tester
    run_in_background: true
    prompt: |
      Wait for "assurance-engineer". Run the suite; intentionally
      regress one metric to prove the gate fails. SendMessage to
      "reviewer".

  • name: "reviewer"
    subagent_type: reviewer
    run_in_background: true
    prompt: |
      Wait for "tester". Block if any anti-pattern from the assure
      guide is present (lowered thresholds, untracked type-ignores,
      irreproducible evidence).
```

For `/validate-design`, the swarm is bigger — see the README's
"Asking ruflo to run /validate-design" subsection.

### Pattern C — Gate before merge (CI-style)

```
ruflo, build the feature in spec.md (architect → coder → tester →
reviewer). Coder reads spec.md ONLY, not scenarios/. After tester
finishes, before reviewer, invoke /holdout-validate then /assure.
Treat any "fail" verdict as a hard merge block.
```

## Holdout discipline (do not skip)

`scenarios/` is the honest test set. The coding agents MUST NOT see
it during build, or they optimise for passing scenarios instead of for
correctness.

- ruflo `coder` is pointed at `spec.md`, never the project root if
  `scenarios/` lives there. Pass file paths explicitly.
- When a `/holdout-validate` scenario fails, translate the failure
  into a **spec amendment** before invoking `coder` again. Never
  paste the scenario text back to the coder.

## Anti-patterns to watch for

- **Running ruflo on vague intent.** Redirect through
  `/socratic-interviewer` first.
- **Skipping `/spec-preflight`.** A spec scoring < 0.80 burns tokens
  in the ruflo loop. Fix the spec first.
- **Letting `coder` see `scenarios/`.** Defeats the holdout.
- **Re-grading after showing failures to `coder`.** The rerun
  optimises for that scenario, not for correctness.
- **Sign-off on text.** PO sign-off requires the evidence pack
  (`docs/<lang>/validation/<slug>/`), not the proposal text alone.
- **Validation theatre.** A pre-mortem with no follow-through, a TLA+
  spec that doesn't model the action that worried you, a fitness
  function with an empty assertion.
- **"Temporary" lowered thresholds.** Temporary == permanent.
  Exclude a module explicitly with a tracked deadline; don't lower
  the global bar.
- **Manual evidence collection.** If a human assembles the audit
  pack, the pack is wrong (stale / partial / biased). Generate it
  from CI on every merge to `main`.
