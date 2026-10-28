#!/usr/bin/env python3
"""Check one decompilation repository against the scaffold spec and the starter kit.

    scaffold_check.py --repo <checkout> [--kit <dir>] [--strict] [--github] [--settings owner/name]

The spec is docs/wiki/starter/scaffold.json and the kit is docs/wiki/starter/ in the site
repository that holds this script, so the kit, the spec and the check are always one revision.
Every finding is one line (`::warning file=<path>::<message>` with --github); the exit code is 0
unless --strict. The kit's own tools (targets, versions, evidence) run against the checkout. With
--settings and a token in GH_TOKEN, the repository settings the default token can read are compared
with config/repo-standard.json. Standard library only."""
import argparse
import fnmatch
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

SITE = Path(__file__).resolve().parents[3]
KIT = SITE / 'docs/wiki/starter'
LIMIT = 40  # findings shown per repeated category
NAME = re.compile(r'^(\s+)(?:- )?name:\s*(.+?)\s*$')
HEADING = re.compile(r'^## .+$', re.M)


def load(kit, name):
    # The kit's tools import each other by plain name (`from targets import ...`), so the loaded
    # module is registered under that name as well.
    spec = importlib.util.spec_from_file_location(name, kit / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Check:
    def __init__(self, repo, kit=KIT, spec=None):
        self.repo = Path(repo).resolve()
        self.kit = Path(kit)
        self.spec = json.loads(Path(spec or self.kit / 'scaffold.json').read_text())
        self.findings = []
        self.targets = None

    def warn(self, path, message):
        self.findings.append((str(path), message))

    def warn_many(self, path, messages, label):
        for message in messages[:LIMIT]:
            self.warn(path, message)
        if len(messages) > LIMIT:
            self.warn(path, '... %d more %s findings' % (len(messages) - LIMIT, label))

    def run(self):
        for method in (self.required, self.root, self.registry, self.per_target, self.versions, self.ci_targets,
                       self.evidence, self.byte_identical, self.outlines, self.workflow, self.forbidden,
                       self.references, self.gitignore):
            try:
                method()
            except Exception as error:  # one broken check never hides the others
                self.warn(method.__name__, 'check crashed: %r' % error)
        return self.findings

    # Paths

    def required(self):
        for path in self.spec['required']:
            if not (self.repo / path).is_file():
                self.warn(path, 'required file is missing')
        if not any((self.repo / p).is_file() for p in self.spec['buildEntry']):
            self.warn(self.spec['buildEntry'][0], 'no build entry point (%s)' % ', '.join(self.spec['buildEntry']))

    def root(self):
        allowed = set(self.spec['rootAllowlist'])
        for entry in sorted(self.repo.iterdir()):
            if entry.name not in allowed:
                self.warn(entry.name, 'not in the root allowlist; project material goes under docs/, tools/ or references/')

    def registry(self):
        try:
            self.kit_targets = load(self.kit, 'targets')
            self.targets = self.kit_targets.registry(self.repo / 'config/targets.json')
        except Exception as error:
            self.warn('config/targets.json', 'registry does not load: %s' % error)

    def per_target(self):
        if not self.targets:
            return
        dtk = (self.repo / 'configure.py').is_file() and (self.repo / 'tools/project.py').is_file()
        for target in self.targets['targets']:
            wanted = list(self.spec['perTarget']['every'])
            if target['status'] == 'active':
                wanted += self.spec['perTarget']['active'] + (self.spec['perTarget']['activeWithDtk'] if dtk else [])
            for pattern in wanted:
                path = pattern.replace('<id>', target['id'])
                if not (self.repo / path).is_file():
                    self.warn(path, 'missing for target %s (%s)' % (target['id'], target['status']))
        for problem in self.kit_targets.check(self.repo, self.targets):
            if 'differs' in problem:
                self.warn(problem.split(' ')[0], problem)

    # Content

    def versions(self):
        if not self.targets:
            return
        versions = load(self.kit, 'versions').Versions(self.repo)
        self.warn_many('src', versions.check(), 'version')

    def ci_targets(self):
        path = self.repo / 'config/ci-targets.json'
        if not path.is_file():
            return
        try:
            value = json.loads(path.read_text())
        except ValueError as error:
            return self.warn('config/ci-targets.json', 'not JSON: %s' % error)
        for key in self.spec['ciTargetsForbiddenKeys']:
            if key in value:
                self.warn('config/ci-targets.json', 'has a %r key; per-target globs are derived from the target id' % key)

    def evidence(self):
        if not self.targets:
            return
        self.warn_many('config', load(self.kit, 'evidence').check(root=self.repo), 'evidence')

    def byte_identical(self):
        for path in self.spec['byteIdentical']:
            mine, theirs = self.repo / path, self.kit / path
            if mine.is_file() and theirs.is_file() and mine.read_bytes() != theirs.read_bytes():
                self.warn(path, 'differs from the kit; copy the kit file')

    def outlines(self):
        readme = self.repo / 'README.md'
        if readme.is_file():
            found = HEADING.findall(readme.read_text())
            wanted = self.spec['readmeHeadings']
            if [h for h in found if h in wanted] != wanted:
                self.warn('README.md', 'headings must be, in order: ' + ', '.join(wanted) + '; found ' + ', '.join(found))
        contributing = self.repo / 'CONTRIBUTING.md'
        if contributing.is_file() and (self.kit / 'CONTRIBUTING.md').is_file():
            wanted = HEADING.findall((self.kit / 'CONTRIBUTING.md').read_text())
            found = HEADING.findall(contributing.read_text())
            if found != wanted:
                self.warn('CONTRIBUTING.md', 'section headings must be, in order: ' + ', '.join(wanted) + '; found ' + ', '.join(found))
        agents = self.repo / 'AGENTS.md'
        if agents.is_file() and (self.kit / 'AGENTS.md').is_file():
            header = (self.kit / 'AGENTS.md').read_text().split('## Project', 1)[0]
            text = agents.read_text()
            if not text.startswith(header):
                self.warn('AGENTS.md', 'must start with the kit header verbatim (everything before "## Project")')
            if '## Project' not in text:
                self.warn('AGENTS.md', 'has no "## Project" section')
        for path, needles in self.spec['mustContain'].items():
            if (self.repo / path).is_file():
                text = (self.repo / path).read_text()
                for needle in needles:
                    if needle not in text:
                        self.warn(path, 'must contain %r' % needle)

    def workflow(self):
        spec = self.spec['workflow']
        path = self.repo / spec['path']
        folder = self.repo / spec['workflowDirectory']
        if folder.is_dir():
            for other in sorted(folder.iterdir()):
                if other.is_file() and other != path:
                    self.warn(str(other.relative_to(self.repo)), 'a second workflow; validate.yml is the only one')
        if not path.is_file():
            return
        text = path.read_text()
        names = []
        for line in text.splitlines():
            m = NAME.match(line)
            if m:
                names.append(m.group(2).strip('"\''))
        for name in spec['jobs']:
            if name not in names:
                self.warn(spec['path'], 'job %r is missing' % name)
        for name in spec['steps']:
            if name not in names:
                self.warn(spec['path'], 'step %r is missing' % name)
        known = set(spec['jobs']) | set(spec['steps']) | set(spec['optionalSteps'])
        for name in names:
            if name not in known:
                self.warn(spec['path'], 'step or job %r is not in the skeleton; only %s may be added' % (name, ', '.join(spec['optionalSteps'])))
        for key in ('publishAction', 'scaffoldAction'):
            if 'uses: ' + spec[key] not in text:
                self.warn(spec['path'], 'does not use %s' % spec[key])
        image = re.search(r'^\s*%s:\s*(\S+)\s*$' % re.escape(spec['imageVariable']), text, re.M)
        if not image:
            self.warn(spec['path'], 'does not export %s' % spec['imageVariable'])
        elif not re.fullmatch(spec['imagePattern'], image.group(1)):
            self.warn(spec['path'], '%s is not a digest-pinned image reference' % spec['imageVariable'])
        for m in re.finditer(r'^\s*(?:container|image):\s*(\S+)\s*$', text, re.M):
            if ':main' in m.group(1) or ':latest' in m.group(1):
                self.warn(spec['path'], 'image referenced by tag %s; use the digest' % m.group(1))

    def forbidden(self):
        ids = [t['id'] for t in self.targets['targets']] if self.targets else []
        for pattern in self.spec['forbidden']:
            paths = [pattern.replace('<id>', i) for i in ids] if '<id>' in pattern else [pattern]
            for path in paths:
                if (self.repo / path).exists():
                    self.warn(path, 'must not exist; link upstream documentation instead of copying it')

    def references(self):
        folder = self.repo / 'references'
        if not folder.is_dir():
            return
        for path in sorted(folder.rglob('*')):
            if path.is_file() and path.stat().st_size > self.spec['referencesMaxBytes']:
                self.warn(str(path.relative_to(self.repo)), 'over %d bytes; references are text, regenerable by a named tool' % self.spec['referencesMaxBytes'])

    def gitignore(self):
        path = self.repo / '.gitignore'
        if not path.is_file():
            return
        lines = [l.strip().lstrip('/') for l in path.read_text().splitlines() if l.strip() and not l.startswith('#')]
        samples = {'orig/*/*': 'orig/x/main.dol', 'build/': 'build', '*.dol': 'x.dol', '*.elf': 'x.elf'}
        for wanted in self.spec['gitignore']:
            sample = samples.get(wanted, wanted)
            if not any(fnmatch.fnmatchcase(sample, line.rstrip('/')) or line == wanted for line in lines):
                self.warn('.gitignore', 'does not cover %s' % wanted)

    # Settings the default token can read

    def settings(self, repo_name, token, fetch=None):
        sys.path.insert(0, str(SITE / 'tools'))
        import repo_settings
        config = repo_settings.load_config(SITE / 'config/repo-standard.json')
        kind = config['repositories'].get(repo_name, {}).get('kind', 'source')
        std = repo_settings.standard(config, repo_name, kind)
        fetch = fetch or github_fetch(token)
        status, repo_json = fetch('/repos/%s' % repo_name)
        if status != 200:
            return self.warn('settings', 'repository settings unreadable with this token (HTTP %s)' % status)
        found = repository_readable(repo_settings, repo_json)
        status, rules = fetch('/repos/%s/rules/branches/%s' % (repo_name, std['defaultBranch']))
        if status == 200:
            found.update(repo_settings.rules_summary(rules))
        wanted = {k: v for k, v in repo_settings.expected(std).items() if k in found or k.startswith('ruleset.rule') or k == 'ruleset.required_status_checks'}
        # The branch's rules are the union of every ruleset: the `update` rule comes from the
        # merges ruleset, so it is expected exactly where the standard has one.
        wanted['ruleset.rule.update'] = bool(std.get('mergeRuleset'))
        for key, value, actual in repo_settings.diff(wanted, found):
            self.warn('settings', '%s: expected %s, found %s' % (key, json.dumps(value), 'unreadable' if actual is None else json.dumps(actual)))


def repository_readable(repo_settings, repo_json):
    found = repo_settings.repository_summary(repo_json)
    return {k: v for k, v in found.items() if not k.startswith('repository.secret_scanning')}


def github_fetch(token):
    def fetch(path):
        request = urllib.request.Request('https://api.github.com' + path, headers={
            'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.loads(response.read().decode() or 'null')
        except urllib.error.HTTPError as error:
            return error.code, None
        except (urllib.error.URLError, OSError):
            return 0, None
    return fetch


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--repo', default='.')
    parser.add_argument('--kit', default=str(KIT))
    parser.add_argument('--spec')
    parser.add_argument('--strict', action='store_true')
    parser.add_argument('--github', action='store_true', help='print ::warning:: lines')
    parser.add_argument('--settings', metavar='OWNER/NAME', help='also read the repository settings (token in GH_TOKEN)')
    args = parser.parse_args(argv)
    check = Check(args.repo, args.kit, args.spec)
    check.run()
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if args.settings and token:
        check.settings(args.settings, token)
    elif args.settings:
        print('scaffold-check: no token; settings not read')
    for path, message in check.findings:
        print('::warning file=%s::%s' % (path, message) if args.github else '%s: %s' % (path, message))
    print('scaffold-check: %d findings against the kit at %s' % (len(check.findings), check.kit))
    return 1 if args.strict and check.findings else 0


if __name__ == '__main__':
    sys.exit(main())
