# GitLab Plugin Design

## Package Layout
- `sidusai/plugins/gitlab/__init__.py` — plugin registration/helpers.
- `sidusai/plugins/gitlab/components.py` — GitLab client wrapper, project resolver, formatting helpers.
- `sidusai/plugins/gitlab/skills.py` — AgentValue types + skills for create/list/comment/pipelines/search.
- `samples/gitlab/` — runnable examples.

## Components
- `GitlabClientComponent`:
  - Wraps `python-gitlab` client with base URL, PAT, timeout, SSL verify, optional dry-run flag.
  - Provides project resolution (`get_project(project_id=None)`) using default project id/path from config, with simple cache.
  - Helpers for pagination defaults and safe request execution (translate gitlab exceptions).
- (Optional) `GitlabFormatterComponent`:
  - Small helpers to convert GitLab objects to lightweight dicts (id/iid, title, state/status, author, web_url, timestamps).

## Agent Values (inputs/outputs)
- Issue:
  - `GitlabIssueCreateValue(title, description, labels=None, assignees=None, milestone=None, confidential=False, project_id=None, dry_run=False)`
  - `GitlabIssueResult(iid, id, web_url, title, state)`
  - `GitlabIssueListValue(state='opened', labels=None, search=None, assignee_id=None, page=None, per_page=None, project_id=None)`
  - `GitlabIssuesResult(issues: list[dict])`
- Comments (notes):
  - `GitlabCommentValue(target_type: Literal['issue','mr'], target_iid, body, project_id=None, dry_run=False)`
  - `GitlabCommentResult(id, body, web_url)`
- Pipelines:
  - `GitlabPipelineTriggerValue(ref, variables=None, project_id=None, dry_run=False)`
  - `GitlabPipelineStatusValue(pipeline_id=None, ref=None, project_id=None)`
  - `GitlabPipelineStatusResult(id, status, web_url, sha, ref, source, started_at, finished_at, duration)`
- Search:
  - `GitlabCodeSearchValue(query, scope='blobs', page=None, per_page=None, project_id=None)`
  - `GitlabSearchResult(matches: list[dict])`

## Skills (examples)
- `gitlab_create_issue_skill(value: GitlabIssueCreateValue, client: GitlabClientComponent) -> GitlabIssueResult`
- `gitlab_list_issues_skill(value: GitlabIssueListValue, client, formatter=None) -> GitlabIssuesResult`
- `gitlab_comment_skill(value: GitlabCommentValue, client) -> GitlabCommentResult`
- `gitlab_trigger_pipeline_skill(value: GitlabPipelineTriggerValue, client) -> GitlabPipelineStatusResult`
- `gitlab_pipeline_status_skill(value: GitlabPipelineStatusValue, client) -> GitlabPipelineStatusResult`
- `gitlab_search_code_skill(value: GitlabCodeSearchValue, client) -> GitlabSearchResult`
- All mutating skills honor `dry_run` to log intent and skip network calls.

## Tasks & Agent Wrapper
- `GitlabPlugin` registers components and the above skills.
- `GitlabAgent`:
  - Extends `sai.Agent`, installs plugin, exposes helper methods:
    - `create_issue(...)`, `list_issues(...)`, `comment_issue(...)`, `comment_mr(...)`,
      `trigger_pipeline(...)`, `pipeline_status(...)`, `search_code(...)`.
  - Uses `CompletedAgentTask` pattern with `build_and_register_task_skill_names` for easy composition with LLM plugins (e.g., DeepSeek/OpenAI).
- Tasks:
  - `GitlabIssueTask`, `GitlabCommentTask`, `GitlabPipelineTask`, `GitlabSearchTask` using `CompletedAgentTask` wrappers where appropriate.

## Config Handling
- Pull defaults from env (`GITLAB_BASE_URL`, `GITLAB_TOKEN`, `GITLAB_PROJECT_ID`, `GITLAB_VERIFY_SSL`, `GITLAB_TIMEOUT`), allow override via constructor kwargs and per-value overrides.
- Pagination defaults: `per_page` bounded (e.g., max 50) to avoid huge responses.
- Error handling: translate `python-gitlab` errors to `ValueError`/`ConnectionError` with concise messages.

## Samples
- `samples/gitlab/main.py`: simple create-issue, comment-on-issue, pipeline status/trigger flows with env-driven config.
- Optional LLM composition sample: take user prompt → LLM summary → create issue/comment.

## Tests/Validation (later tasks)
- Lightweight mocks for formatter and dry-run logic; avoid real network in tests.
