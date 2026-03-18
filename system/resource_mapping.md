# Resource Mapping — OBQ Directory Specifications

> **Version**: 4.0 | **Updated**: 2026-03-18

---

## The Three Repositories

### OBQ_Skills — Executable Capabilities
**Path**: `~/Desktop/OBQ_Skills/`
**Purpose**: Reusable AI skills, automation tools, identity templates

| Type | Contents |
|------|----------|
| **Skills** | auto-skill, Auto-Tool, Auto-Doc, Auto-Review, Skill-Scan, Auto-Learn |
| **Tools** | tool_* folders with executable scripts |
| **Inception** | AI identity templates |
| **Processes** | Bootup checklists, migration guides |

> **Use when**: You need a CAPABILITY to DO something.

---

### OBQ_Knowledge — Company & Product Knowledge
**Path**: `~/Desktop/OBQ_Knowledge/`
**Purpose**: What OBQ products ARE, how they work, business context

| Type | Contents |
|------|----------|
| **Products** | Architecture docs, overviews, workflows, agents |
| **Principles** | Coding principles — the engineering north star |
| **Research** | Reference materials, diagrams, domain research |

> **Use when**: You need to UNDERSTAND what something IS in OBQ's context.

---

### OC_Knowledge — Self-Improvement Knowledge
**Path**: `~/Desktop/OC_Knowledge/`
**Purpose**: How to work better, recursive learning, meta-capabilities

| Type | Contents |
|------|----------|
| **Guides** | Agent build guide, Claude skills guide |
| **Patterns** | Reusable templates |
| **Lessons** | Post-mortems, insights |
| **References** | External docs, workspace reference |

> **Use when**: You need to LEARN how to do something better.

---

## The Key Distinction

```
UNDERSTAND (OBQ_Knowledge) → LEARN (OC_Knowledge) → DO (OBQ_Skills)
```

---

## Quick Reference

| Need | Repository | Path |
|------|------------|------|
| Understand product architecture | OBQ_Knowledge | `products/architecture/` |
| Learn how to build agents | OC_Knowledge | `guides/AGENT_BUILD_GUIDE.md` |
| Execute a skill | OBQ_Skills | `[skill]/SKILL.md` |
| Find reusable pattern | OC_Knowledge | `patterns/` |
| Avoid past mistakes | OC_Knowledge | `lessons/` |
| Load identity template | OBQ_Skills | `inception/` |
| Auto-capture learnings | OBQ_Skills | `Auto-Learn/SKILL.md` |

---

## When to Add New Content

| Content Type | Add To | Naming Convention |
|--------------|--------|-------------------|
| New skill | `OBQ_Skills/` | Via Auto-Skill |
| New tool | `OBQ_Skills/tool_<name>/` | Via Auto-Tool |
| New guide | `OC_Knowledge/guides/` | `SCREAMING_SNAKE.md` |
| New pattern | `OC_Knowledge/patterns/` | `kebab-case.md` |
| New lesson | `OC_Knowledge/lessons/` | `YYYY-MM-DD-description.md` |
| Product docs | `OBQ_Knowledge/` | Matches existing structure |
