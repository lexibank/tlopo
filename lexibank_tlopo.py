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

    def cmd_download(self, args):
        pass

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

        kw = dict(
                Parameter_ID=gloss2id[gloss],
                Description=gloss,
                Value=protoform_or_reflex.form,
                Morpheme_Gloss=protoform_or_reflex.morpheme_gloss,
            )

        if isinstance(protoform_or_reflex, Protoform):
            kw.update(
                ID='{}-{}'.format(slug(protoform_or_reflex.lang), slug(protoform_or_reflex.form)),
                Language_ID=slug(protoform_or_reflex.lang),
                Source=[r.cldf_id for r in protoform_or_reflex.sources or []],
                # Doubt=getattr(form, 'doubt', False),
            )
        else:
            assert isinstance(protoform_or_reflex, Reflex)
            kw.update(
                ID='{}-{}'.format(langs[protoform_or_reflex.lang]['ID'], slug(protoform_or_reflex.form)),
                Language_ID=langs[protoform_or_reflex.lang]['ID'],
                Comment=None,
                Morpheme_Gloss=protoform_or_reflex.morpheme_gloss,
                # Hm. we add Source for the individual gloss.
                Source=[],  # FIXME: add the sources for the language!
                # Doubt=getattr(form, 'doubt', False),
            )
        lex = writer.add_lexemes(**kw)[0]
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
                                '{}: {} vs {}'.format(protoform_or_reflex, gloss.sources, og['Source']))
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
                    ID=slug(w.lang), Name=w.lang, Is_Proto=True)
                langs[w.lang] = slug(w.lang)

        chapter_pages = {}
        for md in self.raw_dir.glob('vol*/md.json'):
            for chap in md.parent.read_json(md.name)['chapters']:
                s, _, e = chap['pages'].partition('-')
                chapter_pages['{}-{}'.format(md.parent.name.replace('vol', ''), chap['number'])] = \
                    (int(s), int(e))

        fgs, egs, taxon2sections = [], [], collections.defaultdict(list)
        for vol in range(1, 7):
            t = self.raw_dir / 'vol{}'.format(vol) / 'text.txt'
            if not t.exists():
                continue
            vol = Volume(
                t.parent,
                langs,
                Source.from_bibtex(self.etc_dir.read('citation.bib')),
                args.writer.cldf.sources,
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
                args.writer.objects['ContributionTable'].append(dict(
                    ID='{}-{}'.format(vol.num, num),
                    Name=chapter.bib['title'],
                    Contributor=chapter.bib['author'],
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
            forms, gloss_ids, fns, sgmap = [], [], {}, {}
            poc_gloss = rec.poc_gloss

            for j, pf in enumerate(rec.reflexes):  # FIXME: pf.sources !
                # We have adopted the
                # convention of providing no gloss beside the items in a cognate set whose gloss is identical to
                # that of the POc (or other lower-order) reconstruction at the head of the set, i.e. the reconstruction
                # which they reflect.
                if j == 0:
                    pfrep = pf
                pfgloss = pf.glosses[0].gloss if pf.glosses else pf.comment
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
                if pf.subgroup:
                    sgmap[lex['ID']] = pf.subgroup
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
                    args.writer.add_cognate(lexeme=lex, Cognateset_ID=csid)
                    cog_forms.append(lex['ID'])

            args.writer.objects['cognatesetreferences.csv'].append(dict(
                ID=rec.id,
                Cognateset_ID=csid,
                Chapter_ID='-'.join(rec.id.split('-')[:2]),
                # section, subsection, page
                Form_IDs=[f['ID'] for f in forms],
                Footnote_Numbers=fns,
                Gloss_IDs=gloss_ids,
                Subgroup_Mapping=sgmap,
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
            {  # Map Form_ID to subgroup name in case the reflexes are organized like that.
                'name': 'Subgroup_Mapping',
                'datatype': 'json'},
            {  # Map Form_ID to footnote number
                'name': 'Footnote_Numbers',
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
            'qualifier',  # A gloss number or other kind of qualifier.
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
            {'name': 'rank', 'datatype': {'base': 'string', 'format': 'SPECIES|GENUS'}},
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
