"""Archived Pages parsing and recorded NFL workflow validation."""
import io
import tarfile
from ..validation import require, timestamp
from ..github import MAX_EXPANDED, zip_members

def pages_reports(raw):
    members = zip_members(raw)
    require(set(members) == {'artifact.tar'}, 'Unexpected Pages archive')
    result = {}
    with tarfile.open(fileobj=io.BytesIO(members['artifact.tar']), mode='r:') as tar:
        total = 0
        seen = set()
        for member in tar:
            total += member.size
            require(total <= MAX_EXPANDED and len(seen) < 1000, 'Pages archive expands beyond limit')
            require(member.isfile() or member.isdir(), 'Links or special entries in Pages archive')
            name = member.name.removeprefix('./')
            require(name not in seen, 'Duplicate Pages entry')
            seen.add(name)
            if name in ('progress.json', 'activity.json'):
                require(member.isfile(), 'Report is not a file')
                result[name] = tar.extractfile(member).read()
    require(set(result) == {'progress.json', 'activity.json'}, 'Missing Pages reports')
    return result


COMMON_STEPS = (
    'Verify publication handoff rules',
    'Decide required validation lanes', 'Upload decomp.dev report',
    'Prepare verified publication history', 'Preserve verified publication history',
    'Run actions/upload-pages-artifact@98ef48e41587a300b82de4cf298aa98b57b2faae',
)
FULL_STEPS = (
    'Verify review clearance logic', 'Prepare pinned compiler stages',
    'Verify source build against complete target', 'Verify provisional function inventory',
    'Verify compiler stages', 'Verify inventory cache invalidation and real warm reuse',
    'Measure exact and fuzzy source comparisons',
    'Verify both progress exports, maps, history and contributor credits',
    'Verify activity and live receipts on the host',
)
REUSE_STEP = 'Publish authenticated final-integration reports'
SELECTION_STEP = 'Select verified final-integration reports'


def authenticate_run(policy, run, jobs, workflow_blob):
    require(run['repository']['full_name'] == policy['repository']
            and run['head_repository']['full_name'] == policy['repository']
            and run['path'] == policy['workflow'] and run['head_branch'] == 'main'
            and run['event'] in ('push', 'workflow_dispatch') and run['status'] == 'completed'
            and run['conclusion'] == 'success', 'Run is not successful trusted main publication')
    require(workflow_blob in policy['workflowBlobs'], 'Producer workflow changed; review its trust policy first')
    baseline = [j for j in jobs if j['name'] == 'Toolchain baseline']
    require(len(baseline) == 1 and baseline[0]['conclusion'] == 'success'
            and baseline[0]['run_attempt'] == run['run_attempt']
            and baseline[0]['head_sha'] == run['head_sha'], 'Wrong baseline job/attempt')
    job = baseline[0]
    steps = job['steps']
    def succeeded(name):
        return sum(s['name'] == name and s['conclusion'] == 'success' for s in steps) == 1
    require(all(succeeded(n) for n in COMMON_STEPS), 'Missing publication validation steps')
    reused = succeeded(REUSE_STEP)
    full = all(succeeded(n) for n in FULL_STEPS)
    require(reused != full, 'Ambiguous or incomplete validation lane')
    # Approved workflow code skips selection only for explicit main audit dispatches.
    # The run/job API provides the actual event and step outcome; report JSON cannot
    # substitute a missing/failed selection or a partial full-validation lane.
    audit = (run['event'] == 'workflow_dispatch' and full
             and sum(s['name'] == SELECTION_STEP and s['conclusion'] == 'skipped'
                     for s in steps) == 1
             and sum(s['name'] == SELECTION_STEP for s in steps) == 1)
    require(succeeded(SELECTION_STEP) or audit, 'Missing publication selection or full audit')
    return ('reused' if reused else 'full'), job


