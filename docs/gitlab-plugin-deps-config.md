# GitLab Plugin Dependencies & Config

## Dependency Choice
- Use `python-gitlab` as the primary client (handles REST v4, pagination, auth headers, retries). Target a recent 4.x release.
- Keep `requests` only if absolutely needed for niche endpoints; default flows use the official client.

## Authentication
- Personal Access Token (PAT) passed to the client; supports `Private-Token` or `Bearer` header under the hood.
- Required scopes:
  - `api` for create/comment/trigger operations.
  - `read_api` sufficient for list/status/search-only scenarios.

## Default Configuration Inputs
- `GITLAB_BASE_URL` (default: `https://gitlab.com`)
- `GITLAB_TOKEN` (PAT; required)
- `GITLAB_PROJECT_ID` (numeric id or `namespace/project` path; used as default project)
- `GITLAB_VERIFY_SSL` (default: `true`; allow `false` for self-signed, but discouraged)
- `GITLAB_TIMEOUT` (request timeout seconds; default: 15)
- Optional per-call overrides:
  - Project id/path
  - Ref/tag/branch for pipelines
  - Pagination params (`page`, `per_page`), bounded by sensible defaults (e.g., `per_page` <= 50)
  - Dry-run flag for mutating operations (log intent without executing)

## Safety Defaults
- Do not perform destructive operations; only create/comment/trigger and read.
- Bound list/search calls with defaults to avoid large responses.
- Allow opt-in dry-run for any mutating skill.
