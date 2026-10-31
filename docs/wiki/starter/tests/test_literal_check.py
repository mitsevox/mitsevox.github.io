"""Comparing an exact function's relocations by address and by value (tools/literal_check.py)."""
import struct
import tempfile
from pathlib import Path
import unittest

import contextlib
import io
import json
import sys
from unittest import mock

from tools import literal_check
from tools.literal_check import Dol,Elf,Symbols,Unit,original,read_splits,stem

LFS_F1=0xC0200000;LFS_F0=0xC0000000;FCMPU=0xFC010000;BLR=0x4E800020;BL=0x48000001
SDA21=109;REL24=10


def elf(path,sections,symbols,relocs):
    """Write a big-endian ELF32 relocatable object. sections: [(name, type, bytes or size)];
    symbols: [(name, value, size, bind, type, section index)]; relocs: {section index:
    [(offset, type, symbol index, addend)]}. Symbol 0 is the null symbol."""
    names=[b'']+[n.encode() for n,_,_ in sections]+[b'.symtab',b'.strtab',b'.shstrtab']
    names+=[b'.rela'+sections[i-1][0].encode() for i in relocs]
    shstr=b'\0';shname={}
    for n in names:
        shname[n]=len(shstr);shstr+=n+b'\0'
    strtab=b'\0';symtab=b'\0'*16
    for n,value,size,bind,typ,shndx in symbols:
        symtab+=struct.pack('>IIIBBH',len(strtab),value,size,bind<<4|typ,0,shndx);strtab+=n.encode()+b'\0'
    body=b'';headers=[b'\0'*40];off=52
    def add(name,typ,data,link=0,info=0,entsize=0,size=None):
        nonlocal body,off
        headers.append(struct.pack('>10I',shname[name],typ,0,0,off,len(data) if size is None else size,link,info,4,entsize))
        body+=data;off+=len(data)
    for n,typ,data in sections:
        if typ==8:
            add(n.encode(),8,b'',size=data)
        else:
            add(n.encode(),1,data)
    symindex=len(headers)
    add(b'.symtab',2,symtab,link=symindex+1,entsize=16)
    add(b'.strtab',3,strtab)
    add(b'.shstrtab',3,shstr)
    for i,rows in relocs.items():
        add(b'.rela'+sections[i-1][0].encode(),4,b''.join(struct.pack('>IIi',o,s<<8|t,a) for o,t,s,a in rows),
            link=symindex,info=i,entsize=12)
    head=b'\x7fELF\x01\x02\x01'+b'\0'*9+struct.pack('>HHIIIIIHHHHHH',1,20,1,0,0,off,0,52,0,0,40,len(headers),
                                                      symindex+2)
    Path(path).write_bytes(head+body+b''.join(headers))


def dol(path,segments):
    """A DOL with the given (address, bytes) data segments."""
    offs=[0]*18;addrs=[0]*18;sizes=[0]*18;data=b'';off=0x100
    for i,(addr,content) in enumerate(segments):
        offs[7+i]=off;addrs[7+i]=addr;sizes[7+i]=len(content);data+=content;off+=len(content)
    head=struct.pack('>18I18I18I',*offs,*addrs,*sizes)
    Path(path).write_bytes(head+b'\0'*(0x100-len(head))+data)


def code(*words):
    return b''.join(struct.pack('>I',w) for w in words)


class Check(unittest.TestCase):
    """A function loading a timer and the literal 0.0f; the original reaches 0x80300004 (0.0f)
    first and the timer at 0x80300100 second."""
    def setUp(self):
        self.dir=Path(tempfile.mkdtemp())
        dol(self.dir/'main.dol',[(0x80300000,struct.pack('>ff',1.5,0.0))])
        (self.dir/'symbols.txt').write_text(
            'Check = .text:0x80010000; // type:function size:0x10\n'
            'timer = .sbss:0x80300100; // type:object size:0x4\n'
            'lbl_80300004 = .sdata2:0x80300004; // type:object size:0x4 data:float\n')
        target=[('.text',1,code(LFS_F1,LFS_F0,FCMPU,BLR)),('.sdata2',1,struct.pack('>ff',1.5,0.0))]
        elf(self.dir/'target.o',target,
            [('Check',0,16,1,2,1),('lbl_80300000',0,4,0,1,2),('lbl_80300004',4,4,0,1,2),('timer',0,0,1,1,0)],
            {1:[(0,SDA21,3,0),(4,SDA21,4,0)]})
        self.symbols=Symbols(self.dir/'symbols.txt');self.dol=Dol(self.dir/'main.dol')

    def base(self,literal,first):
        """The compiled function; first names which symbol the first load reaches."""
        path=self.dir/'base.o'
        rows=[(0,SDA21,2,0),(4,SDA21,3,0)] if first=='literal' else [(0,SDA21,3,0),(4,SDA21,2,0)]
        elf(path,[('.text',1,code(LFS_F1,LFS_F0,FCMPU,BLR)),('.sdata2',1,struct.pack('>f',literal))],
            [('Check',0,16,1,2,1),('@12',0,4,0,1,2),('timer',0,0,1,1,0)],{1:rows})
        return Elf(path)

    def compare(self,base):
        return Unit(base,Elf(self.dir/'target.o'),self.symbols,self.dol,{},None).compare('Check')

    def test_same_value_and_order_agree(self):
        self.assertEqual(self.compare(self.base(0.0,'literal')),[])

    def test_a_literal_one_bit_off_disagrees(self):
        findings=self.compare(self.base(struct.unpack('>f',struct.pack('>I',1))[0],'literal'))
        self.assertEqual(len(findings),1)
        self.assertIn('+0x0: loads 0x00000001',findings[0])

    def test_swapped_loads_disagree(self):
        findings=self.compare(self.base(0.0,'timer'))
        self.assertEqual(len(findings),2)
        self.assertIn('refers to timer+0x0; target reaches lbl_80300004',findings[0])

    def test_different_code_is_not_exact(self):
        path=self.dir/'other.o'
        elf(path,[('.text',1,code(LFS_F0,LFS_F1,FCMPU,BLR)),('.sdata2',1,struct.pack('>f',0.0))],
            [('Check',0,16,1,2,1),('@12',0,4,0,1,2),('timer',0,0,1,1,0)],{1:[(0,SDA21,2,0),(4,SDA21,3,0)]})
        self.assertIsNone(self.compare(Elf(path)))


class Branches(unittest.TestCase):
    def test_a_local_branch_relocation_must_reach_the_encoded_offset(self):
        tmp=Path(tempfile.mkdtemp())
        dol(tmp/'main.dol',[(0x80300000,b'\0'*4)])
        (tmp/'symbols.txt').write_text('A = .text:0x80010000; // type:function size:0x8\n')
        elf(tmp/'target.o',[('.text',1,code(BL|8,BLR,BLR))],[('A',0,8,1,2,1),('B',8,4,0,2,1)],{})
        for addend,exact in ((8,True),(4,False)):
            elf(tmp/'base.o',[('.text',1,code(BL,BLR,BLR))],[('A',0,8,1,2,1),('',0,0,0,3,1)],
                {1:[(0,REL24,2,addend)]})
            result=Unit(Elf(tmp/'base.o'),Elf(tmp/'target.o'),Symbols(tmp/'symbols.txt'),
                        Dol(tmp/'main.dol'),{},None).compare('A')
            self.assertEqual(result is not None,exact)


class Names(unittest.TestCase):
    def test_stem_drops_numbering_and_address_suffixes(self):
        self.assertEqual(stem('init$349'),'init')
        self.assertEqual(stem('vectorModule_8025F7B8'),'vectorModule')
        self.assertEqual(stem('surfSlickTimer'),'surfSlickTimer')

    def test_splits_give_each_units_section_starts(self):
        tmp=Path(tempfile.mkdtemp())/'splits.txt'
        tmp.write_text('Sections:\n\t.text       type:code align:4\n\ngame/unit.cpp:\n'
                       '\t.text       start:0x80005C74 end:0x80006CC4\n'
                       '\t.sdata2     start:0x8025F8C8 end:0x8025F900\n')
        self.assertEqual(read_splits(tmp),{'game/unit':{'.text':0x80005C74,'.sdata2':0x8025F8C8}})


class Repository(unittest.TestCase):
    """main() on a small checkout: the kit's paths, the original named in config.yml, and REL
    module units left out."""
    def setUp(self):
        root=self.root=Path(tempfile.mkdtemp())
        cfg=root/'config/GAME01-rev0';cfg.mkdir(parents=True)
        build=root/'build/GAME01-rev0';build.mkdir(parents=True)
        (root/'disc').mkdir()
        (cfg/'config.yml').write_text('object: disc/main.dol # the original\nhash: 0\n')
        dol(root/'disc/main.dol',[(0x80300000,struct.pack('>ff',1.5,0.0))])
        (cfg/'symbols.txt').write_text('Check = .text:0x80010000; // type:function size:0x10\n'
                                       'lbl_80300004 = .sdata2:0x80300004; // type:object size:0x4 data:float\n')
        (cfg/'splits.txt').write_text('Sections:\n\t.text       type:code align:4\n\ngame/unit.cpp:\n'
                                      '\t.text       start:0x80010000 end:0x80010010\n'
                                      '\t.sdata2     start:0x80300004 end:0x80300008\n')
        text=code(LFS_F0,BLR,BLR,BLR)
        elf(build/'target.o',[('.text',1,text),('.sdata2',1,struct.pack('>f',0.0))],
            [('Check',0,16,1,2,1),('lbl_80300004',0,4,0,1,2)],{1:[(0,SDA21,2,0)]})
        self.build=build;self.text=text

    def base(self,literal):
        elf(self.build/'base.o',[('.text',1,self.text),('.sdata2',1,struct.pack('>f',literal))],
            [('Check',0,16,1,2,1),('@12',0,4,0,1,2)],{1:[(0,SDA21,2,0)]})

    def run_main(self,units,*args):
        (self.build/'objdiff.json').write_text(json.dumps({'units':units}))
        (self.build/'config.json').write_text(json.dumps({'name':'main'}))
        with mock.patch.object(literal_check,'ROOT',self.root),\
             mock.patch.object(sys,'argv',['literal_check.py','--target','GAME01-rev0',*args]),\
             contextlib.redirect_stdout(io.StringIO()):
            return literal_check.main()

    def unit(self,name='main/game/unit'):
        return {'name':name,'target_path':'build/GAME01-rev0/target.o','base_path':'build/GAME01-rev0/base.o'}

    def test_original_comes_from_config_yml(self):
        self.assertEqual(original(self.root/'config/GAME01-rev0/config.yml','GAME01-rev0'),'disc/main.dol')
        self.assertEqual(original(self.root/'missing.yml','GAME01-rev0'),'orig/GAME01-rev0/sys/main.dol')

    def test_right_value_passes_and_wrong_value_fails(self):
        self.base(0.0)
        self.assertEqual(self.run_main([self.unit()]),0)
        self.base(1.5)
        self.assertEqual(self.run_main([self.unit()]),1)

    def test_rel_module_units_are_skipped(self):
        self.base(1.5)
        self.assertEqual(self.run_main([self.unit('module1/game/unit')]),0)

    def test_nothing_exact_passes_unless_a_unit_was_named(self):
        self.assertEqual(self.run_main([]),0)
        self.assertEqual(self.run_main([],'--unit','main/game/unit'),1)

    def test_an_object_the_build_did_not_write_fails(self):
        self.assertEqual(self.run_main([self.unit()]),1)


if __name__=='__main__':
    unittest.main()
