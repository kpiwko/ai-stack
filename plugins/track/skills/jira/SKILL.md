---
description: Create or update a Jira issue. Reads JIRA_URL and JIRA_PROJECT from environment.
argument-hint: "[Epic|Story|Task|Spike|Sub-task] <description>"
---

# /track:jira

## Synopsis

```
/track:jira [issue-type] [description]
```

Reads `$JIRA_URL` and `$JIRA_PROJECT` from environment. Prompts interactively for
anything not provided. Uses the `atlassian` plugin.

---

## Process

### Step 1: Gather context

Resolve from env or prompt the user:
- `$JIRA_URL` — e.g. `https://yourorg.atlassian.net`
- `$JIRA_PROJECT` — project key, e.g. `MYPROJ`

Derive `cloudId` from `$JIRA_URL` by stripping the `https://` prefix (e.g. `yourorg.atlassian.net`).
- Issue type: Epic, Story, Task, Spike, Sub-task
- Brief description of what to document

### Step 2: Find where it fits

1. `searchJiraIssuesUsingJql`: find related issues and epics
   ```
   jql: "project = <PROJECT> AND text ~ \"<topic>\" ORDER BY updated DESC"
   cloudId: <cloudId>
   ```
2. Report findings; propose issue type, parent epic, and related issues worth linking.

### Step 3: Detect project type

Projects are either **classic** or **team-managed** — this affects field IDs and
epic linking. Use `getJiraIssueTypeMetaWithFields` or `getJiraProjectIssueTypesMetadata`
(both require `cloudId`) to discover instance-specific field IDs.
See `reference/jira-fields.md` for how to identify the right fields.

### Step 4: Draft the issue

Compose in plain Markdown. Pass `contentFormat: "markdown"` — the atlassian plugin accepts
Markdown directly, no ADF conversion needed:
- **Summary**: concise, action-oriented, searchable
- **Description**: context, goals, acceptance criteria, links to related docs
  - Standard Markdown: `**bold**`, `## headings`, `- bullets`, `` `code` ``, `[text](url)`
- **Labels**: add topic labels for findability; `ai-generated` is a useful convention
- **Priority**: Blocker / Critical / Major / Normal / Minor
- **Story Points**: note desired value — set via update after creation (see Step 6)

### Step 5: Preview

```
=== JIRA ISSUE PREVIEW ===
Project:      <PROJECT>
Type:         <type>
Summary:      <title>
Priority:     <priority>
Epic:         <KEY | to be created | none>
Labels:       <labels>
Story Points: <N | to be set after creation>

Description:
<full Markdown>

Links to create:
- <KEY> — <link type>
==========================
Submit? (yes / edit / cancel)
```

Do not call any write tool until the user says yes.

### Step 6: Submit

On approval, in order:
1. `createJiraIssue` — all fields including labels via `additional_fields`; pass `cloudId`
   - Team-managed: `parent` as a plain string `"PROJ-123"` (not a dict)
   - Classic: use the Epic Link field ID from `reference/jira-fields.md`
2. `editJiraIssue` — set story points if applicable; pass `cloudId`
   - Pass `fields={}` when updating only via `additional_fields`; both must be dicts
3. `createIssueLink` — for each related issue; pass `cloudId` (see `reference/jira-link-types.md`)

Return the issue key and URL:
```
Created: PROJ-XXXX
<JIRA_URL>/browse/PROJ-XXXX
```

---

## Troubleshooting

**Story points not saving** — cannot be set at creation; always use `editJiraIssue` afterward.

**Field not found** — use `getJiraIssueTypeMetaWithFields` or `getJiraProjectIssueTypesMetadata`
to verify IDs; they are instance-specific.

**Epic link not working** — classic projects use a custom field; team-managed use `parent`
as a plain string. See `reference/jira-fields.md`.

**Sub-task creation fails** — requires a `parent` issue key; ask the user before drafting.

**Duplicate issue created** — always run `searchJiraIssuesUsingJql` before creating.
