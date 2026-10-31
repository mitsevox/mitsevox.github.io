#!/usr/bin/env python3
"""Check what each exact function's relocations point at, by address or by value.

objdiff's progress report does not compare where a relocation lands, and its viewer counts two
compiler-generated literal names as equal, so a function that loads a pool literal (an anonymous
.sdata2 or .rodata constant) scores 100% whatever value that literal holds, and whichever of two
literals or variables each load reaches. A unit that is not Matching links the original object,
so the complete executable stays byte-identical and nothing else notices.

For every function whose compiled code equals the target's with the relocated fields masked (the
functions objdiff calls exact), each relocation is compared with the target's at the same offset:

  - a compiled symbol that symbols.txt names (a global, a named static, a function) must have the
    address the target relocation reaches;
  - a compiled symbol it does not name (a pool literal, a jump table, a function's local static)
    must hold the bytes the original executable holds at that address, with the pointers inside
    it resolved through symbols.txt;
  - a compiled variable without data (.bss) must carry the target symbol's name (apart from the
    $<n> numbering suffix, which moves with the order the compiler met them), or else map to one
    target address across the unit's exact functions, and no two of them to the same one.

    python3 tools/literal_check.py --target GAME01-rev0 [--unit <name>] [--verbose]

It reads objdiff.json (build/<target id>/objdiff.json, or the repository root's for a project that
keeps dtk-template's stock paths) for the units, their compiled objects and their target objects
(the build writes both), config/<target id>/symbols.txt and splits.txt, and the original that
config/<target id>/config.yml names in `object_base` and `object`. It fails when an exact function
disagrees, when objdiff.json names an object the build did not write, when no unit belongs to the
main executable, or when it checks no function while the target's report counts some as exact. Functions that are not
exact are counted and skipped: a partial function is not a review failure, and its relocations do
not line up with the target's. Units of REL modules are skipped and counted too: the check reads
the main executable only."""
import argparse
import json
from pathlib import Path
import re
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]

R_PPC_ADDR32=1;R_PPC_ADDR16_LO=4;R_PPC_ADDR16_HA=6;R_PPC_REL24=10;R_PPC_REL14=11;R_PPC_EMB_SDA21=109
# The instruction bits each relocation type writes; the rest of the word is compiled code.
MASK={1:0xFFFFFFFF,2:0x03FFFFFC,3:0xFFFF,4:0xFFFF,5:0xFFFF,6:0xFFFF,7:0xFFFC,10:0x03FFFFFC,11:0xFFFC,
      26:0xFFFFFFFF,109:0x001FFFFF}
# Bytes a load or store reaches, by primary opcode: lwz stw lfs stfs and their update forms (4);
# lhz lha sth (2); lbz stb (1); lfd stfd psq_l psq_st (8).
WIDTH={32:4,33:4,36:4,37:4,48:4,49:4,52:4,53:4,40:2,41:2,42:2,43:2,44:2,45:2,34:1,35:1,38:1,39:1,
       50:8,51:8,54:8,55:8,56:8,57:8,60:8,61:8}
SYMBOL=re.compile(r'^(\S+) = (\.\w+):0x([0-9A-Fa-f]+);\s*//(.*)$')
ADDRESSED=re.compile(r'^(.*)_([0-9A-F]{8})$')
NUMBERED=re.compile(r'^(.*)\$\d+$')


class Elf:
    """The parts of a big-endian ELF32 relocatable object this check reads."""
    def __init__(self,path):
        data=self.data=Path(path).read_bytes()
        if data[:4]!=b'\x7fELF' or data[4]!=1 or data[5]!=2:
            raise ValueError(f'{path}: not a big-endian ELF32 object')
        shoff,=struct.unpack_from('>I',data,0x20)
        shentsize,shnum,shstrndx=struct.unpack_from('>HHH',data,0x2E)
        self.sections=[]
        for i in range(shnum):
            name,typ,_,_,off,size,link,info,_,_=struct.unpack_from('>10I',data,shoff+i*shentsize)
            self.sections.append(dict(name=name,type=typ,offset=off,size=size,link=link,info=info))
        names=self.sections[shstrndx]['offset']
        for s in self.sections:
            s['name']=self.cstr(names+s['name'])
        self.symbols=[];self.relocs={}
        for s in self.sections:
            if s['type']==2:
                strtab=self.sections[s['link']]['offset']
                for k in range(s['size']//16):
                    name,value,size,info,_,shndx=struct.unpack_from('>IIIBBH',data,s['offset']+k*16)
                    self.symbols.append(dict(name=self.cstr(strtab+name),value=value,size=size,
                                             bind=info>>4,type=info&15,shndx=shndx))
            elif s['type']==4:
                self.relocs[s['info']]=sorted(
                    (off,info&0xFF,info>>8,addend) for off,info,addend in
                    (struct.unpack_from('>IIi',data,s['offset']+k*12) for k in range(s['size']//12)))
        self.functions={s['name']:(s['shndx'],s['value'],s['size']) for s in self.symbols
                        if s['type']==2 and 0<s['shndx']<0xFF00 and s['size']}

    def cstr(self,off):
        return self.data[off:self.data.index(b'\0',off)].decode('latin-1')

    def section_bytes(self,index):
        s=self.sections[index]
        return None if s['type']==8 else self.data[s['offset']:s['offset']+s['size']]

    def symbol_at(self,shndx,offset):
        """(symbol, offset into it) for the named symbol that covers a section offset."""
        for s in self.symbols:
            if (s['shndx']==shndx and s['type'] in (1,2) and not s['name'].startswith('...')
                    and s['value']<=offset<s['value']+max(s['size'],1)):
                return s,offset-s['value']
        return None


class Dol:
    def __init__(self,path):
        data=self.data=Path(path).read_bytes()
        offs=struct.unpack_from('>18I',data,0);addrs=struct.unpack_from('>18I',data,0x48)
        sizes=struct.unpack_from('>18I',data,0x90)
        self.segments=[(a,o,s) for o,a,s in zip(offs,addrs,sizes) if s]

    def read(self,addr,size):
        for a,o,s in self.segments:
            if a<=addr and addr+size<=a+s:
                return self.data[o+addr-a:o+addr-a+size]
        return None


class Symbols:
    """symbols.txt: names to addresses and addresses to (name, size)."""
    def __init__(self,path):
        self.by_name={};self.by_address={}
        for line in Path(path).read_text().splitlines():
            m=SYMBOL.match(line)
            if not m:
                continue
            size=re.search(r'\bsize:0x([0-9A-Fa-f]+)',m.group(4))
            addr=int(m.group(3),16);size=int(size.group(1),16) if size else 0
            self.by_name.setdefault(m.group(1),[]).append(addr)
            if 'type:label' not in m.group(4):
                self.by_address.setdefault(addr,(m.group(1),size))

    def target_address(self,name):
        """The address of a target object's symbol: dtk names a symbol whose name recurs, and an
        unnamed one, with its address as a suffix."""
        m=ADDRESSED.match(name)
        if m and int(m.group(2),16) in self.by_address:
            return int(m.group(2),16)
        found=self.by_name.get(name)
        return found[0] if found and len(found)==1 else None

    def size(self,addr):
        return self.by_address.get(addr,(None,0))[1]

    def name(self,addr):
        return self.by_address.get(addr,(f'0x{addr:08X}',0))[0]


def read_splits(path):
    """{unit path without extension: {section: start address}} from splits.txt."""
    units={};unit=None
    for line in Path(path).read_text().splitlines():
        if line and not line[0].isspace() and line.endswith(':') and line!='Sections:':
            unit=units.setdefault(line[:-1].rsplit('.',1)[0],{})
        elif unit is not None and (m:=re.match(r'\s+(\.\w+)\s+start:0x([0-9A-Fa-f]+)',line)):
            unit.setdefault(m.group(1),int(m.group(2),16))
        elif not line.strip():
            unit=None
    return units


def section_bases(target,symbols,split=None):
    """Where each of a target object's sections sits in the executable, from any symbol in it whose
    address symbols.txt gives without doubt. The object's other symbols (pool literals, whose @<n>
    names recur across units) are then placed by their offset."""
    bases={}
    for sym in target.symbols:
        if 0<sym['shndx']<0xFF00 and sym['type']!=3 and sym['shndx'] not in bases:
            addr=symbols.target_address(sym['name'])
            if addr is not None:
                bases[sym['shndx']]=addr-sym['value']
    for index,section in enumerate(target.sections):
        if index not in bases and split and section['name'] in split:
            bases[index]=split[section['name']]
    return bases


def exported(targets,symbols,splits):
    """{name: address} for every global symbol the target objects define; the split makes these
    names unique, so a reference from another unit resolves through them."""
    found={}
    for name,target in targets.items():
        bases=section_bases(target,symbols,splits.get(name.split('/',1)[-1]))
        for sym in target.symbols:
            if sym['bind']!=0 and sym['shndx'] in bases:
                found[sym['name']]=bases[sym['shndx']]+sym['value']
    return found


class Unit:
    def __init__(self,base,target,symbols,dol,exports,split):
        self.base=base;self.target=target;self.symbols=symbols;self.dol=dol;self.exports=exports
        self.bases=section_bases(target,symbols,split)
        # Compiled locations without data to compare, and the target addresses they reached.
        self.places={}
        # The target object's own symbols, which settle a name that recurs elsewhere.
        self.own={sym['name']:self.bases[sym['shndx']]+sym['value'] for sym in target.symbols
                  if sym['shndx'] in self.bases and sym['type']!=3}

    def compare(self,name):
        """None when the function is not exact; else a list of findings, empty when every
        relocation agrees."""
        base=self.base;target=self.target
        bsec,boff,size=base.functions[name]
        tsec,toff,tsize=target.functions[name]
        if size!=tsize:
            return None
        bcode=base.section_bytes(bsec)[boff:boff+size];tcode=target.section_bytes(tsec)[toff:toff+size]
        brel={(o-boff)&~3:(o-boff,t,s,a) for o,t,s,a in base.relocs.get(bsec,[]) if boff<=o<boff+size}
        trel={(o-toff)&~3:(o-toff,t,s,a) for o,t,s,a in target.relocs.get(tsec,[]) if toff<=o<toff+size}
        masks={}
        for word in sorted(set(brel)|set(trel)):
            b=brel.get(word);t=trel.get(word)
            if b and t:
                if b[1]!=t[1]:
                    return None
                shift=16 if b[1] in (3,4,5,6) and b[0]&3==0 else 0
                masks[word]=MASK.get(b[1],0xFFFFFFFF)<<shift&0xFFFFFFFF
            else:
                # A branch within its own section: ProDG keeps it as a relocation, MWCC and the
                # split encode it. Both must reach the same offset from the instruction.
                elf,start,(_,typ,sym,addend)=(base,boff,b) if b else (target,toff,t)
                other=tcode if b else bcode
                sym=elf.symbols[sym]
                if typ not in (R_PPC_REL24,R_PPC_REL14) or sym['shndx']!=(bsec if b else tsec):
                    return None
                insn,=struct.unpack_from('>I',other,word)
                if typ==R_PPC_REL24:
                    disp=(insn&0x03FFFFFC)-((insn&0x02000000)<<1)
                else:
                    disp=(insn&0xFFFC)-((insn&0x8000)<<1)
                if sym['value']+addend-(start+word)!=disp:
                    return None
                masks[word]=MASK[typ]
        for i in range(0,size,4):
            b,=struct.unpack_from('>I',bcode,i);t,=struct.unpack_from('>I',tcode,i)
            if (b^t)&~masks.get(i,0)&0xFFFFFFFF:
                return None
        pairs=[(brel[w],trel[w]) for w in sorted(brel) if w in trel]
        findings=[]
        for (off,typ,bs,ba),(_,_,ts,ta) in pairs:
            self.at=(name,off&~3)
            word,=struct.unpack_from('>I',bcode,off&~3)
            finding=self.relocation(typ,base.symbols[bs],ba,target.symbols[ts],ta,word)
            if finding:
                findings.append(f'+0x{off&~3:X}: {finding}')
        return findings

    def relocation(self,typ,bsym,ba,tsym,ta,word):
        symbols=self.symbols
        if tsym['shndx'] in self.bases:
            taddr=self.bases[tsym['shndx']]+tsym['value']
        elif tsym['name'] in self.exports:
            taddr=self.exports[tsym['name']]
        else:
            taddr=symbols.target_address(tsym['name']) if tsym['type']!=3 else None
        if taddr is None:
            # Linker-made symbols (_stack_addr) and names that recur in symbols.txt without a
            # definition in reach: the names are all there is to compare, as objdiff does.
            if bsym['type']!=3 and stem(bsym['name'])==stem(tsym['name']) and ba==ta:
                return None
            return f'refers to {bsym["name"] or "(section)"}{ba:+#x}; target refers to {tsym["name"]}{ta:+#x}, which has no address'
        taddr+=ta
        there=f'target reaches {symbols.name(taddr-ta)}{ta:+#x}'
        bname=bsym['name']
        if bsym['type']==3 or bname.startswith('...'):
            bsym,ba=self.base.symbol_at(bsym['shndx'],bsym['value']+ba) or (bsym,ba)
            bname=bsym['name'] if bsym['type']!=3 and not bsym['name'].startswith('...') else None
        named=self.named(bsym,bname)
        if named:
            if taddr in (a+ba for a in named):
                return None
            return f'refers to {bname}{ba:+#x}; {there}'
        m=ADDRESSED.match(bname or '')
        if m and int(m.group(2),16)+ba==taddr:
            return f'refers to {bname}, a placeholder symbols.txt no longer has; {there}'
        code=bsym['type']==2 or self.base.sections[bsym['shndx']]['name'] in ('.text','.init') if 0<bsym['shndx']<0xFF00 else False
        data=None if code else self.compiled_data(bsym,ba)
        label=f'{bname or self.base.sections[bsym["shndx"]]["name"]}{ba:+#x}'
        if data is None:
            if not (bname and stem(bname)==stem(tsym['name'])):
                place=(bsym['shndx'],bsym['value']+ba) if 0<bsym['shndx']<0xFF00 else (bname,ba)
                self.places.setdefault(place,[]).append((taddr,label,self.at))
            return None
        value,mask=data
        n=WIDTH.get(word>>26) if typ in (R_PPC_ADDR16_LO,R_PPC_EMB_SDA21) else None
        n=min(n or symbols.size(taddr-ta)-ta or len(value),len(value))
        want=self.dol.read(taddr,n)
        if want is None:
            return f'loads {fmt(value[:n])} from {label}; {there}, which holds no data'
        diff=[i for i,(v,w,k) in enumerate(zip(value[:n],want,mask[:n])) if (v^w)&k]
        if diff and n<=8:
            return f'loads {fmt(value[:n])} from {label}; {there}, which holds {fmt(want)}'
        if diff:
            i=diff[0]&~3
            return (f'reads {n} bytes from {label}; {there}, which differs first at +0x{i:X}: '
                    f'0x{value[i:i+4].hex().upper()} against 0x{want[i:i+4].hex().upper()}')
        return None

    def uninitialized(self):
        """{(function, offset): finding} for the variables without data (.bss) whose names say
        nothing: each compiled location must reach one target address, and no two locations the
        same one, across the unit's exact functions."""
        found={};reached={}
        for place,uses in self.places.items():
            for taddr,_,_ in uses:
                reached.setdefault(taddr,set()).add(place)
        for place,uses in self.places.items():
            addresses={u[0] for u in uses}
            for taddr,label,at in uses:
                if len(addresses)>1 or len(reached[taddr])>1:
                    found[at]=(f'refers to {label}, which other loads in the unit place elsewhere; '
                               f'target reaches {self.symbols.name(taddr)} (0x{taddr:08X})')
        return found

    def named(self,bsym,name):
        """The addresses symbols.txt gives a compiled symbol's name, or None when the name says
        nothing about the address: a pool literal (@<n>), a numbered function static (name$<n>),
        or a local name that recurs."""
        if name is None or name.startswith(('@','...')) or NUMBERED.match(name):
            return None
        own=self.own.get(name)
        if own is not None:
            return [own]
        found=self.symbols.by_name.get(name)
        if bsym['bind']==0 and bsym['type']!=2 and found and len(found)>1:
            return None
        return found

    def compiled_data(self,bsym,ba):
        """(bytes, mask) from the symbol's own extent onward, with the pointers stored in it
        resolved through symbols.txt and the ones it cannot resolve masked out; None for .bss."""
        if not 0<bsym['shndx']<0xFF00:
            return None
        sec=self.base.section_bytes(bsym['shndx'])
        if sec is None:
            return None
        start=bsym['value']+ba
        end=bsym['value']+bsym['size'] if bsym['size'] and bsym['type']!=3 else len(sec)
        value=bytearray(sec[start:end]);mask=bytearray(b'\xFF'*len(value))
        for off,typ,s,a in self.base.relocs.get(bsym['shndx'],[]):
            if typ!=R_PPC_ADDR32 or not start<=off<end-3:
                continue
            sym=self.base.symbols[s];name=sym['name'];at=off-start
            if sym['type']==3 or name.startswith('...'):
                sym,a=self.base.symbol_at(sym['shndx'],sym['value']+a) or (sym,a)
                name=sym['name']
            found=self.named(sym,name)
            if found and len(found)==1:
                value[at:at+4]=struct.pack('>I',found[0]+a&0xFFFFFFFF)
            else:
                mask[at:at+4]=b'\0\0\0\0'
        return bytes(value),bytes(mask)


def stem(name):
    """A static's name without the $<n> numbering or the split's address suffix."""
    m=NUMBERED.match(name) or ADDRESSED.match(name)
    return m.group(1) if m else name


def fmt(data):
    text=data.hex().upper()
    if len(data)==4:
        return f'0x{text} ({struct.unpack(">f",data)[0]:.9g})'
    if len(data)==8:
        return f'0x{text} ({struct.unpack(">d",data)[0]:.17g})'
    return '0x'+text


def original(config_yml,target):
    """The original executable's path from config.yml (`object`, under `object_base` when it is
    set); the kit's layout when there is no config.yml."""
    keys={}
    if config_yml.is_file():
        for line in config_yml.read_text().splitlines():
            m=re.match(r'^(object_base|object):\s*["\']?([^"\'#]+?)["\']?\s*(?:#.*)?$',line)
            if m:
                keys.setdefault(m.group(1),m.group(2))
    if 'object' not in keys:
        return f'orig/{target}/sys/main.dol'
    return str(Path(keys['object_base'])/keys['object']) if 'object_base' in keys else keys['object']


def exact_in_report(report,main_module):
    """How many of the main executable's functions the target's report counts as exact (None
    without a report)."""
    if not report.is_file():
        return None
    units=json.loads(report.read_text()).get('units',[])
    return sum(1 for u in units if not main_module or u.get('name','').split('/',1)[0]==main_module
               for f in u.get('functions',[]) if f.get('fuzzy_match_percent')==100)


def main():
    ap=argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--target',required=True,help='target id, as in config/targets.json')
    ap.add_argument('--unit',action='append',help='check only this unit (repeatable)')
    ap.add_argument('--verbose',action='store_true',help='list the skipped functions too')
    args=ap.parse_args()
    build=ROOT/'build'/args.target;config=ROOT/'config'/args.target
    objdiff=build/'objdiff.json'
    if not objdiff.is_file():
        objdiff=ROOT/'objdiff.json'
    units=json.loads(objdiff.read_text())['units']
    # A root objdiff.json is the last configured target's; refuse one written for another target.
    if objdiff.parent==ROOT and any(not str(u.get('target_path','build/'+args.target)).startswith(f'build/{args.target}/')
                                   for u in units):
        print(f'{args.target}: objdiff.json at the root belongs to another target; configure {args.target} first')
        return 1
    symbols=Symbols(config/'symbols.txt')
    dol=Dol(ROOT/original(config/'config.yml',args.target))
    splits=read_splits(config/'splits.txt')
    # dtk names the main executable's units after the build's own name; the rest are REL modules.
    main_module=None
    if (build/'config.json').is_file():
        main_module=json.loads((build/'config.json').read_text()).get('name')
    modules=0
    if main_module:
        kept=[u for u in units if u['name'].split('/',1)[0]==main_module]
        if units and not kept:
            print(f'{args.target}: no objdiff unit belongs to the main executable {main_module!r}')
            return 1
        rel=[n for n in args.unit or [] if n.split('/',1)[0]!=main_module]
        if rel:
            print(f'{args.target}: REL module units are not checked: '+', '.join(rel))
            return 1
        modules=len(units)-len(kept);units=kept
    # A unit objdiff.json lists whose object the build did not write would pass unchecked.
    missing=[p for u in units for p in (u.get('target_path'),u.get('base_path')) if p and not (ROOT/p).exists()]
    if missing:
        print(f'{args.target}: objdiff.json names objects the build did not write; build the target first:')
        for p in missing:
            print('    '+p)
        return 1
    targets={u['name']:Elf(ROOT/u['target_path']) for u in units if u.get('target_path')}
    exports=exported(targets,symbols,splits)
    checked=skipped=failed=0
    for unit in units:
        if args.unit and unit['name'] not in args.unit:
            continue
        if unit['name'] not in targets or not unit.get('base_path'):
            continue
        check=Unit(Elf(ROOT/unit['base_path']),targets[unit['name']],symbols,dol,exports,
                   splits.get(unit['name'].split('/',1)[-1]))
        results={}
        for name in sorted(check.base.functions):
            if name not in check.target.functions:
                continue
            results[name]=check.compare(name)
            if results[name] is None:
                skipped+=1
                if args.verbose:
                    print(f'skip {unit["name"]}: {name} (not exact)')
            else:
                checked+=1
        for (name,off),finding in check.uninitialized().items():
            results[name].append(f'+0x{off:X}: {finding}')
        for name,findings in results.items():
            if findings:
                failed+=1
                print(f'FAIL {unit["name"]}: {name}')
                for f in sorted(findings,key=lambda f:int(f[3:f.index(':')],16)):
                    print('    '+f)
    print(f'{args.target}: {checked} exact functions checked, {failed} disagree; {skipped} not exact, skipped'
          +(f'; {modules} REL module units skipped' if modules else ''))
    if args.unit and not checked:
        print(f'{args.target}: no exact function was checked in the units named; a unit name or the build is wrong')
        return 1
    # Checking nothing passes only for a project whose report counts nothing exact yet.
    expected=exact_in_report(build/'report.json',main_module) if not args.unit else None
    if expected and not checked:
        print(f'{args.target}: the report counts {expected} exact functions but none was checked; the build or this check is wrong')
        return 1
    return 1 if failed else 0


if __name__=='__main__':
    sys.exit(main())
