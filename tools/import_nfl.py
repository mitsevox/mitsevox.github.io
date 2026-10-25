#!/usr/bin/env python3
"""Import one authenticated NFL main publication; never build or modify the game."""
import argparse
import math
from pathlib import Path
import re

from reporting.github import GitHub, artifact_bytes, authenticate_run, pages_reports, select_artifact, zip_members
from reporting.validation import ROOT, decode, digest, encoded, require, summary, validate_package


def asset(path, raw, name):
    return {'path':path, 'sha256':digest(raw), 'schema':name}


def authenticate_history(raw, artifact, run, p, activity):
    files = zip_members(raw)
    require(set(files) == {'activity.json', 'manifest.json'}, 'Unexpected history archive')
    manifest = decode(files['manifest.json'])
    expected = {'schema':1, 'repository':'mitsevox/nflstreet2', 'revision':run['head_sha'],
                'run':run['id'], 'attempt':run['run_attempt'], 'target_sha1':p['target_sha1'],
                'activity_sha256':digest(files['activity.json'])}
    require(manifest == expected and decode(files['activity.json']) == activity,
            'History archive differs from Pages publication')


def check_decomp(raw, p):
    files = zip_members(raw)
    require(set(files) == {'report.json'}, 'Unexpected decomp.dev archive')
    report = decode(files['report.json'])
    m = report['measures']
    def byte_count(value):
        require(type(value) is int or (isinstance(value, str) and re.fullmatch(r'0|[1-9][0-9]*', value)),
                'Invalid decomp.dev integer')
        return int(value)
    for kind in ('code', 'data'):
        require(byte_count(m['total_'+kind]) == p['measures'][kind]['total'], 'decomp.dev denominator differs')
        require(byte_count(m['matched_'+kind]) == p['measures'][kind]['matched'], 'decomp.dev exact coverage differs')
        require(byte_count(m['complete_'+kind]) == p['measures'][kind]['linked'], 'decomp.dev linked coverage differs')
    fuzzy = m.get('fuzzy_match_percent')
    require(type(fuzzy) in (int, float) and math.isfinite(fuzzy)
            and math.isclose(fuzzy, 100*p['measures']['code']['fuzzy']/p['measures']['code']['total'],
                             abs_tol=1e-5), 'decomp.dev code fuzzy coverage differs')


def import_run(api, policy, run_id):
    run = api.get(f'actions/runs/{run_id}')
    require(re.fullmatch(r'[a-f0-9]{40}', run['head_sha']), 'Invalid revision')
    revision = run['head_sha']
    jobs = api.pages(f"actions/runs/{run_id}/attempts/{run['run_attempt']}/jobs", 'jobs')
    workflow = api.get(f"contents/{policy['workflow']}?ref={revision}")
    mode, job = authenticate_run(policy, run, jobs, workflow['sha'])
    # A successful run on a removed or rewritten main branch is not eligible.
    relation = api.get(f'compare/{revision}...main')
    require(relation['status'] in ('ahead', 'identical'), 'Measured revision is not an ancestor of main')
    commit = api.get(f'git/commits/{revision}')
    artifacts = api.pages(f'actions/runs/{run_id}/artifacts', 'artifacts')
    selected = [select_artifact(artifacts, name, run, job) for name in
                ('github-pages', f"published-history-v1-{run['run_attempt']}", 'GN7E69_report')]
    archive = artifact_bytes(api, selected[0])
    payloads = pages_reports(archive)
    p, a = (decode(payloads[name]) for name in ('progress.json', 'activity.json'))
    authenticate_history(artifact_bytes(api, selected[1]), selected[1], run, p, a)
    check_decomp(artifact_bytes(api, selected[2]), p)
    measured_at = p['built_at']
    source_artifact = None
    if mode == 'reused':
        proof = p.get('verification', {})
        require(proof.get('kind') == 'workflow-artifact' and proof.get('tree') == commit['tree']['sha']
                and proof.get('environment') == policy['environment'], 'Reused report lacks matching execution proof')
        source_artifact = api.get(f"actions/artifacts/{proof['artifact']}")
        require(source_artifact['workflow_run']['id'] == proof['run'], 'Reused artifact belongs to another run')
        source_files = zip_members(artifact_bytes(api, source_artifact))
        require(set(source_files) == {'manifest.json','progress.json','compiled.json','credits.json'},
                'Unexpected originating verification archive')
        original_manifest = decode(source_files['manifest.json'])
        require(original_manifest['tree'] == commit['tree']['sha']
                and original_manifest['revision'] == proof['tested_revision']
                and original_manifest['run'] == proof['run']
                and original_manifest['environment'] == policy['environment']
                and original_manifest['files']['compiled.json'] == proof['report_sha256']
                and set(original_manifest['files']) == set(source_files)-{'manifest.json'}
                and all(digest(source_files[name]) == value for name,value in original_manifest['files'].items()),
                'Originating verification receipt differs')
        original_progress = decode(source_files['progress.json'])
        def measured_fields(document):
            return {k:v for k,v in document.items() if k not in ('revision','built_at','verification')}
        require(measured_fields(original_progress) == measured_fields(p), 'Reused measurement differs from original')
        measured_at = original_progress['built_at']
    else:
        require('verification' not in p, 'Full-build report unexpectedly claims reused proof')
    # The trusted main job already authenticates the originating PR artifact,
    # environment, source tree, comparisons and original contributor ledger.
    # Retain its receipt; do not rerun the game build in this consumer.
    receipt = {
        'schemaVersion':1, 'repository':policy['repository'], 'revision':revision,
        'tree':commit['tree']['sha'], 'workflowBlob':workflow['sha'], 'mode':mode,
        'run':{k:run[k] for k in ('id','run_attempt','path','head_sha','head_branch','event',
                                 'status','conclusion','run_started_at')},
        'job':{k:job[k] for k in ('id','run_attempt','head_sha','name','conclusion','completed_at','steps')},
        'artifacts':[{k:a[k] for k in ('id','name','digest','size_in_bytes','created_at')} for a in selected],
        'sourceVerification':p.get('verification'),
        'measuredAt':measured_at, 'publishedAt':p['built_at'],
        'sourceArtifact':({k:source_artifact[k] for k in ('id','name','digest','size_in_bytes','created_at')}
                          if source_artifact else None),
    }
    payloads['receipt.json'] = encoded(receipt)
    manifest = {
        'schemaVersion':1, 'origin':'measured', 'project':'nflstreet2', 'repository':policy['repository'],
        'target':policy['target'], 'revision':revision, 'tree':commit['tree']['sha'],
        'methodology':'nflstreet2-verified-export-v1', 'generation':1,
        'measuredAt':measured_at, 'publishedAt':p['built_at'],
        'tools':[{'name':'build-environment','identity':policy['environment']},
                 {'name':'producer-workflow','identity':workflow['sha']}],
        'validation':{'mode':mode,'runId':run_id,'attempt':run['run_attempt'],
                      'workflowRevision':revision,
                      'receipt':asset('receipt.json',payloads['receipt.json'],'nfl-execution-v1')},
        'summary':summary(p),
        'modules':{name:{'status':'supported','asset':asset(path,payloads[path],kind)} for name,path,kind in
                   [('map','progress.json','nfl-progress-v1'), ('timeline','activity.json','nfl-activity-v1'),
                    ('contributors','activity.json','nfl-activity-v1')]},
    }
    payloads['manifest.json'] = encoded(manifest)
    payloads['summary.json'] = encoded({k:p[k] for k in ('measures','built_at','revision')})
    return manifest, payloads


# Compatibility entry points; state and publication rules are shared by all producers.
from reporting.state import check_update, atomic_write, install, latest_commit
from reporting.state import accepted_package as accepted_registered_package


def accepted_package(entry,root=ROOT):
    return accepted_registered_package(root, 'nflstreet2', entry)


def refresh(root, run_id=None):
    policy = decode((root/'config/nflstreet2-producer.json').read_bytes())
    api = GitHub(policy['repository'])
    if run_id is None:
        # Only the newest successful main run is selected. A failed import must
        # surface an error, not silently replace it with an older success.
        runs = api.get('actions/workflows/baseline.yml/runs?branch=main&status=success&per_page=10')['workflow_runs']
        require(runs, 'No successful main publication available')
        run_id = runs[0]['id']
    current_run = api.get(f'actions/runs/{run_id}')
    lock_path = root/'data/reports.lock.json'
    entry = decode(lock_path.read_bytes())['projects'].get('nflstreet2') if lock_path.exists() else None
    cached = False
    if entry:
        path = root/entry['path']
        require(path.resolve().is_relative_to((root/'data/nflstreet2/snapshots').resolve()), 'Unsafe cached package path')
        require(digest((path/'manifest.json').read_bytes()) == entry['manifestSha256'], 'Cached manifest changed')
        manifest, _, _ = validate_package(path,root)
        receipt_blob=decode((path/'receipt.json').read_bytes())['workflowBlob']
        cached = (manifest['target']==policy['target'] and manifest['tools']==[
                    {'name':'build-environment','identity':policy['environment']},
                    {'name':'producer-workflow','identity':receipt_blob}]
                  and manifest['validation']['runId'] == run_id
                  and manifest['validation']['attempt'] == current_run['run_attempt']
                  and manifest['revision'] == current_run['head_sha'] and accepted_package(entry,root))
        if cached:
            receipt = decode((path/'receipt.json').read_bytes())
            jobs = api.pages(f"actions/runs/{run_id}/attempts/{current_run['run_attempt']}/jobs", 'jobs')
            authenticate_run(policy, current_run, jobs, receipt['workflowBlob'])
            require(api.get(f"compare/{manifest['revision']}...main")['status'] in ('ahead','identical'),
                    'Cached revision is no longer on main')
            payloads = {p.name:p.read_bytes() for p in path.iterdir()}
    if not cached:
        manifest, payloads = import_run(api, policy, run_id)
    # Fetch ancillary activity before moving the last-good pointer. A network
    # failure leaves all currently selected measurements and metadata intact.
    latest = latest_commit(api)
    destination = install(root, api, manifest, payloads, latest)
    print(f"Imported {manifest['revision']} from {manifest['validation']['mode']} run {run_id}: {destination}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=int, help='Explicit successful main run; cannot move latest backward')
    args = parser.parse_args()
    refresh(ROOT, args.run)
