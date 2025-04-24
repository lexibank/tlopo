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
    "SHWNG",
]
PROTO = [
    # Oceanic:
    "POc",  # Yap
    "PEAd", # Adm
    "Proto Eastern Admiralty",  # FIXME: identify with PEAd
    "PWOc",  # MM, SJ
      "Proto Northwest Solomonic",
      "Proto Meso-Melanesian",  # MM
      "PNGOc",  # Proto New Guinea Oceanic, i.e. PWOc without reflexes from MM
        "PNNG", # NNG
        "PPT", # PT
    "PEOc",  # NCal
      "Proto Southeast Solomonic",  # FIXME: identify with PSS
      "PSS", # SES
      "PMic",  # Proto Micronesian Mic
        "PChk",
      "PNCV",  # NCV
      "Proto Remote Oceanic", # NCV, SV, Mic
        "PCP",  # Proto Central Pacific, Fij
          "PPn",  # PN
            "PCEPn",  # Proto Central Eastern Polynesian; Hawaiian, Maori, Tuamotuan
            "PNPn",
    # Other Austronesian:
    "PAn",
    "PMP",
    "PWMP",
    "PCEMP",
    "PCMP",
    "PEMP",
    "Proto South Halmahera/West New Guinea",
]
proto_pattern = re.compile(r'(\((?P<relno>[0-9])\)\s*)?'
                           r'(?P<pl>{})\s+'
                           r'(?P<root>root\s+)?'
                           r'(?P<pldoubt>\((POC)?\?\)\s*)?'
                           r'(?P<pos>\((N|V|N LOC|N, N LOC|\?\? N LOC, V|N, \? N LOC)\)\s*)?'
                           r'(?P<fn>\[[0-9]+]\s+)?'
                           r'(?P<pfdoubt>\?)?\*'.format('|'.join(re.escape(g) for g in PROTO)))
PHONEMES = "w p b m i e t d s n r dr l a ā c j y u o k g q R ŋ ñ pʷ bʷ mʷ"
pos_pattern = re.compile(
    r'\s*\((?P<pos>PP|POSTVERBAL ADV|PREPV|V AUX|VF|INTERJECTION|ADN AFFIX|LOC|R-|R|preverbal clitic|DIR clause-final|adverb|V, DIR|DEM|v|V|VT|VI|vI|N|ADJ|ADV|VT,\s*VI|N, V|N, v|V & N|N,V|N LOC|PASS|postposed particle|ADV, ADJ|V, ADJ|DIR|N \+ POSTPOSITION|PREP|POSTPOSITION|RELATIONAL N)\)\s*')

fn_pattern = re.compile(r'\[(?P<fn>[0-9]+)]')  # [2]
gloss_number_pattern = re.compile(r'\s*\(\s*(?P<qualifier>i|1|present meaning|E. dialect)\s*\)\s*')  # ( 1 )


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
    if f.startswith('|') and f.endswith('|'):
        # multi-word protoform
        for word in f[1:-1].split():
            parse_protoform(word, pl)
        return

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
        phonemes.extend(['á', 'C', 'D', 'h', 'N', 'S', 'R', 'T', 'z', 'Z', 'L', '?', 'ə', '+'  # *pu+put
                         ])
    if pl in ['PWMP']:
        phonemes.extend(['S'])
    if pl in ['PNCV']:
        phonemes.extend(['v'])
    if pl in ['PEOc']:
        phonemes.extend(['C'])
    if pl in ['PCP']:
        phonemes.extend(['v', 'ā'])
    if pl in ['PPn', 'PMic', 'PChk', 'PCEPn']:
        phonemes.extend(['ō', 'f', 'ū', 'z', 'V', 'ī', 'ə̄', 'ə', '̄'])
    if pl in ['PNGOc']:
        phonemes.extend(['kʷ'])
    if pl in ['PPn', 'PNPn']:
        phonemes.extend(['ʔ', 'ā', 'h'])
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
            raise ValueError(c, f, pl)
        form += c

    if form != f:
        if f[len(form) + 1:].strip()[0] not in '(*?[ʔ':
            # FIXME: handle multi-word protoforms
            assert ' or ' in f or '(kuron)' in f or ' ni panua' in f or 'mata ' in f or 'patu ' in f or '(fatu)' in f, f
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
            assert not in_etymon, line
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
            assert not in_etymon, i
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
    cf = False
    for line in lines:
        m = witness_pattern.match(line)
        if m:
            yield line, cf, False
            continue
        m = proto_pattern.match(line)
        if m:
            yield line, cf, True
            continue
        if line.strip().startswith("cf. also"):
            line = line.strip().replace("cf. also", "").replace(':', '').strip()
            if line:
                cfcomment = line
            cf = True
            continue
        assert False, line


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


def get_comment(s):
    # Find ( on matching level:
    if s.endswith(')'):
        cmt, level = [], 1
        assert '(' in s, s
        for i, c in enumerate(reversed(s[:-1])):
            if c == ')':
                level += 1
            elif c == '(':
                level -= 1
                if level == 0:
                    break
            cmt.append(c)
        else:
            raise ValueError(s)

        return ''.join(reversed(cmt)).strip(), s[:-i-2].strip()
    return None, s


def glosses_and_note(s, quotes="''"):
        glosses = []
        s = s.replace("n{}s".format(quotes[1]), "n__s")
        rem = s
        while quotes[1] in rem:
            gloss, _, rem = rem.partition(quotes[1])
            assert gloss.strip()
            glosses.append(gloss.strip())
            rem = rem.strip()
            if rem.startswith(","):
                rem = rem[1:].strip()
            if rem.startswith(quotes[0]):
                assert quotes[1] in rem[1:], s
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


def iter_bracketed_and_gloss(s, quotes):
    i = 0
    while s:
        assert s.startswith('('), s
        br, _, rem = s[1:].partition(')')
        w, _, rem = rem.partition(quotes[0])
        assert not w.strip()
        gl, _, rem = rem.partition(quotes[1])
        yield br.strip(), gl.strip()
        s = rem.strip().lstrip(';').strip()
        i += 1
        if i > 10:
            raise ValueError(s)


def get_quotes(s):
    return "‘’" if "‘" in s else "''"


def iter_glosses(s):
    quotes = "‘’" if "‘" in s else "''"

    def make_gloss(pos=None, gloss=None, fn=None, comment=None, qualifier=None, uncertain=False):
        return dict(
            pos=pos,
            gloss=gloss.replace("__s", quotes[1]) if gloss else gloss,
            fn=fn, comment=comment, qualifier=qualifier, uncertain=bool(uncertain))

    gloss, pos, qualifier, fn, uncertain, comment = None, None, None, None, False, None
    rem = s
    rem = re.sub(r"(?P<c>[a-z]){}s".format(quotes[1]), lambda m: m.group('c') + "__s", rem)
    done = False

    m = pos_pattern.match(rem)
    if m:
        # (N) 'stem' ; (V ) 'steer (a boat from the stem)'
        if re.fullmatch(r"(\([^)]+\)\s*{0}[^{1}]+{1}\s*;?\s*)+".format(quotes[0], quotes[1]), rem):
            for br, gl in iter_bracketed_and_gloss(rem, quotes):
                yield make_gloss(pos=br.replace('v', 'V'), gloss=gl)
            return
        pos = m.group('pos')
        rem = rem[m.end():].strip()

    m = gloss_number_pattern.match(rem)
    if m:
        # FIXME: assign glosses with number and comment
        # FIXME: must handle
        # (E. dialect) 'shed for yams'; (W. dialect) 'house with one side of roof only, made in garden' ; 'a shrine, small house on poles' (= _hare ni asi_)
        if re.fullmatch(r"(\([^)]+\)\s*'[^']+'\s*;?\s*)+", rem):
            for br, gl in iter_bracketed_and_gloss(rem, quotes):
                yield make_gloss(qualifier=br.replace('v', 'V'), gloss=gl)
            return
        qualifier = m.group('qualifier')
        rem = rem[m.end():].strip()

    m = fn_pattern.match(rem)
    if m:
        # FIXME: store fn, or load directly content into comment?
        fn = m.group('fn')
        rem = rem[m.end():].strip()

    if rem.startswith('?'):
        uncertain = True
        rem = rem[1].strip()

    m = fn_pattern.search(rem)
    if m and m.end() == len(rem):  # strip footnote from end.
        assert not fn, s
        fn = m.group('fn')
        rem = rem[:m.start()].strip()

    for src in [
        '(Lewis, 1978:33)',
        '(Chowning)',
        '(Elbert 1972)',
    ]:
        if rem.endswith(src):
            # FIXME: store source
            rem = rem.replace(src, '').strip()

    if rem == '(Horridge)':
        # FIXME: store source
        rem = ''

    if rem.startswith('(') and rem.endswith(')'):
        comment = rem[1:-1].strip()
        rem = ''

    # consume comment or source from the end.
    bcomment, rem = get_comment(rem)
    assert not (comment and bcomment), s
    comment = comment or bcomment

    if rem:
        assert rem[0] == quotes[0], s
        assert rem[-1] == quotes[1], s
        # FIXME: assertion below will work once the two cases above are handled!
        # assert rem[0] == "'" and rem[-1] == "'", line
        if quotes[0] in rem[1:-1]:
            print(rem)

    maybe_gloss = rem
    if "'" in maybe_gloss:
        assert maybe_gloss.count("'") >= 2, s
    stuff, _, maybe_gloss = maybe_gloss.partition("'")
    if maybe_gloss.strip():
        gloss = glosses_and_note(maybe_gloss)[0][0]
    if 0:  # stuff.strip():
        if not pos_pattern.fullmatch(stuff) and not gloss_number_pattern.fullmatch(stuff):
            # next part is a question mark, a footnote reference or a comment.
            assert stuff[0] in '?[(', stuff
            # print(words, line)
    yield gloss
