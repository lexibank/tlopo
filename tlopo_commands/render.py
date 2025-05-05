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
    cldf = ds.cldf_reader()
    out.joinpath('references.md').write_text(render(
        '# References\n\n[](Source?with_anchor&with_link#cldf:__all__)', cldf), encoding='utf-8')
    for vol in "12":
        vout = out / 'vol{}'.format(vol)
        if not vout.exists():
            vout.mkdir()
        else:
            for p in vout.iterdir():
                if p.is_file():
                    p.unlink()
        for chapter in tqdm(ds.cldf_dir.joinpath('vol{}'.format(vol)).glob('chapter*.md')):
            res = render(
                chapter,
                cldf,
                template_dir=ds.dir / 'templates',
            )
            vout.joinpath(chapter.name).write_text(render(res, ds.cldf_reader()), encoding='utf-8')
