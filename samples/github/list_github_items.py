import os
import sys
import threading
import time
import traceback
from typing import Callable, Optional, List

# Allow running the sample without installing the package by adding repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import sidusai.plugins.github as gh


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wait_for(handler: Callable):
    """
    Wrap a handler so we can block until the async task finishes.
    """
    event = threading.Event()

    def wrapper(value: gh.components.GitHubRepositoryValue):
        handler(value)
        event.set()

    return wrapper, event


def _print_title(title: str):
    print(f'\n== {title} ==')


# ---------------------------------------------------------------------------
# Read-only operations
# ---------------------------------------------------------------------------

def list_issues(agent: gh.GitHubAgent, repo: str):
    _print_title('List open issues')

    def on_issues(value: gh.components.GitHubIssueListValue):
        for issue in value.issues:
            print(f"- #{issue['number']} {issue['title']} [{issue['state']}] {issue['url']}")
        if len(value.issues) == 0:
            print('(no issues)')

    handler, event = _wait_for(on_issues)
    agent.list_issues(repo_full_name=repo, state='open', limit=5, handler=handler)
    event.wait(10)


def list_pull_requests(agent: gh.GitHubAgent, repo: str):
    _print_title('List open pull requests')

    def on_prs(value: gh.components.GitHubPullRequestListValue):
        for pr in value.pull_requests:
            draft = ' (draft)' if pr['draft'] else ''
            print(f"- #{pr['number']} {pr['title']}{draft} [{pr['state']}] {pr['url']}")
        if len(value.pull_requests) == 0:
            print('(no pull requests)')

    handler, event = _wait_for(on_prs)
    agent.list_pull_requests(repo_full_name=repo, state='open', limit=5, handler=handler)
    event.wait(10)


def read_file(agent: gh.GitHubAgent, repo: str, file_path: str, ref: Optional[str]):
    _print_title(f'Read file: {file_path} ({ref or "default branch"})')

    def on_file(value: gh.components.GitHubFileValue):
        print(f"Path: {value.path} @ {value.ref}")
        print(f"SHA: {value.sha}")
        preview = value.content_text[:400].replace('\n', '\\n')
        print(f"Preview (first 400 chars): {preview}")

    handler, event = _wait_for(on_file)
    agent.read_file(repo_full_name=repo, path=file_path, ref=ref, handler=handler)
    event.wait(10)


# ---------------------------------------------------------------------------
# Write operations (opt-in)
# ---------------------------------------------------------------------------

def create_issue(agent: gh.GitHubAgent, repo: str, title: str, body: Optional[str], labels: Optional[List[str]]):
    _print_title('Create issue')
    result = {}

    def on_issue(value: gh.components.GitHubIssueValue):
        result['number'] = value.issue_number
        print(f"Created issue #{value.issue_number}: {value.issue_url}")

    handler, event = _wait_for(on_issue)
    agent.create_issue(repo_full_name=repo, title=title, body=body, labels=labels, handler=handler)
    event.wait(10)
    return result.get('number')


def comment_issue(agent: gh.GitHubAgent, repo: str, issue_number: int, comment: str):
    _print_title('Comment issue')

    def on_comment(value: gh.components.GitHubIssueCommentValue):
        print(f"Commented on issue #{value.issue_number}: {value.comment_url}")

    handler, event = _wait_for(on_comment)
    agent.comment_issue(repo_full_name=repo, issue_number=issue_number, comment=comment, handler=handler)
    event.wait(10)


def close_issue(agent: gh.GitHubAgent, repo: str, issue_number: int):
    _print_title('Close issue')

    def on_closed(value: gh.components.GitHubIssueValue):
        print(f"Closed issue #{value.issue_number}: {value.issue_url}")

    handler, event = _wait_for(on_closed)
    agent.close_issue(repo_full_name=repo, issue_number=issue_number, handler=handler)
    event.wait(10)


def create_pull_request(agent: gh.GitHubAgent, repo: str, title: str, head: str, base: str, body: Optional[str]):
    _print_title('Create pull request')
    result = {}

    def on_pr(value: gh.components.GitHubPullRequestValue):
        result['number'] = value.pr_number
        print(f"Created PR #{value.pr_number}: {value.pr_url}")

    handler, event = _wait_for(on_pr)
    agent.create_pull_request(
        repo_full_name=repo,
        title=title,
        head=head,
        base=base,
        body=body,
        draft=False,
        handler=handler
    )
    event.wait(20)
    return result.get('number')


def merge_pull_request(agent: gh.GitHubAgent, repo: str, pr_number: int, method: Optional[str], message: Optional[str]):
    _print_title('Merge pull request')

    def on_merge(value: gh.components.GitHubPullRequestValue):
        print(f"Merged PR #{value.pr_number}: merged={value.merged}, sha={value.merge_commit_sha}")

    handler, event = _wait_for(on_merge)
    agent.merge_pull_request(
        repo_full_name=repo,
        pr_number=pr_number,
        merge_method=method,
        merge_message=message,
        handler=handler
    )
    event.wait(20)


if __name__ == '__main__':
    token = os.getenv('GITHUB_TOKEN')
    repo = os.getenv('GITHUB_REPO', 'arshaan-abh/test-sidus-github')  # override with real repo, e.g. "octocat/Hello-World"
    file_path = os.getenv('GITHUB_FILE_PATH', 'README.md')
    file_ref = os.getenv('GITHUB_FILE_REF')  # optional branch/sha for read_file

    write_enabled = True#os.getenv('GITHUB_WRITE_ENABLED') == '1'
    issue_title = os.getenv('GITHUB_ISSUE_TITLE', 'SidusAI sample issue')
    issue_body = os.getenv('GITHUB_ISSUE_BODY', 'Created by the SidusAI GitHub sample.')
    head_branch = os.getenv('GITHUB_PR_HEAD')
    base_branch = os.getenv('GITHUB_PR_BASE')
    pr_title = os.getenv('GITHUB_PR_TITLE', 'SidusAI sample PR')
    pr_body = os.getenv('GITHUB_PR_BODY', 'Created by the SidusAI GitHub sample.')

    if token is None:
        raise EnvironmentError('Set GITHUB_TOKEN to a GitHub personal access token')

    agent = gh.GitHubAgent(access_token=token)

    # Log any uncaught task errors so the sample doesn't fail silently.
    def on_exception(exception: Exception):
        print('\n[ERROR] Task failed:')
        traceback.print_exception(exception)

    agent.add_exception_handler_method(on_exception)

    list_issues(agent, repo)
    list_pull_requests(agent, repo)
    read_file(agent, repo, file_path, file_ref)

    if write_enabled:
        issue_number = create_issue(agent, repo, issue_title, issue_body, labels=None)
        if issue_number is not None:
            comment_issue(agent, repo, issue_number, 'Thanks for testing the SidusAI sample!')
            close_issue(agent, repo, issue_number)

        if head_branch and base_branch:
            pr_number = create_pull_request(agent, repo, pr_title, head_branch, base_branch, pr_body)
            if pr_number is not None:
                merge_pull_request(agent, repo, pr_number, method=None, message=None)
        else:
            print('\n[INFO] Skip PR create/merge: set GITHUB_PR_HEAD and GITHUB_PR_BASE to enable.')
    else:
        _print_title('Write operations skipped')
        print('Set GITHUB_WRITE_ENABLED=1 to enable creating/commenting/closing issues and creating/merging PRs.')

    # Give background tasks time to finish if any stragglers remain
    time.sleep(2)
