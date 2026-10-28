// Exercises the clearance script in .github/workflows/review.yml without GitHub.
// Run from the repository root: node --test tests/review_gate.mjs
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import test from 'node:test';

const workflow = readFileSync(new URL('../.github/workflows/review.yml', import.meta.url), 'utf8');
const script = workflow.split('          script: |\n')[1].split('\n').map(line => line.slice(12)).join('\n');
const execute = new (Object.getPrototypeOf(async function () {}).constructor)('github', 'context', 'process', script);
// PARAMETER: the owner login and repository, as in REVIEW_OWNER and the PR URLs.
const owner = 'OWNER_LOGIN', repository = 'owner/game';
const sha = 'a'.repeat(40);
const prefix = `https://github.com/${repository}/pull/1#issuecomment-`;

async function check(change = {}) {
  const pr = { state: 'open', draft: false, html_url: prefix.split('#')[0],
    head: { sha, repo: { full_name: repository } },
    base: { repo: { full_name: repository } } };
  const clearance = { id: 3, user: { login: owner }, updated_at: '2026-10-01T00:00:00Z',
    html_url: prefix + '3', body: `<!-- owner-review-clearance -->\nRevision: ${sha}\nAccuracy: ${prefix}1\nHostile: ${prefix}2` };
  const records = {
    1: { issue_url: `https://api.github.com/repos/${repository}/issues/1`, body: `Revision: ${sha}\nAccuracy: PASS` },
    2: { issue_url: `https://api.github.com/repos/${repository}/issues/1`, body: `Revision: ${sha}\nHostile: SHIP` }
  };
  const comments = [clearance];
  change.mutate?.({ pr, clearance, records, comments });
  const statuses = [];
  const github = { paginate: async () => comments, rest: {
    pulls: { get: async () => ({ data: pr }) },
    issues: { listComments() {}, getComment: async ({ comment_id }) => {
      if (!records[comment_id]) throw new Error('Record missing');
      return { data: records[comment_id] };
    } },
    repos: { createCommitStatus: async status => statuses.push(status) }
  } };
  const [repoOwner, repoName] = repository.split('/');
  try {
    await execute(github, { repo: { owner: repoOwner, repo: repoName },
      payload: { pull_request: { number: 1 } } }, { env: { REVIEW_OWNER: owner } });
  } catch (error) {
    if (!change.error) throw error;
  }
  return statuses.at(-1)?.state;
}

test('current owner clearance with two current passing records succeeds', async () => {
  assert.equal(await check(), 'success');
});
for (const [name, mutate] of [
  ['another actor cannot clear', ({ clearance }) => { clearance.user.login = 'contributor'; }],
  ['new head invalidates old clearance', ({ pr }) => { pr.head.sha = 'b'.repeat(40); }],
  ['draft remains pending', ({ pr }) => { pr.draft = true; }],
  ['same record cannot cover both lanes', ({ clearance }) => { clearance.body = clearance.body.replace(prefix + '2', prefix + '1'); }],
  ['wrong PR record fails', ({ records }) => { records[1].issue_url = records[1].issue_url.replace('/issues/1', '/issues/2'); }],
  ['hostile failure fails', ({ records }) => { records[2].body = records[2].body.replace('SHIP', 'FIX'); }],
  ['edited stale review fails', ({ records }) => { records[1].body = records[1].body.replace(sha, 'b'.repeat(40)); }],
  ['latest owner withdrawal supersedes clearance', ({ comments }) => { comments.push({ id: 4, user: { login: owner }, updated_at: '2026-10-02T00:00:00Z', body: '<!-- owner-review-clearance -->\nWithdrawn' }); }],
]) {
  test(name, async () => assert.equal(await check({ mutate }), 'pending'));
}
test('missing evidence leaves a previous success invalidated', async () => {
  assert.equal(await check({ mutate: ({ records }) => { delete records[2]; }, error: true }), 'pending');
});
test('justified accuracy N/A record is allowed for owner evaluation', async () => {
  assert.equal(await check({ mutate: ({ records }) => { records[1].body = records[1].body.replace('PASS', 'N/A - documentation only'); } }), 'success');
});
test('foreign contribution is never given clearance', async () => {
  assert.equal(await check({ mutate: ({ pr }) => { pr.head.repo.full_name = 'other/game'; } }), undefined);
});
for (const [name, mutate] of [
  ['later hostile FIX cannot coexist with SHIP', ({ records }) => { records[2].body += '\nHostile: FIX - unresolved defect'; }],
  ['historical SHA cannot substitute for declared revision', ({ records }) => { records[1].body = `Revision: ${'b'.repeat(40)}\nAccuracy: PASS\nPrevious revision: ${sha}`; }],
  ['unexplained N/A fails', ({ records }) => { records[1].body = `Revision: ${sha}\nAccuracy: N/A`; }],
  ['blank N/A explanation fails', ({ records }) => { records[1].body = `Revision: ${sha}\nAccuracy: N/A -   `; }],
  ['quoted example cannot supply review headers', ({ records }) => { records[2].body = 'Example only:\n```text\n' + records[2].body + '\n```'; }],
  ['duplicate owner revision invalidates clearance', ({ clearance }) => { clearance.body += `\nRevision: ${'b'.repeat(40)}`; }],
  ['conflicting accuracy verdict invalidates clearance', ({ records }) => { records[1].body += '\nAccuracy: FAIL'; }],
]) {
  test(name, async () => assert.equal(await check({ mutate }), 'pending'));
}
