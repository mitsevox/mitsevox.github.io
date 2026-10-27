"""Check that every wiki chapter is routable and the clearance template behaves."""
import json
from pathlib import Path
import subprocess
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HandbookTests(unittest.TestCase):
    def test_every_registered_chapter_is_routable(self):
        module = (ROOT/'assets/wiki-chapters.js').read_text()
        slugs = json.loads(module.split('Object.freeze(', 1)[1].split(');', 1)[0])
        chapters = json.loads((ROOT/'docs/wiki/chapters.json').read_text())
        self.assertEqual(slugs, [chapter['slug'] for chapter in chapters])
        for slug in slugs:
            route = ROOT/'wiki' if slug == 'start-here' else ROOT/'wiki'/slug
            self.assertTrue((route/'index.html').is_file())
            self.assertTrue((route/'content.html').is_file())

    def test_clearance_template_rejects_invalid_or_deleted_evidence(self):
        template = (ROOT/'docs/wiki/starter/.github/workflows/review.yml.template').read_text()
        script = textwrap.dedent(template.split('script: |\n', 1)[1])
        node = r'''
const fs = require('fs');
const source = JSON.parse(fs.readFileSync(0, 'utf8'));
const run = new (Object.getPrototypeOf(async function(){}).constructor)('context', 'github', source);
process.env.REVIEW_OWNER = 'owner';
const sha = 'a'.repeat(40), link = id => `https://github.com/owner/game/pull/1#issuecomment-${id}`;
const record = (id, lane, verdict) => ({id, issue_url:'https://api.github.com/repos/owner/game/issues/1',
  body:`Revision: ${sha}\n${lane}: ${verdict}\n`});
const clearance = () => ({id:1,user:{login:'owner'},updated_at:'2026-01-01T00:00:00Z',
  html_url:link(1),body:`<!-- owner-review-clearance -->\nRevision: ${sha}\nAccuracy: ${link(2)}\nHostile: ${link(3)}`});
(async () => {
 for (const scenario of ['valid','absent','draft','stale','same-link','foreign-owner','deleted','failed-review','wrong-pr','withdrawn']) {
  const comments = scenario === 'absent' ? [] : [clearance()];
  if (scenario === 'stale') comments[0].body = comments[0].body.replace(sha, 'b'.repeat(40));
  if (scenario === 'same-link') comments[0].body = comments[0].body.replace(link(3), link(2));
  if (scenario === 'foreign-owner') comments[0].user.login = 'someone';
  if (scenario === 'withdrawn') comments[0].body = '<!-- owner-review-clearance -->';
  const records = {2:record(2,'Accuracy','PASS'),3:record(3,'Hostile','SHIP')};
  if (scenario === 'failed-review') records[3].body = records[3].body.replace('SHIP','FIX');
  if (scenario === 'wrong-pr') records[2].issue_url = 'https://api.github.com/repos/owner/game/issues/2';
  const states = [];
  const github = {rest:{pulls:{get:async()=>({data:{state:'open',head:{sha,repo:{full_name:'owner/game'}},
    base:{repo:{full_name:'owner/game'}},draft:scenario==='draft',html_url:link(1)}})},
    repos:{createCommitStatus:async status=>states.push(status.state)},
    issues:{listComments:()=>{},getComment:async({comment_id})=>{
      if (scenario==='deleted') throw {status:404};
      return {data:records[comment_id]};
    }}},paginate:async()=>comments};
  await run({repo:{owner:'owner',repo:'game'},payload:{pull_request:{number:1}}},github);
  if (states[0]!=='pending' || states.at(-1)!==(scenario==='valid'?'success':'pending'))
    throw new Error(`Incorrect ${scenario}: ${states}`);
 }
})().catch(error=>{console.error(error);process.exit(1)});
'''
        subprocess.run(['node', '-e', node], input=json.dumps(script), text=True, check=True, capture_output=True)


if __name__ == '__main__':
    unittest.main()
