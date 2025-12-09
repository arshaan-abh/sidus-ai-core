# GitLab Plugin Scope

## Goals
- Provide a SidusAI plugin to interact with GitLab REST v4 for common DevOps and collaboration workflows.
- Cover safe, non-destructive defaults; focus on create/read/comment operations and pipeline triggers/status.

## Primary Use Cases
- Create issues from agent output (title/description, labels/assignees optional).
- Comment on issues or merge requests (status updates, summaries, approvals/requests for changes text).
- List or search issues/MRs for prioritization or context (open items, by label, by assignee).
- Fetch pipeline status (latest for ref or specific pipeline id) and surface job details.
- Trigger pipelines for a ref/tag (ChatOps-style “run pipeline”).
- Search project code snippets for context (optional, bounded by query/limit).

## Target Operations & REST Endpoints (GitLab v4)
- Auth: Personal Access Token via `Private-Token` header (or `Authorization: Bearer`), base URL configurable (default `https://gitlab.com`).
- Projects are addressed by id or path; allow env/default project id with override per call.
- Issues:
  - `POST /projects/:id/issues` (create)
  - `GET /projects/:id/issues` with filters (state=opened, labels, search) (list/search)
  - `POST /projects/:id/issues/:issue_iid/notes` (comment)
- Merge Requests:
  - `GET /projects/:id/merge_requests` with filters (state=opened, labels, search)
  - `POST /projects/:id/merge_requests/:mr_iid/notes` (comment)
  - (optional) `POST /projects/:id/merge_requests/:mr_iid/approve` / `unapprove` guarded by flag
- Pipelines:
  - `POST /projects/:id/pipeline` (trigger by ref/tag with variables)
  - `GET /projects/:id/pipelines` (list/filter latest for ref)
  - `GET /projects/:id/pipelines/:pipeline_id` (status/detail)
  - `GET /projects/:id/pipelines/:pipeline_id/jobs` (jobs/status)
- Search:
  - `GET /projects/:id/search?scope=blobs&search=<query>` (code/text search, with limit)

## Non-Goals (initial cut)
- Destructive ops (delete issues/MRs/pipelines), user/group admin, project settings mutation.
- Webhook server; instead, accept webhook payloads as value objects if needed.

## Safety & Constraints
- Default read-only queries; mutating ops require explicit inputs.
- Bound list/search with pagination/limit defaults to avoid large responses.
- Support dry-run flag to log intended mutations without executing.

## Required Token Scopes
- `api` for create/comment/trigger; `read_api` sufficient for read-only list/status/search.
