"""
What about the ca. 50 food plants reconstructions - without witnesses?

comparing with data from Mae:

>>> s1 = "ūŋ-wūŋ"
>>> s2 = "ūŋ-wūŋ"
>>> len(s1)
8
>>> len(s2)
6
>>> import unicodedata
>>> unicodedata.normalize('NFC', s1) == s2
True
>>> unicodedata.normalize('NFD', s2) == s1
True
"""
import re
import pathlib
import itertools
import dataclasses

GROUPS = [
    # Oceanic:
    "Adm",  # Admiralty
    "Fij",  # Fijian
    "Mic",  # Micronesian
    "MM",  # Meso-Melanesian
    "NCal",  # New Caledonia
    "NCV",  # North and Central Vanuatu
    "NNG",  # North New Guinea
    "Pn",  # Polynesian
    "PT",  # Papuan Tip
    "SES",  # Southeast Solomons
    "SJ",  # Sarmi/Jayapura
    "SV",  # South Vanuatu
    "Yap",  # Yapese
    # Other Austronesian:
    "CMP",  # Central Malayo-Polynesian
    "Fma",  # Formosan
    "IJ",  # Irin Jaya
    "WMP",  # Western Malayo-Polynesian
]
PROTO = [
    # Oceanic:
    "POc",  # Yap
    "PEAd", # Adm
    "Proto Eastern Admiralty",  # FIXME: identify with PEAd
    "PWOc",  # MM, SJ
      "PNGOc",  # Proto New Guinea Oceanic, i.e. PWOc without reflexes from MM
        "PNNG", # NNG
        "PPT", # PT
    "PEOc",  # NCal
      "Proto Southeast Solomonic",  # FIXME: identify with PSS
      "PSS", # SES
      "Proto Remote Oceanic", # NCV, SV, Mic
        "PCP",  # Proto Central Pacific, Fij
          "PPn",  # PN
            "PCEPn",  # Proto Central Eastern Polynesian; Hawaiian, Maori, Tuamotuan
    # Other Austronesian:
    "PAn",
    "PMP",
    "PWMP",
    "PCEMP",
    "PEMP",
    "Proto South Halmahera/West New Guinea",
]
proto_pattern = re.compile(r'(\((?P<relno>[0-9])\)\s*)?'
                           r'(?P<pl>{})\s+'
                           r'(?P<root>root\s+)?'
                           r'(?P<pldoubt>\((POC)?\?\)\s*)?'
                           r'(?P<fn>\[[0-9]+]\s+)?'
                           r'(?P<pfdoubt>\?)?\*'.format('|'.join(re.escape(g) for g in PROTO)))
PHONEMES = "w p b m i e t d s n r dr l a c j y u o k g q R ŋ ñ pʷ bʷ mʷ"


def iter_phoenemes(s):
    c, comb, prev = None, 'ʷ', None
    for c in s:
        if c == comb:
            assert prev
            yield prev + c
            prev = None
            continue
        if prev:
            yield prev
        prev = c
    if c:
        yield c


def parse_protoform(f, pl):
    """
    (x)       it cannot be determined whether x was present
    (x,y)     either x or y was present
    [x]       the item is reconstructable in two forms, one with and one without x
    [x,y]     the item is reconstructable in two forms, one with x and one with y
    x-y       x and y are separate morphemes
    x-        x takes an enclitic or a suffix
    <x>       x is an infix
    """
    if '((' in f:
        assert '))' in f
        f = f.replace('))', ')')
        f = f.replace('((', '(')
    in_bracket = False
    in_sbracket = False
    in_abracket = False
    phonemes = PHONEMES.split()
    phonemes.append('-')
    if pl in ['PAn', 'PMP']:
        phonemes.extend(['á', 'C', 'D', 'h', 'N', 'S', 'R', 'T', 'z'])
    if pl in ['PWMP']:
        phonemes.extend(['S'])
    if pl in ['PEOc']:
        phonemes.extend(['C'])
    if pl in ['PCP']:
        phonemes.extend(['v', 'ā'])
    if pl in ['PPn']:
        phonemes.extend(['f'])
    if pl in ['PNGOc']:
        phonemes.extend(['kʷ'])
    # Tahitian, Arosi: "ʔ"
    # Bauan: "ð"
    # Raga: "ᵑg"
    form = ''


    chunks = f.split(', ')
    for c in iter_phoenemes(chunks[0]):
        if c == '(':
            in_bracket = True
        elif c == ')':
            assert in_bracket, f
            in_bracket = False
        elif c == '[':
            in_sbracket = True
        elif c == ']':
            assert in_sbracket, f
            in_sbracket = False
        elif c == '<':
            in_abracket = True
        elif c == '>':
            assert in_abracket, f
            in_abracket = False
        elif c == ',':
            assert in_bracket or in_sbracket, f
        elif c == ' ':
            break
        elif c in phonemes:
            pass
        else:
            raise ValueError(c, f)
        form += c

    if form != f:
        if f[len(form) + 1:].strip()[0] not in '(*?[ʔ':
            assert ' or ' in f or '(kuron)' in f, f
            #print("{}\t{}".format(form, f[len(form) + 1:]))

    for chunk in chunks[1:]:
        if chunk.startswith('*'):
            parse_protoform(chunk[1:], pl)


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

    def __str__(self):
        return "{} *{} '{}'".format(self.protolanguage, self.form, self.glosses[0] if self.glosses else "")

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
        #
        # 1. Find matching end-quote.
        # 2. consume everything in parens after that, iteratively.
        #
        pf, _, rem = rem.partition("'")
        #if not re.fullmatch('[A-Za-z]+', pf.strip()):
        #    print(pf)
        parse_protoform(pf.strip(), kw['protolanguage'])
        #if kw['protolanguage'] == 'PMP':
        #    print(line, pf)
        #if '1)' in pf:
        #    print(pf.strip())
        """
        usu(q,p), *usu(p)-i 
ubi/*ibu 
tuRi[-J 
tup-a((n,IJ))
tuki- (v)
titey (also *teytey)
tau (ni) waga         - multiple words
taRa(q) (N, V)
sauq ? (N) 
*rabut/*rubat
        """
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
                assert "'" in rem[1:], s
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
class Reflex:
    group: str
    lang: str
    form: str
    gloss: str = None

    def __str__(self):
        return "\t{}: {}\t{}\t'{}'".format(self.group, self.lang, self.form, self.gloss or '')

    @classmethod
    def from_line(cls, langs, line):
        pos_pattern = re.compile(r'\s*\((?P<pos>v|V|VT|VI|vI|N|ADJ|ADV|VT,\s*VI|N, V|N, v)\)\s*')

        fn_pattern = None  # [2]
        gloss_number_pattern = re.compile(r'\s*\(\s*1\s*\)\s*') # ( 1 )

        lang, word, gloss = None, None, None
        group, _, rem = line.partition(':')
        rem_words = rem.strip().split()
        for lg in sorted(langs, key=lambda l: -len(l)):
            lg = lg.split()
            if rem_words[:len(lg)] == lg:
                lang = ' '.join(lg)
                for word in lg:
                    rem = rem.lstrip(' ')
                    assert rem.startswith(word), rem
                    rem = rem[len(word):].strip()
                break
        # get the next word:
        if re.match(r'\s*\[[0-9]]\s*', rem):
            fnref, _, rem = rem.partition(']')
            # FIXME: handle footnote.
        rem = rem.strip()
        if rem.startswith('|'):
            # multi word marker
            assert rem.count('|') == 2, rem
            word, _, rem = rem[1:].strip().partition('|')
            rem = rem.strip()
        else:
            rem_comps = rem.split()
            word, comma = rem_comps.pop(0), None
            if word.endswith(','):
                word = word[:-1]
                comma = True
            for c in word:
                if c not in PHONEMES + 'ɸháāfzʔðᵑg()[]<>-ūɣɔvøʷəо̄öītʰxɨīθbˠŋɛūčēæñIéȴòr̃íṣṛêɒčü':
                    raise ValueError(rem, line)
            if comma:
                word += ', {}'.format(rem_comps.pop(0))
            maybe_gloss = ' '.join(rem_comps)
            if "'" in maybe_gloss:
                assert maybe_gloss.count("'") >= 2
            stuff, _, maybe_gloss = maybe_gloss.partition("'")
            if maybe_gloss.strip():
                gloss = Protoform.glosses_and_note(maybe_gloss)[0][0]
            if stuff.strip():
                if not pos_pattern.fullmatch(stuff) and not gloss_number_pattern.fullmatch(stuff):
                    # next part is a question mark, a footnote reference or a comment.
                    assert stuff[0] in '?[(', stuff
                    #print(words, line)
        assert lang, line
        return cls(group=group.strip(), lang=' '.join(lg), form=word, gloss=gloss)


@dataclasses.dataclass
class Reconstruction:
    protoforms: list
    reflexes: list = None
    cat1: str = ''
    cat2: str = ''
    page: int = 0
    desc: list = None

    @classmethod
    def from_data(cls, langs, **kw):
        #if any('*soka, *soka-i-' in line for line in kw['protoforms']):
        #    for l in kw['reflexes']:
        #        print(l)
        kw['protoforms'] = [Protoform.from_line(pf) for pf in kw['protoforms']]
        kw['reflexes'] = [Reflex.from_line(langs, line) for line in kw['reflexes']]
        return cls(**kw)

    def __str__(self):
        return """\
{} / {} / Page {}
{}
{}
""".format(self.cat1, self.cat2, self.page,
             '\n'.join(str(pf) for pf in self.protoforms),
             '\n'.join(str(w) for w in self.reflexes),
           #'\n\n'.join(self.desc)
           )


h1_pattern = re.compile(r'([0-9]+)\.?\s+(?P<title>[A-Z].+)')
h2_pattern = re.compile(r'([0-9]+)(\.|\s)\s*([0-9]+)\.?\s+(?P<title>[A-Z].+)')
h3_pattern = re.compile(r'([0-9]+)(\.|\s)\s*([0-9]+)(\.|\s)\s*([0-9]+)\.?\s+(?P<title>[A-Z].+)')

witness_pattern = re.compile(r'\s+({})(\s*:\s+)'.format('|'.join(re.escape(g) for g in GROUPS)))
figure_pattern = re.compile(r'Figure\s+[0-9]+[a-z]*:')


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


def iter_reflexes(lines):
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
            if line.strip() and line.startswith('     '):
                raise ValueError(line)
            #witness += line
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


def parse(p, langs):
    for h1, h2, h3, pageno, paras in iter_etyma(p.read_text(encoding='utf8').split('\n')):
        protoforms = []
        reflexes = []
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
                reflexes = list(iter_reflexes(lines))
            else:
                desc.append(' '.join(para).strip())
        assert protoforms, paras
        # FIXME: three!
        yield Reconstruction.from_data(
            langs,
            cat1=h1, cat2=h2, protoforms=protoforms, reflexes=reflexes, page=pageno, desc=desc)
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

