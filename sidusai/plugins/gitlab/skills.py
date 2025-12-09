import sidusai as sai
import sidusai.plugins.gitlab.components as components

__all__ = [
    'GitlabIssueCreateValue', 'GitlabIssueResult', 'GitlabIssueListValue', 'GitlabIssuesResult',
    'GitlabCommentValue', 'GitlabCommentResult',
    'GitlabPipelineTriggerValue', 'GitlabPipelineStatusValue', 'GitlabPipelineStatusResult',
    'GitlabCodeSearchValue', 'GitlabSearchResult',
    'gitlab_create_issue_skill', 'gitlab_list_issues_skill', 'gitlab_comment_skill',
    'gitlab_trigger_pipeline_skill', 'gitlab_pipeline_status_skill', 'gitlab_search_code_skill'
]


class GitlabIssueCreateValue(sai.AgentValue):
    """
    Request payload for creating a GitLab issue.
    """

    def __init__(self, title: str, description: str | None = None, labels: list[str] | None = None,
                 assignee_ids: list[int] | None = None, milestone_id: int | None = None, confidential: bool = False,
                 project_id: str | int | None = None, dry_run: bool = False):
        super().__init__()
        self.title = title
        self.description = description
        self.labels = labels
        self.assignee_ids = assignee_ids
        self.milestone_id = milestone_id
        self.confidential = confidential
        self.project_id = project_id
        self.dry_run = dry_run


class GitlabIssueResult(sai.AgentValue):
    def __init__(self, data: dict):
        super().__init__()
        self.id = data.get('id')
        self.iid = data.get('iid')
        self.project_id = data.get('project_id')
        self.title = data.get('title')
        self.state = data.get('state')
        self.labels = data.get('labels')
        self.web_url = data.get('web_url')
        self.raw = data


class GitlabIssueListValue(sai.AgentValue):
    """
    Filters for listing/searching issues.
    """

    def __init__(self, state: str = 'opened', labels: list[str] | None = None, search: str | None = None,
                 assignee_id: int | None = None, milestone: str | None = None, page: int | None = None,
                 per_page: int | None = None, project_id: str | int | None = None):
        super().__init__()
        self.state = state
        self.labels = labels
        self.search = search
        self.assignee_id = assignee_id
        self.milestone = milestone
        self.page = page
        self.per_page = per_page
        self.project_id = project_id


class GitlabIssuesResult(sai.AgentValue):
    def __init__(self, items: list[dict]):
        super().__init__()
        self.items = items


class GitlabCommentValue(sai.AgentValue):
    """
    Comment on an issue or merge request.
    target_type: "issue" or "mr"
    """

    def __init__(self, target_type: str, target_iid: int, body: str, project_id: str | int | None = None,
                 dry_run: bool = False):
        super().__init__()
        self.target_type = target_type
        self.target_iid = target_iid
        self.body = body
        self.project_id = project_id
        self.dry_run = dry_run


class GitlabCommentResult(sai.AgentValue):
    def __init__(self, data: dict):
        super().__init__()
        self.id = data.get('id')
        self.body = data.get('body')
        self.author = data.get('author')
        self.created_at = data.get('created_at')
        self.web_url = data.get('web_url')
        self.raw = data


class GitlabPipelineTriggerValue(sai.AgentValue):
    def __init__(self, ref: str, variables: dict | None = None, project_id: str | int | None = None,
                 dry_run: bool = False):
        super().__init__()
        self.ref = ref
        self.variables = variables
        self.project_id = project_id
        self.dry_run = dry_run


class GitlabPipelineStatusValue(sai.AgentValue):
    def __init__(self, pipeline_id: int | None = None, ref: str | None = None,
                 project_id: str | int | None = None):
        super().__init__()
        self.pipeline_id = pipeline_id
        self.ref = ref
        self.project_id = project_id


class GitlabPipelineStatusResult(sai.AgentValue):
    def __init__(self, data: dict):
        super().__init__()
        self.id = data.get('id')
        self.status = data.get('status')
        self.ref = data.get('ref')
        self.sha = data.get('sha')
        self.web_url = data.get('web_url')
        self.source = data.get('source')
        self.started_at = data.get('started_at')
        self.finished_at = data.get('finished_at')
        self.duration = data.get('duration')
        self.raw = data


class GitlabCodeSearchValue(sai.AgentValue):
    def __init__(self, query: str, scope: str = 'blobs', page: int | None = None, per_page: int | None = None,
                 project_id: str | int | None = None):
        super().__init__()
        self.query = query
        self.scope = scope
        self.page = page
        self.per_page = per_page
        self.project_id = project_id


class GitlabSearchResult(sai.AgentValue):
    def __init__(self, matches: list[dict]):
        super().__init__()
        self.matches = matches


#############################################################
# Skills
#############################################################

def gitlab_create_issue_skill(value: GitlabIssueCreateValue, client: components.GitlabClientComponent) -> GitlabIssueResult:
    if value.title is None or len(str(value.title).strip()) == 0:
        raise ValueError('Issue title cannot be empty')

    payload = {'title': value.title}
    if value.description is not None:
        payload['description'] = value.description
    if value.labels is not None:
        payload['labels'] = value.labels
    if value.assignee_ids is not None:
        payload['assignee_ids'] = value.assignee_ids
    if value.milestone_id is not None:
        payload['milestone_id'] = value.milestone_id
    payload['confidential'] = value.confidential

    data = client.create_issue(payload, project_id=value.project_id, dry_run=value.dry_run)
    return GitlabIssueResult(data)


def gitlab_list_issues_skill(value: GitlabIssueListValue, client: components.GitlabClientComponent) -> GitlabIssuesResult:
    params = {}
    if value.state is not None:
        params['state'] = value.state
    if value.labels is not None:
        params['labels'] = value.labels
    if value.search is not None:
        params['search'] = value.search
    if value.assignee_id is not None:
        params['assignee_id'] = value.assignee_id
    if value.milestone is not None:
        params['milestone'] = value.milestone
    if value.page is not None:
        params['page'] = value.page
    if value.per_page is not None:
        params['per_page'] = value.per_page

    items = client.list_issues(params, project_id=value.project_id)
    return GitlabIssuesResult(items)


def gitlab_comment_skill(value: GitlabCommentValue, client: components.GitlabClientComponent) -> GitlabCommentResult:
    target = value.target_type.lower() if value.target_type is not None else None
    if target not in ['issue', 'mr', 'merge_request']:
        raise ValueError('target_type must be "issue" or "mr"')
    if value.body is None or len(str(value.body).strip()) == 0:
        raise ValueError('Comment body cannot be empty')

    if target == 'issue':
        data = client.comment_issue(value.target_iid, value.body, project_id=value.project_id, dry_run=value.dry_run)
    else:
        data = client.comment_merge_request(value.target_iid, value.body, project_id=value.project_id,
                                            dry_run=value.dry_run)
    return GitlabCommentResult(data)


def gitlab_trigger_pipeline_skill(value: GitlabPipelineTriggerValue,
                                  client: components.GitlabClientComponent) -> GitlabPipelineStatusResult:
    if value.ref is None or len(str(value.ref).strip()) == 0:
        raise ValueError('Pipeline ref cannot be empty')

    data = client.trigger_pipeline(value.ref, variables=value.variables,
                                   project_id=value.project_id, dry_run=value.dry_run)
    return GitlabPipelineStatusResult(data)


def gitlab_pipeline_status_skill(value: GitlabPipelineStatusValue,
                                 client: components.GitlabClientComponent) -> GitlabPipelineStatusResult:
    if value.pipeline_id is None and value.ref is None:
        raise ValueError('pipeline_id or ref must be provided')

    data = client.pipeline_status(value.pipeline_id, project_id=value.project_id, ref=value.ref)
    return GitlabPipelineStatusResult(data)


def gitlab_search_code_skill(value: GitlabCodeSearchValue,
                             client: components.GitlabClientComponent) -> GitlabSearchResult:
    if value.query is None or len(str(value.query).strip()) == 0:
        raise ValueError('Search query cannot be empty')

    matches = client.search_code(
        query=value.query,
        project_id=value.project_id,
        scope=value.scope,
        page=value.page,
        per_page=value.per_page
    )
    return GitlabSearchResult(matches)
