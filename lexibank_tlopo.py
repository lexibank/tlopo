import shutil
import pathlib
import functools
import collections

import attr
import pylexibank
from clldutils.misc import slug
from pyetymdict import Dataset as BaseDataset, Language as BaseLanguage, Form as BaseForm
from pylexibank import LexibankWriter, Cognate as BaseCognate
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
class Form(BaseForm):
    Morpheme_Gloss = attr.ib(
        default=None,
        metadata={
            'dc:description':
                'Some forms (often multi-word expressions) are listed with morpheme glosses.'}
    )


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
    lexeme_class = Form

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
        res.data_fnames = {'ContributionTable': 'chapters.csv'}
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
        from pytlopo.parser.refs import refs2bib
        refs2bib(self.raw_dir.joinpath('vol6', 'references.txt').read_text(encoding='utf8').split('\n'))
        return
        #from pytlopo.parser.refs import CROSS_REF_PATTERN
        #for line in self.raw_dir.joinpath('vol1').read('text.txt').split('\n'):
        #    for m in CROSS_REF_PATTERN.finditer(line):
        #        print(m.string[m.start():m.end()])
        #return
        langs = {r['Name']: r for r in self.etc_dir.read_csv('languages.csv', dicts=True)}
        for v in list(langs.values()):
            for alt in v['Alternative_Names'].split('; '):
                langs[alt] = v
        allps = 0
        per_pl = collections.defaultdict(list)
        for vol in range(1, 7):
            print(vol)
            if vol != 6:
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
                words += len(rec.reflexes)
                #if 'Arch' in rec.cat1:
                #    print(rec)
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
            #print(vol.igts)
            for i, rec in enumerate(vol.formgroups):
                str(rec)
            list(vol.chapters)

    @functools.cached_property
    def taxa(self):
        _taxa = {}
        for row in self.etc_dir.read_csv('species_and_genera.csv', dicts=True):
            if row['synonyms']:
                for syn in row['synonyms'].split('; '):
                    _taxa['_' + syn + '_'] = row['ID']
            _taxa['_' + row['name'] + '_'] = row['ID']
        return _taxa

    def add_form(self, writer, protoform_or_reflex, gloss2id, langs, lexid2fn, poc_gloss='none'):
        gloss = protoform_or_reflex.glosses[0].gloss if protoform_or_reflex.glosses else poc_gloss

        if gloss not in gloss2id:
            gloss2id[gloss] = slug(str(gloss))
            writer.add_concept(ID=slug(str(gloss)), Name=gloss)

        if isinstance(protoform_or_reflex, Protoform):
            try:
                lex = writer.add_lexemes(
                ID='{}-{}'.format(slug(protoform_or_reflex.lang), slug(protoform_or_reflex.form)),
                Language_ID=slug(protoform_or_reflex.lang),
                Parameter_ID=gloss2id[gloss],
                Description=gloss,
                Value=protoform_or_reflex.form,
                Comment=protoform_or_reflex.comment,
                Morpheme_Gloss=protoform_or_reflex.morpheme_gloss,
                Source=[r.cldf_id for r in protoform_or_reflex.sources or []],
                # Doubt=getattr(form, 'doubt', False),
                )[0]
            except IndexError:
                print(protoform_or_reflex)
                raise
        else:
            assert isinstance(protoform_or_reflex, Reflex)
            lex = writer.add_lexemes(
                ID='{}-{}'.format(langs[protoform_or_reflex.lang]['ID'], slug(protoform_or_reflex.form)),
                Language_ID=langs[protoform_or_reflex.lang]['ID'],
                Parameter_ID=gloss2id[gloss],
                Description=gloss,
                Value=protoform_or_reflex.form,
                Comment=None,
                Morpheme_Gloss=protoform_or_reflex.morpheme_gloss,
                Source=[],  # FIXME: add the sources for the language!
                # Doubt=getattr(form, 'doubt', False),
            )[0]
        if protoform_or_reflex.footnote_number:
            lexid2fn[lex['ID']] = protoform_or_reflex.footnote_number
        return lex

    def add_glosses(self, writer, protoform_or_reflex, fid, old_glosses, gloss_ids=None):
        if gloss_ids is None:
            gloss_ids = []
        for k, gloss in enumerate(protoform_or_reflex.glosses, start=1):
            if gloss not in old_glosses:
                # Must create a new gloss
                global GLOSS_ID
                GLOSS_ID += 1
                g = dict(
                    Form_ID=fid,
                    ID=str(GLOSS_ID),
                    Name=gloss.gloss,
                    Comment=gloss.comment,
                    Part_Of_Speech=gloss.pos,
                    qualifier=gloss.qualifier,
                    Source=[ref.cldf_id for ref in gloss.sources],
                    Taxon_IDs=sorted(v for k, v in self.taxa.items() if k in (gloss.gloss or '')),
                )
                writer.objects['glosses.csv'].append(g)
                old_glosses[gloss] = g
                gloss_ids.append(g['ID'])
            else:
                # FIXME: make sure the existing gloss has all the metadata of the new one, e.g. comment, source, POS
                og = old_glosses[gloss]
                if gloss.sources:
                    if not og['Source']:
                        og['Source'] = [ref.cldf_id for ref in gloss.sources]
                    else:
                        assert [ref.cldf_id for ref in gloss.sources] == og['Source'], (
                            '{} vs {}'.format(gloss.sources, og['Source']))
                # FIXME: for matching source IDs, merge pages!
                #assert og['Source'] == [ref.cldf_id for ref in gloss.sources], '{} vs. {}'.format(og['Source'], gloss.sources)
                gloss_ids.append(og['ID'])
        return gloss_ids

    def iter_figures(self, md, vol):
        from pycldf.ext.markdown import CLDFMarkdownLink

        source = self.raw_dir / 'vol{}'.format(vol) / 'maps'
        figs = []

        def repl(ml):
            if ml.table_or_fname == 'MediaTable':
                mtype, vnum, fignum = ml.objid.split('-', maxsplit=2)  # translate to filename!
                p = source / '{}_{}.png'.format(mtype, fignum.replace('_', '.'))
                if p.exists():
                    figs.append((ml.objid, ml.label, p))

        CLDFMarkdownLink.replace(md, repl)
        yield from figs

    def cmd_makecldf(self, args):
        self.schema(args.writer.cldf, with_borrowings=False)
        self.local_schema(args.writer.cldf)

        args.writer.cldf.sources = Sources.from_file(self.etc_dir / 'sources.bib')

        langs = {r['Name']: r for r in self.etc_dir.read_csv('languages.csv', dicts=True)}
        reconstructions = []
        for v in list(langs.values()):
            for alt in v['Alternative_Names'].split('; '):
                if alt:
                    langs[alt] = v

        def add_protolang(w):
            if isinstance(w, Protoform) and w.lang not in langs:
                args.writer.add_language(
                    ID=slug(w.lang), Name=slug(w.lang, lowercase=False), Is_Proto=True)
                langs[w.lang] = slug(w.lang)

        chapter_pages = {}
        for md in self.raw_dir.glob('vol*/md.json'):
            for chap in md.parent.read_json(md.name)['chapters']:
                s, _, e = chap['pages'].partition('-')
                chapter_pages['{}-{}'.format(md.parent.name.replace('vol', ''), chap['number'])] = \
                    (int(s), int(e))

        fgs, egs, taxon2sections = [], [], collections.defaultdict(list)
        for vol in range(1, 7):
            #if vol not in {1, 2, 3, 4, 5}:
            #    continue
            t = self.raw_dir / 'vol{}'.format(vol) / 'text.txt'
            if not t.exists():
                continue
            vol = Volume(
                t.parent,
                langs,
                Source.from_bibtex(self.etc_dir.read('citation.bib')),
                args.writer.cldf.sources,
                chapter_pages=chapter_pages,
            )
            for i, rec in enumerate(vol.reconstructions):
                reconstructions.append(rec)
            for i, fg in enumerate(vol.formgroups):
                fgs.append(fg)

            egs.extend(list(vol.igts))
            mddir = self.cldf_dir.joinpath(vol.dir.name)
            mddir.mkdir(exist_ok=True)
            for num, chapter in vol.chapters.items():
                for fid, label, p in self.iter_figures(chapter.text, vol.num):
                    shutil.copy(p, mddir / p.name)
                    args.writer.objects['MediaTable'].append(dict(
                        ID=fid,
                        Name='Volume {} {}'.format(vol.num, p.stem),
                        Description=label,
                        Download_URL=str(mddir.joinpath(p.name).relative_to(self.cldf_dir)),
                        Media_Type='image/png',
                    ))
                p = mddir.joinpath('chapter{}.md'.format(num))
                p.write_text(chapter.text, encoding='utf-8')
                for sid, text in chapter.iter_sections():
                    for k, v in self.taxa.items():
                        if k in text:
                            taxon2sections[v].append(('{}-{}'.format(vol.num, num), sid))
                args.writer.objects['MediaTable'].append(dict(
                    ID='{}-{}-text'.format(vol.num, num),
                    Name='Volume {} Chapter {}'.format(vol.num, num),
                    Description='Chapter text formatted as CLDF Markdown document',
                    Download_URL=str(p.relative_to(self.cldf_dir)),
                    Media_Type='text/markdown',
                    Conforms_To='CLDF Markdown',
                ))
                # look for and copy figures and maps!
                args.writer.objects['ContributionTable'].append(dict(
                    ID='{}-{}'.format(vol.num, num),
                    Name=chapter.bib['title'],
                    Contributor=chapter.bib['author'],
                    # FIXME: pages?
                    Citation=chapter.bib.text(),
                    Volume_Number=vol.num,
                    Volume=vol.metadata['title'],
                    Table_Of_Contents=chapter.toc,
                ))

        for lg in langs.values():
            args.writer.add_language(
                ID=lg['ID'],
                Name=lg['Name'],
                Glottocode=lg['Glottocode'],
                Is_Proto=False, Group=lg['Group'],
                Latitude=lg['Latitude'], Longitude=lg['Longitude'])

        for row in self.etc_dir.read_csv('species_and_genera.csv', dicts=True):
            row['GBIF_ID'] = row['ID']
            row['synonyms'] = [s.strip() for s in (row['synonyms'] or '').split(';') if s.strip()]
            row['sections'] = taxon2sections.get(row['ID'], [])
            args.writer.objects['taxa.csv'].append(row)

        # map (lang, form) pairs to associated glosses (as dict mapping gloss to gloss object with all properties.).
        words, lexid2fn, lexid2doubt = {}, {}, {}
        cognatesets = {}

        gloss2id = {}
        for i, rec in enumerate(reconstructions):
            # Add protoforms and reflex forms and glosses, keep IDs of forms and glosses!
            pfrep, pflex = None, None
            # We store the forms and glosses and footnote numbers listed in this cognateset reference
            forms, gloss_ids, fns = [], [], {}
            poc_gloss = rec.poc_gloss

            for j, pf in enumerate(rec.reflexes):  # FIXME: pf.sources !
                # We have adopted the
                # convention of providing no gloss beside the items in a cognate set whose gloss is identical to
                # that of the POc (or other lower-order) reconstruction at the head of the set, i.e. the reconstruction
                # which they reflect.
                if j == 0:
                    pfrep = pf
                try:
                    pfgloss = pf.glosses[0].gloss
                except IndexError:
                    pfgloss = pf.comment
                if isinstance(pf, Protoform):
                    add_protolang(pf)

                    if (pf.lang, pf.form) not in words:
                        lex = self.add_form(args.writer, pf, gloss2id, langs, lexid2fn)
                        # FIXME: we'll adapt the Description and Parameter_ID lateron, when all glosses have been collected!
                        words[(pf.lang, pf.form)] = (lex, {})
                    else:
                        # FIXME: make sure the other properties are the same, e.g. sources
                        lex = words[(pf.lang, pf.form)][0]

                    self.add_glosses(args.writer, pf, lex['ID'], words[(pf.lang, pf.form)][1], gloss_ids)
                    if pflex is None:
                        pflex = lex
                else:
                    assert isinstance(pf, Reflex)
                    w = pf
                    assert w.lang in langs
                    lid = langs[w.lang]['ID']

                    if (lid, w.form) not in words:
                        lex = self.add_form(args.writer, w, gloss2id, langs, lexid2fn, poc_gloss=poc_gloss)
                        # FIXME: we'll adapt the Description and Parameter_ID lateron, when all glosses have been collected!
                        words[(lid, w.form)] = (lex, {})
                    else:
                        lex = words[(lid, w.form)][0]
                    self.add_glosses(args.writer, w, lex['ID'], words[(lid, w.form)][1], gloss_ids)

                forms.append(lex)
                if pf.footnote_number:
                    fns[lex['ID']] = pf.footnote_number

            if (pfrep.lang, pfrep.form) not in cognatesets:
                args.writer.objects['CognatesetTable'].append(dict(
                    ID=rec.id,
                    Form_ID=pflex['ID'],
                    Name=pfrep.form,
                    Description=pfgloss,
                    Level=pfrep.lang,
                    # Source=['pmr1'],
                    # Doubt=cset.doubt,
                ))
                cognatesets[(pfrep.lang, pfrep.form)] = (rec.id, [])

            csid, cog_forms = cognatesets[(pfrep.lang, pfrep.form)]
            for lex in forms:
                if lex['ID'] not in cog_forms:
                    args.writer.add_cognate(
                        lexeme=lex,
                        Cognateset_ID=csid,
                    )
                    cog_forms.append(lex['ID'])

            args.writer.objects['cognatesetreferences.csv'].append(dict(
                ID=rec.id,
                Cognateset_ID=csid,
                Chapter_ID='-'.join(rec.id.split('-')[:2]),
                # section, subsection, page
                Form_IDs=[f['ID'] for f in forms],
                Footnote_Numbers=fns,
                Gloss_IDs=gloss_ids,
            ))

            for i, (name, items) in enumerate(rec.cfs, start=1):
                #
                # FIXME: inherit gloss from proto-form gloss!
                #
                args.writer.objects['cf.csv'].append(dict(
                    ID='{}-{}'.format(rec.id, i),
                    Name=name,
                    Cognateset_ID=csid,
                    CognatesetReference_ID=rec.id,
                    Chapter_ID='-'.join(rec.id.split('-')[:2]),
                ))
                for j, w in enumerate(items, start=1):
                    add_protolang(w)
                    assert w.lang in langs, w.lang
                    lid = langs[w.lang]['ID'] if isinstance(langs[w.lang], dict) else langs[w.lang]

                    if (lid, w.form) not in words:
                        lex = self.add_form(args.writer, w, gloss2id, langs, lexid2fn, poc_gloss=poc_gloss)
                        words[(lid, w.form)] = (lex, {})
                    else:
                        lex = words[(lid, w.form)][0]

                    args.writer.objects['cfitems.csv'].append(dict(
                        ID='{}-{}-{}'.format(rec.id, i, j),
                        Form_ID=lex['ID'],
                        Ordinal=j,
                        Cfset_ID='{}-{}'.format(rec.id, i),
                        Footnote_Number=lexid2fn.get(lex['ID']),
                        Gloss_IDs=self.add_glosses(args.writer, w, lex['ID'], words[(lid, w.form)][1]),
                        # Source=[str(ref) for ref in form.gloss.refs],
                        # Doubt=form.doubt,
                    ))

        for fg in fgs:
            args.writer.objects['cf.csv'].append(dict(
                ID=fg.id,
                Name=fg.id,
                Cognateset_ID=None,
                CognatesetReference_ID=None,
                Chapter_ID='-'.join(fg.id.split('-')[:2]),
            ))
            for j, w in enumerate(fg.forms, start=1):
                add_protolang(w)
                assert w.lang in langs
                lid = langs[w.lang]['ID']

                if (lid, w.form) not in words:
                    lex = self.add_form(args.writer, w, gloss2id, langs, lexid2fn)
                    words[(lid, w.form)] = (lex, {})
                else:
                    lex = words[(lid, w.form)][0]

                args.writer.objects['cfitems.csv'].append(dict(
                    ID='{}-{}'.format(fg.id, j),
                    Form_ID=lex['ID'],
                    Cfset_ID=fg.id,
                    Footnote_Number=lexid2fn.get(lex['ID']),
                    Ordinal=j,
                    Gloss_IDs=self.add_glosses(args.writer, w, lex['ID'], words[(lid, w.form)][1]),
                    # Source=[str(ref) for ref in form.gloss.refs],
                ))
        for eg in egs:
            for ex in eg.examples:
                args.writer.objects['ExampleTable'].append(dict(
                    ID=ex.id,
                    Primary_Text=ex.igt.primary_text,
                    Language_ID=langs[ex.language] if isinstance(langs[ex.language], str) else langs[ex.language]['ID'],
                    Analyzed_Word=ex.analyzed,
                    Gloss=ex.gloss,
                    Translated_Text=ex.translation,
                    label=ex.label,
                    Movement_Gloss=ex.add_gloss,
                    Source=[ex.reference.cldf_id] if ex.reference else [],
                    Reference_Label=ex.reference.label if ex.reference else '',
                    Comment=ex.comment,
                ))
            args.writer.objects['examplegroups.csv'].append(dict(
                ID=eg.id,
                Number=eg.number,
                Example_IDs=[ex.id for ex in eg.examples],
                Context=eg.context,
            ))

    def local_schema(self, cldf):
        """
        Gloss
        - number
        """
        #
        # Add GBIF ID to ParameterTable and store taxa as parameters!
        #
        cldf.add_table(
            'examplegroups.csv',
            {
                'name': 'ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id'},
            {
                'name': 'Example_IDs',
                'separator': ' ',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#exampleReference'},
            'Number',
            {
                'name': 'Context',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#comment'},
        )
        cldf.add_component(
            'ExampleTable',
            {
                'name': 'Source',
                'separator': ';',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source'},
            'Reference_Label',
            'label',
            {
                'name': 'Movement_Gloss',
                'separator': '\t',
            },
        )
        cldf.add_component(
            'MediaTable',
            {
                'name': 'Chapter_ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#contributionReference'},
            {
                'name': 'Conforms_To',
                'propertyUrl': 'http://purl.org/dc/terms/conformsTo'},
        )
        cldf.add_columns('CognatesetTable', 'Level')
        cldf.add_columns(
            'cf.csv',
            {
                'name': 'CognatesetReference_ID',
            },
        )
        cldf.add_columns(
            'ContributionTable',
            {'name': 'Volume_Number', 'datatype': 'integer'},
            'Volume',
            {'name': 'Table_Of_Contents', 'datatype': 'json'},
        )
        cldf.add_table(
            'cognatesetreferences.csv',
            #
            # FIXME: store IDs of taxa mentioned in glosses of reflexes!
            #
            {
                'name': 'ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id'},
            {
                'name': 'Cognateset_ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#cognatesetReference'},
            {
                'name': 'Chapter_ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#contributionReference'},
            # Cognateset references are selections of forms and specific glosses from a bigger,
            # somewhat gloss-agnostic cognateset.
            {
                'name': 'Form_IDs',
                'separator': ' ',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#formReference'},
            {
                'name': 'Footnote_Numbers',  # Must store fn for each form!
                'datatype': 'json'},
            {
                'name': 'Gloss_IDs',
                'separator': ' '},
        )
        cldf.add_columns(
            'cf.csv',
            {
                'name': 'Chapter_ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#contributionReference'},
        )
        cldf.add_columns(
            'cfitems.csv',
            'Footnote_Number',
            {'name': 'Ordinal', 'datatype': 'integer'},
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
                'name': 'Taxon_IDs',
                'separator': ' ',
            },
            'qualifier',
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
        cldf.add_table(
            'taxa.csv',
            {'name': 'ID', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id'},
            {'name': 'GBIF_ID', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#gbifReference'},
            {'name': 'name', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#name'},
            {'name': 'name_eng'},
            {'name': 'rank'},  # FIXME: one of SPCIES|GENUS
            {'name': 'kingdom'},
            {'name': 'phylum'},
            {'name': 'class'},
            {'name': 'order'},
            {'name': 'family'},
            {'name': 'genus'},
            {'name': 'genus_eng'},
            {'name': 'family_eng'},
            {'name': 'synonyms', 'separator': '; '},
            {'name': 'sections', 'datatype': 'json'},
        )
        cldf.add_foreign_key('glosses.csv', 'Taxon_IDs', 'taxa.csv', 'ID')
        cldf.add_foreign_key('cfitems.csv', 'Gloss_IDs', 'glosses.csv', 'ID')
        cldf.add_foreign_key('cognatesetreferences.csv', 'Gloss_IDs', 'glosses.csv', 'ID')
        cldf.add_foreign_key('cf.csv', 'CognatesetReference_ID', 'cognatesetreferences.csv', 'ID')
