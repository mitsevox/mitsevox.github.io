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
    rules = [{'type': 'deletion'}, {'type': 'non_fast_forward'},
             {'type': 'pull_request', 'parameters': {'dismiss_stale_reviews_on_push': True, 'allowed_merge_methods': [std['merge']]}},
             {'type': 'required_status_checks', 'parameters': {'strict_required_status_checks_policy': False,
              'required_status_checks': [{'context': std['ruleset']['requiredCheck']}]}}] if std['ruleset'] else []
    rulesets = [{'id': 7, 'name': 'main'}] if std['ruleset'] else []
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
        '/repos/%s/rulesets' % repo: (200, rulesets),
        '/repos/%s/rulesets/7' % repo: (200, {'id': 7, 'name': 'main', 'enforcement': 'active', 'bypass_actors': [],
                                              'conditions': {'ref_name': {'include': ['~DEFAULT_BRANCH'], 'exclude': []}}, 'rules': rules}),
    }
    if std.get('mergeRuleset'):
        rulesets.append({'id': 8, 'name': 'merges'})
        responses['/repos/%s/rulesets/8' % repo] = (200, {
            'id': 8, 'name': 'merges', 'enforcement': 'active',
            'bypass_actors': [{'actor_id': 5, 'actor_type': 'RepositoryRole', 'bypass_mode': 'pull_request'}],
            'conditions': {'ref_name': {'include': ['~DEFAULT_BRANCH'], 'exclude': []}}, 'rules': [{'type': 'update'}]})
    environments = std.get('environments', {})
    responses['/repos/%s/environments' % repo] = (200, {'total_count': len(environments), 'environments': [
        {'name': name, 'deployment_branch_policy': {'protected_branches': False, 'custom_branch_policies': True}
         if env['branches'] is not None else None} for name, env in environments.items()]})
    for name, env in environments.items():
        responses['/repos/%s/environments/%s/secrets' % (repo, name)] = (200, {'secrets': [{'name': n} for n in env['secrets']]})
        if env['branches'] is not None:
            responses['/repos/%s/environments/%s/deployment-branch-policies' % (repo, name)] = (200, {
                'branch_policies': [{'id': i + 1, 'name': b, 'type': 'branch'} for i, b in enumerate(env['branches'])]})
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
        for repo in ('mitsevox/n100f', 'mitsevox/tw2004', 'mitsevox/n100f-build', 'mitsevox/mitsevox.github.io'):
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
        responses['/repos/mitsevox/n100f/environments/publish/secrets'] = (200, {'secrets': []})
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


    def test_ruleset_drift_inside_the_rules_and_under_another_name(self):
        # n100f's drift: an admin bypass, stale approvals kept, an extra required check.
        std, responses = ideal('mitsevox/n100f')
        detail = responses['/repos/mitsevox/n100f/rulesets/7'][1]
        detail['bypass_actors'] = [{'actor_id': 5, 'actor_type': 'RepositoryRole', 'bypass_mode': 'always'}]
        detail['rules'][2]['parameters']['dismiss_stale_reviews_on_push'] = False
        detail['rules'][3]['parameters']['required_status_checks'].append({'context': 'Tool tests'})
        keys = {k for k, _, _ in repo_settings.diff(repo_settings.expected(std), repo_settings.current(FakeApi(responses), 'mitsevox/n100f', std))}
        self.assertEqual(keys, {'ruleset.bypass_actors', 'ruleset.pull_request.dismiss_stale_reviews', 'ruleset.required_status_checks'})
        # mvp2005's: the default branch's ruleset under another name is found, and apply renames it.
        std, responses = ideal('mitsevox/mvp2005')
        responses['/repos/mitsevox/mvp2005/rulesets'] = (200, [{'id': 7, 'name': 'main protection'}, {'id': 8, 'name': 'merges'}])
        responses['/repos/mitsevox/mvp2005/rulesets/7'][1]['name'] = 'main protection'
        api = FakeApi(responses)
        found = repo_settings.current(api, 'mitsevox/mvp2005', std)
        drift = repo_settings.diff(repo_settings.expected(std), found)
        self.assertEqual({k for k, _, _ in drift}, {'ruleset.name'})
        repo_settings.apply(api, 'mitsevox/mvp2005', std, drift, found)
        self.assertEqual([(m, p) for m, p, _ in api.writes], [('PUT', '/repos/mitsevox/mvp2005/rulesets/7')])

    def test_merges_ruleset_is_required_for_source_repositories(self):
        std, responses = ideal('mitsevox/n100f')
        self.assertEqual(repo_settings.expected(std)['merges.rule.update'], True)
        for other in ('mitsevox/mitsevox.github.io', 'mitsevox/n100f-build'):
            self.assertNotIn('merges.exists', repo_settings.expected(repo_settings.standard(CONFIG, other)))
        # Missing: drift, and apply creates it with the update rule and the admin bypass on pull requests only.
        responses['/repos/mitsevox/n100f/rulesets'] = (200, [{'id': 7, 'name': 'main'}])
        api = FakeApi(responses)
        found = repo_settings.current(api, 'mitsevox/n100f', std)
        drift = repo_settings.diff(repo_settings.expected(std), found)
        keys = {k for k, _, _ in drift}
        self.assertIn('merges.exists', keys)
        self.assertTrue(all(k.startswith('merges.') for k in keys), keys)  # the main ruleset is untouched
        repo_settings.apply(api, 'mitsevox/n100f', std, drift, found)
        self.assertEqual([(m, p) for m, p, _ in api.writes], [('POST', '/repos/mitsevox/n100f/rulesets')])
        body = api.writes[0][2]
        self.assertEqual((body['name'], [r['type'] for r in body['rules']], body['conditions']['ref_name']['include']),
                         ('merges', ['update'], ['~DEFAULT_BRANCH']))
        self.assertEqual(body['bypass_actors'], [{'actor_id': 5, 'actor_type': 'RepositoryRole', 'bypass_mode': 'pull_request'}])
        # An admin bypass that is not limited to pull requests is drift.
        std, responses = ideal('mitsevox/n100f')
        responses['/repos/mitsevox/n100f/rulesets/8'][1]['bypass_actors'][0]['bypass_mode'] = 'always'
        drift = repo_settings.diff(repo_settings.expected(std), repo_settings.current(FakeApi(responses), 'mitsevox/n100f', std))
        self.assertEqual({k for k, _, _ in drift}, {'merges.bypass_actors'})

    def test_rulesets_are_told_apart_by_shape_under_other_names(self):
        # nflstreet2 before its rename: 'Main Merge Authority' (update only) listed before 'Main'.
        std, responses = ideal('mitsevox/nflstreet2')
        responses['/repos/mitsevox/nflstreet2/rulesets'] = (200, [{'id': 8, 'name': 'Main Merge Authority'}, {'id': 7, 'name': 'Main'}])
        responses['/repos/mitsevox/nflstreet2/rulesets/8'][1]['name'] = 'Main Merge Authority'
        responses['/repos/mitsevox/nflstreet2/rulesets/7'][1]['name'] = 'Main'
        api = FakeApi(responses)
        found = repo_settings.current(api, 'mitsevox/nflstreet2', std)
        self.assertEqual((found['ruleset.id'], found['merges.id']), (7, 8))
        drift = repo_settings.diff(repo_settings.expected(std), found)
        self.assertEqual({k for k, _, _ in drift}, {'ruleset.name', 'merges.name'})
        repo_settings.apply(api, 'mitsevox/nflstreet2', std, drift, found)
        self.assertEqual(sorted((m, p) for m, p, _ in api.writes),
                         [('PUT', '/repos/mitsevox/nflstreet2/rulesets/7'), ('PUT', '/repos/mitsevox/nflstreet2/rulesets/8')])
        self.assertEqual({body['name'] for _, _, body in api.writes}, {'main', 'merges'})

    def test_publish_environment_holds_the_key_and_main_only(self):
        std, responses = ideal('mitsevox/n100f')
        wanted = repo_settings.expected(std)
        self.assertEqual((wanted['actions.secrets'], wanted['environments.publish.branches'], wanted['environments.publish.secrets'],
                          wanted['environments.validate.branches'], wanted['environments.validate.secrets']),
                         ([], ['main'], ['DATA_APP_PRIVATE_KEY'], 'all', []))
        for other in ('mitsevox/mitsevox.github.io', 'mitsevox/n100f-build'):
            self.assertFalse([k for k in repo_settings.expected(repo_settings.standard(CONFIG, other)) if k.startswith('environments.')])
        self.assertEqual(repo_settings.diff(wanted, repo_settings.current(FakeApi(responses), 'mitsevox/n100f', std)), [])
        # The key as a repository secret, readable by every branch: drift.
        responses['/repos/mitsevox/n100f/actions/secrets'] = (200, {'secrets': [{'name': 'DATA_APP_PRIVATE_KEY'}]})
        keys = {k for k, _, _ in repo_settings.diff(wanted, repo_settings.current(FakeApi(responses), 'mitsevox/n100f', std))}
        self.assertEqual(keys, {'actions.secrets'})
        # A key in the empty environment, or publish open to every branch: drift.
        std, responses = ideal('mitsevox/n100f')
        responses['/repos/mitsevox/n100f/environments/validate/secrets'] = (200, {'secrets': [{'name': 'DATA_APP_PRIVATE_KEY'}]})
        responses['/repos/mitsevox/n100f/environments'][1]['environments'][0]['deployment_branch_policy'] = None
        api = FakeApi(responses)
        found = repo_settings.current(api, 'mitsevox/n100f', std)
        drift = repo_settings.diff(wanted, found)
        self.assertEqual({k for k, _, _ in drift}, {'environments.validate.secrets', 'environments.publish.branches'})
        hand = repo_settings.apply(api, 'mitsevox/n100f', std, drift, found)
        self.assertEqual([(m, p) for m, p, _ in api.writes], [
            ('PUT', '/repos/mitsevox/n100f/environments/publish'),
            ('POST', '/repos/mitsevox/n100f/environments/publish/deployment-branch-policies')])
        self.assertEqual(api.writes[0][2], {'deployment_branch_policy': {'protected_branches': False, 'custom_branch_policies': True}})
        self.assertEqual(api.writes[1][2], {'name': 'main', 'type': 'branch'})
        self.assertTrue(any(step.startswith('Environment validate: hold exactly the secrets none') for step in hand), hand)
        # No environment at all: every key is drift, apply creates publish with its policy and
        # validate without one, and the secret is a hand step.
        std, responses = ideal('mitsevox/n100f')
        responses['/repos/mitsevox/n100f/environments'] = (200, {'total_count': 0, 'environments': []})
        api = FakeApi(responses)
        found = repo_settings.current(api, 'mitsevox/n100f', std)
        drift = repo_settings.diff(wanted, found)
        self.assertIn('environments.publish.exists', {k for k, _, _ in drift})
        hand = repo_settings.apply(api, 'mitsevox/n100f', std, drift, found)
        self.assertEqual([(m, p) for m, p, _ in api.writes], [
            ('PUT', '/repos/mitsevox/n100f/environments/publish'),
            ('POST', '/repos/mitsevox/n100f/environments/publish/deployment-branch-policies'),
            ('PUT', '/repos/mitsevox/n100f/environments/validate')])
        self.assertEqual(api.writes[2][2], {'deployment_branch_policy': None})
        self.assertTrue(any('Environment publish: hold exactly the secrets DATA_APP_PRIVATE_KEY' in step for step in hand), hand)

    def test_tag_policies_and_extra_branch_policies_are_removed(self):
        # A tag policy on publish would let any contributor's tag push reach the key; an extra
        # branch policy widens it. Both drift and apply deletes them, keeping main.
        std, responses = ideal('mitsevox/n100f')
        responses['/repos/mitsevox/n100f/environments/publish/deployment-branch-policies'] = (200, {'branch_policies': [
            {'id': 1, 'name': 'main', 'type': 'branch'}, {'id': 2, 'name': '*', 'type': 'tag'},
            {'id': 3, 'name': 'release/*', 'type': 'branch'}]})
        api = FakeApi(responses)
        found = repo_settings.current(api, 'mitsevox/n100f', std)
        self.assertEqual(found['environments.publish.branches'], ['main', 'release/*', 'tag:*'])
        drift = repo_settings.diff(repo_settings.expected(std), found)
        self.assertEqual({k for k, _, _ in drift}, {'environments.publish.branches'})
        repo_settings.apply(api, 'mitsevox/n100f', std, drift, found)
        self.assertEqual([(m, p) for m, p, _ in api.writes], [
            ('PUT', '/repos/mitsevox/n100f/environments/publish'),
            ('DELETE', '/repos/mitsevox/n100f/environments/publish/deployment-branch-policies/2'),
            ('DELETE', '/repos/mitsevox/n100f/environments/publish/deployment-branch-policies/3')])

    def test_a_main_ruleset_holding_only_update_is_never_the_merges_ruleset(self):
        # One ruleset named `main` whose only rule is `update`, no `merges`: both standard rulesets
        # must not resolve to it, or apply would write the merges body over the main body.
        std, responses = ideal('mitsevox/n100f')
        responses['/repos/mitsevox/n100f/rulesets'] = (200, [{'id': 7, 'name': 'main'}])
        responses['/repos/mitsevox/n100f/rulesets/7'][1]['rules'] = [{'type': 'update'}]
        api = FakeApi(responses)
        found = repo_settings.current(api, 'mitsevox/n100f', std)
        self.assertEqual((found['ruleset.id'], found['merges.exists'], found['ruleset.rule.update']), (7, False, True))
        drift = repo_settings.diff(repo_settings.expected(std), found)
        keys = {k for k, _, _ in drift}
        self.assertTrue({'ruleset.rule.update', 'ruleset.rule.pull_request', 'merges.exists'} <= keys, keys)
        repo_settings.apply(api, 'mitsevox/n100f', std, drift, found)
        self.assertEqual([(m, p) for m, p, _ in api.writes],
                         [('PUT', '/repos/mitsevox/n100f/rulesets/7'), ('POST', '/repos/mitsevox/n100f/rulesets')])
        main_body, merges_body = (body for _, _, body in api.writes)
        self.assertEqual([r['type'] for r in main_body['rules']], ['deletion', 'non_fast_forward', 'pull_request', 'required_status_checks'])
        self.assertEqual((merges_body['name'], [r['type'] for r in merges_body['rules']]), ('merges', ['update']))

    def test_an_update_rule_inside_main_is_drift(self):
        # With no bypass actor on main, an update rule there would let nobody merge.
        std, responses = ideal('mitsevox/n100f')
        responses['/repos/mitsevox/n100f/rulesets/7'][1]['rules'].insert(0, {'type': 'update'})
        api = FakeApi(responses)
        found = repo_settings.current(api, 'mitsevox/n100f', std)
        drift = repo_settings.diff(repo_settings.expected(std), found)
        self.assertEqual({k for k, _, _ in drift}, {'ruleset.rule.update'})
        repo_settings.apply(api, 'mitsevox/n100f', std, drift, found)
        self.assertEqual([(m, p) for m, p, _ in api.writes], [('PUT', '/repos/mitsevox/n100f/rulesets/7')])
        self.assertNotIn('update', [r['type'] for r in api.writes[0][2]['rules']])

    def test_merges_ruleset_must_target_the_default_branch_and_hold_only_update(self):
        std, responses = ideal('mitsevox/n100f')
        responses['/repos/mitsevox/n100f/rulesets/8'][1]['conditions'] = {'ref_name': {'include': ['refs/heads/release'], 'exclude': []}}
        drift = repo_settings.diff(repo_settings.expected(std), repo_settings.current(FakeApi(responses), 'mitsevox/n100f', std))
        self.assertEqual({k for k, _, _ in drift}, {'merges.targets_default'})
        std, responses = ideal('mitsevox/n100f')
        responses['/repos/mitsevox/n100f/rulesets/8'][1]['rules'] = [{'type': 'update'}, {'type': 'deletion'}]
        api = FakeApi(responses)
        found = repo_settings.current(api, 'mitsevox/n100f', std)
        drift = repo_settings.diff(repo_settings.expected(std), found)
        self.assertEqual({k for k, _, _ in drift}, {'merges.rule.update'})
        repo_settings.apply(api, 'mitsevox/n100f', std, drift, found)
        self.assertEqual([(m, p) for m, p, _ in api.writes], [('PUT', '/repos/mitsevox/n100f/rulesets/8')])
        body = api.writes[0][2]
        self.assertEqual(([r['type'] for r in body['rules']], body['conditions']['ref_name']['include']), (['update'], ['~DEFAULT_BRANCH']))

    def test_build_repositories_hold_no_ruleset(self):
        std, responses = ideal('mitsevox/n100f-build')
        self.assertNotIn('ruleset.exists', repo_settings.expected(std))
        del responses['/repos/mitsevox/n100f-build/rulesets']
        api = FakeApi(responses)
        found = repo_settings.current(api, 'mitsevox/n100f-build', std)
        self.assertEqual(repo_settings.diff(repo_settings.expected(std), found), [])
        self.assertEqual(api.writes, [])


if __name__ == '__main__':
    unittest.main()
