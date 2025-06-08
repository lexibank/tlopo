import pathlib
import collections

import attr
import pylexibank
from clldutils.misc import slug
from pyetymdict import Dataset as BaseDataset, Language as BaseLanguage
from pylexibank import LexibankWriter
from pycldf.sources import Source, Sources

from pytlopo.models import Volume, Reflex, Protoform

GLOSS_ID = 0


class TlopoWriter(LexibankWriter):
    def lexeme_id(self, kw):
        form = slug(kw['Value'])
        self._count[(kw['Language_ID'], form)] += 1
        return '{0}-{1}-{2}'.format(
            kw['Language_ID'],
            form,
            self._count[(kw['Language_ID'], form)])


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
        strip_inside_brackets=True,   # do you want data removed in brackets or not?
        first_form_only=True,
    )

    def cldf_specs(self):
        res = super().cldf_specs()
        res.writer_cls = TlopoWriter
        return res

    def __cmd_download(self, args):
        from csvw.dsv import reader, UnicodeWriter
        import sqlite3
        conn = sqlite3.connect("tlopo.sqlite")
        rows = []
        for n, lg, wd, gl in conn.execute(
            "select count(cldf_id) as c, cldf_languageReference, cldf_value, group_concat(cldf_description, ' / ') "
            "from formtable group by cldf_languageReference, cldf_value having c > 1 order by c;"
        ):
            if gl:
                gls = gl.split(' / ')
                if len(set(gls)) > 1:
                    glsets = [set(s.strip() for s in g.split(';')) for g in gls]
                    if not glsets[0].intersection(*glsets[1:]):
                        for g in sorted(set(gls)):
                            rows.append([n, lg, wd, g])
        #print(i, len(rows))
        with UnicodeWriter(self.dir / 'multi_problems.tsv', delimiter='\t') as w:
            w.writerow(['Count', 'Language', 'Form', 'Glosses'])
            w.writerows(rows)
        return

    def cmd_gbif(self, args):
        import pygbif
        import re
        from pytlopo.config import re_choice

        def iter_names(f):
            for row in f:
                yield row['Scientific_Name']
                if row['Name_In_Text']:
                    yield row['Name_In_Text']
                if len(row['Scientific_Name'].split()) == 2:  # a binomial
                    g, s = row['Scientific_Name'].split()
                    yield '{}. {}'.format(g[0], s)

        pattern = re.compile(
            re_choice(
                list(iter_names(self.raw_dir.joinpath('vol3').read_csv('taxa.csv', dicts=True)))))

        for m in pattern.finditer(self.raw_dir.joinpath('vol3').read('text.txt')):
            if m.string[m.start() - 1] == '_':
                print(m.string[m.start() - 1:m.end() + 1])

        return
        pygbif.caching(True, name='gbif.sqlite')
        names = set()
        for row in self.raw_dir.joinpath('vol3').read_csv('taxa.csv'):
            res = pygbif.species.name_suggest(q=re.sub(r'\s+spp?\.?$', '', row[0].strip()))
            if not res:
                res = pygbif.species.name_lookup(q=re.sub(r'\s+spp?\.?$', '', row[0].strip()))

            assert res, row
            for r in res:
                if 'nubKey' in r:
                    nub = r['nubKey']
                    break
            else:
                raise ValueError(re.sub(r'\s+spp?\.?$', '', row[0].strip()), row[0])
            def fmt(s):
                if s is None:
                    return ''
                s = s.strip()
                if not s:
                    return ''
                if ',' not in s:
                    return s
                return '"{}"'.format(s)

            vernacular_names = pygbif.species.name_usage(key=nub, data="vernacularNames")
            english_names = [name["vernacularName"] for name in vernacular_names["results"] if name["language"] == "eng" and name.get("preferred")]
            if not english_names:
                english_names = [name["vernacularName"] for name in vernacular_names["results"]
                                 if name["language"] == "eng"]
            #if english_names:
            print(','.join([row[0].strip(), row[1].strip() if len(row) > 1 else '', str(nub), fmt(english_names[0] if english_names else '')]))
            #print(row['Scientific_Name'], nub, english_names[0])
            #>>> english_names
            #['Coconut Crab']
            #break
        return

    def cmd_download(self, args):
        #from pytlopo.parser.refs import refs2bib
        #refs2bib(self.raw_dir.joinpath('vol3', 'references.txt').read_text(encoding='utf8').split('\n'))
        #return
        #from pytlopo.parser.refs import CROSS_REF_PATTERN
        #for line in self.raw_dir.joinpath('vol1').read('text.txt').split('\n'):
        #    for m in CROSS_REF_PATTERN.finditer(line):
        #        print(m.string[m.start():m.end()])
        #return
        langs = {r['Name']: r for r in self.raw_dir.joinpath('vol1').read_csv('languages.csv', dicts=True)}
        for v in list(langs.values()):
            for alt in v['Alternative_Names'].split('; '):
                langs[alt] = v
        allps = 0
        per_pl = collections.defaultdict(list)
        for vol in range(1, 7):
            print(vol)
            if vol != 5:
                continue
            t = self.raw_dir / 'vol{}'.format(vol) / 'text.txt'
            if not t.exists():
                continue
            vol = Volume(t.parent, langs, Source.from_bibtex(self.etc_dir.read('citation.bib')), Sources.from_file(self.etc_dir / 'sources.bib'))
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
            print(vol.igts)

    def add_form(self, writer, protoform_or_reflex, gloss2id, langs, poc_gloss='none'):
        gloss = protoform_or_reflex.glosses[0].gloss if protoform_or_reflex.glosses else poc_gloss

        if gloss not in gloss2id:
            gloss2id[gloss] = slug(str(gloss))
            writer.add_concept(ID=slug(str(gloss)), Name=gloss)

        if isinstance(protoform_or_reflex, Protoform):
            return writer.add_lexemes(
                ID='{}-{}'.format(slug(protoform_or_reflex.protolanguage), slug(protoform_or_reflex.form)),
                Language_ID=slug(protoform_or_reflex.protolanguage),
                Parameter_ID=gloss2id[gloss],
                Description=gloss,
                Value=protoform_or_reflex.form,
                Comment=protoform_or_reflex.comment,
                Source=[r.cldf_id for r in protoform_or_reflex.sources or []],
                # Doubt=getattr(form, 'doubt', False),
            )[0]
        else:
            assert isinstance(protoform_or_reflex, Reflex)
            return writer.add_lexemes(
                ID='{}-{}'.format(langs[protoform_or_reflex.lang]['ID'], slug(protoform_or_reflex.form)),
                Language_ID=langs[protoform_or_reflex.lang]['ID'],
                Parameter_ID=gloss2id[gloss],
                Description=gloss,
                Value=protoform_or_reflex.form,
                Comment=None,
                Source=[],  # FIXME: add the sources for the language!
                # Doubt=getattr(form, 'doubt', False),
            )[0]

    def add_glosses(self, writer, protoform_or_reflex, fid, old_glosses, gloss_ids):
        for k, gloss in enumerate(protoform_or_reflex.glosses, start=1):
            if gloss.gloss not in old_glosses:
                # Must create a new gloss
                global GLOSS_ID
                GLOSS_ID += 1
                g = dict(
                    Form_ID=fid,
                    ID=str(GLOSS_ID),
                    Name=gloss.gloss,
                    Comment=gloss.comment,
                    Part_Of_Speech=gloss.pos,
                    Source=[ref.cldf_id for ref in gloss.sources],
                )
                writer.objects['glosses.csv'].append(g)
                old_glosses[gloss.gloss] = g
                gloss_ids.append(g['ID'])
            else:
                # FIXME: make sure the existing gloss has all the metadata of the new one, e.g. comment, source, POS
                og = old_glosses[gloss.gloss]
                # FIXME: aggregate comments!
                #assert (not og['Comment']) or (not gloss.comment) or og['Comment'] == gloss.comment, '{} vs. {}'.format(og['Comment'], gloss.comment)
                #assert og['Part_Of_Speech'] == gloss.pos
                # FIXME: for matching source IDs, merge pages!
                #assert og['Source'] == [ref.cldf_id for ref in gloss.sources], '{} vs. {}'.format(og['Source'], gloss.sources)
                gloss_ids.append(og['ID'])

    def cmd_makecldf(self, args):
        self.schema(args.writer.cldf, with_borrowings=False)
        self.local_schema(args.writer.cldf)

        args.writer.cldf.sources = Sources.from_file(self.etc_dir / 'sources.bib')

        langs = {r['Name']: r for r in self.raw_dir.joinpath('vol1').read_csv('languages.csv', dicts=True)}
        reconstructions = []
        for v in list(langs.values()):
            for alt in v['Alternative_Names'].split('; '):
                langs[alt] = v

        for vol in range(1, 7):
            if vol not in {1, 2, 3, 4}:
                continue
            t = self.raw_dir / 'vol{}'.format(vol) / 'text.txt'
            if not t.exists():
                continue
            vol = Volume(t.parent, langs, Source.from_bibtex(self.etc_dir.read('citation.bib')), args.writer.cldf.sources)
            for i, rec in enumerate(vol.reconstructions):
                reconstructions.append(rec)
            mddir = self.cldf_dir.joinpath(vol.dir.name)
            mddir.mkdir(exist_ok=True)
            for num, chapter in vol.chapters.items():
                mddir.joinpath('chapter{}.md'.format(num)).write_text(chapter.text)
                args.writer.objects['ContributionTable'].append(dict(
                    ID='{}-{}'.format(vol.num, num),
                    Name=chapter.bib['title'],
                ))

        for lg in langs.values():
            args.writer.add_language(
                ID=lg['ID'], Name=lg['Name'], Is_Proto=False, Group=lg['Group'],
                Latitude=lg['Latitude'], Longitude=lg['Longitude'])

        # map (lang, form) pairs to associated glosses (as dict mapping gloss to gloss object with all properties.).
        words = {}
        cognatesets = {}

        gloss2id = {}
        for i, rec in enumerate(reconstructions):
            # Add protoforms and reflex forms and glosses, keep IDs of forms and glosses!
            pfrep, pflex = None, None
            forms, gloss_ids = [], []  # We store the forms and glosses listed in this cognateset reference
            poc_gloss = None

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

                if pf.protolanguage == 'POc' and not poc_gloss and pf.glosses:
                    # FIXME: if gloss is None, take the gloss of the POc (or lower!) reconstruction!
                    poc_gloss = pf.glosses[0].gloss

                if (pf.protolanguage, pf.form) not in words:
                    lex = self.add_form(args.writer, pf, gloss2id, langs)
                    # FIXME: we'll adapt the Description and Parameter_ID lateron, when all glosses have been collected!
                    words[(pf.protolanguage, pf.form)] = (lex, {})
                else:
                    # FIXME: make sure the other properties are the same, e.g. sources
                    lex = words[(pf.protolanguage, pf.form)][0]

                forms.append(lex)
                self.add_glosses(args.writer, pf, lex['ID'], words[(pf.protolanguage, pf.form)][1], gloss_ids)

                if j == 0:
                    pflex = lex

            for w in rec.reflexes:
                # FIXME: supplement glosses from matching, i.e. closest reconstruction!
                assert w.lang in langs
                lid = langs[w.lang]['ID']

                if (lid, w.form) not in words:
                    lex = self.add_form(args.writer, w, gloss2id, langs, poc_gloss=poc_gloss)
                    # FIXME: we'll adapt the Description and Parameter_ID lateron, when all glosses have been collected!
                    words[(lid, w.form)] = (lex, {})
                else:
                    lex = words[(lid, w.form)][0]

                forms.append(lex)
                self.add_glosses(args.writer, w, lex['ID'], words[(lid, w.form)][1], gloss_ids)

            if (pfrep.protolanguage, pfrep.form) not in cognatesets:
                args.writer.objects['CognatesetTable'].append(dict(
                    ID=rec.id,
                    Form_ID=pflex['ID'],
                    Comment='\n\n'.join(line.replace('*', '&ast;') for line in rec.desc()),
                    Name=pfrep.form,
                    Description=pfgloss,
                    Level=pfrep.protolanguage,
                    # Source=['pmr1'],
                    # Doubt=cset.doubt,
                ))
                cognatesets[(pfrep.protolanguage, pfrep.form)] = (rec.id, [])

            csid, cog_forms = cognatesets[(pfrep.protolanguage, pfrep.form)]
            for lex in forms:
                if lex['ID'] not in cog_forms:
                    args.writer.add_cognate(lexeme=lex, Cognateset_ID=csid)
                    cog_forms.append(lex['ID'])

            args.writer.objects['cognatesetreferences.csv'].append(dict(
                ID=rec.id,
                Cognateset_ID=csid,
                Contribution_ID='-'.join(rec.id.split('-')[:2]),
                # section, subsection, page
                Form_IDs=[f['ID'] for f in forms],
                Gloss_IDs=gloss_ids,
            ))

            for i, (name, items) in enumerate(rec.cfs, start=1):
                # We simply link cf sets to cognatesetreferences!
                #if known_cogset:
                #    print('cf table {} for known cogset!: {}'.format(i, rec.id))
                #
                # FIXME: cfsets must also remember gloss_ids!
                #
                args.writer.objects['cf.csv'].append(dict(
                    ID='{}-{}'.format(rec.id, i),
                    Name=name,
                    Cognateset_ID=csid,
                    CognatesetReference_ID=rec.id,
                ))
                for j, w in enumerate(items, start=1):
                    assert w.lang in langs
                    lid = langs[w.lang]['ID']

                    if (lid, w.form) not in words:
                        lex = self.add_form(args.writer, w, gloss2id, langs, poc_gloss=poc_gloss)
                        words[(lid, w.form)] = (lex, {})
                    else:
                        lex = words[(lid, w.form)][0]
                    self.add_glosses(args.writer, w, lex['ID'], words[(lid, w.form)][1], [])

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
        - number
        """
        cldf.add_columns('CognatesetTable', 'Level')
        cldf.add_columns(
            'cf.csv',
            {
                'name': 'CognatesetReference_ID',
            },
        )
        cldf.add_component('ContributionTable')
        cldf.add_table(
            'cognatesetreferences.csv',
            {
                'name': 'ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id'},
            {
                'name': 'Cognateset_ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#cognatesetReference'},
            {
                'name': 'Form_IDs',
                'separator': ' ',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#formReference'},
            {
                'name': 'Gloss_IDs',
                'separator': ' '},
        )
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
        cldf.add_foreign_key('cognatesetreferences.csv', 'Gloss_IDs', 'glosses.csv', 'ID')
        cldf.add_foreign_key('cf.csv', 'CognatesetReference_ID', 'cognatesetreferences.csv', 'ID')
