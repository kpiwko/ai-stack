# Migration Plan Format

Use this format for phase plan files saved to `docs/` by `/track:gdrive-organize`.

## File naming

```
docs/<drive-name-kebab-case>-migration-plan.md              # overall plan
docs/<drive-name-kebab-case>-migration-plan-phase-<N>.md    # per-phase plan
docs/<drive-name-kebab-case>-audit-trail.md                 # appended after each phase
```

## Overall plan structure

```markdown
# <Drive Name> – Drive Migration Plan

> Based on snapshot: <YYYY-MM-DD>
> Status: **DRAFT – for review before any changes are made**

## Proposed New Root Structure

\`\`\`
<Drive Name>
├── 📁 00 Folder One/
├── 📁 01 Folder Two/
└── 📄 README – Drive Structure
\`\`\`

## Decisions Needed

| # | Item | Question |
|---|---|---|
| D1 | `Ambiguous File` | Duplicate of `Other File`? |

## Folder Operations

### New folders to create
| Folder | Notes |
|---|---|
| `00 Folder One/Subfolder/` | Absorbs `OldFolder/` |

### Folders to rename
| From | To |
|---|---|
| `OldName/` | `NewName/` |

## Content Moves by Destination

### → `00 Folder One/`
| Item | From | Note |
|---|---|---|
| `Document Name` | root | Needs update/review |

## Archive Moves → `99 Archive/`
| Item | From |
|---|---|
| `Old Document` | `OldFolder/` |

## Items to Delete
| Item | Location | Reason |
|---|---|---|
| `duplicate.md` | root | Duplicate |

## New Items to Create
| Item | Location | Purpose |
|---|---|---|
| `README – Drive Structure` (Google Doc) | root | Explains folder structure |
```

## Per-phase plan structure

```markdown
# <Drive Name> – Drive Migration Plan Phase <N>

> Based on snapshot: <YYYY-MM-DD>
> Status: **DRAFT – for review before any changes are made**

## Renames
| Current name | Proposed name | Location |
|---|---|---|

## New Items to Create
| Item | Location | Purpose |
|---|---|---|

## Content Moves by Destination

### → `Target Folder/`
| Item | From | Note |
|---|---|---|

## Archive Moves → `99 Archive/<Category>/`
| Item | From | Note |
|---|---|---|
```

## Audit trail entry (append after each phase)

```markdown
## Phase <N> – <Phase Name> — <YYYY-MM-DD>

**Status:** Completed
**Operations:** <N> succeeded, <N> failed

### Completed
| Operation | Item | From | To |
|---|---|---|---|
| rename | `Old Name` | `Parent/` | — |
| move | `Document` | `Source/` | `Target/` |

### Failed
| Operation | Item | Reason |
|---|---|---|
```
