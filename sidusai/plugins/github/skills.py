from sidusai.plugins.github.components import (
    GitHubClientComponent,
    GitHubRepositoryValue,
    GitHubRepoValue,
    GitHubIssueValue,
    GitHubIssueListValue,
    GitHubIssueCommentValue,
    GitHubPullRequestValue,
    GitHubPullRequestListValue,
    GitHubFileValue
)
from sidusai.plugins.github import utils


def gh_load_repository_skill(value: GitHubRepositoryValue, client: GitHubClientComponent) -> GitHubRepositoryValue:
    repo = _require_repository(value, client)
    value.repository = repo
    if isinstance(value, GitHubRepoValue):
        value.default_branch = repo.default_branch
        if value.branch is None:
            value.branch = repo.default_branch
    return value


def gh_create_issue_skill(value: GitHubIssueValue, client: GitHubClientComponent) -> GitHubIssueValue:
    if value.title is None:
        raise ValueError('Issue title can not be None')
    repo = _require_repository(value, client)
    kwargs = {'title': value.title}
    utils.set_if_not_none(kwargs, 'body', value.body)
    utils.set_if_not_none(kwargs, 'labels', value.labels)
    utils.set_if_not_none(kwargs, 'assignees', value.assignees)

    issue = repo.create_issue(**kwargs)
    value.repository = repo
    value.issue_number = issue.number
    value.issue_url = issue.html_url
    value.state = issue.state
    return value


def gh_comment_issue_skill(value: GitHubIssueCommentValue, client: GitHubClientComponent) -> GitHubIssueCommentValue:
    if value.issue_number is None:
        raise ValueError('Issue number can not be None')
    if value.comment is None:
        raise ValueError('Comment can not be None')

    repo = _require_repository(value, client)
    issue = repo.get_issue(number=value.issue_number)
    comment = issue.create_comment(value.comment)

    value.repository = repo
    value.comment_id = comment.id
    value.comment_url = comment.html_url
    value.issue_url = issue.html_url
    return value


def gh_close_issue_skill(value: GitHubIssueValue, client: GitHubClientComponent) -> GitHubIssueValue:
    if value.issue_number is None:
        raise ValueError('Issue number can not be None')
    repo = _require_repository(value, client)
    issue = repo.get_issue(number=value.issue_number)
    issue.edit(state='closed')

    value.repository = repo
    value.state = 'closed'
    value.issue_url = issue.html_url
    return value


def gh_list_issues_skill(value: GitHubIssueListValue, client: GitHubClientComponent) -> GitHubIssueListValue:
    repo = _require_repository(value, client)
    kwargs = {
        'state': value.state,
        'sort': value.sort,
        'direction': value.direction
    }
    utils.set_if_not_none(kwargs, 'labels', value.labels)
    utils.set_if_not_none(kwargs, 'assignee', value.assignee)
    utils.set_if_not_none(kwargs, 'creator', value.creator)
    utils.set_if_not_none(kwargs, 'since', value.since)

    issues = repo.get_issues(**kwargs)

    collected = []
    for issue in issues:
        collected.append({
            'number': issue.number,
            'title': issue.title,
            'state': issue.state,
            'url': issue.html_url,
            'user': issue.user.login if issue.user is not None else None,
            'labels': [label.name for label in issue.labels],
            'assignees': [assignee.login for assignee in issue.assignees],
            'comments': issue.comments
        })
        if value.limit is not None and len(collected) >= value.limit:
            break

    value.repository = repo
    value.issues = collected
    return value


def gh_list_pull_requests_skill(value: GitHubPullRequestListValue,
                                client: GitHubClientComponent) -> GitHubPullRequestListValue:
    repo = _require_repository(value, client)
    kwargs = {
        'state': value.state,
        'sort': value.sort,
        'direction': value.direction
    }
    utils.set_if_not_none(kwargs, 'base', value.base)
    utils.set_if_not_none(kwargs, 'head', value.head)

    pulls = repo.get_pulls(**kwargs)

    collected = []
    for pr in pulls:
        collected.append({
            'number': pr.number,
            'title': pr.title,
            'state': pr.state,
            'url': pr.html_url,
            'user': pr.user.login if pr.user is not None else None,
            'draft': pr.draft,
            'head': pr.head.label if pr.head is not None else None,
            'base': pr.base.label if pr.base is not None else None
        })
        if value.limit is not None and len(collected) >= value.limit:
            break

    value.repository = repo
    value.pull_requests = collected
    return value


def gh_create_pull_request_skill(value: GitHubPullRequestValue,
                                 client: GitHubClientComponent) -> GitHubPullRequestValue:
    if value.title is None:
        raise ValueError('Pull request title can not be None')
    if value.head is None:
        raise ValueError('Head branch can not be None')

    repo = _require_repository(value, client)
    base_branch = value.base if value.base is not None else repo.default_branch
    kwargs = {
        'title': value.title,
        'head': value.head,
        'base': base_branch,
        'draft': value.draft
    }
    utils.set_if_not_none(kwargs, 'body', value.body)

    pr = repo.create_pull(**kwargs)

    value.repository = repo
    value.pr_number = pr.number
    value.pr_url = pr.html_url
    value.state = pr.state
    value.base = base_branch
    return value


def gh_merge_pull_request_skill(value: GitHubPullRequestValue,
                                client: GitHubClientComponent) -> GitHubPullRequestValue:
    if value.pr_number is None:
        raise ValueError('Pull request number can not be None')

    repo = _require_repository(value, client)
    pr = repo.get_pull(number=value.pr_number)
    merge_kwargs = {}
    if value.merge_method is not None:
        merge_kwargs['merge_method'] = value.merge_method
    if value.merge_message is not None:
        merge_kwargs['commit_message'] = value.merge_message

    result = pr.merge(**merge_kwargs)

    value.repository = repo
    value.pr_url = pr.html_url
    value.state = pr.state
    value.merged = result.merged if hasattr(result, 'merged') else None
    value.merge_commit_sha = result.sha if hasattr(result, 'sha') else None
    return value


def gh_read_file_skill(value: GitHubFileValue, client: GitHubClientComponent) -> GitHubFileValue:
    repo = _require_repository(value, client)
    ref = value.ref
    if ref is None and hasattr(value, 'branch') and getattr(value, 'branch') is not None:
        ref = getattr(value, 'branch')
    if ref is None:
        ref = repo.default_branch

    content_file = repo.get_contents(value.path, ref=ref)

    value.repository = repo
    value.ref = ref
    value.sha = content_file.sha
    value.encoding = content_file.encoding
    value.content_text = content_file.decoded_content.decode('utf-8', errors='replace')
    return value


def _require_repository(value: GitHubRepositoryValue, client: GitHubClientComponent):
    if getattr(value, 'repository', None) is None:
        value.repository = client.get_repo(value.repo_full_name)
    return value.repository
