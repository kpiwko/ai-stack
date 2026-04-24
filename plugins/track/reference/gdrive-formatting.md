# Google Doc Formatting Rules

Reference for `/track:gdrive-doc`. Apply after document creation.

## Why plain text?

`createGoogleDoc` and `updateGoogleDoc` paste raw text without Markdown interpretation.
Markdown syntax (`##`, `-`, `**`, `| tables |`) will appear literally. Apply all
formatting via separate tool calls after writing the content.

## Headings — applyParagraphStyle

```
applyParagraphStyle(documentId, textToFind="Section Title", namedStyleType="HEADING_1")
```

Available styles: `TITLE`, `SUBTITLE`, `HEADING_1` through `HEADING_6`, `NORMAL_TEXT`

Rules:
- `textToFind` targets the paragraph containing that exact text
- All heading calls are independent — batch in parallel for speed
- Make heading text unique in the document; use `matchInstance: N` (1-based) if not

Recommended hierarchy:
- `TITLE` — document title (one per doc)
- `HEADING_1` — major sections
- `HEADING_2` — subsections

## Bullet lists — createParagraphBullets

```
createParagraphBullets(documentId, textToFind="Unique text in item", bulletPreset="BULLET_DISC_CIRCLE_SQUARE")
```

Rules:
- One call per bullet item — each targets a single paragraph
- Batch all calls in parallel
- Each list item must be on its own line in the source text (no leading `-` or `*`)

Presets:
- `BULLET_DISC_CIRCLE_SQUARE` — standard nested bullets (default)
- `NUMBERED_DECIMAL_ALPHA_ROMAN` — numbered list
- `BULLET_CHECKBOX` — checklist

## Hyperlinks — applyTextStyle

```
applyTextStyle(documentId, textToFind="link text", linkUrl="https://...")
```

## Bold / italic — applyTextStyle

```
applyTextStyle(documentId, textToFind="text to bold", bold=true)
applyTextStyle(documentId, textToFind="text to italicise", italic=true)
```

## Document tabs — not supported

`addDocumentTab` is not functional in the current MCP server version.
Use `HEADING_1` sections instead — the Docs outline panel provides equivalent navigation.

## Workflow summary

| Step | Tool | Batch? |
|---|---|---|
| 1. Write text | `createGoogleDoc` / `updateGoogleDoc` | — |
| 2. Title | `applyParagraphStyle` TITLE | With H1s |
| 3. H1 headings | `applyParagraphStyle` HEADING_1 | All in parallel |
| 4. H2 subheadings | `applyParagraphStyle` HEADING_2 | All in parallel |
| 5. Bullets | `createParagraphBullets` | All in parallel |
| 6. Links / bold | `applyTextStyle` | All in parallel |
