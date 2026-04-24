---
description: Gather activity data from Gmail, Jira, and Google Drive for a given quarter. Saves a structured markdown file for use with /quarterly:connect.
argument-hint: "[Q1|Q2|Q3|Q4] [year]"
---

# /quarterly:prep

## Synopsis

```
/quarterly:prep [Q1|Q2|Q3|Q4] [year]
/quarterly:prep Q1 2026
/quarterly:prep          ← interactive mode
```

Reads `$JIRA_URL` from environment. Saves output to `reports/quarterly-data-<QN-YYYY>.md`.
Uses MCP servers: `gmail`, `mcp-atlassian`, `gdrive`.

## Quarter date ranges

| Quarter | Start | End |
|---|---|---|
| Q1 | Jan 1 | Mar 31 |
| Q2 | Apr 1 | Jun 30 |
| Q3 | Jul 1 | Sep 30 |
| Q4 | Oct 1 | Dec 31 |

---

## Process

### Step 1: Confirm quarter

If not provided, ask. Convert to concrete date range and state it before proceeding.

---

### Step 2: Gmail activity

Use `mcp__gmail__search_threads` in parallel, each with `max_results: 100`.
Append this calendar exclusion filter to every query:
```
-filename:ics -subject:"Invitation:" -subject:"Accepted:" -subject:"Declined:"
-subject:"Proposed new time:" -subject:"Updated invitation" -subject:"New event:"
```

Queries:
1. Sent mail: `after:<YYYY/MM/DD> before:<YYYY/MM/DD> in:sent <calendar-filter>`
2. Active threads: `after:<YYYY/MM/DD> before:<YYYY/MM/DD> -in:chats label:sent <calendar-filter>`
3. Important/starred: `after:<YYYY/MM/DD> before:<YYYY/MM/DD> (is:starred OR is:important) -in:sent <calendar-filter>`

**Filter by snippet first** — keep threads where the snippet suggests: you initiated,
a decision was reached, you were primary recipient (To:, not CC:), multiple exchanges.
Skip: newsletters, automated notifications, Jira/GitHub automation, HR/Workday, Slack digests.

**Fetch full bodies** (`mcp__gmail__fetch_email_bodies`) only for the highest-value threads
(up to 15 total). For threads where the snippet gives enough context, skip the full fetch.

Extract per thread: subject, key participants, date, 1–2 sentence summary of outcome.

---

### Step 3: Jira activity

Read `$JIRA_URL` from environment. Run JQL queries in parallel via `jira_search`.

**All projects, all involvement** — find everything the user touched this quarter:
```
updated >= "<YYYY-MM-DD>" AND updated <= "<YYYY-MM-DD>"
AND (
  assignee = currentUser()
  OR reporter = currentUser()
  OR worklogAuthor = currentUser()
)
ORDER BY updated DESC
```

Fetch up to 50 issues total; deduplicate by key.

For each issue extract: key + URL, summary, type, status, your role, 1-sentence contribution.
Group into: Completed / In Progress at quarter end / Created or Initiated.

---

### Step 4: Google Drive activity

Use `mcp__gdrive__search` with `rawQuery: true`. Paginate each query to completion
(`pageSize: 100`; follow `pageToken` until exhausted). Run searches sequentially per type.

1. Google Docs: `mimeType = 'application/vnd.google-apps.document' AND trashed = false AND modifiedTime > '<YYYY-MM-DDT00:00:00Z>' AND modifiedTime < '<YYYY-MM-DDT23:59:59Z>'`
2. Presentations: same with `mimeType = 'application/vnd.google-apps.presentation'`
3. Spreadsheets: same with `mimeType = 'application/vnd.google-apps.spreadsheet'`

Filter: skip org-wide templates, auto-generated meeting notes from meetings you didn't organize,
items with generic titles unrelated to your known projects.

Use `mcp__gdrive__getDocumentInfo` for metadata on the most relevant items.

Extract per document: title, type, URL, modified date, owner/collaborator status, 1-sentence description.
Group into: Authored / Presentations / Collaborative contributions.

---

### Step 5: Compile and save

Save to `reports/quarterly-data-<QN-YYYY>.md` (e.g. `reports/quarterly-data-Q1-2026.md`).

```markdown
# Quarterly Data: Q[N] [YYYY]
> Period: [Start] – [End]  |  Generated: [today]  |  Sources: Gmail, Jira, Google Drive

## Executive Summary
[3–5 bullet points: biggest themes across all sources]

## Gmail Highlights
### Key Threads & Communications
| Thread | Participants | Date | Summary |
...

## Jira Activity
### Delivered / Completed
| Issue | Summary | Type | Your Role |
...
### In Progress at Quarter End
...
### Initiated (You Created/Reported)
...

## Google Drive Activity
### Documents Authored
...
### Presentations
...
### Collaborative Contributions
...

## Notes for /quarterly:connect
[Patterns, themes, or highlights that should inform the quarterly reflection]
```

---

### Step 6: Report to user

```
=== QUARTERLY DATA PREP COMPLETE ===
Quarter:  Q[N] [YYYY] ([Start] – [End])
Saved to: reports/quarterly-data-Q[N]-[YYYY].md

Gmail:  [N] threads → [N] highlights
Jira:   [N] issues ([N] completed, [N] in-progress, [N] created)
Drive:  [N] docs ([N] authored, [N] collaborated)

Next: /quarterly:connect  (reference this file in your prompt)
=====================================
```

---

## Error handling

**Gmail no results** — broaden date range by ±1 week; try `in:anywhere`.

**Jira currentUser() fails** — use `jira_get_user_profile` to verify account, then substitute username directly.

**Drive search times out** — use `listFolder` on known project folders; try monthly windows.

**File already exists** — ask whether to overwrite or create `quarterly-data-Q[N]-[YYYY]-v2.md`.
