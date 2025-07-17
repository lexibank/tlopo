"""
Run

$ pandoc -s -f markdown -t html5 out/vol1/chapter3.md -c pandoc.css  > c3.html

to create HTML!
"""
import json
import shlex
import sqlite3
import itertools
import subprocess
import collections

from tqdm import tqdm
from jinja2.filters import FILTERS

from markdown import markdown

from cldfviz.text import render
from clldutils.html import HTML
from pycldf.db import Database as BaseDatabase
from pycldf.media import MediaTable
from clldutils.misc import data_url

from lexibank_tlopo import Dataset



class Database(BaseDatabase):
    def query(self, sql: str, params=None) -> list:
        with self.connection() as conn:
            cu = conn.cursor()
            cu.row_factory = sqlite3.Row
            cu.execute(sql, params or ())
            return list(cu.fetchall())


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

    def eg(egid):
        q = """
            select gr.number, gr.cldf_comment, ex.label, l.cldf_name, l.`Group`, ex.cldf_analyzedWord, ex.cldf_gloss, ex.cldf_translatedText, ex.cldf_comment, exs.SourceTable_id, ex.Reference_Label \
            from ExampleTable as ex \
                     join `examplegroups.csv_ExampleTable` as eggr on (ex.cldf_id = eggr.ExampleTable_cldf_id) \
                     join `examplegroups.csv` as gr on (gr.cldf_id = eggr.`examplegroups.csv_cldf_id`) \
                     join languagetable as l on (ex.cldf_languageReference = l.cldf_id) \
                     left join ExampleTable_SourceTable as exs on ex.cldf_id = exs.ExampleTable_cldf_id
            where gr.cldf_id = ? \
            """
        num, ctx, ex, labels = None, None, [], False
        rows = db.query(q, (egid,))
        for row in rows:
            row = list(row)
            if row[0]:
                num = row[0]
            if row[1]:
                ctx = row[1]
            if row[2]:
                labels = True
            row[5] = [s.replace('[', r'\[').replace(']', r'\]') for s in row[5].split()]
            row[6] = [s.replace('[', r'\[').replace(']', r'\]') for s in row[6].split()]
            ex.append(row[3:])
        return num, ctx, labels, ex

    def f(rid):
        # `cognatesetreferences.csv_FormTable`
        # `cognatesetreferences.csv_glosses.csv`
        q = """
select f.cldf_id as id, 
       l.`Group` as `group`, 
       l.cldf_name as lname, 
       l.cldf_id as lid, 
       l.is_proto, 
       f.cldf_value as form, 
       csr.footnote_numbers as fn
from 
  `cognatesetreferences.csv_FormTable` as csrf 
  join formtable as f on (csrf.formtable_cldf_id = f.cldf_id)
  join languagetable as l on f.cldf_languageReference = l.cldf_id
    join `cognatesetreferences.csv` as csr on csr.cldf_id = csrf.`cognatesetreferences.csv_cldf_id`
    join cognatetable as c on csr.cldf_cognatesetReference = c.cldf_cognatesetReference and c.cldf_formReference = f.cldf_id
where csrf.`cognatesetreferences.csv_cldf_id` = ?
"""
        res = db.query(q, (rid,))
        return res, json.loads(res[0]['fn'] or '{}')

    def cfs(rid):
        q = """
            select cf.cldf_id as id, \
                   cf.cldf_name as name, \
                   l.`Group` as 'group', \
                   l.cldf_name as lname, \
                   l.is_proto, \
                   f.cldf_value as form, \
                   g.cldf_name as gloss, \
                   g.cldf_comment as gcomment, \
                   g.Part_Of_Speech as gpos, \
                   gs.SourceTable_id as srcid, \
                   gs.context as pages, \
                    c.footnote_number as fn
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
        for cfid, rows in itertools.groupby(db.query(q, (rid,)), lambda r: r['id']):
            rows = list(rows)
            res[(cfid, rows[0]['name'])] = []
            for (group, lname, form, fn), glosses in itertools.groupby(
                    rows, lambda r: (r['group'], r['lname'], r['form'], r['fn'])):
                res[(cfid, rows[0]['name'])].append((group, lname, form, [], fn))
                for (g, cmt, pos), sources in itertools.groupby(
                        glosses, lambda r: (r['gloss'], r['gcomment'], r['gpos'])):
                    res[(cfid, rows[0]['name'])][-1][-2].append(
                        (g, cmt, pos, [(r['srcid'], r['pages']) for r in sources if r['srcid']]))
        return collections.OrderedDict(
            ((k[0], (k[1] or '').replace('*', '&ast;')), v) for k, v in res.items())

    def cfitems(cfid):
        q = """
select l.`Group` as `group`, 
       l.cldf_name as lname, 
       l.is_proto, 
       f.cldf_value as form, 
       f.Morpheme_Gloss as mgloss,
       c.footnote_number as fn,
       g.cldf_name as gloss, 
       g.cldf_comment as gcomment, 
       g.Part_Of_Speech as pos, 
       gs.SourceTable_id as srcid, 
       gs.context as pages
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
        for (group, lname, form, mgloss, fn), glosses in itertools.groupby(
                rows, lambda r: (r['group'], r['lname'], r['form'], r['mgloss'], r['fn'])):
            res.append((group, lname, form, mgloss, fn, []))
            if mgloss:
                with_morpheme_gloss = True
            for (g, cmt, pos), sources in itertools.groupby(
                    glosses, lambda r: (r['gloss'], r['gcomment'], r['pos'])):
                res[-1][-1].append((g, cmt, pos, [(r['srcid'], r['pages']) for r in sources if r['srcid']]))
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
                    get_eg=eg,
                    get_cfitems=cfitems,
                    glosses_by_formid=glosses_by_formid),
            )
            vout.joinpath(chapter.name).write_text(render(res, ds.cldf_reader()), encoding='utf-8')
            pandoc(vout.joinpath(chapter.name), cmd)
