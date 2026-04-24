---
description: Reorganize a Google Drive based on a structure document found inside the drive. Snapshots current state, generates a phased migration plan, executes on approval.
argument-hint: "[drive-name-or-id] [task-focus]"
---

# /track:gdrive-organize

## Synopsis

```
/track:gdrive-organize [drive-name-or-id] [task-focus]
```

| Argument | Description |
|---|---|
| `drive-name-or-id` | Drive name (partial match ok) or raw ID. Omit to pick from list. |
| `task-focus` | Scope or intent, e.g. "archive phase only" or "check what doesn't fit". |

All arguments optional — omit any to enter interactive mode. Uses the `gdrive` MCP server.

---

## Prerequisites

Verify the gdrive MCP is connected:
```
mcp__gdrive__authGetStatus
```

If not connected, show setup instructions and stop.

---

## Process

### Step 0: Resolve the drive

| Type | How to list | Root folder ID |
|---|---|---|
| Shared drive | `listSharedDrives` | The drive ID itself |
| My Drive | Always available | `root` |
| Folder shared with user | `search` with `sharedWithMe=true` | The folder ID |

If a `drive-name-or-id` was given: raw IDs (20+ alphanumeric chars) use directly;
`"my drive"` uses `root`; otherwise search shared drives and folders in parallel.

Display: `Drive: <name>  Type: <type>  ID: <id>` before continuing.

### Step 1: Snapshot current state

List the Drive recursively. Format the snapshot as a tree (see `reference/snapshot-format.md`).
Save to `docs/<drive-name>-snapshot-<YYYY-MM-DD>.md`. Ask whether to overwrite if one exists for today.

### Step 2: Find the structure document inside the drive

**Do not use local files** unless the user explicitly provides a local path.

Discovery order (stop at first hit):
1. Check drive root for docs named: `README`, `README – Drive Structure`, `Drive Structure`, `Folder Structure`, `Structure`
2. Search whole drive for Google Docs matching those terms
3. Ask the user if nothing found

Extract from the document: target folder layout, naming conventions, archival rules, items to delete.

### Step 3: Gap analysis

Compare snapshot against target structure. Categorize:

| Category | Description |
|---|---|
| Create | Folders that must be created |
| Rename | Items with wrong names |
| Move | Items in wrong location |
| Archive | Items to move to archive folder |
| Delete | Items explicitly flagged for deletion |
| Create doc | New Google Docs to create |

### Step 4: Generate phased migration plan

Recommended phase order:
1. Rename existing folders
2. Create new folders
3. Move active content
4. Archive old content
5. Rename files
6. Delete flagged items
7. Create new docs

Save each phase to `docs/<drive-name>-migration-plan-phase-<N>.md` and the
combined plan to `docs/<drive-name>-migration-plan.md`. See `reference/plan-format.md`.

### Step 5: Preview and confirm

```
=== DRIVE ORGANIZATION PLAN ===
Drive:    <name> (<id>)
Snapshot: docs/<snapshot-file>
Phases:   <N> phases planned

Phase 1 – Rename folders     : <N> operations
...

Execute Phase 1 now? (yes / skip / stop)
```

Do not execute any Drive operations until the user says yes.

### Step 6: Execute phases (on approval)

Run independent operations in parallel per phase. Tools:
- `renameItem`, `createFolder`, `moveItem`, `deleteItem`, `createGoogleDoc`

After each phase: report results, update phase plan status to `COMPLETED – <date>`,
append to `docs/<drive-name>-audit-trail.md`.

---

## Naming conventions

- Number prefixes: zero-pad to two digits (`01`, `02`, … `99`).
- Archive prefix: `[archived]` (lowercase, square brackets).
- Do not renumber existing items unless the structure document says to.

---

## Troubleshooting

**`listFolder` returns empty** — for shared drives pass drive ID as `folderId`; for My Drive use `root`.

**`moveItem` permission error** — account needs "Content Manager" or higher on the shared drive.

**Large drives time out** — snapshot in sections: list top-level first, recurse per subfolder.

**Item not found by name** — use `search` to find the current ID, then use ID for operations.
