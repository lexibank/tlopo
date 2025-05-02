import pathlib
import collections

import attr
import pylexibank
from clldutils.misc import slug
from pyetymdict import Dataset as BaseDataset, Language as BaseLanguage
from pycldf.sources import Source, Sources

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
        #from pytlopo.parser.refs import CROSS_REF_PATTERN
        #for line in self.raw_dir.joinpath('vol1').read('text.txt').split('\n'):
        #    for m in CROSS_REF_PATTERN.finditer(line):
        #        print(m.string[m.start():m.end()])
        #return
        glosses = [{slug(w) for w in r['Gloss'].split() if slug(w)} for r in self.etc_dir.read_csv('vol1_poc_reconstructions.csv', dicts=True)]
        langs = {r['Name']: r for r in self.raw_dir.joinpath('vol1').read_csv('languages.csv', dicts=True)}
        for v in list(langs.values()):
            for alt in v['Alternative_Names'].split('; '):
                langs[alt] = v
        allps = 0
        per_pl = collections.defaultdict(list)
        for vol in range(1, 7):
            if vol != 1:
                continue
            t = self.raw_dir / 'vol{}'.format(vol) / 'text.txt'
            if not t.exists():
                continue
            vol = Volume(t.parent, langs, Source.from_bibtex(self.etc_dir.read('citation.bib')))
            print(vol)
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
                #if 'Arch' in rec.cat1:
                #    print(rec)
                for pf in rec.protoforms:
                    pfs.update([str(pf)])
                    per_pl[pf.protolanguage].append(pf)
                for w in rec.reflexes:
                    reflexes.update([str(w)])
                if 1:#i < 15:
                    r = str(rec)
                    #if 'T)aRaq' in r:
                    #print(r)
                    #print('---')
                #if i == 3:
                #    break
            #print('Reconstructions:', i, 'Reflexes:', words, 'POc reconstructions:', sum(1 for pf in pfs if 'POc' in pf))
            #print(vol.bib)
            #print(vol.chapters['5'].text)
            #print(len(vol._lines))
            #for line in vol._lines[-250:-180]:
            #    print(line)
            #for k, v in pfs.most_common():
            #    if v > 1:
            #        print(v, k)
            #for k, v in reflexes.most_common():
            #    if v > 1:
            #        print(v, k)
            #for k, v in bycat.items():
            #     print(k, v)

    def cmd_makecldf(self, args):
        self.schema(args.writer.cldf, with_cf=False, with_borrowings=False)
        args.writer.cldf.add_columns('CognatesetTable', 'Pre_Note', 'Post_Note')

        langs = {r['Name']: r for r in self.raw_dir.joinpath('vol1').read_csv('languages.csv', dicts=True)}
        reconstructions = []
        for v in list(langs.values()):
            for alt in v['Alternative_Names'].split('; '):
                langs[alt] = v
        for vol in range(1, 7):
            if vol != 1:
                continue
            t = self.raw_dir / 'vol{}'.format(vol) / 'text.txt'
            if not t.exists():
                continue
            vol = Volume(t.parent, langs, Source.from_bibtex(self.etc_dir.read('citation.bib')))
            for i, rec in enumerate(vol.reconstructions):
                reconstructions.append(rec)
            mddir = self.cldf_dir.joinpath(vol.dir.name)
            mddir.mkdir(exist_ok=True)
            for num, chapter in vol.chapters.items():
                mddir.joinpath('chapter{}.md'.format(num)).write_text(chapter.text)

            args.writer.cldf.sources = Sources.from_file(vol.dir / 'references.bib')

        for lg in langs.values():
            args.writer.add_language(ID=lg['ID'], Name=lg['Name'], Is_Proto=False, Group=lg['Group'])

        gloss2id = {}
        for i, rec in enumerate(reconstructions):
            pf = rec.protoforms[0]
            if pf.protolanguage not in langs:
                args.writer.add_language(ID=slug(pf.protolanguage), Name=slug(pf.protolanguage), Is_Proto=True)
                langs[pf.protolanguage] = slug(pf.protolanguage)
            pfgloss = pf.glosses[0].gloss if pf.glosses else 'none'
            if pfgloss not in gloss2id:
                gloss2id[pfgloss] = slug(pfgloss)
                args.writer.add_concept(ID=slug(pfgloss), Name=pfgloss)
            pflex = args.writer.add_lexemes(
                Language_ID=slug(pf.protolanguage),
                Parameter_ID=gloss2id[pfgloss],
                Description=pfgloss,
                Value=pf.forms[0],
                Comment=None,
                Source=[],
                # Doubt=getattr(form, 'doubt', False),
            )[0]

            csid = str(i + 1)
            args.writer.objects['CognatesetTable'].append(dict(
                ID=rec.id,
                Language_ID=slug(pf.protolanguage),
                Form_ID=pflex['ID'],
                Comment='\n\n'.join(line.replace('*', '&ast;') for line in rec.desc()),
                Name=pf.forms[0],
                Description=pf.glosses[0].gloss if pf.glosses else None,
                Pre_Note=rec.pre_note(),
                Post_Note=rec.post_note(),
                #Source=['pmr1'],
                #Doubt=cset.doubt,
            ))
            args.writer.add_cognate(
                lexeme=pflex,
                Cognateset_ID=rec.id,
                # Source=[str(ref) for ref in form.gloss.refs],
                # Doubt=form.doubt,
            )

            for pf in rec.protoforms[1:]:
                if pf.protolanguage not in langs:
                    args.writer.add_language(ID=slug(pf.protolanguage), Name=slug(pf.protolanguage), Is_Proto=True)
                    langs[pf.protolanguage] = slug(pf.protolanguage)
                if pfgloss not in gloss2id:
                    gloss2id[pfgloss] = slug(pfgloss)
                    args.writer.add_concept(ID=slug(pfgloss), Name=pfgloss)
                pflex = args.writer.add_lexemes(
                    Language_ID=slug(pf.protolanguage),
                    Parameter_ID=gloss2id[pfgloss],
                    Description=pfgloss,
                    Value=pf.forms[0],
                    Comment=None,
                    Source=[],
                    # Doubt=getattr(form, 'doubt', False),
                )[0]
                args.writer.add_cognate(
                    lexeme=pflex,
                    Cognateset_ID=rec.id,
                    # Source=[str(ref) for ref in form.gloss.refs],
                    # Doubt=form.doubt,
                )

            for w in rec.reflexes:
                #
                # FIXME: supplement glosses from matching, i.e. closest reconstruction!
                #
                assert w.lang in langs
                gloss = w.glosses[0].gloss
                if gloss not in gloss2id:
                    gloss2id[gloss] = slug(gloss or 'none')
                    args.writer.add_concept(ID=slug(gloss or 'none'), Name=gloss)
                lex = args.writer.add_lexemes(
                    Language_ID=langs[w.lang]['ID'],
                    Parameter_ID=gloss2id[gloss],
                    Description=gloss,
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
                    Cognateset_ID=rec.id,
                    #Source=[str(ref) for ref in form.gloss.refs],
                    #Doubt=form.doubt,
                )
