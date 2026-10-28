#!/usr/bin/env python3
"""Validate a data tree with both readers of the contract: the publish action's checker
(`publish.py check`) and the page's own map validator (assets/report-map-validation.js, run with
node, fed exactly what assets/reports.js feeds it). The site's CI runs it on a fresh clone of the
data repository, so that a validator that gets stricter cannot strand published data unnoticed; it
also takes the tree a `publish.py publish --dry-run --output <tree>` wrote.

    python3 tools/check_data_tree.py <tree>

Exit code 1 and one line per refused file when either reader refuses something."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/actions/publish'))
import publish  # noqa: E402

PAGE = r"""
import fs from 'node:fs';
import {validateMap} from './assets/report-map-validation.js';
const tree = process.argv[1];
const read = path => JSON.parse(fs.readFileSync(path));
let checked = 0;
for (const slug of read(`${tree}/index.json`).games) {
  for (const target of read(`${tree}/data/${slug}/game.json`).targets) {
    const directory = `${tree}/data/${slug}/${target.id}`;
    if (!fs.existsSync(`${directory}/latest.json`)) continue;
    const latest = read(`${directory}/latest.json`);
    if (!latest.modules || !latest.modules.map) continue;
    // What assets/reports.js hands the validator: the summary's measures, fuzzy left out when null.
    const measures = Object.fromEntries(['code', 'data'].map(kind => {
      const m = latest.summary[kind];
      return [kind, {total:m.total, linked:m.linked, matched:m.matched, ...(m.fuzzy === null ? {} : {fuzzy:m.fuzzy})}];
    }));
    try {
      validateMap(read(`${directory}/${latest.modules.map}`), measures);
      checked++;
    } catch (error) {
      console.log(`${slug}/${target.id}: the page refuses ${latest.modules.map}: ${error.message}`);
      process.exitCode = 1;
    }
  }
}
console.log(`page validator: ${checked} map(s) accepted`);
"""


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        sys.exit(__doc__)
    tree = Path(argv[0]).resolve()
    try:
        count = publish.check_tree(tree)
    except publish.ContractError as error:
        print('publish.py check refuses the tree: %s' % error)
        return 1
    print('publish.py check: %d target(s) accepted' % count)
    result = subprocess.run(['node', '--input-type=module', '-e', PAGE, str(tree)], cwd=ROOT)
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
