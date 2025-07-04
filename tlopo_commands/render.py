"""
Run

$ pandoc -s -f markdown -t html5 out/vol1/chapter3.md -c pandoc.css  > c3.html

to create HTML!
"""
import shlex
import itertools
import subprocess
import collections

from tqdm import tqdm
from jinja2.filters import FILTERS

from markdown import markdown

from cldfviz.text import render
from clldutils.html import HTML
from pycldf.db import Database
from pycldf.media import MediaTable
from clldutils.misc import data_url

from lexibank_tlopo import Dataset


def md_string(s):
    return markdown(s).replace('<p>', '<span>').replace('</p>', '</span>')


FILTERS['markdown'] = md_string


def register(parser):
    parser.add_argument('--chapter', default=None)
    parser.add_argument('--index', action='store_true', default=False)


def run(args):
    ds = Dataset()
    out = ds.dir / 'out'
    if not out.exists():
        out.mkdir()
    cldf = ds.cldf_reader()
    media = {f.row['ID']: f for f in MediaTable(cldf)}
    #
    # Must precompute data for cognatesetreferences and store with cldf!
    #
    # create in-memory sqlite db!

    if args.index:
        for (vnum, vol), chapters in itertools.groupby(
                cldf.iter_rows('ContributionTable'),
                lambda r: (r['Volume_Number'], r['Volume'])
        ):
            print(HTML.h2('Volume {}: {}'.format(vnum, vol)))

            l1 = []
            for chapter in chapters:
                secs = HTML.ol(*[HTML.li(HTML.a(t, href="vol{}/chapter{}.html#{}".format(vnum, chapter['ID'].split('-')[-1], a))) for l, a, t in chapter['Table_Of_Contents'] if l == 1])
                l1.append(HTML.li(chapter['Name'], HTML.br(), HTML.i(chapter['Contributor']), secs))
            print(HTML.html(HTML.body(HTML.ol(*l1))))

        return

    db = Database(cldf)
    db.write_from_tg()

    def f(rid):
        # `cognatesetreferences.csv_FormTable`
        # `cognatesetreferences.csv_glosses.csv`
        q = """
select f.cldf_id, l.`Group`, l.cldf_name, l.cldf_id, l.is_proto, f.cldf_value 
from 
  `cognatesetreferences.csv_FormTable` as csrf 
  join formtable as f on (csrf.formtable_cldf_id = f.cldf_id)
  join languagetable as l on f.cldf_languageReference = l.cldf_id
where csrf.`cognatesetreferences.csv_cldf_id` = ?
"""
        return db.query(q, (rid,))

    def cfs(rid):
        q = """
            select cf.cldf_id, \
                   cf.cldf_name, \
                   l.`Group`, \
                   l.cldf_name, \
                   l.is_proto, \
                   f.cldf_value, \
                   g.cldf_name, \
                   g.cldf_comment, \
                   g.Part_Of_Speech, \
                   gs.SourceTable_id, \
                   gs.context
            from `cf.csv` as cf \
                     join `cfitems.csv` as c on (cf.cldf_id = c.Cfset_ID) \
                     join formtable as f on (c.cldf_formReference = f.cldf_id) \
                     join languagetable as l on f.cldf_languageReference = l.cldf_id \
                     left join `cfitems.csv_glosses.csv` as cfg on c.cldf_id = cfg.`cfitems.csv_cldf_id`
                     left join `glosses.csv` as g on cfg.`glosses.csv_cldf_id` = g.cldf_id
                     left join `glosses.csv_SourceTable` as gs \
                               on gs.`glosses.csv_cldf_id` = g.cldf_id
            where cf.cognatesetreference_id = ?
            order by cf.cldf_id, c.ordinal \
            """
        res = collections.OrderedDict()
        for cfid, rows in itertools.groupby(db.query(q, (rid,)), lambda r: r[0]):
            # _, cfname, group, lname, _, form, gloss, cmt, pos, srcid, pages
            rows = list(rows)
            res[(cfid, rows[0][1])] = []
            for (group, lname, form), glosses in itertools.groupby(rows, lambda r: (r[2], r[3],
                                                                                    r[5])):
                res[(cfid, rows[0][1])].append((group, lname, form, []))
                for (g, cmt, pos), sources in itertools.groupby(glosses,
                                                                lambda r: (r[6], r[7], r[8])):
                    res[(cfid, rows[0][1])][-1][-1].append(
                        (g, cmt, pos, [(r[-2], r[-1]) for r in sources if r[-2]]))
        return collections.OrderedDict(
            ((k[0], (k[1] or '').replace('*', '&ast;')), v) for k, v in res.items())

    def cfitems(cfid):
        q = """
select l.`Group`, l.cldf_name, l.is_proto, f.cldf_value, f.Morpheme_Gloss, g.cldf_name, g.cldf_comment, g.Part_Of_Speech, gs.SourceTable_id, gs.context
from 
      `cf.csv` as cf
      join `cfitems.csv` as c on (cf.cldf_id = c.Cfset_ID)
      join formtable as f on (c.cldf_formReference = f.cldf_id)
      join languagetable as l on f.cldf_languageReference = l.cldf_id      
      left join `cfitems.csv_glosses.csv` as cfg on c.cldf_id = cfg.`cfitems.csv_cldf_id`
      left join `glosses.csv` as g on cfg.`glosses.csv_cldf_id` = g.cldf_id
      left join `glosses.csv_SourceTable` as gs on gs.`glosses.csv_cldf_id` = g.cldf_id
where cf.cldf_id = ?
"""
        res = []
        rows = db.query(q, (cfid,))
        with_morpheme_gloss = False
        for (group, lname, form, mgloss), glosses in itertools.groupby(rows, lambda r: (r[0], r[1], r[3], r[4])):
            res.append((group, lname, form, mgloss, []))
            if mgloss:
                with_morpheme_gloss = True
            for (g, cmt, pos), sources in itertools.groupby(glosses, lambda r: (r[5], r[6], r[7])):
                res[-1][-1].append((g, cmt, pos, [(r[-2], r[-1]) for r in sources if r[-2]]))
        # FIXME: determine whether there are non-empty morpheme glosses!
        return res, with_morpheme_gloss

    def glosses_by_formid(rid):
        def iter_glosses(rows):
            for (g, cmt, pos), srcs in itertools.groupby(rows, lambda row: row[1:4]):
                yield (g or '', cmt or '', pos, [(row[-2], row[-1]) for row in srcs if row[-2]])

        q = """
select g.cldf_formReference, g.cldf_name, g.cldf_comment, g.Part_Of_Speech, gs.SourceTable_id, gs.context
from 
      `cognatesetreferences.csv_glosses.csv` as csrg 
      join `glosses.csv` as g on csrg.`glosses.csv_cldf_id` = g.cldf_id
      left join `glosses.csv_SourceTable` as gs on gs.`glosses.csv_cldf_id` = g.cldf_id
where csrg.`cognatesetreferences.csv_cldf_id` = ?
order by g.cldf_formReference
"""
        return {fid: list(iter_glosses(rows)) for fid, rows in itertools.groupby(db.query(q, (rid,)), lambda r: r[0])}

    def pandoc(input, md):
        subprocess.check_call(shlex.split(
            'pandoc --metadata title="{}" -s -f markdown -t html5 -c ../../pandoc_book.css {} -o {}/{}.html'.format(
                md['title'], input, input.parent, input.stem)))

    out.joinpath('references.md').write_text(render(
        '# References\n\n[](Source?with_anchor&with_link#cldf:__all__)', cldf), encoding='utf-8')
    pandoc(out.joinpath('references.md'), dict(title='References'))

    v, c = None, None
    if args.chapter:
        v, _, c = args.chapter.partition('-')

    for vol in "123456":
        if v and vol != v:
            continue
        md = ds.raw_dir.joinpath('vol{}'.format(vol)).read_json('md.json')
        vout = out / 'vol{}'.format(vol)
        if not vout.exists():
            vout.mkdir()
        else:
            for p in vout.iterdir():
                if p.is_file():
                    p.unlink()
        for chapter in tqdm(ds.cldf_dir.joinpath('vol{}'.format(vol)).glob('chapter*.md')):
            cnum = chapter.stem.replace('chapter', '')
            if c and cnum != c:
                continue
            for cmd in md['chapters']:
                if cmd['number'] == cnum:
                    break
            else:
                raise ValueError((vol, cnum))
            res = render(
                chapter,
                cldf,
                template_dir=ds.dir / 'templates',
                func_dict=dict(
                    href_source=lambda srcid: '../sources/' + srcid,
                    href_language=lambda lid: '../languages/' + lid,
                    href_chapter=lambda cid, anchor: '../contributions/{}#{}'.format(cid, anchor),
                    href_media=lambda mid: data_url(media[mid].read(), 'image/png'),
                    get_reconstruction=f,
                    get_cfs=cfs,
                    get_cfitems=cfitems,
                    glosses_by_formid=glosses_by_formid),
            )
            vout.joinpath(chapter.name).write_text(render(res, ds.cldf_reader()), encoding='utf-8')
            pandoc(vout.joinpath(chapter.name), cmd)
