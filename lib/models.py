"""

"""
import re
import dataclasses

from .parse import proto_pattern, parse_protoform, PHONEMES, iter_etyma, iter_protoforms, iter_reflexes, witness_pattern


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
                    raise ValueError(c, rem, line)
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


def iter_reconstructions(p, langs):
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
