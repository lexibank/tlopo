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
        #from pytlopo.parser.refs import refs2bib
        #refs2bib(self.raw_dir.joinpath('vol2', 'references.bib').read_text(encoding='utf8').split('\n'))
        #return
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
            if vol != 2:
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
                    print(r)
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
        self.schema(args.writer.cldf, with_borrowings=False)
        self.local_schema(args.writer.cldf)

        langs = {r['Name']: r for r in self.raw_dir.joinpath('vol1').read_csv('languages.csv', dicts=True)}
        reconstructions = []
        for v in list(langs.values()):
            for alt in v['Alternative_Names'].split('; '):
                langs[alt] = v
        for vol in range(1, 7):
            if vol not in {1, 2}:
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

            #
            # FIXME: must merge sources!!!
            #
            args.writer.cldf.sources = Sources.from_file(vol.dir / 'references.bib')

        for lg in langs.values():
            args.writer.add_language(ID=lg['ID'], Name=lg['Name'], Is_Proto=False, Group=lg['Group'])

        gloss2id = {}
        for i, rec in enumerate(reconstructions):
            pfrep, pflex = None, None
            for j, pf in enumerate(rec.protoforms):  # FIXME: pf.sources !
                if j == 0:
                    pfrep = pf
                try:
                    pfgloss = pf.glosses[0].gloss
                except IndexError:
                    pfgloss = pf.comment
                if pf.protolanguage not in langs:
                    args.writer.add_language(ID=slug(pf.protolanguage), Name=slug(pf.protolanguage, lowercase=False), Is_Proto=True)
                    langs[pf.protolanguage] = slug(pf.protolanguage)
                if pfgloss not in gloss2id:
                    gloss2id[pfgloss] = slug(pfgloss)
                    args.writer.add_concept(ID=slug(pfgloss), Name=pfgloss)
                lex = args.writer.add_lexemes(
                    Language_ID=slug(pf.protolanguage),
                    Parameter_ID=gloss2id[pfgloss],
                    Description=pfgloss,
                    Value=pf.forms[0],
                    Comment=None,
                    Source=[r.cldf_id for r in pf.sources or []],
                    # Doubt=getattr(form, 'doubt', False),
                )[0]
                for k, gloss in enumerate(pf.glosses, start=1):
                    args.writer.objects['glosses.csv'].append(dict(
                        Form_ID=lex['ID'],
                        ID='{}-{}'.format(lex['ID'], k),
                        Name=gloss.gloss,
                        Comment=gloss.comment,
                        Part_Of_Speech=gloss.pos,
                        Source=[ref.cldf_id for ref in gloss.sources],
                    ))
                if j == 0:
                    pflex = lex
                args.writer.add_cognate(
                    lexeme=lex,
                    Cognateset_ID=rec.id,
                    # Source=[str(ref) for ref in form.gloss.refs],
                    # Doubt=form.doubt,
                )

            pf = pfrep
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

            for w in rec.reflexes:
                # FIXME: supplement glosses from matching, i.e. closest reconstruction!
                assert w.lang in langs
                gloss = w.glosses[0].gloss
                # FIXME: if gloss is None, take the gloss of the POc reconstruction!
                if gloss not in gloss2id:
                    gloss2id[gloss] = slug(gloss or 'none')
                    args.writer.add_concept(ID=slug(gloss or 'none'), Name=gloss)
                lex = args.writer.add_lexemes(
                    Language_ID=langs[w.lang]['ID'],
                    Parameter_ID=gloss2id[gloss],
                    Description=gloss,
                    Value=w.form,
                    Comment=None,
                    Source=[],  # FIXME: add the sources for the language!
                    #Doubt=getattr(form, 'doubt', False),
                )[0]
                for k, gloss in enumerate(w.glosses, start=1):
                    args.writer.objects['glosses.csv'].append(dict(
                        Form_ID=lex['ID'],
                        ID='{}-{}'.format(lex['ID'], k),
                        Name=gloss.gloss,
                        Comment=gloss.comment,
                        Part_Of_Speech=gloss.pos,
                        Source=[ref.cldf_id for ref in gloss.sources],
                    ))
                # FIXME: deduplicate words!
                #forms[lg['ID']][form.form, self.gloss_lookup(form.gloss)] = lex

                args.writer.add_cognate(
                    lexeme=lex,
                    Cognateset_ID=rec.id,
                    #Source=[str(ref) for ref in form.gloss.refs],
                    #Doubt=form.doubt,
                )
            for i, (name, items) in enumerate(rec.cfs, start=1):
                args.writer.objects['cf.csv'].append(dict(
                    ID='{}-{}'.format(rec.id, i),
                    Name=name,
                    Cognateset_ID=rec.id,
                ))
                for j, w in enumerate(items, start=1):
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
                        # Doubt=getattr(form, 'doubt', False),
                    )[0]
                    # FIXME: deduplicate words!
                    # forms[lg['ID']][form.form, self.gloss_lookup(form.gloss)] = lex

                    args.writer.objects['cfitems.csv'].append(dict(
                        ID='{}-{}-{}'.format(rec.id, i, j),
                        Form_ID=lex['ID'],
                        Cfset_ID='{}-{}'.format(rec.id, i),
                        # Source=[str(ref) for ref in form.gloss.refs],
                        # Doubt=form.doubt,
                    ))

    def local_schema(self, cldf):
        """
        Gloss
        - id
        - name (the gloss)
        - comment
        - source
        - number
        - pos
        """
        cldf.add_columns('CognatesetTable', 'Pre_Note', 'Post_Note')
        #
        # FIXME: CognatesetReference: fk to cognateset, fk to chapter, pre_note, post_note, ...
        #
        cldf.add_table(
            'glosses.csv',
            {
                'name': 'ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id'},
            {
                'name': 'Name',
                'dc:description':
                    '',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#name'},
            {
                'name': 'Form_ID',
                'dc:description': 'Links to the form in FormTable.',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#formReference'},
            {
                'name': 'Comment',
                "dc:format": "text/markdown",
                "dc:conformsTo": "CLDF Markdown",
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#comment'},
            {
                'name': 'Source',
                'separator': ';',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source'},
            'Part_Of_Speech'
        )
