# Quarterly Connection Output Template

Default output format for `/quarterly:connect`. Company-specific formats (if present
in this `reference/` directory) take precedence over this template.

---

## File naming

```
reports/quarterly-connection-Q<N>-<YYYY>.md
```

---

## Source linking rule

Every Jira issue and document referenced in the report **must include a hyperlink**
to the original source. Use markdown links throughout:
- Jira issues: `[PROJ-123](https://yourorg.atlassian.net/browse/PROJ-123)`
- Google Docs / Drive: `[Document Title](https://docs.google.com/...)`
- Other URLs: inline as markdown links

Do not reference issues or documents by name or key alone without a link.

---

## Output structure

```markdown
# Quarterly Connection – [Name], Q[N] [Year]

---

## 1. Goals

SMART goals framed as "Q[N] [Year]: [Goal title]". Each goal should be Specific,
Measurable, Achievable, Relevant, and Time-bound.

### Q[N] [Year]: [Goal Title]

[1–2 paragraph description of the goal, its motivation, and what was delivered.
Use bullet points for specific deliverables. Link Jira issues and documents.]

- Delivered [feature/outcome] — [PROJ-123](url)
- Published [document] — [Doc Title](url)

### Q[N] [Year]: [Goal Title 2]

...

---

## 2. Key Accomplishments

Top 3–5 accomplishments with business impact, stakeholders, and linked evidence.

- **[Achievement]**
  - **Impact:** [Measurable outcome]
  - **Stakeholders:** [Who benefited]
  - **Value alignment:** [Company core value this exemplifies]
  - **References:** [PROJ-123](url), [Doc Title](url)

---

## 3. Areas of Excellence

Where you excelled, tied to company values.

- **[Strength area]:** [Specific example and which core value it demonstrates]

---

## 4. Challenges & Growth Areas

What didn't go as planned, and what was learned. Keep tone constructive.

- **Challenge:** [What happened]
  - **Learning:** [What was learned]
  - **Action:** [How you're addressing it]

---

## 5. Priorities for Next Quarter

Clear priorities aligned to team OKRs and company strategy.

- **[Priority]** — [brief description and connection to team/company goals]
- **[Priority]** — ...

**Support needed:**
- [Resources, collaboration, or coaching]

---

## 6. Career Growth & Aspirations

Role evolution, future interests, stretch opportunities.

- **Current focus:** [Where you're growing now]
- **Future direction:** [Long-term interests and goals]
- **Stretch opportunities:** [Desired experiences or projects]

---

## 7. Feedback & Lessons Learnt

Key feedback received and how it was applied.

- **Feedback:** [Key point]
- **Application:** [How it was integrated]

---

## 8. Supporting Data & Metrics *(optional)*

| Metric | Target | Actual | References |
|---|---|---|---|
| [Metric] | [Value] | [Value] | [PROJ-123](url) |
```

---

## Writing guidelines

- Every Jira issue and document must be a hyperlink — never a bare key or title.
- Use concise language with action verbs.
- Prioritize outcomes over activity — avoid "helped with" or "involved in".
- Align achievements with company values where possible.
- Write in first person from the employee's perspective.
- Goals section: frame each as SMART with `Q[N] [Year]:` prefix in the heading.
