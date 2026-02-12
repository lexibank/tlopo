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
    if s.startswith('+'):
        s = s.replace('+', '&plus;')
    if s.startswith('>'):
        s = s.replace('>', '&gt;')
    return markdown(s).replace('<p>', '<span>').replace('</p>', '</span>')


def first_as_html_entity(s):
    if s:
        return '&#{};{}'.format(ord(s[0]), s[1:])
    return s


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
            select gr.number, 
                   gr.cldf_comment as 'gcmt', 
                   ex.label, 
                   l.cldf_name as 'lname', 
                   l.`Group`, 
                   ex.cldf_analyzedWord as 'aw', 
                   ex.cldf_gloss as 'gloss', 
                   ex.Movement_Gloss as 'mgloss', 
                   ex.cldf_translatedText as 'tt', 
                   ex.cldf_comment as 'cmt', 
                   exs.SourceTable_id as 'srcid', 
                   ex.Reference_Label as 'pages'\
            from ExampleTable as ex \
                     join `examplegroups.csv_ExampleTable` as eggr on (ex.cldf_id = eggr.ExampleTable_cldf_id) \
                     join `examplegroups.csv` as gr on (gr.cldf_id = eggr.`examplegroups.csv_cldf_id`) \
                     join languagetable as l on (ex.cldf_languageReference = l.cldf_id) \
                     left join ExampleTable_SourceTable as exs on ex.cldf_id = exs.ExampleTable_cldf_id
            where gr.cldf_id = ? \
            """
        num, ctx, exs, labels = None, None, [], False
        rows = db.query(q, (egid,))
        for row in rows:
            if row['number']:
                num = row['number']
            if row['gcmt']:
                ctx = row['gcmt']
            if row['label']:
                labels = True
            ex = [row['lname'], row['Group']]
            ex.extend([
                [s.replace('[', r'\[').replace(']', r'\]') for s in row['aw'].split()],
                [s.replace('[', r'\[').replace(']', r'\]') for s in row['gloss'].split()],
                [s.replace('[', r'\[').replace(']', r'\]') for s in row['mgloss'].split()]])
            ex.extend([row['tt'], row['cmt'], row['srcid'], row['pages']])
            exs.append(ex)
        return num, ctx, labels, exs

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
       f.Morpheme_Gloss as mg,
       csr.footnote_numbers as fn,
       csr.subgroup_mapping as sg
from 
  `cognatesetreferences.csv_FormTable` as csrf 
  join formtable as f on (csrf.formtable_cldf_id = f.cldf_id)
  join languagetable as l on f.cldf_languageReference = l.cldf_id
    join `cognatesetreferences.csv` as csr on csr.cldf_id = csrf.`cognatesetreferences.csv_cldf_id`
    join cognatetable as c on csr.cldf_cognatesetReference = c.cldf_cognatesetReference and c.cldf_formReference = f.cldf_id
where csrf.`cognatesetreferences.csv_cldf_id` = ?
"""
        res, fn, sg = [], None, {}
        for i, row in enumerate(db.query(q, (rid,))):
            if i == 0:
                fn = row['fn']
                sg = row['sg']
            r = list(row)
            if row['is_proto']:
                r[5] = ', '.join('&ast;' + f.strip() for f in row['form'].split(', '))
                if '](' in r[5]:
                    r[5] = r[5].replace('[', '&#91;')
            res.append(r)
        return res, json.loads(fn or '{}'), json.loads(sg or '{}')

    def cfs(rid):
        q = """
            select cf.cldf_id as id, \
                   cf.cldf_name as name, \
                   l.`Group` as 'group', \
                   l.cldf_id as lid, \
                   l.cldf_name as lname, \
                   l.is_proto, \
                   f.cldf_value as form, \
                   g.cldf_name as gloss, \
                   g.cldf_comment as gcomment, \
                   g.Part_Of_Speech as gpos, \
                   gs.SourceTable_id as srcid, \
                   gs.context as pages, \
                   s.key, 
                    c.footnote_number as fn
            from `cf.csv` as cf \
                     join `cfitems.csv` as c on (cf.cldf_id = c.Cfset_ID) \
                     join formtable as f on (c.cldf_formReference = f.cldf_id) \
                     join languagetable as l on f.cldf_languageReference = l.cldf_id \
                     left join `cfitems.csv_glosses.csv` as cfg on c.cldf_id = cfg.`cfitems.csv_cldf_id`
                     left join `glosses.csv` as g on cfg.`glosses.csv_cldf_id` = g.cldf_id
                     left join `glosses.csv_SourceTable` as gs \
                               on gs.`glosses.csv_cldf_id` = g.cldf_id
                     left join SourceTable as s on (gs.SourceTable_id = s.id)
            where cf.cognatesetreference_id = ?
            order by cf.cldf_id, c.ordinal \
            """
        res = collections.OrderedDict()
        for cfid, rows in itertools.groupby(db.query(q, (rid,)), lambda r: r['id']):
            rows = list(rows)
            res[(cfid, rows[0]['name'])] = []
            for (group, lid, lname, form, fn), glosses in itertools.groupby(
                    rows, lambda r: (r['group'], r['lid'], r['lname'], r['form'], r['fn'])):
                res[(cfid, rows[0]['name'])].append((group, lid, lname, form, [], fn))
                for (g, cmt, pos), sources in itertools.groupby(
                        glosses, lambda r: (r['gloss'], r['gcomment'], r['gpos'])):
                    res[(cfid, rows[0]['name'])][-1][-2].append(
                        (g, cmt, pos, [(r['srcid'], r['pages'], r['key']) for r in sources if r['srcid']]))
        return collections.OrderedDict(
            ((k[0], (k[1] or '').replace('*', '&ast;')), v) for k, v in res.items())

    def cfitems(cfid):
        q = """
select l.`Group` as `group`,
       l.cldf_id as lid,
       l.cldf_name as lname, 
       l.is_proto, 
       f.cldf_value as form, 
       f.Morpheme_Gloss as mgloss,
       c.footnote_number as fn,
       g.cldf_name as gloss, 
       g.cldf_comment as gcomment, 
       g.Part_Of_Speech as pos, 
       gs.SourceTable_id as srcid, 
       gs.context as pages,
       s.key
from 
      `cf.csv` as cf
      join `cfitems.csv` as c on (cf.cldf_id = c.Cfset_ID)
      join formtable as f on (c.cldf_formReference = f.cldf_id)
      join languagetable as l on f.cldf_languageReference = l.cldf_id      
      left join `cfitems.csv_glosses.csv` as cfg on c.cldf_id = cfg.`cfitems.csv_cldf_id`
      left join `glosses.csv` as g on cfg.`glosses.csv_cldf_id` = g.cldf_id
      left join `glosses.csv_SourceTable` as gs on gs.`glosses.csv_cldf_id` = g.cldf_id
      left join SourceTable as s on (gs.SourceTable_id = s.id)
where cf.cldf_id = ?
"""
        res = []
        rows = db.query(q, (cfid,))
        with_morpheme_gloss = False
        for (group, lid, lname, form, mgloss, fn), glosses in itertools.groupby(
                rows, lambda r: (r['group'], r['lid'], r['lname'], r['form'], r['mgloss'], r['fn'])):
            res.append((group, lid, lname, form, mgloss, fn, []))
            if mgloss:
                with_morpheme_gloss = True
            for (g, cmt, pos), sources in itertools.groupby(
                    glosses, lambda r: (r['gloss'], r['gcomment'], r['pos'])):
                res[-1][-1].append((g, cmt, pos, [(r['srcid'], r['pages'], r['key']) for r in sources if r['srcid']]))
        # FIXME: determine whether there are non-empty morpheme glosses!
        return res, with_morpheme_gloss

    def glosses_by_formid(rid):
        def iter_glosses(rows):
            for (g, cmt, pos, qual), srcs in itertools.groupby(rows, lambda row: row[1:5]):
                yield (
                    (g or '').replace('*', '&ast;'),
                    (cmt or '').replace('<', '&lt;').replace('*', '&ast;'),
                    pos,
                    first_as_html_entity(qual),
                    [(row[-3], row[-2], row[-1]) for row in srcs if row[-3]])

        q = """
select g.cldf_formReference, 
       g.cldf_name, 
       g.cldf_comment, 
       g.Part_Of_Speech, 
       g.qualifier,
       gs.SourceTable_id, 
       gs.context,
       s.key
from 
      `cognatesetreferences.csv_glosses.csv` as csrg 
      join `glosses.csv` as g on csrg.`glosses.csv_cldf_id` = g.cldf_id
      left join `glosses.csv_SourceTable` as gs on gs.`glosses.csv_cldf_id` = g.cldf_id
      left join SourceTable as s on gs.SourceTable_id = s.id
where csrg.`cognatesetreferences.csv_cldf_id` = ?
order by g.cldf_formReference
"""
        return {fid: list(iter_glosses(rows)) for fid, rows in itertools.groupby(db.query(q, (rid,)), lambda r: r[0])}


    def pandoc(input, md, css_path='..'):
        css = 'pandoc_book.css'
        assert input.parent.joinpath(css_path, css).exists()
        subprocess.check_call(shlex.split(
            'pandoc --metadata title="{}" -s -f markdown -t html5 -c {}/{} {} -o {}/{}.html'.format(
                md['title'], css_path, css, input, input.parent, input.stem)))

    out.joinpath('references.md').write_text(render(
        '# References\n\n[](Source?with_anchor&with_link#cldf:__all__)', cldf), encoding='utf-8')
    pandoc(out.joinpath('references.md'), dict(title='References'), css_path='.')

    v, c = None, None
    if args.chapter:
        v, _, c = args.chapter.partition('-')

    for vol in "123456":
        if v and vol != v:
            continue
        md = ds.raw_dir.joinpath('vol{}'.format(vol)).read_json('md.json')

        # Prepare the output directory for the chapter files:
        vout = out / 'vol{}'.format(vol)
        if not vout.exists():
            vout.mkdir()
        else:
            for p in vout.iterdir():
                if p.is_file():
                    p.unlink()

        for chapter in tqdm(ds.cldf_dir.joinpath('vol{}'.format(vol)).glob('chapter*.md')):
            cnum = chapter.stem.replace('chapter', '')
            if c and cnum != c:  # Not the user-selected chapter
                continue
            for cmd in md['chapters']:
                if cmd['number'] == cnum:
                    break
            else:
                raise ValueError((vol, cnum))
            # Render the CLDF Markdown file to regular Markdown:
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
            # Run pandoc to convert the Markdown to HTML:
            pandoc(vout.joinpath(chapter.name), cmd)
