"""Isolated contract fixtures; never registered in production configuration."""
import copy
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from reporting.validation import ROOT, decode, encoded
from package_report import package

SLUG='contract-test'
REVISION='a'*40
POLICY={'schemaVersion':1,'repository':'mitsevox/contract-test','target':{'id':'TEST','console':'Test console','sha1':'b'*40},
        'workflow':'.github/workflows/build.yml','branch':'main','workflowBlobs':['c'*40],
        'artifact':'public-report','job':'Measure','requiredSteps':['Validate measurements'],
        'lanes':{'full':['Build complete target'],'reused':['Verify complete source proof']},
        'tools':[{'name':'test-toolchain','identity':'sha256:'+'d'*64}]}


def registered_root(root,include_real=False):
    root=Path(root)
    if not (root/'config').exists():shutil.copytree(ROOT/'config',root/'config')
    if include_real:
        lock=decode((ROOT/'data/reports.lock.json').read_bytes())
        for entry in lock['projects'].values():shutil.copytree(ROOT/entry['path'],root/entry['path'])
        (root/'data/reports.lock.json').write_bytes(encoded(lock))
    registry=decode((root/'config/producers.json').read_bytes())
    registry[SLUG]={'format':'report-v1','policy':SLUG+'-producer.json'}
    (root/'config/producers.json').write_bytes(encoded(registry))
    (root/'config'/registry[SLUG]['policy']).write_bytes(encoded(POLICY))
    return root


def report(base,timeline=False,contributors=False,map_data=False,revision=REVISION,linked=20,fuzzy=True,metadata_updates=None,joint=False):
    base=Path(base);source=base/'input';source.mkdir(parents=True)
    counts={'total':2,'exact':1,'named':1,'basis':'contract-inventory-v1'}
    summary={'code':{'totalBytes':100,'linkedBytes':linked,'matchedBytes':50,'fuzzyEquivalentBytes':70 if fuzzy else None},
             'data':{'totalBytes':10,'linkedBytes':0,'matchedBytes':0,'fuzzyEquivalentBytes':None},
             'functions':counts if contributors or map_data else None,'files':None}
    (source/'summary.json').write_bytes(encoded(summary))
    if timeline:
        doc={'schemaVersion':1,'snapshots':[{'revision':revision,'built_at':'2026-10-25T10:00:00Z',
             'code':{'total':100,'linked':linked},'data':{'total':10,'linked':0},
             'provenance':{'kind':'measured','source':'isolated test execution'}}]}
        (source/'timeline.json').write_bytes(encoded(doc))
    if contributors:
        people=[{'login':'test-author','id':123,'functions':1}]
        if joint:people.append({'login':'second-author','id':456,'functions':1})
        (source/'contributors.json').write_bytes(encoded({'schemaVersion':1,'credited_functions':1,
            'contributors':people,
            'functions':[{'id':'TEST:0x80000000:50','authors':[p['id'] for p in people]}]}))
    if map_data:
        def leaf(name,address,size,matched,link,fz=None,function=False):
            result={'name':name,'address':f'0x{address:08X}','kind':'code' if function else 'data',
                    'size':size,'linked':link,'matched':matched}
            if fz is not None:result['fuzzy']=fz
            if function:result.update(type='function',function_address=result['address'],original_size=size)
            return result
        code=[leaf('Exact',0x80000000,50,50,linked,50 if fuzzy else None,True),
              leaf('Partial',0x80000032,50,0,0,20 if fuzzy else None,True)]
        data=leaf('Data',0x80000100,10,0,0)
        doc={'schemaVersion':1,'sections':copy.deepcopy(code+[data]),'files':code+[data]}
        (source/'map.json').write_bytes(encoded(doc))
    metadata={'project':SLUG,'repository':POLICY['repository'],'target':POLICY['target'],'revision':revision,
              'tree':'e'*40,'methodology':'contract-report-v1','generation':1,'tools':POLICY['tools'],
              'measuredAt':'2026-10-25T10:00:00Z','publishedAt':'2026-10-25T10:01:00Z',
              'runId':42,'attempt':1,'workflowBlob':'c'*40}
    metadata.update(metadata_updates or {})
    return package(source,metadata,POLICY,base/'package')


def presentation(root,**enabled):
    projects=decode((Path(root)/'config/projects.json').read_bytes())
    projects.append({'schemaVersion':1,'slug':SLUG,'title':'Contract test project','console':'Test console',
        'repository':POLICY['repository'],'target':'TEST','artwork':{'cover':'/assets/covers/nflstreet2.webp','width':630,'height':908},
        'modules':{name:enabled.get(name,False) for name in ('map','functionCounts','fileCounts','timeline','contributors')},
        'contributions':{'accepting':False}})
    (Path(root)/'config/projects.json').write_bytes(encoded(projects))
