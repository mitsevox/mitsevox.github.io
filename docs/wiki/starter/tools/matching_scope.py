#!/usr/bin/env python3
"""The scope of every Matching declaration in configure.py: the targets a unit is declared to link
on. `Object(Matching, ...)` claims every active target, including one activated later, and a target
that has not yet linked a unit byte-identically must not inherit that claim.

    python3 tools/matching_scope.py show                 one line per unit: all, none, or the targets
    python3 tools/matching_scope.py pin <id> [<id>...]   before a new target is activated: rewrite
                                                         every unconditional Matching to MatchingFor(<ids>)

`pin` names the targets that have proven the units so far (every target active before the new one).
It changes nothing for those targets: MatchingFor(<ids>) is true exactly where Matching was, so
configure.py generates the same build for each of them, which `python3 configure.py --version <id>`
and a comparison of build/<id>/build.ninja and build/<id>/objdiff.json before and after shows. For
the new target every unit is then NonMatching until it is proven. NonMatching, Equivalent and
existing MatchingFor declarations are left alone. A use of the identifier Matching anywhere but in
`Object(Matching, ...)` and its definition stops the rewrite and is listed: the tool cannot know
what such a use claims, so it is pinned by hand first."""
import argparse
from pathlib import Path
import re
import sys
try:
    from tools.targets import registry,build_targets
except ModuleNotFoundError:
    from targets import registry,build_targets

ROOT=Path(__file__).resolve().parents[1]
UNCONDITIONAL=re.compile(r'\bObject\(\s*Matching\s*,')
CONDITIONAL=re.compile(r'\bObject\(\s*MatchingFor\(([^)]*)\)\s*,')
UNLINKED=re.compile(r'\bObject\(\s*(NonMatching|Equivalent)\s*,')
UNIT=re.compile(r'\bObject\([^,]*,\s*"([^"]+)"')
DEFINITION=re.compile(r'^\s*Matching\s*=')
WORD=re.compile(r'\bMatching\b')  # neither NonMatching nor MatchingFor: both continue the word


def code(line):
    return line.split('#',1)[0]


def scopes(text):
    """[(line number, unit, scope)] for every Object declaration: 'all', 'none' or the target ids."""
    result=[]
    for number,line in enumerate(text.splitlines(),1):
        m=UNIT.search(code(line))
        if not m:continue
        if UNCONDITIONAL.search(code(line)):result.append((number,m.group(1),'all'))
        elif UNLINKED.search(code(line)):result.append((number,m.group(1),'none'))
        else:
            c=CONDITIONAL.search(code(line))
            if c:result.append((number,m.group(1),sorted(re.findall(r'["\']([^"\']*)["\']',c.group(1)))))
    return result


def other_uses(text):
    """Lines that use the identifier Matching other than in Object(Matching, ...) or its definition."""
    found=[]
    for number,line in enumerate(text.splitlines(),1):
        stripped=code(line)
        if DEFINITION.match(stripped) or UNCONDITIONAL.search(stripped):continue
        if WORD.search(stripped):found.append('%d: %s'%(number,line.strip()))
    return found


def pin(text,ids):
    """(new text, count): every Object(Matching, ...) becomes Object(MatchingFor(<ids>), ...)."""
    arguments=', '.join('"%s"'%i for i in ids)
    return UNCONDITIONAL.subn(lambda m:'Object(MatchingFor(%s),'%arguments,text)


def run(root,command,ids=()):
    root=Path(root);active=build_targets(registry(root/'config/targets.json'))
    path=root/'configure.py';text=path.read_text()
    if command=='show':
        return ['%s: %s'%(unit,scope if isinstance(scope,str) else ', '.join(scope)) for _,unit,scope in scopes(text)]
    if not ids:raise SystemExit('matching_scope: pin needs the targets that have proven the units')
    unknown=[i for i in ids if i not in active]
    if unknown:raise SystemExit('matching_scope: not an active target: '+', '.join(unknown))
    if 'def MatchingFor' not in text:raise SystemExit('matching_scope: configure.py defines no MatchingFor')
    uses=other_uses(text)
    if uses:raise SystemExit('matching_scope: Matching is used outside Object(Matching, ...); pin these by hand first:\n'+'\n'.join(uses))
    new,count=pin(text,ids)
    if count:path.write_text(new)
    return ['pinned %d Matching declaration(s) to MatchingFor(%s); NonMatching, Equivalent and MatchingFor declarations untouched'%(count,', '.join(ids)),
            'now run `python3 configure.py --version <id>` for each of %s and compare build/<id>/build.ninja and build/<id>/objdiff.json with the build before the rewrite: they are identical'%', '.join(ids)]


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command',choices=['show','pin']);parser.add_argument('targets',nargs='*')
    args=parser.parse_args()
    try:print('\n'.join(run(ROOT,args.command,args.targets)))
    except ValueError as error:sys.exit('matching_scope: '+str(error))
