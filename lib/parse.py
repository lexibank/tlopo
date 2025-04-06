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
