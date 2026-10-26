"""Read GitHub execution metadata and archives with bounded, data-only parsing."""
import io
import subprocess
import zipfile

from .validation import decode, digest, require, timestamp

MAX_ARCHIVE = 32 * 1024 * 1024
MAX_EXPANDED = 80 * 1024 * 1024


class GitHub:
    def __init__(self, repository):
        self.repository = repository

    def raw(self, path):
        return subprocess.check_output(['gh', 'api', '--method', 'GET',
                                        f'repos/{self.repository}/{path}'], timeout=90)

    def get(self, path):
        return decode(self.raw(path))

    def pages(self, path, field=None):
        rows = []
        for page in range(1, 11):
            result = self.get(path + ('&' if '?' in path else '?') + f'per_page=100&page={page}')
            batch = result[field] if field else result
            rows.extend(batch)
            if len(batch) < 100:
                return rows
        raise ValueError('GitHub response exceeds pagination bound')


def artifact_bytes(api, artifact):
    require(not artifact['expired'] and 0 < artifact['size_in_bytes'] <= MAX_ARCHIVE, 'Artifact unavailable/oversized')
    raw = api.raw(f"actions/artifacts/{artifact['id']}/zip")
    require(len(raw) == artifact['size_in_bytes'] and len(raw) <= MAX_ARCHIVE
            and artifact['digest'] == 'sha256:' + digest(raw), 'GitHub artifact digest/size differs')
    return raw


def zip_members(raw):
    require(len(raw) <= MAX_ARCHIVE, 'Archive too large')
    with zipfile.ZipFile(io.BytesIO(raw)) as zipped:
        entries = zipped.infolist()
        require(len(entries) <= 20 and sum(e.file_size for e in entries) <= MAX_EXPANDED,
                'Archive expands beyond limit')
        require(len({e.filename for e in entries}) == len(entries), 'Duplicate archive entries')
        require(all(not e.is_dir() and ((e.external_attr >> 16) & 0o170000) in (0, 0o100000)
                    and '/' not in e.filename and '\\' not in e.filename for e in entries), 'Unsafe archive entries')
        return {e.filename:zipped.read(e) for e in entries}


def select_artifact(artifacts, name, run, job):
    matches = [a for a in artifacts if a['name'] == name and not a['expired']
               and timestamp(run['run_started_at']) <= timestamp(a['created_at']) <= timestamp(job['completed_at'])]
    require(len(matches) == 1, 'Missing or ambiguous artifact: ' + name)
    artifact = matches[0]
    require(artifact['workflow_run']['id'] == run['id']
            and artifact['workflow_run']['head_sha'] == run['head_sha'], 'Artifact from another execution')
    return artifact
