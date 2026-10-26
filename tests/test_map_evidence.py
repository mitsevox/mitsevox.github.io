"""Versioned map evidence survives packaging without changing measured identity."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from platform_fixtures import POLICY, SLUG, registered_root, report
from package_report import package
from reporting.standard import check_map, view
from reporting.validation import decode, encoded, validate_package


class MapEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=registered_root(self.base/'site')
        self.manifest,self.payloads=report(self.base/'original',map_data=True,contributors=True,joint=True)
        self.source=self.base/'original/input'
        self.metadata={**decode(self.payloads['receipt.json']),'project':SLUG,'tools':POLICY['tools']}
        self.original=decode(self.payloads['map.json']);self.serial=0

    def evidence_map(self):
        doc=copy.deepcopy(self.original);doc['schemaVersion']=2
        functions=doc['files'][:2]
        functions[0].update(source='src/game/unit.cpp',comparison_source='src/compare/unit+partial.cpp')
        group=dict(name='Geometry',type='group',kind='code',size=100,linked=20,matched=50,fuzzy=70,
                   address='0x80000000',source='src/game/unit.cpp',children=functions)
        file=dict(name='src/game/unit.cpp',type='file',kind='code',size=100,linked=20,matched=50,fuzzy=70,
                  address='0x80000000',source='src/game/unit.cpp',complete=False,boundary='provisional',
                  scope='mapped-ranges',children=[group])
        data=doc['files'][2];data.update(type='file',auto_generated=True,complete=False,scope='candidate-ranges')
        doc['files']=[file,data]
        return doc

    def pack(self,doc):
        (self.source/'map.json').write_bytes(encoded(doc));self.serial+=1
        output=self.base/f'package-{self.serial}'
        manifest,payloads=package(self.source,self.metadata,POLICY,output)
        return output,manifest,payloads

    def test_v2_evidence_round_trip_preserves_metrics_full_extent_ids_and_joint_credit(self):
        doc=self.evidence_map();output,manifest,payloads=self.pack(doc)
        checked,progress,activity=validate_package(output,self.root)
        self.assertEqual(manifest['modules']['map']['asset']['schema'],'map-v2')
        self.assertEqual(manifest['summary'],self.manifest['summary'])
        self.assertEqual(payloads['contributors.json'],self.payloads['contributors.json'])
        self.assertEqual(progress['files'],doc['files'])
        expected=check_map(self.original,view(self.manifest))
        self.assertEqual(check_map(doc,view(manifest),'map-v2'),expected)
        self.assertEqual(expected,{'TEST:0x80000000:50'})
        self.assertEqual(activity['credited_functions'],1)
        self.assertEqual(decode(payloads['map.json']),doc)

    def test_evidence_is_optional_and_old_v1_remains_strict(self):
        doc=copy.deepcopy(self.original);doc['schemaVersion']=2
        output,_,_=self.pack(doc);validate_package(output,self.root)
        output,manifest,_=self.pack(self.original);validate_package(output,self.root)
        self.assertEqual(manifest['modules']['map']['asset']['schema'],'map-v1')
        # JSON Schema treats integral numeric spellings as the same version.
        for version in (1.0,2.0):
            doc=copy.deepcopy(self.original);doc['schemaVersion']=version
            output,_,_=self.pack(doc);validate_package(output,self.root)
        doc=copy.deepcopy(self.original);doc['files'][0]['source']='src/unit.c'
        with self.assertRaises(ValueError):self.pack(doc)

    def test_each_evidence_field_requires_an_explicit_allowed_node_type(self):
        values={'source':'src/unit.c','comparison_source':'src/compare/unit.c','complete':False,
                'auto_generated':True,'boundary':'provisional','scope':'mapped-ranges'}
        allowed={'source':{'file','group','function'},'comparison_source':{'function'}}
        for field,value in values.items():
            for node_type in (None,'section','gap','file','group','function'):
                if node_type in allowed.get(field,{'file'}):continue
                with self.subTest(field=field,node_type=node_type):
                    doc=copy.deepcopy(self.original);doc['schemaVersion']=2
                    node=doc['sections'][0];node[field]=value
                    if node_type is None:node.pop('type',None)
                    else:node['type']=node_type
                    with self.assertRaises(ValueError):self.pack(doc)

    def test_nested_wrong_types_unknown_fields_bad_enums_and_booleans_fail(self):
        for field,value in [('boundary','guessed'),('scope','measured-ranges'),('auto_generated',False),
                            ('auto_generated',1),('complete',1),('complete','false'),('boundary',None),
                            ('scope',None),('evidence_typo','x')]:
            with self.subTest(field=field,value=value):
                doc=self.evidence_map();doc['files'][0][field]=value
                with self.assertRaises(ValueError):self.pack(doc)
        doc=self.evidence_map();doc['files'][0]['children'][0]['children'][0]['complete']=False
        with self.assertRaises(ValueError):self.pack(doc)
        for boundary in ('exact','provisional','open'):
            for scope in ('mapped-ranges','candidate-ranges'):
                doc=self.evidence_map();doc['files'][0].update(boundary=boundary,scope=scope,complete=True)
                output,_,_=self.pack(doc);validate_package(output,self.root)

    def test_paths_reject_traversal_urls_controls_and_noncanonical_spelling_in_both_fields(self):
        invalid=('../unit.c','/src/unit.c','src/../../unit.c','src\\unit.c','src//unit.c',
                 './src/unit.c','src/./unit.c','src/unit.c/','C:/unit.c','https://example.com/a.c',
                 'src/%2e%2e/unit.c','src/unit.c\n','src/unit.c\0','','src/a b.c',None,True)
        for field in ('source','comparison_source'):
            for path in invalid:
                with self.subTest(field=field,path=path):
                    doc=self.evidence_map();doc['files'][0]['children'][0]['children'][0][field]=path
                    with self.assertRaises(ValueError):self.pack(doc)
        doc=self.evidence_map()
        doc['files'][0]['children'][0]['children'][0].update(source='Source/SDK-v2/name_with+parts.cpp',
                                                          comparison_source='comparisons/foo.c')
        output,_,_=self.pack(doc);validate_package(output,self.root)

    def test_unknown_or_mismatched_map_versions_fail_closed(self):
        for version in (0,3,'2',True,None):
            with self.subTest(version=version):
                doc=self.evidence_map();doc['schemaVersion']=version
                with self.assertRaises(ValueError):self.pack(doc)
        for doc,identifier in ((self.evidence_map(),'map-v1'),(self.original,'map-v2'),(self.original,'map-v99')):
            output,manifest,_=self.pack(doc);manifest['modules']['map']['asset']['schema']=identifier
            (output/'manifest.json').write_bytes(encoded(manifest))
            with self.subTest(identifier=identifier),self.assertRaises(ValueError):validate_package(output,self.root)

    def test_v2_keeps_aggregation_coverage_and_full_function_extent_checks(self):
        for change in ('matched','address','extent'):
            doc=self.evidence_map();leaf=doc['files'][0]['children'][0]['children'][0]
            if change=='matched':leaf['matched']-=1
            if change=='address':leaf['address']='0x80001000';leaf['function_address']=leaf['address']
            if change=='extent':leaf['original_size']+=1
            with self.subTest(change=change),self.assertRaises(ValueError):self.pack(doc)


if __name__=='__main__':unittest.main()
