# Repository Guidelines

These instructions apply to the whole repository.

## Domain Rules

- Put service/company domains under `domains/` and include the file from `ruleset.cn` or `ruleset.noncn`.
- Prefer an existing service/company file before creating a new `domains/` file.
- Domain entries must be lowercase and end with a trailing dot, for example `example.com.`.
- Keep entries in each `domains/` file sorted lexicographically.
- Do not leave a trailing blank line or final newline in `domains/` files.
- Use root domains when `match-subdomain=yes` should cover API, CDN, app, support, and other subdomains.
- Do not add redundant child domains when a parent domain is already listed.
- Keep `domains/` filenames safe for RouterOS address-list names: lowercase letters, numbers, and hyphens.

## Validation

- Run `make check` after changing rules or generator code.
- Do not commit generated release artifacts unless the task explicitly asks for them.

## Git

- Use the repository/user's normal signed commit setup.
- Do not add agent `Co-authored-by` trailers.
- Match nearby commit message style. For domain rules, prefer subjects like `chore(rules): add example domains`.
