from typing import Optional, List

import sidusai as sai

__required_modules__ = ['github']
sai.utils.validate_modules(__required_modules__)

import sidusai.core.plugin as _cp
import sidusai.plugins.github.skills as skills
import sidusai.plugins.github.components as components

__github_agent_name__ = 'github_agent_name'


class GitHubPlugin(sai.AgentPlugin):

    def __init__(self, access_token: str, base_url: Optional[str] = None, per_page: Optional[int] = None):
        super().__init__()
        self.access_token = access_token
        self.base_url = base_url
        self.per_page = per_page

    def apply_plugin(self, agent: sai.Agent):
        agent.add_component_builder(self._build_github_client)

        agent.add_skill(skills.gh_load_repository_skill)
        agent.add_skill(skills.gh_create_issue_skill)
        agent.add_skill(skills.gh_comment_issue_skill)
        agent.add_skill(skills.gh_close_issue_skill)
        agent.add_skill(skills.gh_list_issues_skill)
        agent.add_skill(skills.gh_list_pull_requests_skill)
        agent.add_skill(skills.gh_create_pull_request_skill)
        agent.add_skill(skills.gh_merge_pull_request_skill)
        agent.add_skill(skills.gh_read_file_skill)

    def _build_github_client(self) -> components.GitHubClientComponent:
        return components.GitHubClientComponent(
            access_token=self.access_token,
            base_url=self.base_url,
            per_page=self.per_page
        )


class GitHubCreateIssueTask(sai.CompletedAgentTask):
    pass


class GitHubCommentIssueTask(sai.CompletedAgentTask):
    pass


class GitHubCloseIssueTask(sai.CompletedAgentTask):
    pass


class GitHubListIssuesTask(sai.CompletedAgentTask):
    pass


class GitHubListPullRequestsTask(sai.CompletedAgentTask):
    pass


class GitHubCreatePullRequestTask(sai.CompletedAgentTask):
    pass


class GitHubMergePullRequestTask(sai.CompletedAgentTask):
    pass


class GitHubReadFileTask(sai.CompletedAgentTask):
    pass


class GitHubAgent(sai.Agent):
    """
    A convenience agent that registers GitHub interaction tasks and exposes helper methods.
    """

    def __init__(self, access_token: str, base_url: Optional[str] = None, per_page: Optional[int] = None,
                 plugins: Optional[List[sai.AgentPlugin]] = None):
        super().__init__(__github_agent_name__)

        self.access_token = access_token
        self.base_url = base_url
        self.per_page = per_page

        github_plugin = GitHubPlugin(access_token, base_url=base_url, per_page=per_page)
        github_plugin.apply_plugin(self)

        if plugins is not None:
            for plugin in plugins:
                plugin.apply_plugin(self)

        self._register_task(GitHubCreateIssueTask, [skills.gh_load_repository_skill, skills.gh_create_issue_skill])
        self._register_task(GitHubCommentIssueTask, [skills.gh_load_repository_skill, skills.gh_comment_issue_skill])
        self._register_task(GitHubCloseIssueTask, [skills.gh_load_repository_skill, skills.gh_close_issue_skill])
        self._register_task(GitHubListIssuesTask, [skills.gh_load_repository_skill, skills.gh_list_issues_skill])
        self._register_task(
            GitHubListPullRequestsTask,
            [skills.gh_load_repository_skill, skills.gh_list_pull_requests_skill]
        )
        self._register_task(
            GitHubCreatePullRequestTask,
            [skills.gh_load_repository_skill, skills.gh_create_pull_request_skill]
        )
        self._register_task(
            GitHubMergePullRequestTask,
            [skills.gh_load_repository_skill, skills.gh_merge_pull_request_skill]
        )
        self._register_task(GitHubReadFileTask, [skills.gh_load_repository_skill, skills.gh_read_file_skill])

    def create_issue(self, repo_full_name: str, title: str, body: Optional[str] = None,
                     labels: Optional[List[str]] = None, assignees: Optional[List[str]] = None, handler=None):
        value = components.GitHubIssueValue(
            repo_full_name=repo_full_name,
            title=title,
            body=body,
            labels=labels,
            assignees=assignees
        )
        self._run_task(GitHubCreateIssueTask, value, handler)

    def comment_issue(self, repo_full_name: str, issue_number: int, comment: str, handler=None):
        value = components.GitHubIssueCommentValue(
            repo_full_name=repo_full_name,
            issue_number=issue_number,
            comment=comment
        )
        self._run_task(GitHubCommentIssueTask, value, handler)

    def close_issue(self, repo_full_name: str, issue_number: int, handler=None):
        value = components.GitHubIssueValue(
            repo_full_name=repo_full_name,
            issue_number=issue_number
        )
        self._run_task(GitHubCloseIssueTask, value, handler)

    def list_issues(self, repo_full_name: str, state: str = 'open', labels: Optional[List[str]] = None,
                    assignee: Optional[str] = None, creator: Optional[str] = None,
                    since=None, sort: str = 'created', direction: str = 'desc',
                    limit: Optional[int] = 20, handler=None):
        value = components.GitHubIssueListValue(
            repo_full_name=repo_full_name,
            state=state,
            labels=labels,
            assignee=assignee,
            creator=creator,
            since=since,
            sort=sort,
            direction=direction,
            limit=limit
        )
        self._run_task(GitHubListIssuesTask, value, handler)

    def list_pull_requests(self, repo_full_name: str, state: str = 'open', head: Optional[str] = None,
                           base: Optional[str] = None, sort: str = 'updated', direction: str = 'desc',
                           limit: Optional[int] = 20, handler=None):
        value = components.GitHubPullRequestListValue(
            repo_full_name=repo_full_name,
            state=state,
            head=head,
            base=base,
            sort=sort,
            direction=direction,
            limit=limit
        )
        self._run_task(GitHubListPullRequestsTask, value, handler)

    def create_pull_request(self, repo_full_name: str, title: str, head: str, base: Optional[str] = None,
                            body: Optional[str] = None, draft: bool = False, handler=None):
        value = components.GitHubPullRequestValue(
            repo_full_name=repo_full_name,
            title=title,
            head=head,
            base=base,
            body=body,
            draft=draft
        )
        self._run_task(GitHubCreatePullRequestTask, value, handler)

    def merge_pull_request(self, repo_full_name: str, pr_number: int, merge_method: Optional[str] = None,
                            merge_message: Optional[str] = None, handler=None):
        value = components.GitHubPullRequestValue(
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            merge_method=merge_method,
            merge_message=merge_message
        )
        self._run_task(GitHubMergePullRequestTask, value, handler)

    def read_file(self, repo_full_name: str, path: str, ref: Optional[str] = None, handler=None):
        value = components.GitHubFileValue(
            repo_full_name=repo_full_name,
            path=path,
            ref=ref
        )
        self._run_task(GitHubReadFileTask, value, handler)

    def _register_task(self, task_cls, task_skills: []):
        skill_names = _cp.build_and_register_task_skill_names(task_skills, self)
        self.task_registration(task_cls, skill_names=skill_names)

    def _run_task(self, task_cls, value, handler):
        if not self.is_builded:
            self.application_build()
        task = task_cls(self).data(value).then(handler)
        self.task_execute(task)
