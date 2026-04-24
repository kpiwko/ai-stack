# Drive Snapshot Format

Use this format for drive snapshots saved to `docs/` by `/track:gdrive-organize`.

## File naming

```
docs/<drive-name-kebab-case>-snapshot-<YYYY-MM-DD>.md
```

## Document structure

```markdown
# <Drive Name> – Drive Snapshot

> **Drive:** <Drive Name>
> **Drive ID:** `<drive-id>`
> **Snapshot date:** <YYYY-MM-DD>
> **Purpose:** Pre-reorganization baseline. Do not modify.

---

\`\`\`
<Drive Name>
│
├── 📁 FolderA/
│   ├── 📁 Subfolder/
│   │   └── 📄 document name   (Google Doc)
│   ├── 📄 another file   (Sheet)
│   └── 📄 [empty]
│
├── 📁 FolderB/   [empty]
│
└── 📄 root level file
\`\`\`
```

## Tree conventions

| Symbol | Meaning |
|---|---|
| `📁` | Folder |
| `📄` | File (any type) |
| `[empty]` | Folder with no contents |
| `(Google Doc)` | Type annotation — add for non-obvious types: Sheet, Slides, Form, PDF |
| `...` | Contents abbreviated (large folders not relevant to current phase) |

Indent with two spaces per level. Use `│`, `├──`, `└──` (same style as the `tree` command).
