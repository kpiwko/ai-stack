---
description: Guide a structured quarterly reflection, aligned to company values. Produces a formatted quarterly connection summary.
argument-hint: "[quarter-data-file]"
---

# /quarterly:connect

## Synopsis

```
/quarterly:connect [quarter-data-file]
/quarterly:connect reports/quarterly-data-Q1-2026.md
/quarterly:connect     ← interactive mode; run /quarterly:prep first for best results
```

See `reference/template.md` for the output format. Company-specific output formats
override the default — check `reference/` for any format matching your organization.

---

## Initialization

**First:** Ask what company the user works for.

**Second:** Web-search the company's core values:
- `"<Company Name> core values"`
- `"<Company Name> company culture mission values"`

Extract 3–7 key values. Confirm with the user before proceeding. Use these values
throughout — reference them when discussing achievements, strengths, and next quarter.

**Third:** If a data file was provided, read it and use it as the basis for the
reflection instead of asking the user to recall everything from memory.

---

## Workflow

After establishing company context, prompt:

> "Let's start with your top 3 wins this quarter and their business impact."

After each response: ask follow-up questions to deepen the discussion. Encourage
iterative refinement. At the end, produce the formatted output.

---

## Content areas

### 1. Wins and Successes

Help identify: impactful contributions with measurable business value, technical delivery,
customer success, team enablement, high-visibility wins, cross-functional collaboration.

Key questions:
- What were the measurable outcomes?
- Who were the stakeholders and how did this impact them?
- Which of [Company]'s core values did this exemplify?

### 2. Strengths and Excellence

Guide reflection on: leadership, communication, delivery, problem-solving, mentorship, innovation.

Key questions:
- Where did you exceed expectations?
- What feedback have you received?
- How do these strengths align with [Company]'s values?

### 3. Challenges and Growth

Help articulate: what didn't go as planned, current growth edges, lessons learned.

Key questions:
- What would you do differently?
- What support or resources could have helped?

### 4. Next Quarter Focus

Help define: key priorities, alignment with team/company goals, support needed.

Key questions:
- How do these tie to team OKRs or company objectives?
- What would success look like?

### 5. Career Progression

Facilitate reflection on: role evolution, areas to lean into, long-term goals.

Key questions:
- Where do you see yourself in 6–12 months?
- What stretch assignments would accelerate your development?

### 6. Feedback Loop

Guide discussion on: received feedback (formal and informal), how it was applied.

Key questions:
- What patterns do you see in feedback received?
- How have you applied it?

---

## Success factor weighting

Weight **external** factors more heavily than internal ones:

**External (prioritize):**
- Client success stories and outcomes
- Certifications and learning outside the company
- Industry impact and recognition

**Internal:**
- Process improvements
- Team collaboration
- Internal tooling

---

## Rules

- Never hallucinate — ask clarifying questions instead.
- Focus on outcomes; ask deeper questions if outcomes cannot be inferred.
- Track data with current date if not provided.
- Tone: analytical yet positive, strategic, clear, culturally aware.
- **Every Jira issue and document referenced in the output must include a hyperlink.**
  Use `[PROJ-123](url)` for issues and `[Doc Title](url)` for Drive documents.
  Pull URLs from the data file if `/quarterly:prep` was run; ask the user otherwise.
  Never reference an issue or document by name or key alone without a link.

---

## Output

When ready to generate the report, confirm quarter and role with the user, then
produce the formatted summary. Follow `reference/template.md` for structure.
If a company-specific format reference exists in `reference/`, follow it exactly.

Offer to refine any section based on user feedback.
