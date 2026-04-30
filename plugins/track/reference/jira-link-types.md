# Jira Issue Link Types

Use `createIssueLink` with these link type names.
Link type names vary by instance — verify with `getIssueLinkTypes` if a link fails.

## Verified link types

| Link Type | Outward (from → to) | Inward (to → from) |
|---|---|---|
| Blocks | blocks | is blocked by |
| Depend | depends on | is depended on by |
| Related | relates to | is related to |
| Duplicate | duplicates | is duplicated by |
| Cloners | clones | is cloned by |
| Incorporates | incorporates | is incorporated by |
| Issue split | split to | split from |
| Informs | informs | is informed by |

## Description format

Pass `contentFormat: "markdown"` when calling `createIssueLink` or any write tool —
the `atlassian` plugin converts Markdown to Atlassian Document Format (ADF) automatically.
Do not hand-craft ADF JSON.
