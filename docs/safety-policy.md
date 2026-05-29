# Safety Policy

## Purpose

This document defines the permissions, approvals, and restrictions that govern the Background Scientific Cognition System. The system must remain bounded by safety, cost, access, and permission rules at all times.

---

## Permission Model

Three tiers of actions:

### Tier 1: Always Allowed

These actions require no approval:

| Action | Rationale |
|---|---|
| Search allowed academic APIs | Core research function |
| Read paper metadata | Core research function |
| Read paper abstracts | Core research function |
| Read legally available full text | Core research function |
| Generate ideas | Core research function |
| Score ideas | Core research function |
| Create skills | Core learning function |
| Write reports locally | Documentation function |
| Update research wiki | Documentation function |
| Run code in sandbox | Analysis function (sandboxed) |
| Log audit events | Safety function |

### Tier 2: Approval Required

These actions require explicit user approval before execution:

| Action | Rationale |
|---|---|
| Send emails | External communication |
| Publish content externally | External communication |
| Submit papers | External action |
| Spend money (API costs) | Financial impact |
| Access private accounts | Security risk |
| Download restricted datasets | Access control |
| Modify important configuration | System stability |
| Change safety settings | Safety impact |
| Expand permission scope | Safety impact |
| Use sensitive data | Privacy risk |
| Access non-public repositories | Access control |

### Tier 3: Never Allowed

These actions are blocked by default and cannot be enabled:

| Action | Rationale |
|---|---|
| Bypass paywalls | Legal and ethical violation |
| Scrape disallowed sites | Terms of service violation |
| Fabricate citations | Scientific integrity violation |
| Hide failed searches | Audit integrity violation |
| Delete rejection logs | Audit integrity violation |
| Disable audit logs | Safety violation |
| Treat simulated data as real | Scientific integrity violation |
| Claim guaranteed novelty | Scientific integrity violation |
| Disguise AI authorship | Transparency violation |
| Access personal private data | Privacy violation |
| Modify external systems without permission | Safety violation |

---

## Approval Workflow

### Requesting Approval

When an action requires approval:

1. System creates an `ApprovalRequest` record
2. Request includes:
   - Action type
   - Action description
   - Action payload (what will happen)
   - Run ID (which research run triggered this)
   - Project ID
3. Research run pauses in `waiting_for_approval` state
4. User is notified (dashboard, future: email/webhook)

### Approving

1. User reviews request details
2. User approves with optional notes
3. System records approval in `ApprovalRequest`
4. Research run resumes
5. Action is executed
6. Audit log records the approval and execution

### Denying

1. User reviews request details
2. User denies with required reason
3. System records denial in `ApprovalRequest`
4. Research run resumes with denial recorded
5. System adapts behavior (may choose alternative approach)
6. Audit log records the denial and adaptation

---

## Budget Controls

### Per-Run Budgets

Each research run has configurable limits:

```json
{
  "max_minutes": 60,
  "max_sources": 50,
  "max_cost_usd": 5.0
}
```

### Budget Enforcement

- System tracks cumulative cost during run
- When budget is 80% consumed, system logs warning
- When budget is 100% consumed, run pauses
- User can approve budget extension or terminate run

### Cost Tracking

LLM calls tracked per provider:

| Provider | Cost Model |
|---|---|
| OpenAI | Per token (varies by model) |
| Anthropic | Per token (varies by model) |
| Local | Hardware cost only |

Cost estimated before each LLM call. Actual cost logged after.

---

## Source Compliance

### Allowed Sources (Default)

| Source | Access Method | Compliance |
|---|---|---|
| OpenAlex | REST API | Free, open access |
| Semantic Scholar | REST API | Free tier available |
| Crossref | REST API | Free, open access |
| arXiv | REST API | Free, open access |
| PubMed | E-utilities | Free, public domain |
| DOAJ | REST API | Free, open access |
| CORE | REST API (with key) | Free with registration |
| Unpaywall | REST API (with email) | Free, legal |

### Restricted Sources

| Source | Restriction |
|---|---|
| Google Scholar | No scraping allowed |
| IEEE Xplore | API key required, check terms |
| ScienceDirect | API key required, check terms |
| Springer | API key required, check terms |
| Wiley | API key required, check terms |
| Taylor & Francis | API key required, check terms |

### Source Rules

1. Never scrape websites without API access
2. Always respect robots.txt
3. Always rate-limit requests
4. Store provenance for all metadata
5. Do not download paywalled full text
6. Do not bypass authentication

---

## Data Safety

### Simulated Data

When the system generates simulated or synthetic data:

1. Must be clearly labeled as simulated
2. Must not be presented as real experimental results
3. Must be stored with a `simulated: true` flag
4. Must be excluded from novelty claims

### User Data

1. User research ideas stored locally only
2. No data sent to external services without explicit consent
3. LLM calls may send text to provider APIs (user consents via API key configuration)
4. No user data sold or shared with third parties

### Audit Data

1. Audit logs cannot be disabled
2. Audit logs cannot be deleted (except by database admin)
3. Audit logs are append-only
4. Failed runs still preserve audit logs

---

## Agent Safety

### Agent Permissions

Each agent has defined tool permissions:

| Agent | Allowed Tools |
|---|---|
| Orchestrator | All (with budget limits) |
| User Intent | None (analysis only) |
| Idle Cognition | Literature search, idea scoring |
| Literature | Academic connectors |
| Paper Analyst | LLM analysis |
| Cluster | Embeddings, clustering |
| Conflict | LLM analysis |
| Research Question | LLM generation |
| Hypothesis | LLM generation |
| Validation Planner | Dataset search, LLM |
| Data Analyst | Sandbox execution only |
| Skeptic | Literature search, LLM |
| Decision | LLM analysis |
| Skill Curator | Skill CRUD |
| Archivist | Report/wiki generation |

### Agent Restrictions

1. Agents cannot modify safety settings
2. Agents cannot disable audit logging
3. Agents cannot expand their own permissions
4. Agents cannot approve their own requests
5. Agents must stay within budget limits
6. Agents must log all external API calls

---

## Novelty Claims

The system must never:

1. Claim guaranteed novelty without thorough prior-art search
2. Claim "first" or "only" without evidence
3. Claim novelty based on incomplete literature review
4. Present incremental modifications as breakthroughs
5. Omit conflicting evidence that weakens novelty claims

The system must always:

1. Link novelty claims to prior-art search results
2. Include confidence level in novelty assessments
3. Present supporting and opposing evidence
4. Recommend human verification for high-stakes claims
5. Store the complete search history for audit

---

## Transparency

### Generated Content

All LLM-generated content must be:

1. Labeled as AI-generated
2. Linked to the prompts that produced it
3. Linked to the evidence that informed it
4. Distinguishable from human-written content
5. Auditable through the audit log

### Decision Transparency

Every system decision must include:

1. What was decided
2. Why it was decided
3. What evidence supported the decision
4. What alternatives were considered
5. What the confidence level is

---

## Failure Handling

When something fails:

1. Log the failure immediately
2. Preserve all partial state
3. Notify the user if critical
4. Do not silently continue
5. Do not fabricate success
6. Do not hide error messages
7. Record what was attempted and why it failed

---

## Incident Response

If the system detects a safety violation:

1. Immediately pause the current run
2. Log the violation as a system event
3. Notify the user
4. Do not attempt to continue
5. Require explicit user instruction to resume

---

## Configuration

Safety settings are per-project:

```json
{
  "approval_required_for_external_actions": true,
  "allowed_sources": ["openalex", "semantic_scholar", "crossref", "arxiv"],
  "max_cost_per_run_usd": 5.0,
  "max_idle_cycles_per_day": 3,
  "idle_research_enabled": true,
  "require_novelty_verification": true,
  "log_all_llm_calls": true
}
```

These settings can only be changed by the user through the settings UI. The system cannot modify its own safety settings.
