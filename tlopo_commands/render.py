"""

"""
from tqdm import tqdm
from jinja2.filters import FILTERS

from markdown import markdown

from cldfviz.text import render

from lexibank_tlopo import Dataset


def md_string(s):
    return markdown(s).replace('<p>', '<span>').replace('</p>', '</span>')


FILTERS['markdown'] = md_string


def run(args):
    ds = Dataset()
    out = ds.dir / 'out'
    if not out.exists():
        out.mkdir()
    out = out / 'vol1'
    if not out.exists():
        out.mkdir()
    cldf = ds.cldf_reader()
    for chapter in tqdm(ds.cldf_dir.joinpath('vol1').glob('chapter*.md')):
        res = render(
            chapter,
            cldf,
            template_dir=ds.dir / 'templates',
        )
        out.joinpath(chapter.name).write_text(render(res, ds.cldf_reader()), encoding='utf-8')
    out.joinpath('references.md').write_text(render('# References\n\n[](Source?with_anchor&with_link#cldf:__all__)', ds.cldf_reader()), encoding='utf-8')
    #
    # FIXME: render references!
    #