from typing import Optional, List

import sidusai as sai
from github import Auth, Github


class GitHubClientComponent:
    """
    Wrapper around PyGithub client with configurable base URL for GitHub Enterprise.
    """

    def __init__(self, access_token: str, base_url: Optional[str] = None, per_page: Optional[int] = None):
        if access_token is None:
            raise ValueError('GitHub access token can not be None')

        self.access_token = access_token
        self.base_url = base_url
        self.per_page = per_page

        auth = Auth.Token(self.access_token)
        client_kwargs = {'auth': auth}
        if self.base_url is not None:
            client_kwargs['base_url'] = self.base_url
        if self.per_page is not None:
            client_kwargs['per_page'] = self.per_page

        self.client = Github(**client_kwargs)

    def get_repo(self, full_name: str):
        if full_name is None:
            raise ValueError('Repository name can not be None')
        return self.client.get_repo(full_name)


class GitHubRepositoryValue(sai.AgentValue):
    """
    Base AgentValue carrying repository identification and cached repository object.
    """

    def __init__(self, repo_full_name: str):
        super().__init__()
        self.repo_full_name = repo_full_name
        self.repository = None


class GitHubRepoValue(GitHubRepositoryValue):
    """
    Holds repository context and branch preferences.
    """

    def __init__(self, repo_full_name: str, branch: Optional[str] = None):
        super().__init__(repo_full_name)
        self.branch = branch
        self.default_branch = None


class GitHubIssueValue(GitHubRepositoryValue):
    """
    Data wrapper for working with a single issue.
    """

    def __init__(
            self,
            repo_full_name: str,
            title: Optional[str] = None,
            body: Optional[str] = None,
            labels: Optional[List[str]] = None,
            assignees: Optional[List[str]] = None,
            issue_number: Optional[int] = None,
            comment: Optional[str] = None
    ):
        super().__init__(repo_full_name)
        self.title = title
        self.body = body
        self.labels = labels
        self.assignees = assignees
        self.issue_number = issue_number
        self.comment = comment

        self.issue_url = None
        self.state = None


class GitHubIssueCommentValue(GitHubRepositoryValue):
    """
    Data wrapper for creating issue comments.
    """

    def __init__(self, repo_full_name: str, issue_number: int, comment: str):
        super().__init__(repo_full_name)
        self.issue_number = issue_number
        self.comment = comment

        self.comment_id = None
        self.comment_url = None
        self.issue_url = None


class GitHubIssueListValue(GitHubRepositoryValue):
    """
    Container for listing issues with optional filters.
    """

    def __init__(
            self,
            repo_full_name: str,
            state: str = 'open',
            labels: Optional[List[str]] = None,
            assignee: Optional[str] = None,
            creator: Optional[str] = None,
            since=None,
            sort: str = 'created',
            direction: str = 'desc',
            limit: Optional[int] = 20
    ):
        super().__init__(repo_full_name)
        self.state = state
        self.labels = labels
        self.assignee = assignee
        self.creator = creator
        self.since = since
        self.sort = sort
        self.direction = direction
        self.limit = limit

        self.issues = []


class GitHubPullRequestValue(GitHubRepositoryValue):
    """
    Container for creating and managing pull requests.
    """

    def __init__(
            self,
            repo_full_name: str,
            title: Optional[str] = None,
            head: Optional[str] = None,
            base: Optional[str] = None,
            body: Optional[str] = None,
            draft: bool = False,
            pr_number: Optional[int] = None,
            merge_method: Optional[str] = None,
            merge_message: Optional[str] = None
    ):
        super().__init__(repo_full_name)
        self.title = title
        self.body = body
        self.head = head
        self.base = base
        self.draft = draft
        self.pr_number = pr_number
        self.merge_method = merge_method
        self.merge_message = merge_message

        self.pr_url = None
        self.state = None
        self.merged = None
        self.merge_commit_sha = None


class GitHubPullRequestListValue(GitHubRepositoryValue):
    """
    Container for listing pull requests.
    """

    def __init__(
            self,
            repo_full_name: str,
            state: str = 'open',
            head: Optional[str] = None,
            base: Optional[str] = None,
            sort: str = 'updated',
            direction: str = 'desc',
            limit: Optional[int] = 20
    ):
        super().__init__(repo_full_name)
        self.state = state
        self.head = head
        self.base = base
        self.sort = sort
        self.direction = direction
        self.limit = limit

        self.pull_requests = []


class GitHubFileValue(GitHubRepositoryValue):
    """
    Container for reading repository files.
    """

    def __init__(self, repo_full_name: str, path: str, ref: Optional[str] = None):
        super().__init__(repo_full_name)
        self.path = path
        self.ref = ref

        self.sha = None
        self.encoding = None
        self.content_text = None
