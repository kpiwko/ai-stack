# Jira Issue Link Types

Use `jira_create_issue_link` with these link type names.
Link type names are typically consistent across instances but verify with
`jira_get_link_types` if a link fails.

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

Pass plain text or Markdown in the description field — `mcp-atlassian` converts
it to Atlassian Document Format (ADF) automatically. Do not hand-craft ADF JSON.
