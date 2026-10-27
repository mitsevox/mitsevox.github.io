#!/usr/bin/env python3
"""Assemble a static site from validated locked snapshots; fixtures are never copied."""
import argparse
import fcntl
from html.parser import HTMLParser
import shutil
import tempfile
from pathlib import Path

from reporting.validation import ROOT, decode, digest, encoded, require, schema, validate_package
from reporting.targets import entries, selected, registered_catalog, canonical_target, validate_selection
from reporting.state import read_lock
from reporting.registry import SLUG, producer, registrations, snapshot_path, snapshot_directory


def copy_redirects(root,stage):
    aliases=Path(root)/'redirects'
    if not aliases.exists():return
    require(aliases.is_dir() and not aliases.is_symlink(),'Unsafe redirect directory')
    for folder in aliases.iterdir():
        require(folder.is_dir() and not folder.is_symlink() and SLUG.fullmatch(folder.name)
                and not (stage/folder.name).exists(),'Unsafe or conflicting redirect')
        require({p.name for p in folder.iterdir()}=={'index.html'}
                and (folder/'index.html').is_file() and not (folder/'index.html').is_symlink(),'Unsafe redirect file')
        shutil.copytree(folder,stage/folder.name)


def version_html_assets(source, prefix):
    """Version real tag references, preserving literal URLs inside documentation."""
    offsets, position = [], 0
    for line in source.splitlines(keepends=True):
        offsets.append(position)
        position += len(line)
    edits = []

    class References(HTMLParser):
        def handle_starttag(self, tag, attrs):
            raw = self.get_starttag_text()
            changed = raw.replace('/assets/', prefix)
            if raw != changed:
                line, column = self.getpos()
                start = offsets[line - 1] + column
                edits.append((start, start + len(raw), changed))

        handle_startendtag = handle_starttag

    References(convert_charrefs=False).feed(source)
    for start, end, changed in reversed(edits):
        source = source[:start] + changed + source[end:]
    return source


def locked_projects(root):
    lock=read_lock(root)
    configurations=decode((root/'config/projects.json').read_bytes())
    require(len({c['slug'] for c in configurations})==len(configurations),'Duplicate project configuration')
    result=[]
    for config in configurations:
        version=config.get('schemaVersion')
        require(type(version) is int and version in (1,2),'Unknown project configuration version')
        schema(config,'project-v'+str(version)+'.schema.json')
        slug=config['slug'];document=registered_catalog(root,slug)
        require((version==2)==(document is not None),'Project/producer target format differs')
        if document:require(config['targetRegistry']==registrations(root)[slug]['catalog'],'Project target registry differs')
        cover=root/config['artwork']['cover'].lstrip('/')
        require(cover.is_file() and not cover.is_symlink(),'Project cover is missing or unsafe')
        variants=[x['target']['id'] for x in document['targets']] if document else [None]
        bindings={}
        for target in variants:
            entry=selected(lock,slug,target)
            if entry is None:
                require(document and target!=document['defaultTarget'],'Enabled project lacks verified data: '+slug)
                bindings[target]={'available':False}
                continue
            directory=snapshot_directory(root,slug,entry,target)
            require(digest((directory/'manifest.json').read_bytes())==entry['manifestSha256'],'Locked manifest changed')
            manifest,_,_=validate_package(directory,root)
            require(manifest['revision']==entry['revision'] and manifest['repository']==config['repository']
                    and manifest['project']==slug,'Project configuration differs from report')
            identity=canonical_target(root,slug,manifest['target'])
            if document:require(identity['id']==target,'Target selection differs from report')
            else:require(identity['id']==config['target'] and identity['console']==config['console'],'Console/target identity differs')
            modules=dict(config['modules'])
            for key,enabled in modules.items():
                if not enabled:continue
                if key in ('functionCounts','fileCounts'):
                    counts=manifest['summary']['functions' if key=='functionCounts' else 'files']
                    supported=counts is not None and counts['exact'] is not None and counts['named'] is not None
                else:supported=manifest['modules'][key]['status']=='supported'
                # Modules are target capabilities; a new target need not produce
                # every optional module the game enables for its other targets.
                if document:modules[key]=supported
                else:require(supported,'Enabled module is unsupported: '+key)
            bindings[target]={'available':True,'target':identity['id'],'targetSha1':identity['sha1'],
                'reportBase':'/'+entry['path'],'report':manifest,'latestCommit':entry['latestCommit'],'modules':modules}
        primary=bindings[document['defaultTarget'] if document else None]
        result.append((config,primary,document,bindings))
    return result


def project_bindings(root,output,production=False):
    projects={}
    for config,primary,document,variants in locked_projects(root):
        project={**config,**primary,'preview':False,'contributionsEnabled':config['contributions']['accepting'],
                 'contributeUrl':config['contributions'].get('guideUrl')}
        if document:
            project.update(targetCatalog=document,targetReports=variants)
            commits=[item['latestCommit'] for item in variants.values() if item.get('available') and item.get('latestCommit',{}).get('date')]
            if commits:project['latestCommit']=max(commits,key=lambda commit:commit['date'])
        projects[config['slug']]=project
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text('// Generated by tools/build_site.py from validated report locks.\n'
        +'export const production = '+('true' if production else 'false')+';\n'
        +'export const reportProjects = '+encoded(projects).decode().strip()+';\n')
    return projects


def build(root, output):
    root = Path(root).resolve()
    read_lock(root)
    require(not (root/'data/.report-refresh.lock').is_symlink(),'Unsafe report lock')
    with (root/'data/.report-refresh.lock').open('a') as guard:
        fcntl.flock(guard, fcntl.LOCK_SH)
        return _build_locked(root, output)


def _build_locked(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    require(output != root and not root.is_relative_to(output), 'Unsafe build output')
    require(not output.exists(), 'Build output must be new; preserve existing artifacts')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.site-', dir=output.parent) as temp:
        stage = Path(temp)
        shutil.copytree(root/'assets', stage/'assets')
        projects = project_bindings(root, stage/'assets/report-projects.js', production=True)
        lock = read_lock(root)
        # Archive every locked producer, including one hidden from presentation.
        for slug,target,entry in entries(lock):
            producer(root,slug,target)
            directory=snapshot_directory(root,slug,entry,target)
            manifest,_,_=validate_package(directory,root)
            require(digest((directory/'manifest.json').read_bytes())==entry['manifestSha256']
                    and manifest['project']==slug and manifest['revision']==entry['revision'],'Archive lock differs')
            validate_selection(root,slug,target,entry,manifest)
            shutil.copytree(directory, stage/entry['path'])
        for slug in projects:
            # Routes do not require a hand-authored entry file per game.
            destination=stage/'games'/slug
            destination.mkdir(parents=True)
            shutil.copyfile(root/'index.html',destination/'index.html')
        (stage/'data/reports.lock.json').write_bytes(encoded(lock))
        shutil.copytree(root/'wiki', stage/'wiki')
        # Keep per-chapter Markdown and starter links available in the public wiki.
        shutil.copytree(root/'docs', stage/'docs')
        for name in ('index.html','404.html'):
            shutil.copyfile(root/name, stage/name)
        copy_redirects(root,stage)
        # One content-addressed asset directory keeps every module, stylesheet
        # and template in a release together, even across browser caches.
        fingerprints = [p.relative_to(stage).as_posix().encode()+b'\0'+p.read_bytes()
                        for p in sorted(stage.rglob('*')) if p.is_file()]
        release = digest(b'\0'.join(fingerprints))[:20]
        for path in stage.rglob('*'):
            if path.suffix in ('.html','.js','.css'):
                source=path.read_text();prefix=f'/releases/{release}/assets/'
                path.write_text(version_html_assets(source,prefix) if path.suffix=='.html'
                                else source.replace('/assets/',prefix))
        target = stage/'releases'/release
        target.mkdir(parents=True)
        shutil.move(stage/'assets', target/'assets')
        # Route shells stay at stable URLs; fetched chapters belong to the release.
        # Otherwise a browser can combine a newly loaded module with cached old prose.
        for chapter in (stage/'wiki').rglob('content.html'):
            destination = target/'wiki'/chapter.relative_to(stage/'wiki')
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(chapter, destination)
        (stage/'.nojekyll').touch()
        (stage/'site-manifest.json').write_bytes(encoded({'schemaVersion':1,'release':release,
            'projects':{slug:lock['projects'][slug] for slug in projects}}))
        shutil.copytree(stage, output)
    print('Validated static site:', output)
    return release


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/site')
    parser.add_argument('--bindings-only', action='store_true')
    args = parser.parse_args()
    if args.bindings_only:
        project_bindings(ROOT, ROOT/'assets/report-projects.js')
    else:
        build(ROOT, args.output)
