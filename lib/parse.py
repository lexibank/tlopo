import re
import pathlib
import itertools
import dataclasses

"""
1) -> ŋ
IJ -> ŋ
6.IJ -> áŋ
bwalJ -> b-raised-w-aŋ
brv) -> b(raised-w)
"""

GROUPS = [
    "Adm",
    "CMP",
    "Fij",
    "Fma",
    "IJ",
    "Mic",
    "MM",
    "NCaI",
    "NCal",
    "NCV",
    "NNG",
    "Pn",
    "PT",
    "SES",
    "SJ",
    "SV",
    "Yap",
    "PI",
    "WMP",
]
PROTO = [
    "PAn",
    "PMP",
    "PWMP",
    "PEMP",
    "PCEMP",
    "PEOc",
    "POc",
    "PNGOc",
    "PNNG",
    "PCP",
    "PPn",
    "PPT",
    "Proto South HalmaheralWest New Guinea",
    "PWOc",
    "PEAd",
    "Proto Eastern Admiralty",
    "Proto Remote Oceanic",
    "PSS",
    "Proto Southeast Solomonic",
    "PCEPn",
]
proto_pattern = re.compile(r'(\((?P<relno>[0-9])\)\s*)?'
                           r'(?P<pl>{})\s+'
                           r'(?P<root>root\s+)?'
                           r'(?P<pldoubt>\((POC)?\?\)\s*)?'
                           r'(?P<fn>\[[0-9]+]\s+)?'
                           r'(?P<pfdoubt>\?)?\*'.format('|'.join(re.escape(g) for g in PROTO)))


@dataclasses.dataclass
class Protoform:
    """
    PEOc (POC?)[6] *kori(s), *koris-i- 'scrape (esp. coconuts), grate (esp. coconuts)
    """
    form: str
    glosses: str
    protolanguage: str
    note: str = None
    pfdoubt: bool = False
    pldoubt: bool = False

    @classmethod
    def from_line(cls, line):
        kw = {}
        m = proto_pattern.match(line)
        assert m
        kw['protolanguage'] = m.group('pl')
        kw['pfdoubt'] = bool(m.group('pfdoubt'))
        kw['pldoubt'] = bool(m.group('pldoubt'))
        pl, _, rem = line.partition('*')
        assert "'" in rem, line
        pf, _, rem = rem.partition("'")
        kw['form'] = pf.strip()
        kw['glosses'], kw['note'] = Protoform.glosses_and_note(rem)
        return cls(**kw)

    @staticmethod
    def glosses_and_note(s):
        glosses = []
        s = s.replace("men's", "men__s")
        rem = s
        while "'" in rem:
            gloss, _, rem = rem.partition("'")
            assert gloss.strip()
            glosses.append(gloss.strip())
            rem = rem.strip()
            if rem.startswith(","):
                rem = rem[1:].strip()
            if rem.startswith("'"):
                assert "'" in rem[1:]
                rem = rem[1:].strip()
            #
            # FIXME: parse nested protoforms ...
            #
            #elif proto_pattern.match(rem):
            #    # POc *bayat 'fence, boundary marker', POc *bayat-i 'make a garden boundary'
            #    #
            #    # FIXME: handle three reconstructions!
            #    #
            #    rec = Reconstruction.from_data(protoform=rem)
            #    glosses.extend(rec.glosses)
            #    break
            else:
                break
        return glosses, rem.strip()


@dataclasses.dataclass
class Reconstruction:
    protoforms: list
    witnesses: list = None
    cat1: str = ''
    cat2: str = ''
    page: int = 0
    desc: list = None

    @classmethod
    def from_data(cls, **kw):
        kw['protoforms'] = [Protoform.from_line(pf) for pf in kw['protoforms'] ]
        return cls(**kw)

    def __str__(self):
        return """\
{} / {} / Page {}
{}
{}
{}

{}""".format(self.cat1, self.cat2, self.page, self.annotation, self.protoform, '\n'.join('  {}'.format(w.strip()) for w in self.witnesses), '\n\n'.join(self.desc))


h1_pattern = re.compile(r'([0-9]+)\.?\s+(?P<title>[A-Z].+)')
h2_pattern = re.compile(r'([0-9]+)(\.|\s)\s*([0-9]+)\.?\s+(?P<title>[A-Z].+)')
h3_pattern = re.compile(r'([0-9]+)(\.|\s)\s*([0-9]+)(\.|\s)\s*([0-9]+)\.?\s+(?P<title>[A-Z].+)')

witness_pattern = re.compile(r'\s+({})(\s*\:\s+|\s+Marino)'.format('|'.join(re.escape(g) for g in GROUPS)))
figure_pattern = re.compile(r'Figure\s+[0-9]+[a-z]*\:')


def iter_lines(lines):
    for line in lines:
        yield line


def iter_etyma(lines):
    pageno_right_pattern = re.compile(r'\x0c\s+[^0-9]+(?P<no>[0-9]+)')
    pageno_left_pattern = re.compile(r'\x0c(?P<no>[0-9]+)\s+[^0-9]+')
    pageno = -1
    dropempty = False
    paras, para = [], []
    h1, h2, h3 = None, None, None
    in_etymon = False

    for i, line in enumerate(iter_lines(lines), start=1):
        # FIXME: stop at "Data sources which were consulted in relation to a particular terminology are noted in" in line
        m = pageno_left_pattern.fullmatch(line)
        if m:
            pageno = int(m.group('no'))
            assert not in_etymon, pageno
            dropempty = True
            continue
        m = pageno_right_pattern.fullmatch(line)
        if m:
            pageno = int(m.group('no'))
            assert not in_etymon
            dropempty = True
            continue
        if not line:
            if dropempty:
                dropempty = False
                continue
            if para:
                paras.append(para)
                para = []
            continue

        if line == '<':
            assert not in_etymon
            in_etymon = True
            paras, para = [], []
            continue
        if line == '>':
            if para:
                paras.append(para)
            assert paras, i
            yield h1, h2, h3, pageno, paras
            assert in_etymon
            in_etymon = False
            continue

        if not in_etymon:
            m = h1_pattern.match(line)
            if m:
                h1 = m.group('title')
                h2, h3 = None, None
            else:
                m = h2_pattern.match(line)
                if m:
                    h2 = m.group('title')
                    h3 = None
                else:
                    m = h3_pattern.match(line)
                    if m:
                        h3 = m.group('title')

        para.append(line)


def iter_witness(lines):
    witness = ''
    for line in lines:
        m = witness_pattern.match(line)
        if m:
            if witness:
                yield witness
            witness = line
            continue
        m = proto_pattern.match(line)
        if m:
            pass  # yield a Reconstruction (without witnesses, because these can be inferred from the tree!)
            #
            # FIXME: allow for interspersed, intermediate reconstructions.
            #
        elif line.strip().startswith("cf. also"):
            # FIXME: cf sets!
            continue
        else:
            assert line.startswith('     '), line
            witness += line
    yield witness


def iter_protoforms(lines):
    protoform, nlines = '', 0
    for line in lines:
        m = proto_pattern.match(line)
        if m:
            if protoform:
                yield protoform, nlines
            protoform, nlines = line, 1
            continue
        if witness_pattern.match(line):
            break
        if re.fullmatch(r'   \s+,', line):
            nlines += 1
            continue
        assert re.match(' ([a-z]|Chowning|Lichten)', line), line
        protoform += line
        nlines += 1
    if protoform:
        yield protoform, nlines


def parse(p):
    for h1, h2, h3, pageno, paras in iter_etyma(p.read_text(encoding='utf8').split('\n')):
        protoforms = []
        witnesses = []
        desc = []
        for para in paras:
            if proto_pattern.match(para[0]):
                consumed = 0
                for pf, nl in iter_protoforms(para):
                    protoforms.append(pf)
                    consumed += nl
                lines = para[consumed:]
                try:
                    assert witness_pattern.match(lines[0]), lines[0]
                except IndexError:
                    print(para)
                    raise
                witnesses = list(iter_witness(lines))
            else:
                desc.append(' '.join(para).strip())
        assert protoforms, paras
        # FIXME: three!
        yield Reconstruction.from_data(cat1=h1, cat2=h2, protoforms=protoforms, witnesses=witnesses, page=pageno, desc=desc)
    # FIXME: yield last reconstruction!


if __name__ == '__main__':
    import sys
    from csvw.dsv import reader
    glosses = [r['Gloss'] for r in reader('../vol1_poc_reconstructions.csv', dicts=True)] 
    for t in pathlib.Path('../raw').glob('*.txt'):
        m = re.search(r'Vol(?P<no>[1-6])', t.stem)
        if '1' not in t.stem:
            continue
        print(t.stem)
        for i, rec in enumerate(parse(t)):
            if len(sys.argv) > 1:
                if rec.gloss == glosses[0]:
                    print(glosses.pop(0))
                #else:
                #    print('+++', rec.gloss, glosses[0], rec.gloss == glosses[0])
            else:
                print(i + 1, rec.protoform, rec.gloss)
            #print('  ---  ')

    if len(sys.argv) > 1:
        print('---', glosses[0])

