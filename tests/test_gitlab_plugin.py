import importlib.util
import unittest
from unittest.mock import MagicMock

SKIP_GITLAB = importlib.util.find_spec('gitlab') is None

if not SKIP_GITLAB:
    import sidusai.plugins.gitlab.skills as skills


@unittest.skipIf(SKIP_GITLAB, "python-gitlab not installed")
class GitlabSkillsTests(unittest.TestCase):

    def test_create_issue_builds_payload(self):
        client = MagicMock()
        client.create_issue.return_value = {
            'id': 1,
            'iid': 2,
            'title': 'hello',
            'state': 'opened',
            'web_url': 'https://gitlab.example/issue/2'
        }

        value = skills.GitlabIssueCreateValue(
            title='hello',
            description='desc',
            labels=['a'],
            assignee_ids=[5],
            milestone_id=10,
            confidential=True,
            project_id='proj'
        )

        result = skills.gitlab_create_issue_skill(value, client)

        client.create_issue.assert_called_once_with(
            {
                'title': 'hello',
                'description': 'desc',
                'labels': ['a'],
                'assignee_ids': [5],
                'milestone_id': 10,
                'confidential': True
            },
            project_id='proj',
            dry_run=False
        )
        self.assertEqual(result.iid, 2)
        self.assertEqual(result.state, 'opened')

    def test_comment_skill_dispatches_to_issue(self):
        client = MagicMock()
        client.comment_issue.return_value = {'id': 7, 'body': 'hi'}

        value = skills.GitlabCommentValue('issue', target_iid=3, body='hi', project_id='proj', dry_run=True)
        result = skills.gitlab_comment_skill(value, client)

        client.comment_issue.assert_called_once_with(3, 'hi', project_id='proj', dry_run=True)
        self.assertEqual(result.id, 7)

    def test_pipeline_status_requires_identifier(self):
        client = MagicMock()
        value = skills.GitlabPipelineStatusValue()
        with self.assertRaises(ValueError):
            skills.gitlab_pipeline_status_skill(value, client)

    def test_list_issues_skill_passes_filters(self):
        client = MagicMock()
        client.list_issues.return_value = [{'iid': 1, 'title': 't'}]

        value = skills.GitlabIssueListValue(
            state='opened',
            labels=['bug'],
            search='urgent',
            assignee_id=42,
            milestone='m1',
            page=2,
            per_page=5,
            project_id='proj'
        )

        result = skills.gitlab_list_issues_skill(value, client)

        client.list_issues.assert_called_once_with(
            {
                'state': 'opened',
                'labels': ['bug'],
                'search': 'urgent',
                'assignee_id': 42,
                'milestone': 'm1',
                'page': 2,
                'per_page': 5
            },
            project_id='proj'
        )
        self.assertEqual(len(result.items), 1)

    def test_trigger_pipeline_skill(self):
        client = MagicMock()
        client.trigger_pipeline.return_value = {'id': 123, 'status': 'pending', 'ref': 'main'}

        value = skills.GitlabPipelineTriggerValue(
            ref='main',
            variables={'A': 'B'},
            project_id='proj',
            dry_run=False
        )

        result = skills.gitlab_trigger_pipeline_skill(value, client)

        client.trigger_pipeline.assert_called_once_with(
            'main',
            variables={'A': 'B'},
            project_id='proj',
            dry_run=False
        )
        self.assertEqual(result.id, 123)
        self.assertEqual(result.ref, 'main')

    def test_pipeline_status_with_ref(self):
        client = MagicMock()
        client.pipeline_status.return_value = {'id': 11, 'status': 'success', 'ref': 'develop'}

        value = skills.GitlabPipelineStatusValue(pipeline_id=None, ref='develop', project_id='proj')
        result = skills.gitlab_pipeline_status_skill(value, client)

        client.pipeline_status.assert_called_once_with(None, project_id='proj', ref='develop')
        self.assertEqual(result.status, 'success')

    def test_comment_skill_dispatches_to_mr(self):
        client = MagicMock()
        client.comment_merge_request.return_value = {'id': 8, 'body': 'mr note'}

        value = skills.GitlabCommentValue('mr', target_iid=5, body='mr note', project_id='proj', dry_run=False)
        result = skills.gitlab_comment_skill(value, client)

        client.comment_merge_request.assert_called_once_with(5, 'mr note', project_id='proj', dry_run=False)
        self.assertEqual(result.id, 8)

    def test_search_code_skill(self):
        client = MagicMock()
        client.search_code.return_value = [{'path': 'README.md', 'startline': 1}]

        value = skills.GitlabCodeSearchValue(query='TODO', scope='blobs', page=1, per_page=2, project_id='proj')
        result = skills.gitlab_search_code_skill(value, client)

        client.search_code.assert_called_once_with(
            query='TODO',
            project_id='proj',
            scope='blobs',
            page=1,
            per_page=2
        )
        self.assertEqual(len(result.matches), 1)


if __name__ == '__main__':
    unittest.main()
