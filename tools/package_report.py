#!/usr/bin/env python3
"""Package validated producer output into report-v1; does not build the game."""
import argparse
from pathlib import Path
import shutil
import tempfile

from reporting.validation import decode, digest, encoded, require, schema
from reporting.standard import asset_schema, validate_package
from reporting.registry import SLUG

INPUTS={'map':'map.json','timeline':'timeline.json','contributors':'contributors.json'}


def package(source,metadata,policy,output):
    source,output=Path(source),Path(output)
    require(not output.exists(),'Package output must be new')
    require(SLUG.fullmatch(metadata['project']),'Invalid project slug')
    version=policy.get('schemaVersion')
    require(type(version) is int and version in (1,2),'Unsupported producer version')
    schema(policy,'producer-v'+str(version)+'.schema.json')
    require(metadata['repository']==policy['repository'] and metadata['target']==policy['target'],'Producer identity differs')
    allowed={'summary.json',*INPUTS.values()}
    require({p.name for p in source.iterdir()}<=allowed and (source/'summary.json').exists()
            and all(p.is_file() and not p.is_symlink() for p in source.iterdir()),'Unsafe or unknown producer inputs')
    payloads={p.name:p.read_bytes() for p in source.iterdir()}
    summary=decode(payloads['summary.json'])
    assets={key:({'status':'supported','asset':{'path':name,'schema':asset_schema(key,decode(payloads[name])),'sha256':digest(payloads[name])}}
                 if name in payloads else {'status':'unsupported','reason':'Not supplied by this producer.'})
            for key,name in INPUTS.items()}
    identity={k:metadata[k] for k in ('repository','target','revision','tree','methodology','generation','measuredAt','publishedAt')}
    receipt={'schemaVersion':version,**identity,'mode':metadata.get('mode','full'),'source':metadata.get('source'),**{k:metadata[k] for k in ('runId','attempt','workflowBlob')},
             'files':{name:digest(raw) for name,raw in payloads.items()}}
    payloads['receipt.json']=encoded(receipt)
    manifest={'schemaVersion':version,'origin':'measured','project':metadata['project'],**identity,'tools':metadata['tools'],
              'validation':{'mode':receipt['mode'],'runId':metadata['runId'],'attempt':metadata['attempt'],
                            'workflowRevision':metadata['revision'],
                            'receipt':{'path':'receipt.json','schema':'execution-v'+str(version),'sha256':digest(payloads['receipt.json'])}},
              'summary':summary,'modules':assets}
    schema(manifest,'report-v'+str(version)+'.schema.json');payloads['manifest.json']=encoded(manifest)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.report-',dir=output.parent) as temp:
        stage=Path(temp)
        for name,raw in payloads.items():(stage/name).write_bytes(raw)
        validate_package(stage,manifest,policy)
        shutil.copytree(stage,output)
    return manifest,payloads


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--metadata',type=Path,required=True)
    parser.add_argument('--policy',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    package(args.input,decode(args.metadata.read_bytes()),decode(args.policy.read_bytes()),args.output)
    print('Validated report-v1 package:',args.output)
