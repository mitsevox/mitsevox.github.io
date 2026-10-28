"""repo_settings.py's pure logic: the standard per repository kind with overrides, the expected
values, the diff against a current state, and the apply plan, all against a fake API."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import repo_settings  # noqa: E402

CONFIG = repo_settings.load_config()


class FakeApi:
    """Answers GET from a dictionary of path -> (status, json) and records every write."""
    def __init__(self, responses):
        self.responses = responses
        self.writes = []

    def __call__(self, method, path, body=None):
        if method == 'GET':
            return self.responses.get(path, (404, {}))
        self.writes.append((method, path, body))
        return 200, {}


def ideal(repo):
    """A current state equal to the standard, as the API would show it."""
    std = repo_settings.standard(CONFIG, repo)
    wanted = repo_settings.expected(std)
    repo_json = {k.split('.', 1)[1]: v for k, v in wanted.items() if k.startswith('repository.')}
    repo_json['security_and_analysis'] = {
        'secret_scanning': {'status': 'enabled'}, 'secret_scanning_push_protection': {'status': 'enabled'}}
    rules = [{'type': 'deletion'}, {'type': 'non_fast_forward'}, {'type': 'pull_request'},
             {'type': 'required_status_checks', 'parameters': {'required_status_checks': [{'context': std['ruleset']['requiredCheck']}]}}]
    responses = {
        '/repos/%s' % repo: (200, repo_json),
        '/repos/%s/actions/permissions' % repo: (200, {'allowed_actions': 'selected'}),
        '/repos/%s/actions/permissions/selected-actions' % repo: (200, {
            'github_owned_allowed': True, 'verified_allowed': False, 'patterns_allowed': std['allowedActions']['patterns']}),
        '/repos/%s/actions/permissions/workflow' % repo: (200, {'default_workflow_permissions': 'read', 'can_approve_pull_request_reviews': False}),
        '/repos/%s/actions/permissions/artifact-and-log-retention' % repo: (200, {'days': 30}),
        '/repos/%s/actions/permissions/fork-pr-contributor-approval' % repo: (200, {'approval_policy': 'all_external_contributors'}),
        '/repos/%s/vulnerability-alerts' % repo: (204, {}),
        '/repos/%s/private-vulnerability-reporting' % repo: (200, {'enabled': True}),
        '/repos/%s/contents/.github/dependabot.yml' % repo: (404, {}),
        '/repos/%s/actions/variables' % repo: (200, {'variables': [{'name': n} for n in std['variables']]}),
        '/repos/%s/actions/secrets' % repo: (200, {'secrets': [{'name': n} for n in std['secrets']]}),
        '/repos/%s/rulesets' % repo: (200, [{'id': 7, 'name': 'main'}]),
        '/repos/%s/rulesets/7' % repo: (200, {'id': 7, 'enforcement': 'active', 'bypass_actors': [], 'rules': rules}),
    }
    return std, responses


class RepoSettingsTests(unittest.TestCase):
    def test_standard_applies_kind_values_and_overrides(self):
        source = repo_settings.standard(CONFIG, 'mitsevox/n100f')
        self.assertEqual(source['merge'], 'squash')
        self.assertEqual(source['description'], 'Scooby-Doo! Night of 100 Frights (GameCube, 2002) decompilation')
        self.assertEqual(source['homepage'], 'https://mitsevox.github.io/games/n100f/')
        self.assertEqual(source['topics'], ['decompilation', 'gamecube', 'n100f'])
        self.assertEqual(repo_settings.standard(CONFIG, 'mitsevox/tw2004')['merge'], 'merge')
        self.assertEqual(repo_settings.standard(CONFIG, 'mitsevox/n100f-build')['description'], 'Private build environment for mitsevox/n100f')
        self.assertIsNone(repo_settings.standard(CONFIG, 'someone/else', 'source')['description'])
        with self.assertRaises(ValueError):
            repo_settings.standard(CONFIG, 'someone/else')

    def test_expected_merge_method_follows_the_override(self):
        squash = repo_settings.expected(repo_settings.standard(CONFIG, 'mitsevox/n100f'))
        merge = repo_settings.expected(repo_settings.standard(CONFIG, 'mitsevox/tw2004'))
        self.assertEqual((squash['repository.allow_squash_merge'], squash['repository.allow_merge_commit']), (True, False))
        self.assertEqual((merge['repository.allow_squash_merge'], merge['repository.allow_merge_commit']), (False, True))
        self.assertNotIn('actions.fork_pr_approval_policy', repo_settings.expected(repo_settings.standard(CONFIG, 'mitsevox/n100f-build')))

    def test_ideal_state_has_no_drift_and_changes_are_found(self):
        for repo in ('mitsevox/n100f', 'mitsevox/tw2004', 'mitsevox/n100f-build'):
            with self.subTest(repo=repo):
                std, responses = ideal(repo)
                found = repo_settings.current(FakeApi(responses), repo, std)
                self.assertEqual(repo_settings.diff(repo_settings.expected(std), found), [])
        std, responses = ideal('mitsevox/n100f')
        responses['/repos/mitsevox/n100f'][1]['has_wiki'] = True
        responses['/repos/mitsevox/n100f'][1]['topics'] = ['decompilation']
        responses['/repos/mitsevox/n100f/actions/variables'] = (200, {'variables': [{'name': 'PORTFOLIO_APP_CLIENT_ID'}]})
        responses['/repos/mitsevox/n100f/rulesets'] = (200, [])
        del responses['/repos/mitsevox/n100f/actions/permissions/workflow']
        drift = repo_settings.diff(repo_settings.expected(std), repo_settings.current(FakeApi(responses), 'mitsevox/n100f', std))
        keys = {key for key, _, _ in drift}
        self.assertIn('repository.has_wiki', keys)
        self.assertIn('repository.topics', keys)
        self.assertIn('actions.variables', keys)
        self.assertIn('ruleset.exists', keys)
        self.assertIn('actions.default_workflow_permissions', keys)  # unreadable counts as drift

    def test_apply_writes_only_the_drifted_groups_and_lists_hand_steps(self):
        std, responses = ideal('mitsevox/n100f')
        responses['/repos/mitsevox/n100f'][1]['has_wiki'] = True
        responses['/repos/mitsevox/n100f/rulesets'] = (200, [])
        responses['/repos/mitsevox/n100f/actions/secrets'] = (200, {'secrets': []})
        api = FakeApi(responses)
        found = repo_settings.current(api, 'mitsevox/n100f', std)
        drift = repo_settings.diff(repo_settings.expected(std), found)
        hand = repo_settings.apply(api, 'mitsevox/n100f', std, drift, found)
        methods = [(method, path) for method, path, _ in api.writes]
        self.assertIn(('PATCH', '/repos/mitsevox/n100f'), methods)
        self.assertIn(('POST', '/repos/mitsevox/n100f/rulesets'), methods)
        self.assertNotIn(('PUT', '/repos/mitsevox/n100f/actions/permissions/workflow'), methods)
        patch = next(body for method, path, body in api.writes if method == 'PATCH')
        self.assertEqual(patch, {'has_wiki': False})
        ruleset = next(body for method, path, body in api.writes if method == 'POST')
        self.assertEqual([r['type'] for r in ruleset['rules']], ['deletion', 'non_fast_forward', 'pull_request', 'required_status_checks'])
        self.assertTrue(any('DATA_APP_PRIVATE_KEY' in step for step in hand))


if __name__ == '__main__':
    unittest.main()
