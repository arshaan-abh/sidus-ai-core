"""
GitLab plugin package.
"""

import os

import sidusai as sai

__required_modules__ = ['gitlab']
sai.utils.validate_modules(__required_modules__)

import sidusai.core.plugin as _cp
import sidusai.plugins.gitlab.components as components
import sidusai.plugins.gitlab.skills as skills

__default_agent_name__ = 'gitlab_agent'


class GitlabPlugin(sai.AgentPlugin):
    """
    Registers GitLab client and skills for issue, comment, pipeline, and search flows.
    """

    def __init__(self, token: str | None = None, base_url: str | None = None,
                 project_id: str | int | None = None, verify_ssl: bool = True,
                 timeout: int | None = None, dry_run: bool = False):
        super().__init__()
        env_token = os.environ.get('GITLAB_TOKEN')
        env_base_url = os.environ.get('GITLAB_BASE_URL')
        env_project_id = os.environ.get('GITLAB_PROJECT_ID')
        env_verify = os.environ.get('GITLAB_VERIFY_SSL')
        env_timeout = os.environ.get('GITLAB_TIMEOUT')
        env_dry_run = os.environ.get('GITLAB_DRY_RUN')

        self.token = token if token is not None else env_token
        self.base_url = base_url if base_url is not None else env_base_url
        self.project_id = project_id if project_id is not None else env_project_id
        self.verify_ssl = self._parse_bool(env_verify, verify_ssl)
        self.timeout = timeout if timeout is not None else self._parse_int(env_timeout, components.__default_timeout__)
        self.dry_run = self._parse_bool(env_dry_run, dry_run)

    def apply_plugin(self, agent: sai.Agent):
        agent.add_component_builder(self._build_gitlab_client)

        agent.add_skill(skills.gitlab_create_issue_skill)
        agent.add_skill(skills.gitlab_list_issues_skill)
        agent.add_skill(skills.gitlab_comment_skill)
        agent.add_skill(skills.gitlab_trigger_pipeline_skill)
        agent.add_skill(skills.gitlab_pipeline_status_skill)
        agent.add_skill(skills.gitlab_search_code_skill)

    def _build_gitlab_client(self) -> components.GitlabClientComponent:
        if self.token is None:
            raise ValueError('GITLAB_TOKEN is required for GitLab plugin.')
        return components.GitlabClientComponent(
            token=self.token,
            base_url=self.base_url,
            default_project_id=self.project_id,
            verify_ssl=self.verify_ssl,
            timeout=self.timeout,
            dry_run=self.dry_run
        )

    @staticmethod
    def _parse_bool(value: str | None, default: bool) -> bool:
        if value is None:
            return default
        return str(value).lower() in ['1', 'true', 'yes', 'y']

    @staticmethod
    def _parse_int(value: str | None, default: int) -> int:
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default


class GitlabIssueTask(sai.CompletedAgentTask):
    pass


class GitlabIssueListTask(sai.CompletedAgentTask):
    pass


class GitlabCommentTask(sai.CompletedAgentTask):
    pass


class GitlabPipelineTask(sai.CompletedAgentTask):
    pass


class GitlabPipelineStatusTask(sai.CompletedAgentTask):
    pass


class GitlabSearchTask(sai.CompletedAgentTask):
    pass


class GitlabAgent(sai.Agent):
    """
    Convenience agent wrapping GitLab skills with simple helper methods.
    """

    def __init__(self, token: str | None = None, base_url: str | None = None,
                 project_id: str | int | None = None, verify_ssl: bool = True,
                 timeout: int | None = None, dry_run: bool = False,
                 plugins: list[sai.AgentPlugin] | None = None):
        super().__init__(__default_agent_name__)

        _plugins = plugins if plugins is not None else []
        gitlab_plugin = GitlabPlugin(
            token=token,
            base_url=base_url,
            project_id=project_id,
            verify_ssl=verify_ssl,
            timeout=timeout,
            dry_run=dry_run
        )
        _plugins.append(gitlab_plugin)

        for plugin in _plugins:
            plugin.apply_plugin(self)

        self._register_tasks()

    def _register_tasks(self):
        create_issue_skills = _cp.build_and_register_task_skill_names([skills.gitlab_create_issue_skill], self)
        self.task_registration(GitlabIssueTask, skill_names=create_issue_skills)

        list_issue_skills = _cp.build_and_register_task_skill_names([skills.gitlab_list_issues_skill], self)
        self.task_registration(GitlabIssueListTask, skill_names=list_issue_skills)

        comment_skills = _cp.build_and_register_task_skill_names([skills.gitlab_comment_skill], self)
        self.task_registration(GitlabCommentTask, skill_names=comment_skills)

        pipeline_skills = _cp.build_and_register_task_skill_names([skills.gitlab_trigger_pipeline_skill], self)
        self.task_registration(GitlabPipelineTask, skill_names=pipeline_skills)

        pipeline_status_skills = _cp.build_and_register_task_skill_names([skills.gitlab_pipeline_status_skill], self)
        self.task_registration(GitlabPipelineStatusTask, skill_names=pipeline_status_skills)

        search_skills = _cp.build_and_register_task_skill_names([skills.gitlab_search_code_skill], self)
        self.task_registration(GitlabSearchTask, skill_names=search_skills)

    #############################################################
    # Helper methods
    #############################################################

    def create_issue(self, title: str, description: str | None = None, labels: list[str] | None = None,
                     assignee_ids: list[int] | None = None, milestone_id: int | None = None,
                     confidential: bool = False, project_id: str | int | None = None, dry_run: bool = False,
                     handler=None):
        value = skills.GitlabIssueCreateValue(
            title=title,
            description=description,
            labels=labels,
            assignee_ids=assignee_ids,
            milestone_id=milestone_id,
            confidential=confidential,
            project_id=project_id,
            dry_run=dry_run
        )
        task = GitlabIssueTask(self).data(value).then(handler)
        self.task_execute(task)

    def list_issues(self, state: str = 'opened', labels: list[str] | None = None, search: str | None = None,
                    assignee_id: int | None = None, milestone: str | None = None, page: int | None = None,
                    per_page: int | None = None, project_id: str | int | None = None, handler=None):
        value = skills.GitlabIssueListValue(
            state=state,
            labels=labels,
            search=search,
            assignee_id=assignee_id,
            milestone=milestone,
            page=page,
            per_page=per_page,
            project_id=project_id
        )
        task = GitlabIssueListTask(self).data(value).then(handler)
        self.task_execute(task)

    def comment_issue(self, issue_iid: int, body: str, project_id: str | int | None = None,
                      dry_run: bool = False, handler=None):
        value = skills.GitlabCommentValue('issue', issue_iid, body, project_id=project_id, dry_run=dry_run)
        task = GitlabCommentTask(self).data(value).then(handler)
        self.task_execute(task)

    def comment_merge_request(self, mr_iid: int, body: str, project_id: str | int | None = None,
                              dry_run: bool = False, handler=None):
        value = skills.GitlabCommentValue('mr', mr_iid, body, project_id=project_id, dry_run=dry_run)
        task = GitlabCommentTask(self).data(value).then(handler)
        self.task_execute(task)

    def trigger_pipeline(self, ref: str, variables: dict | None = None, project_id: str | int | None = None,
                         dry_run: bool = False, handler=None):
        value = skills.GitlabPipelineTriggerValue(ref=ref, variables=variables, project_id=project_id, dry_run=dry_run)
        task = GitlabPipelineTask(self).data(value).then(handler)
        self.task_execute(task)

    def pipeline_status(self, pipeline_id: int | None = None, ref: str | None = None,
                        project_id: str | int | None = None, handler=None):
        value = skills.GitlabPipelineStatusValue(pipeline_id=pipeline_id, ref=ref, project_id=project_id)
        task = GitlabPipelineStatusTask(self).data(value).then(handler)
        self.task_execute(task)

    def search_code(self, query: str, scope: str = 'blobs', page: int | None = None,
                    per_page: int | None = None, project_id: str | int | None = None, handler=None):
        value = skills.GitlabCodeSearchValue(
            query=query,
            scope=scope,
            page=page,
            per_page=per_page,
            project_id=project_id
        )
        task = GitlabSearchTask(self).data(value).then(handler)
        self.task_execute(task)
