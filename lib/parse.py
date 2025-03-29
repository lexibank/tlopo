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


@dataclasses.dataclass
class Reconstruction:
    protoform: str
    annotation: str
    witnesses: list
    cat1: str
    cat2:str
    page: int
    desc: list

    @classmethod
    def from_data(cls, **kw):
        return cls(**kw)

    def __str__(self):
        return """\
{} / {} / Page {}
{}
{}
{}

{}""".format(self.cat1, self.cat2, self.page, self.annotation, self.protoform, '\n'.join('  {}'.format(w.strip()) for w in self.witnesses), '\n\n'.join(self.desc))


h1_pattern = re.compile(r'([0-9]+)\.\s+(?P<title>[A-Z].+)')
h2_pattern = re.compile(r'([0-9]+)\.\s*([0-9]+)(\.\s*[0-9]+)?\s+(?P<title>[A-Z].+)')
witness_pattern = re.compile(r'\s+({})(\s*\:\s+|\s+Marino)'.format('|'.join(re.escape(g) for g in GROUPS)))
proto_pattern = re.compile(r'{}\s+(\([^\)]+\)\s*)?\*'.format('|'.join(re.escape(g) for g in PROTO)))
figure_pattern = re.compile(r'Figure\s+[0-9]+[a-z]*\:')


def iter_lines(lines):
    for line in lines:
        yield line


def iter_etyma(lines):
    pageno_right_pattern = re.compile(r'\x0c\s+[^0-9]+(?P<no>[0-9]+)')
    pageno_left_pattern = re.compile(r'\x0c(?P<no>[0-9]+)\s+[^0-9]+')
    pageno = None
    dropempty, firstline = False, False
    paras, para = [], []
    h1, h2 = None, None
    in_etymon = False

    for i, line in enumerate(iter_lines(lines), start=1):
        # FIXME: stop at "Data sources which were consulted in relation to a particular terminology are noted in" in line
        m = pageno_left_pattern.fullmatch(line)
        if m:
            pageno = int(m.group('no')) - 1
            dropempty = True
            continue
        m = pageno_right_pattern.fullmatch(line)
        if m:
            pageno = int(m.group('no')) - 1
            dropempty = True
            continue
        if not line:
            if dropempty:
                dropempty = False
                firstline = True
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
            yield h1, h2, pageno, paras
            assert in_etymon
            in_etymon = False
            continue

        m = h1_pattern.match(line)
        if m:
            h1 = m.group('title')
        else:
            m = h2_pattern.match(line)
            if m:
                h2 = m.group('title')
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
    for h1, h2, pageno, paras in iter_etyma(p.read_text(encoding='utf8').split('\n')):
        protoforms = []
        witnesses = []
        desc = []
        ann = None
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
        if len(protoforms) == 1:
            protoform = protoforms[0]
        else:
            ann, protoform = protoforms[:2]
        # FIXME: three!
        yield Reconstruction.from_data(cat1=h1, cat2=h2, protoform=protoform, annotation=ann, witnesses=witnesses, page=pageno, desc=desc)
    # FIXME: yield last reconstruction!


if __name__ == '__main__':
    for t in pathlib.Path('../raw').glob('*.txt'):
        m = re.search(r'Vol(?P<no>[1-6])', t.stem)
        if '1' not in t.stem:
            continue
        print(t.stem)
        for i, rec in enumerate(parse(t)):
            print(i + 1, rec.protoform)
            #print('  ---  ')

