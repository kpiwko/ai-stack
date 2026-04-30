---
description: Create or update a Google Doc in the right Drive location. Browses Drive, drafts structured content, previews, and applies formatting after creation.
argument-hint: "[topic or description]"
---

# /track:gdrive-doc

## Synopsis

```
/track:gdrive-doc [topic or description]
```

Leave empty for interactive mode. Uses the `gdrive` MCP server.

---

## Process

### Step 1: Gather context

If not provided, ask:
- What are you documenting?
- Known folder or existing document to update? (or "find for me")
- Audience: internal team, management, external?

### Step 2: Find where it fits

1. Search Drive for existing documents on the topic to avoid duplicates.
2. List the target folder to confirm location.
3. Propose: update existing doc (preferred) / new doc / new folder + doc.

Present options and confirm before proceeding.

### Step 3: Draft the content

Every document starts with a metadata header:
```
Status: Draft | Review | Final
Owner: <name>
Last updated: <YYYY-MM-DD>
Related: <Jira issue key or Drive URL>
Tags: <comma-separated keywords>
```

Then the body as **plain text only** — no Markdown syntax.
See `reference/gdrive-formatting.md` for the full formatting workflow.

Keep titles descriptive and stable — no dates in titles; use metadata for version/status.

### Step 4: Preview

```
=== GOOGLE DRIVE DOC PREVIEW ===
Action:   [Create new | Update existing]
Location: <folder path>
Title:    <document title>
Sections: <H1 section names>

Content:
<full plain text>
=================================
Submit? (yes / edit / cancel)
```

Do not create or update anything until the user says yes.

### Step 5: Submit

On approval, in this order:
1. `createGoogleDoc` or `updateGoogleDoc` — write plain text content
2. Apply `TITLE` style via `applyParagraphStyle`
3. Apply `HEADING_1` sections — all in parallel
4. Apply `HEADING_2` subsections — all in parallel
5. Apply bullets via `createParagraphBullets` — all in parallel
6. Return the document URL
7. If a related Jira issue exists, offer to add the Drive link via `editJiraIssue`

**Critical:** `createGoogleDoc` and `updateGoogleDoc` paste raw text — no Markdown.
Never use `##`, `-`, `**`, or `|tables|` in the content string. Apply all formatting
via separate tool calls after creation. See `reference/gdrive-formatting.md`.

---

## Troubleshooting

**Markdown appears as literal text** — write plain text, then apply styles after creation.

**`applyParagraphStyle` targets wrong paragraph** — use `matchInstance: N` if the same
text appears more than once.

**`createParagraphBullets` only bullets one item** — make one call per bullet item;
batch all calls in parallel.

**Drive search returns wrong folder** — use `listFolder` with the known folder ID.
