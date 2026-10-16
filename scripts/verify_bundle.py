"""Verify pinned upstream bytes and explicitly recorded adaptations."""
import argparse
import hashlib
import json
from pathlib import Path


def git_blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def verify(root):
    root=Path(root).resolve()
    doc=json.loads((root/'config/source-bundle.json').read_text(encoding='utf-8'))
    errors=[]
    for item in doc['files']:
        active=root/item['destination']
        source=root/item.get('preserved_source',item['destination'])
        if not active.is_file() or not source.is_file():
            errors.append('Missing bundled asset: '+item['destination'])
            continue
        if git_blob(source.read_bytes())!=item['source_blob_sha']:
            errors.append('Upstream byte mismatch: '+str(source.relative_to(root)))
        expected=item.get('adapted_sha256')
        if expected and hashlib.sha256(active.read_bytes()).hexdigest()!=expected:
            errors.append('Unrecorded adaptation: '+item['destination'])
    for item in doc.get('personal_entries',[]):
        file=root/item['preserved_source']
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=item['source_sha256']:
            errors.append('Personal source entry mismatch: '+item['skill'])
    return errors,len(doc['files'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.parse_args()
    root=Path(__file__).resolve().parent.parent
    try: errors,count=verify(root)
    except (OSError,ValueError,KeyError) as e: errors,count=[str(e)],0
    for e in errors: print('FAIL: '+e)
    if not errors: print(f'PASS: {count} pinned upstream assets and personal entry snapshots')
    return int(bool(errors))


if __name__=='__main__':
    raise SystemExit(main())
