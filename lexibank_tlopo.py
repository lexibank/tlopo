import pathlib
import collections

import attr
import pylexibank
from clldutils.misc import slug
from pyetymdict import Dataset as BaseDataset, Language as BaseLanguage

from pytlopo.models import Volume


@attr.s
class Variety(BaseLanguage):
    Classification = attr.ib(
        default=None,
        metadata={
            'dc:description':
                'Classification within Oceanic, given as /-separated nodes.',
            'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#description'}
    )
    Alternative_Names = attr.ib(default=None)
    Note = attr.ib(default=None)


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "tlopo"

    language_class = Variety

    # define the way in which forms should be handled
    form_spec = pylexibank.FormSpec(
        brackets={"(": ")"},  # characters that function as brackets
        separators=";/,",  # characters that split forms e.g. "a, b".
        missing_data=('?', '-'),  # characters that denote missing data.
        strip_inside_brackets=True   # do you want data removed in brackets or not?
    )

    def cmd_download(self, args):
        import re
        from clldutils.source import Source
        from clldutils.misc import slug
        refs, key = [], None
        for i, line in enumerate(self.raw_dir.joinpath('vol1', 'references.bib').read_text(encoding='utf-8').split('\n'), start=1):
            if i % 2 == 1:
                key = line
            else:
                assert key
                refs.append((key, line))
        bib = []
        for key, line in refs:
            line = re.sub(
                r'1\s*(?P<a>[0-9])\s*(?P<b>[0-9])\s*(?P<c>[0-9])(?P<d>[abcde])?\s*,',
                lambda m: '1{}{}{}{},'.format(m.group('a'), m.group('b'), m.group('c'), m.group('d') or ''),
                line)
            m = re.search('(?P<year>([0-9]{4}|forthcoming|n\.d\.|in press))', line)
            assert m
            assert m.group('year') in key
            author = line[:m.start()].strip()
            edp = re.compile(r'\s+ed(s)?\.?,?\s*$')
            ctype = 'author'
            if edp.search(author):
                ctype = 'editor'
                author = author[:m.start()].strip()
            if author.endswith(','):
                author = author[:-1].strip()
            genre = 'misc'
            kw = {ctype: author, 'year': m.group('year'), 'key': key}

            rem = line[m.end():].strip()
            if rem.startswith(','):
                rem = rem.lstrip(',').strip()
            inm = re.search(r'\.\s+In\s+', rem)
            if inm:
                edm = re.search(',\s+eds?\.?\s*,\s*', rem[inm.end():])
                if edm:
                    assert ctype == 'author'
                    kw['editor'] = rem[inm.end():inm.end() + edm.start()].replace('1', 'I')
                    genre = 'incollection'
                    kw['booktitle'] = rem[inm.end() + edm.end():].strip().rstrip('.').strip()
                    rem = rem[:inm.start()].strip()

            rem.rstrip('.')
            kw['title'] = rem
            src = Source(genre, slug(key, lowercase=False), **kw)
            print(src.bibtex())
        return
        glosses = [{slug(w) for w in r['Gloss'].split() if slug(w)} for r in self.etc_dir.read_csv('vol1_poc_reconstructions.csv', dicts=True)]
        langs = {r['Name']: r for r in self.raw_dir.joinpath('vol1').read_csv('languages.csv', dicts=True)}
        for v in list(langs.values()):
            for alt in v['Alternative_Names'].split('; '):
                langs[alt] = v
        allps = 0
        per_pl = collections.defaultdict(list)
        bycat = collections.Counter()
        for vol in range(1, 7):
            #if vol == 1:
            #    continue
            t = self.raw_dir / 'vol{}'.format(vol) / 'text.txt'
            if not t.exists():
                continue
            print('Volume', vol)
            vol = Volume(t.parent, langs)
            words = 0
            pfs = collections.Counter()
            reflexes = collections.Counter()
            for i, rec in enumerate(vol.reconstructions):
                #gloss_words = set()
                #for gloss in rec.glosses:
                #    gloss_words |= {slug(w) for w in gloss.split() if slug(w)}
                #if gloss_words == glosses[0]:
                #    print(glosses.pop(0))
                #if glosses[0] in [
                #    {'warm', 'the', 'fire', 'over', 'st'},  # check *raraŋ, *raraŋ-i-
                #]:
                #    glosses.pop(0)
                # else:
                #    print('+++', rec.gloss, glosses[0], rec.gloss == glosses[0])
                #print(rec)
                allps += len(rec.protoforms)
                words += len(rec.reflexes)
                bycat.update([rec.cat1])
                #if 'Arch' in rec.cat1:
                #    print(rec)
                for pf in rec.protoforms:
                    pfs.update([str(pf)])
                    per_pl[pf.protolanguage].append(pf)
                for w in rec.reflexes:
                    reflexes.update([str(w)])
            print('Reconstructions:', i, 'Reflexes:', words, 'POc reconstructions:', sum(1 for pf in pfs if 'POc' in pf))
            #for k, v in pfs.most_common():
            #    if v > 1:
            #        print(v, k)
            #for k, v in reflexes.most_common():
            #    if v > 1:
            #        print(v, k)
            #for k, v in bycat.items():
            #     print(k, v)

    def cmd_makecldf(self, args):
        #
        # FIXME: should we model that protoforms may have different glosses, tied to different sources?
        # e.g.
        # PMP *qatep 'thatch of sago palm leaves' (Dutton 1994), 'roof, thatch' (ACD)
        #
        self.schema(args.writer.cldf)
        langs = {r['Name']: r for r in self.raw_dir.joinpath('vol1').read_csv('languages.csv', dicts=True)}
        for v in list(langs.values()):
            for alt in v['Alternative_Names'].split('; '):
                langs[alt] = v
            args.writer.add_language(**v)
        gloss2id = {}
        t = self.raw_dir / 'vol1' / 'text.txt'
        vol = Volume(t.parent, langs)
        for i, rec in enumerate(vol.reconstructions):
            #
            # Check if we need to create the reconstruction!
            #
            pf = rec.protoforms[0]
            if pf.protolanguage not in langs:
                args.writer.add_language(ID=slug(pf.protolanguage), Name=slug(pf.protolanguage), Is_Proto=True)
                langs[pf.protolanguage] = slug(pf.protolanguage)
            pfgloss = pf.glosses[0] if pf.glosses else 'none'
            if pfgloss not in gloss2id:
                gloss2id[pfgloss] = slug(pfgloss)
                args.writer.add_concept(ID=slug(pfgloss), Name=pfgloss)
            pflex = args.writer.add_lexemes(
                Language_ID=slug(pf.protolanguage),
                Parameter_ID=gloss2id[pfgloss],
                Description=pfgloss,
                Value=pf.form,
                Comment=None,
                Source=[],
                # Doubt=getattr(form, 'doubt', False),
            )[0]
            csid = str(i + 1)
            args.writer.objects['CognatesetTable'].append(dict(
                ID=csid,
                Language_ID=slug(pf.protolanguage),
                Form_ID=pflex['ID'],
                Comment='\n\n'.join(line.replace('*', '&ast;') for line in rec.desc),
                Name=pf.form,
                Description=pf.glosses[0] if pf.glosses else None,
                #Source=['pmr1'],
                #Doubt=cset.doubt,
            ))

            for w in rec.reflexes:
                #
                # FIXME: supplement glosses from matching, i.e. closest reconstruction!
                #
                assert w.lang in langs
                if w.gloss not in gloss2id:
                    gloss2id[w.gloss] = slug(w.gloss or 'none')
                    args.writer.add_concept(ID=slug(w.gloss or 'none'), Name=w.gloss)
                lex = args.writer.add_lexemes(
                    Language_ID=langs[w.lang]['ID'],
                    Parameter_ID=gloss2id[w.gloss],
                    Description=w.gloss,
                    Value=w.form,
                    Comment=None,
                    Source=[],
                    #Doubt=getattr(form, 'doubt', False),
                )[0]
                #
                # FIXME: deduplicate words!
                #
                #forms[lg['ID']][form.form, self.gloss_lookup(form.gloss)] = lex

                args.writer.add_cognate(
                    lexeme=lex,
                    Cognateset_ID=csid,
                    #Source=[str(ref) for ref in form.gloss.refs],
                    #Doubt=form.doubt,
                )
