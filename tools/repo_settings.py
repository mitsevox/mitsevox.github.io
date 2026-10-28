#!/usr/bin/env python3
"""Check or apply the repository settings standard in config/repo-standard.json.

    python3 tools/repo_settings.py --repo owner/game --check            print the drift
    python3 tools/repo_settings.py --repo owner/game --apply            set what the API can set
    python3 tools/repo_settings.py --all --check                        every listed repository

--check exits 1 when anything drifts. --apply sets repository fields, merge settings, features,
Actions permissions, token defaults, retention, the ruleset by name and the security features, then
prints the hand steps it cannot do (secrets and variables, package access, the GitHub App). Both are
idempotent. The token comes from GH_TOKEN or `gh auth token`; --check works with a fine-grained token
limited to Administration: read and Metadata: read. Standard library only."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config/repo-standard.json'
API = 'https://api.github.com'
MERGE = {'squash': ('allow_squash_merge', True, 'allow_merge_commit', False),
         'merge': ('allow_merge_commit', True, 'allow_squash_merge', False)}


def load_config(path=CONFIG):
    config = json.loads(Path(path).read_text())
    if config.get('schema') != 1 or set(config['kinds']) != {'source', 'build'}:
        raise ValueError('Invalid repository standard')
    return config


def standard(config, repo, kind=None):
    """The settings one repository must have: its kind's standard, its overrides, its own values."""
    entry = config['repositories'].get(repo, {})
    kind = kind or entry.get('kind')
    if kind not in config['kinds']:
        raise ValueError('%s: unknown repository; pass --kind source or --kind build' % repo)
    result = json.loads(json.dumps(config['kinds'][kind]))
    result.update(entry.get('overrides', {}))
    values = {'owner': repo.split('/')[0], 'repo': repo.split('/')[-1]}
    values.update({k: v for k, v in entry.items() if isinstance(v, str)})

    def fill(text):
        for key, value in values.items():
            text = text.replace('<%s>' % key, value)
        return text
    if entry:
        result['description'] = fill(result['description'])
        result['homepage'] = fill(result['homepage'])
        result['topics'] = [fill(t) for t in result['topics']]
    else:
        # An unlisted repository is held to its kind only; its presentation is its own.
        result['description'] = result['homepage'] = result['topics'] = None
    return result


# What the API shows, as flat keys, so that drift reads as one line per setting.

def expected(std):
    merge = MERGE[std['merge']]
    items = {
        'repository.default_branch': std['defaultBranch'],
        'repository.description': std['description'],
        'repository.homepage': std['homepage'],
        'repository.topics': sorted(std['topics']) if std['topics'] is not None else None,
        'repository.has_issues': std['features']['issues'],
        'repository.has_wiki': std['features']['wiki'],
        'repository.has_projects': std['features']['projects'],
        'repository.has_discussions': std['features']['discussions'],
        'repository.%s' % merge[0]: merge[1],
        'repository.%s' % merge[2]: merge[3],
        'repository.allow_rebase_merge': False,
        'repository.allow_auto_merge': False,
        'repository.delete_branch_on_merge': std['autoDeleteHeadBranches'],
        'repository.secret_scanning': std['security']['secretScanning'],
        'repository.secret_scanning_push_protection': std['security']['pushProtection'],
        'actions.allowed_actions': 'selected',
        'actions.github_owned_allowed': std['allowedActions']['githubOwned'],
        'actions.verified_allowed': std['allowedActions']['verified'],
        'actions.patterns_allowed': sorted(std['allowedActions']['patterns']),
        'actions.default_workflow_permissions': std['defaultTokenPermissions'],
        'actions.can_approve_pull_request_reviews': std['actionsApprovePullRequests'],
        'actions.retention_days': std['retentionDays'],
        'security.dependabot_alerts': std['security']['dependabotAlerts'],
        'security.private_vulnerability_reporting': std['security']['privateVulnerabilityReporting'],
        'security.dependabot_version_updates': std['security']['dependabotVersionUpdates'],
        'actions.variables': sorted(std['variables']),
        'actions.secrets': sorted(std['secrets']),
    }
    if std['forkPullRequestApproval']:
        items['actions.fork_pr_approval_policy'] = std['forkPullRequestApproval']
    rules = std['ruleset']
    items.update({
        'ruleset.exists': True,
        'ruleset.enforcement': 'active',
        'ruleset.bypass_actors': rules['bypassActors'],
        'ruleset.rule.deletion': rules['blockDeletion'],
        'ruleset.rule.non_fast_forward': rules['blockForcePush'],
        'ruleset.rule.pull_request': rules['requirePullRequest'],
        'ruleset.required_status_checks': [rules['requiredCheck']],
    })
    return items


def rules_summary(rules, prefix='ruleset'):
    """Flatten a list of rules (from a ruleset or from /rules/branches/<branch>)."""
    types = {rule['type'] for rule in rules}
    checks = [c['context'] for rule in rules if rule['type'] == 'required_status_checks'
              for c in rule.get('parameters', {}).get('required_status_checks', [])]
    return {prefix + '.rule.deletion': 'deletion' in types,
            prefix + '.rule.non_fast_forward': 'non_fast_forward' in types,
            prefix + '.rule.pull_request': 'pull_request' in types,
            prefix + '.required_status_checks': sorted(checks)}


def repository_summary(repo_json):
    """The readable half of the standard, from GET /repos/{r} alone."""
    security = repo_json.get('security_and_analysis') or {}
    current = {'repository.%s' % k: repo_json.get(k) for k in (
        'default_branch', 'description', 'homepage', 'has_issues', 'has_wiki', 'has_projects', 'has_discussions',
        'allow_squash_merge', 'allow_merge_commit', 'allow_rebase_merge', 'allow_auto_merge', 'delete_branch_on_merge')}
    current['repository.description'] = current['repository.description'] or ''
    current['repository.homepage'] = current['repository.homepage'] or ''
    current['repository.topics'] = sorted(repo_json.get('topics') or [])
    for key in ('secret_scanning', 'secret_scanning_push_protection'):
        status = (security.get(key) or {}).get('status')
        current['repository.' + key] = status == 'enabled' if status else None
    return current


def current(api, repo, std):
    """Read every setting the standard names. api(method, path, body) returns (status, json)."""
    status, repo_json = api('GET', '/repos/%s' % repo)
    if status != 200:
        raise SystemExit('%s: cannot read the repository (HTTP %s)' % (repo, status))
    found = repository_summary(repo_json)
    status, permissions = api('GET', '/repos/%s/actions/permissions' % repo)
    found['actions.allowed_actions'] = permissions.get('allowed_actions') if status == 200 else None
    status, selected = api('GET', '/repos/%s/actions/permissions/selected-actions' % repo)
    if status == 200:
        found['actions.github_owned_allowed'] = selected.get('github_owned_allowed')
        found['actions.verified_allowed'] = selected.get('verified_allowed')
        found['actions.patterns_allowed'] = sorted(selected.get('patterns_allowed') or [])
    status, workflow = api('GET', '/repos/%s/actions/permissions/workflow' % repo)
    if status == 200:
        found['actions.default_workflow_permissions'] = workflow.get('default_workflow_permissions')
        found['actions.can_approve_pull_request_reviews'] = workflow.get('can_approve_pull_request_reviews')
    status, retention = api('GET', '/repos/%s/actions/permissions/artifact-and-log-retention' % repo)
    found['actions.retention_days'] = retention.get('days') if status == 200 else None
    if std['forkPullRequestApproval']:
        status, fork = api('GET', '/repos/%s/actions/permissions/fork-pr-contributor-approval' % repo)
        found['actions.fork_pr_approval_policy'] = fork.get('approval_policy') if status == 200 else None
    status, _ = api('GET', '/repos/%s/vulnerability-alerts' % repo)
    found['security.dependabot_alerts'] = {204: True, 404: False}.get(status)
    status, pvr = api('GET', '/repos/%s/private-vulnerability-reporting' % repo)
    found['security.private_vulnerability_reporting'] = pvr.get('enabled') if status == 200 else None
    status, _ = api('GET', '/repos/%s/contents/.github/dependabot.yml' % repo)
    found['security.dependabot_version_updates'] = {200: True, 404: False}.get(status)
    status, variables = api('GET', '/repos/%s/actions/variables' % repo)
    found['actions.variables'] = sorted(v['name'] for v in variables.get('variables', [])) if status == 200 else None
    status, secrets = api('GET', '/repos/%s/actions/secrets' % repo)
    found['actions.secrets'] = sorted(s['name'] for s in secrets.get('secrets', [])) if status == 200 else None
    status, rulesets = api('GET', '/repos/%s/rulesets' % repo)
    ruleset = next((r for r in (rulesets if status == 200 else []) if r['name'] == std['ruleset']['name']), None)
    found['ruleset.exists'] = ruleset is not None
    if ruleset:
        status, detail = api('GET', '/repos/%s/rulesets/%s' % (repo, ruleset['id']))
        if status == 200:
            found['ruleset.id'] = detail['id']
            found['ruleset.enforcement'] = detail.get('enforcement')
            found['ruleset.bypass_actors'] = detail.get('bypass_actors') or []
            found.update(rules_summary(detail.get('rules', [])))
    return found


def diff(wanted, found):
    """The settings whose current value differs: (key, expected, actual). A key the token could not
    read (actual None) counts as drift so that a check never passes blind. An expected None is a
    setting the standard leaves to the repository."""
    result = []
    for key, value in wanted.items():
        if value is None:
            continue
        actual = found.get(key)
        if actual != value:
            result.append((key, value, actual))
    return result


def ruleset_body(std, default_branch):
    rules = std['ruleset']
    body = {'name': rules['name'], 'target': 'branch', 'enforcement': 'active', 'bypass_actors': rules['bypassActors'],
            'conditions': {'ref_name': {'include': ['~DEFAULT_BRANCH'], 'exclude': []}}, 'rules': []}
    if rules['blockDeletion']:
        body['rules'].append({'type': 'deletion'})
    if rules['blockForcePush']:
        body['rules'].append({'type': 'non_fast_forward'})
    if rules['requirePullRequest']:
        body['rules'].append({'type': 'pull_request', 'parameters': {
            'required_approving_review_count': 0, 'dismiss_stale_reviews_on_push': True,
            'require_code_owner_review': False, 'require_last_push_approval': False,
            'required_review_thread_resolution': False, 'allowed_merge_methods': [std['merge']]}})
    body['rules'].append({'type': 'required_status_checks', 'parameters': {
        'strict_required_status_checks_policy': False,
        'required_status_checks': [{'context': rules['requiredCheck']}]}})
    return body


def apply(api, repo, std, drift, found):
    """Set every drifted setting the API can set; return the hand steps."""
    keys = {key for key, _, _ in drift}
    merge = MERGE[std['merge']]
    patch = {}
    for key in keys:
        if key.startswith('repository.') and key not in ('repository.secret_scanning', 'repository.secret_scanning_push_protection'):
            name = key.split('.', 1)[1]
            if name == 'topics':
                api('PUT', '/repos/%s/topics' % repo, {'names': std['topics']})
            else:
                patch[name] = dict(expected(std))[key]
    patch.update({merge[0]: merge[1], merge[2]: merge[3]} if any(k.startswith('repository.allow_') for k in keys) else {})
    if {'repository.secret_scanning', 'repository.secret_scanning_push_protection'} & keys:
        patch['security_and_analysis'] = {
            'secret_scanning': {'status': 'enabled' if std['security']['secretScanning'] else 'disabled'},
            'secret_scanning_push_protection': {'status': 'enabled' if std['security']['pushProtection'] else 'disabled'}}
    if patch:
        api('PATCH', '/repos/%s' % repo, patch)
    if any(k.startswith('actions.') and k in ('actions.allowed_actions', 'actions.github_owned_allowed',
                                               'actions.verified_allowed', 'actions.patterns_allowed') for k in keys):
        api('PUT', '/repos/%s/actions/permissions' % repo, {'enabled': True, 'allowed_actions': 'selected'})
        api('PUT', '/repos/%s/actions/permissions/selected-actions' % repo, {
            'github_owned_allowed': std['allowedActions']['githubOwned'],
            'verified_allowed': std['allowedActions']['verified'],
            'patterns_allowed': std['allowedActions']['patterns']})
    if {'actions.default_workflow_permissions', 'actions.can_approve_pull_request_reviews'} & keys:
        api('PUT', '/repos/%s/actions/permissions/workflow' % repo, {
            'default_workflow_permissions': std['defaultTokenPermissions'],
            'can_approve_pull_request_reviews': std['actionsApprovePullRequests']})
    if 'actions.retention_days' in keys:
        api('PUT', '/repos/%s/actions/permissions/artifact-and-log-retention' % repo, {'days': std['retentionDays']})
    if 'actions.fork_pr_approval_policy' in keys:
        api('PUT', '/repos/%s/actions/permissions/fork-pr-contributor-approval' % repo, {'approval_policy': std['forkPullRequestApproval']})
    if 'security.dependabot_alerts' in keys:
        api('PUT' if std['security']['dependabotAlerts'] else 'DELETE', '/repos/%s/vulnerability-alerts' % repo)
    if 'security.private_vulnerability_reporting' in keys:
        api('PUT' if std['security']['privateVulnerabilityReporting'] else 'DELETE', '/repos/%s/private-vulnerability-reporting' % repo)
    if any(k.startswith('ruleset.') for k in keys):
        body = ruleset_body(std, std['defaultBranch'])
        if found.get('ruleset.id'):
            api('PUT', '/repos/%s/rulesets/%s' % (repo, found['ruleset.id']), body)
        else:
            api('POST', '/repos/%s/rulesets' % repo, body)
    hand = []
    if 'actions.variables' in keys or 'actions.secrets' in keys:
        hand.append('Set the repository variables %s and secrets %s, and delete every other one (Settings, Secrets and variables, Actions).'
                    % (', '.join(std['variables']) or 'none', ', '.join(std['secrets']) or 'none'))
    if 'security.dependabot_version_updates' in keys:
        hand.append('Remove .github/dependabot.yml; pinned actions are bumped by hand.')
    hand.append('Confirm package access: the private build image grants the source repository Read under Manage Actions access.')
    hand.append('Confirm the GitHub App that writes the data repository is installed there with Contents: read and write.')
    return hand


def github_api(token):
    def api(method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(API + path, data=data, method=method, headers={
            'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request) as response:
                text = response.read().decode()
                return response.status, (json.loads(text) if text.strip() else {})
        except urllib.error.HTTPError as error:
            if error.code in (403, 404, 409):
                return error.code, {}
            raise SystemExit('%s %s: HTTP %s %s' % (method, path, error.code, error.read().decode()[:200]))
    return api


def token_from_environment():
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if not token:
        try:
            token = subprocess.check_output(['gh', 'auth', 'token'], text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            raise SystemExit('No token: set GH_TOKEN or run gh auth login')
    return token


def report(repo, drift):
    if not drift:
        print('%s: no drift' % repo)
        return
    print('%s: %d settings drift' % (repo, len(drift)))
    for key, value, actual in drift:
        print('  %-48s expected %s, found %s' % (key, json.dumps(value), 'unreadable' if actual is None else json.dumps(actual)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--repo', action='append', default=[])
    parser.add_argument('--all', action='store_true', help='every repository listed in the config')
    parser.add_argument('--kind', choices=['source', 'build'])
    parser.add_argument('--config', default=str(CONFIG))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    config = load_config(args.config)
    repos = args.repo + (sorted(config['repositories']) if args.all else [])
    if not repos:
        parser.error('pass --repo owner/name or --all')
    api = github_api(token_from_environment())
    drifted = 0
    for repo in repos:
        std = standard(config, repo, args.kind)
        found = current(api, repo, std)
        drift = diff(expected(std), found)
        report(repo, drift)
        if args.apply and drift:
            for step in apply(api, repo, std, drift, found):
                print('  by hand: ' + step)
            drift = diff(expected(std), current(api, repo, std))
            report(repo, drift)
        drifted += bool(drift)
    return 1 if drifted else 0


if __name__ == '__main__':
    sys.exit(main())
