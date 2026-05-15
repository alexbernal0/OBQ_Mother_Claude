# Containment Protocol — ACL-Based Scope Control

> **Purpose**: Define clear boundaries for what Mother and its agents can access and modify.

---

## Overview

| Layer | Scope | Can Read | Can Write |
|-------|-------|----------|-----------|
| **Mother** | Global governance | Everything | `governance/`, `system/` only |
| **Agent** | Task-level | Project + Mother refs | Project files + OC_Knowledge lessons |

**Core Rule**: Agents cannot write outside their scope. Reading upward is permitted; writing upward requires escalation.

---

## ACL File Format

```yaml
name: [layer-name]
description: [scope description]

read:
  - path: [glob pattern]
    description: [why access is needed]

write:
  - path: [glob pattern]
    description: [what gets written here]

forbidden:
  - path: [glob pattern]
    reason: [why off-limits]
```

---

## Mother ACL (Global Governance)

Location: `Mother/system/acl/mother.yaml`

```yaml
name: mother
description: Global governance layer — Prime Directive enforcement

read:
  - path: "**/*"
    description: Full read access for governance validation

write:
  - path: "Mother/governance/**"
    description: Override logs, decision records
  - path: "Mother/system/**"
    description: System configuration updates
  - path: "Mother/master_projects/**"
    description: Archived project knowledge

forbidden:
  - path: "Mother/prime_directive/Prime_Directive.pdf"
    reason: Immutable source of truth — read-only
  - path: "**/node_modules/**"
    reason: External dependencies
  - path: "**/.git/**"
    reason: Git internals — use git commands instead
```

---

## Agent ACL (Task Execution)

```yaml
name: agent-[task]
description: Task execution scope

read:
  - path: "Mother/prime_directive/**"
    description: Governance validation
  - path: "Mother/system/**"
    description: System configuration
  - path: "[project-path]/**"
    description: Full project codebase access
  - path: "~/Desktop/OBQ_Skills/**"
    description: Available skills and tools
  - path: "~/Desktop/OBQ_Knowledge/**"
    description: Company/product knowledge
  - path: "~/Desktop/OC_Knowledge/**"
    description: How-to knowledge

write:
  - path: "[project-path]/**"
    description: Actual code changes
  - path: "~/Desktop/OC_Knowledge/lessons/**"
    description: New lessons learned
  - path: "~/Desktop/OC_Knowledge/patterns/**"
    description: New patterns discovered

forbidden:
  - path: "Mother/prime_directive/**"
    reason: Cannot modify governance
```

---

## Containment Enforcement

### Before Any Write Operation

1. **Check ACL**: Is target path in `write` list?
2. **Check forbidden**: Is target in `forbidden` list?
3. **Verify scope**: Am I the correct layer for this operation?

### If Scope Violation Detected

```
WARNING: CONTAINMENT VIOLATION

Layer: [layer]
Attempted: [read|write] to [path]
Action Required: Escalate to human with justification
```

---

## Summary

```
Mother (governance/)
  Reads: Everything
  Writes: governance/, system/, master_projects/
  Enforces: Prime Directive

Agent (project scope)
  Reads: Mother refs, project code, OBQ_Skills, OBQ_Knowledge, OC_Knowledge
  Writes: Project files, OC_Knowledge lessons/patterns
  Enforces: Task scope

Lower layers READ up, WRITE within, ESCALATE out.
```
