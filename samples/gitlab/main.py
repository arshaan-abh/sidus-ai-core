import os
import sys
from pathlib import Path

# Allow running the sample without editable install: add repo root to sys.path
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import sidusai.plugins.gitlab as gl

PROJECT_ID = os.environ.get('GITLAB_PROJECT_ID')
BASE_URL = os.environ.get('GITLAB_BASE_URL')
TOKEN = os.environ.get('GITLAB_TOKEN')
PIPELINE_REF = os.environ.get('GITLAB_PIPELINE_REF', 'main')

_dry_run_env = os.environ.get('GITLAB_SAMPLE_DRY_RUN')
DRY_RUN = str(_dry_run_env).lower() in ['1', 'true', 'yes', 'y'] if _dry_run_env is not None else True


def print_issue(result: gl.skills.GitlabIssueResult):
    raw = getattr(result, 'raw', {}) if result is not None else {}
    if isinstance(raw, dict) and raw.get('dry_run'):
        payload = raw.get('payload', {})
        print(f"[issue:create] dry-run => project={raw.get('project_id')} payload={payload}")
        return
    print(f"[issue:create] iid={result.iid} state={result.state} url={result.web_url}")


def print_issue_list(result: gl.skills.GitlabIssuesResult):
    items = result.items if result is not None and result.items is not None else []
    print(f"[issues:list] returned={len(items)}")
    for issue in items:
        print(f" - #{issue.get('iid')} {issue.get('title')} [{issue.get('state')}] url={issue.get('web_url')}")


def print_search(result: gl.skills.GitlabSearchResult):
    matches = result.matches if result is not None and result.matches is not None else []
    print(f"[search] matches={len(matches)}")
    for match in matches:
        print(f" - {match.get('path')}:{match.get('startline')} ref={match.get('ref')}")


def print_pipeline_status(result: gl.skills.GitlabPipelineStatusResult):
    if result.id is None:
        print("[pipeline:status] no pipeline found for ref/pipeline_id")
        return
    print(f"[pipeline:status] id={result.id} status={result.status} ref={result.ref} url={result.web_url}")


def main():
    agent = gl.GitlabAgent(
        token=TOKEN,
        base_url=BASE_URL,
        project_id=PROJECT_ID,
        dry_run=DRY_RUN
    )
    agent.application_build()

    agent.create_issue(
        title='SidusAI GitLab plugin sample issue',
        description='Hello from SidusAI GitLab sample script.',
        labels=['sidusai', 'sample'],
        dry_run=DRY_RUN,
        handler=print_issue
    )

    agent.list_issues(per_page=5, handler=print_issue_list)

    agent.search_code(query='TODO', per_page=3, handler=print_search)

    agent.pipeline_status(ref=PIPELINE_REF, handler=print_pipeline_status)


if __name__ == '__main__':
    main()
