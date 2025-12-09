import gitlab
from gitlab import exceptions as gl_exceptions

__default_base_url__ = 'https://gitlab.com'
__default_timeout__ = 15
__default_per_page__ = 20
__max_per_page__ = 50


class GitlabClientComponent:
    """
    Lightweight GitLab client wrapper with project resolution, paging clamps,
    and dry-run support for mutating calls.
    """

    def __init__(self, token: str, base_url: str = None, default_project_id: str | int = None,
                 verify_ssl: bool = True, timeout: int = __default_timeout__, dry_run: bool = False):
        if token is None:
            raise ValueError('GitLab token is required')

        self.base_url = base_url if base_url is not None else __default_base_url__
        self.token = token
        self.default_project_id = default_project_id
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.dry_run = dry_run

        self.client = gitlab.Gitlab(
            url=self.base_url,
            private_token=self.token,
            ssl_verify=self.verify_ssl,
            timeout=self.timeout
        )

    #############################################################
    # Helpers
    #############################################################

    def resolve_project_id(self, project_id: str | int | None) -> str | int:
        pid = project_id if project_id is not None else self.default_project_id
        if pid is None:
            raise ValueError('GitLab project id/path is required.')
        return pid

    def get_project(self, project_id: str | int | None = None):
        pid = self.resolve_project_id(project_id)
        try:
            return self.client.projects.get(pid)
        except gl_exceptions.GitlabAuthenticationError as e:
            raise ConnectionError('GitLab authentication failed.') from e
        except gl_exceptions.GitlabGetError as e:
            raise ValueError(f'GitLab project "{pid}" not found or inaccessible.') from e
        except gl_exceptions.GitlabError as e:
            msg = getattr(e, 'error_message', None) or str(e)
            raise RuntimeError(f'GitLab error while fetching project "{pid}": {msg}') from e

    def _clamp_per_page(self, per_page: int | None) -> int:
        if per_page is None:
            return __default_per_page__
        per_page = max(1, per_page)
        return min(per_page, __max_per_page__)

    def _dry_run_result(self, action: str, project_id, payload: dict | None = None):
        return {
            'dry_run': True,
            'action': action,
            'project_id': project_id,
            'payload': payload
        }

    def _wrap(self, action: str, func):
        try:
            return func()
        except gl_exceptions.GitlabAuthenticationError as e:
            raise ConnectionError(f'GitLab authentication failed during {action}.') from e
        except gl_exceptions.GitlabHttpError as e:
            msg = getattr(e, 'error_message', None) or str(e)
            raise RuntimeError(f'GitLab HTTP error during {action}: {msg}') from e
        except gl_exceptions.GitlabError as e:
            msg = getattr(e, 'error_message', None) or str(e)
            raise RuntimeError(f'GitLab error during {action}: {msg}') from e

    @staticmethod
    def _issue_dict(issue) -> dict:
        data = issue.attributes if hasattr(issue, 'attributes') else {}
        return {
            'id': data.get('id'),
            'iid': data.get('iid'),
            'project_id': data.get('project_id'),
            'title': data.get('title'),
            'state': data.get('state'),
            'labels': data.get('labels'),
            'assignees': data.get('assignees'),
            'author': data.get('author'),
            'web_url': data.get('web_url'),
            'created_at': data.get('created_at'),
            'updated_at': data.get('updated_at'),
            'references': data.get('references'),
        }

    @staticmethod
    def _note_dict(note) -> dict:
        data = note.attributes if hasattr(note, 'attributes') else {}
        return {
            'id': data.get('id'),
            'body': data.get('body'),
            'author': data.get('author'),
            'system': data.get('system'),
            'created_at': data.get('created_at'),
            'noteable_type': data.get('noteable_type'),
            'noteable_iid': data.get('noteable_iid'),
            'web_url': data.get('web_url') if 'web_url' in data else None
        }

    @staticmethod
    def _pipeline_dict(pipeline) -> dict:
        data = pipeline.attributes if hasattr(pipeline, 'attributes') else {}
        return {
            'id': data.get('id'),
            'iid': data.get('iid'),
            'project_id': data.get('project_id'),
            'status': data.get('status'),
            'ref': data.get('ref'),
            'sha': data.get('sha'),
            'source': data.get('source'),
            'web_url': data.get('web_url'),
            'created_at': data.get('created_at'),
            'updated_at': data.get('updated_at'),
            'started_at': data.get('started_at'),
            'finished_at': data.get('finished_at'),
            'duration': data.get('duration'),
        }

    @staticmethod
    def _search_dict(item: dict) -> dict:
        return {
            'path': item['path'] if 'path' in item else None,
            'basename': item['basename'] if 'basename' in item else None,
            'ref': item['ref'] if 'ref' in item else None,
            'startline': item['startline'] if 'startline' in item else None,
            'data': item['data'] if 'data' in item else None
        }

    #############################################################
    # Operations
    #############################################################

    def create_issue(self, payload: dict, project_id: str | int | None = None, dry_run: bool | None = None) -> dict:
        pid = self.resolve_project_id(project_id)
        if payload is None:
            raise ValueError('Issue payload cannot be None')
        _dry_run = self.dry_run if dry_run is None else dry_run
        if _dry_run:
            return self._dry_run_result('create_issue', pid, payload)

        def _op():
            project = self.get_project(pid)
            issue = project.issues.create(payload)
            return self._issue_dict(issue)

        return self._wrap('create_issue', _op)

    def list_issues(self, params: dict | None = None, project_id: str | int | None = None) -> list[dict]:
        pid = self.resolve_project_id(project_id)
        _params = params if params is not None else {}
        per_page = self._clamp_per_page(_params.pop('per_page', None))
        page = _params.pop('page', None)

        def _op():
            project = self.get_project(pid)
            issues = project.issues.list(
                per_page=per_page,
                page=page if page is not None else 1,
                get_all=False,
                **_params
            )
            return [self._issue_dict(issue) for issue in issues]

        return self._wrap('list_issues', _op)

    def comment_issue(self, issue_iid: int, body: str, project_id: str | int | None = None,
                      dry_run: bool | None = None) -> dict:
        pid = self.resolve_project_id(project_id)
        if body is None:
            raise ValueError('Comment body cannot be None')
        _dry_run = self.dry_run if dry_run is None else dry_run
        if _dry_run:
            return self._dry_run_result('comment_issue', pid, {'issue_iid': issue_iid, 'body': body})

        def _op():
            project = self.get_project(pid)
            issue = project.issues.get(issue_iid)
            note = issue.notes.create({'body': body})
            return self._note_dict(note)

        return self._wrap('comment_issue', _op)

    def comment_merge_request(self, mr_iid: int, body: str, project_id: str | int | None = None,
                              dry_run: bool | None = None) -> dict:
        pid = self.resolve_project_id(project_id)
        if body is None:
            raise ValueError('Comment body cannot be None')
        _dry_run = self.dry_run if dry_run is None else dry_run
        if _dry_run:
            return self._dry_run_result('comment_mr', pid, {'mr_iid': mr_iid, 'body': body})

        def _op():
            project = self.get_project(pid)
            mr = project.mergerequests.get(mr_iid)
            note = mr.notes.create({'body': body})
            return self._note_dict(note)

        return self._wrap('comment_mr', _op)

    def trigger_pipeline(self, ref: str, variables: dict | None = None, project_id: str | int | None = None,
                         dry_run: bool | None = None) -> dict:
        pid = self.resolve_project_id(project_id)
        if ref is None:
            raise ValueError('Pipeline ref cannot be None')

        payload = {'ref': ref}
        if variables is not None:
            payload['variables'] = [{'key': k, 'value': v} for k, v in variables.items()]

        _dry_run = self.dry_run if dry_run is None else dry_run
        if _dry_run:
            return self._dry_run_result('trigger_pipeline', pid, payload)

        def _op():
            project = self.get_project(pid)
            pipeline = project.pipelines.create(payload)
            return self._pipeline_dict(pipeline)

        return self._wrap('trigger_pipeline', _op)

    def pipeline_status(self, pipeline_id: int | None, project_id: str | int | None = None,
                       ref: str | None = None) -> dict:
        pid = self.resolve_project_id(project_id)

        def _op():
            project = self.get_project(pid)
            pipeline = None

            if pipeline_id is not None:
                pipeline = project.pipelines.get(pipeline_id)
            else:
                if ref is None:
                    raise ValueError('pipeline_id or ref must be provided')
                pipelines = project.pipelines.list(ref=ref, per_page=1, page=1, order_by='id', sort='desc')
                if len(pipelines) == 0:
                    return {}
                pipeline = pipelines[0]

            return self._pipeline_dict(pipeline)

        return self._wrap('pipeline_status', _op)

    def search_code(self, query: str, project_id: str | int | None = None, scope: str = 'blobs',
                    page: int | None = None, per_page: int | None = None) -> list[dict]:
        pid = self.resolve_project_id(project_id)
        if query is None:
            raise ValueError('Search query cannot be None')
        _per_page = self._clamp_per_page(per_page)
        _page = page if page is not None else 1

        def _op():
            project = self.get_project(pid)
            results = project.search(scope=scope, search=query, page=_page, per_page=_per_page)
            return [self._search_dict(item) for item in results]

        return self._wrap('search_code', _op)
