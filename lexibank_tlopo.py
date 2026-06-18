import shutil
import pathlib
import functools
import collections
import dataclasses

import pylexibank
from clldutils.misc import slug
from pylexibank import LexibankWriter, Cognate as BaseCognate
from pycldf.sources import Source, Sources

from pyetymdict import Dataset as BaseDataset, Language as BaseLanguage, Form as BaseForm
from pyetymdict.forms import Forms
from pyetymdict.parser.models import Reflex, Protoform, Gloss, Parser, Volume, Reconstruction
from pyetymdict.parser.util import nested_toc

# Unexpected:'gʷ',  ā and kʷ
# See https://en.wikipedia.org/wiki/Proto-Oceanic_language for a mapping to BIPA
# dr: ⁿr   pre-nasalized voiced alveolar trill consonant
# R: ʀ   voiced uvular trill consonant



class TlopoWriter(LexibankWriter):
    def lexeme_id(self, kw):
        form = slug(kw['Value'])
        self._count[(kw['Language_ID'], form)] += 1
        return '{0}-{1}-{2}'.format(
            kw['Language_ID'],
            form,
            self._count[(kw['Language_ID'], form)])


@dataclasses.dataclass
class Variety(BaseLanguage):
    Classification: str = dataclasses.field(
        default=None,
        metadata={
            'dc:description':
                'Classification within Oceanic, given as /-separated nodes.',
            'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#description'}
    )
    Note: str = None
    Map: str = None
    Icon: str = None



@dataclasses.dataclass
class TlopoReconstruction(Reconstruction):
    @functools.cached_property
    def oceanic_protoforms(self):
        return [
            pf for pf in self.reflexes
            if isinstance(pf, Protoform) and pf.lang != 'PAn' and not pf.lang.endswith('MP')]

    @functools.cached_property
    def first_oceanic_protoform(self):
        if self.oceanic_protoforms:
            return self.oceanic_protoforms[0]
        return self.reflexes[0]

    @property
    def computed_gloss(self):
        # We have adopted the
        # convention of providing no gloss beside the items in a cognate set whose gloss is identical to
        # that of the POc (or other lower-order) reconstruction at the head of the set, i.e. the reconstruction
        # which they reflect.
        for pf in self.oceanic_protoforms:
            if pf.glosses:
                return pf.glosses[0].gloss
            if pf.comment:
                return pf.comment
            if pf.morpheme_gloss:
                return pf.morpheme_gloss
        return self.reflexes[0].morpheme_gloss or self.reflexes[0].glosses[0].gloss

    def key(self):
        if not self.section:  # pragma: no cover
            raise ValueError(self)
        pf = self.first_oceanic_protoform
        return (
            self.volume,
            self.chapter[0],
            self.section[0] if self.section else None,
            self.subsection[0] if self.subsection else None,
            self.page,
            slug(pf.lang, lowercase=False),
            slug(pf.forms[0]),
            self.disambiguation,
        )


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "tlopo"

    language_class = Variety

    # define the way in which forms should be handled
    form_spec = pylexibank.FormSpec(
        brackets={"(": ")", "[": "]"},  # characters that function as brackets
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

    def cmd_makecldf(self, args):
        self.schema(args.writer.cldf, with_borrowings=False)

        args.writer.cldf.sources = self.sources
        ldicts = collections.defaultdict(list)
        for src in args.writer.cldf.sources:
            if 'dictionary' in src.get('hhtype', ''):
                for gc in src['lgcode'].split('; '):
                    assert gc.startswith('[') and gc.endswith(']')
                    ldicts[gc[1:-1]].append(src.id)

        reconstructions, fgs, egs = self.parse_chapters(
            args.writer,
            reconstruction_cls=TlopoReconstruction,
        )

        self.languoids.add(
            args.writer, 
            {lg.id: lg for lg in args.glottolog.api.languoids()}, 
            ldicts)

        formtable = Forms(args.writer, self.languoids, self.taxa)
        formtable.add_reconstructions(reconstructions)
        formtable.add_formgroups(fgs)
        formtable.add_examplegroups(egs)

        self.add_tree(
            args.writer,
            self.etc_dir.joinpath('tree.nwk').read_text(encoding='utf8'),
            separate_file=True,
            description=self.etc_dir.joinpath('tree_description.txt').read_text(encoding='utf8'),
        )

        args.writer.cldf.properties['dc:spatial'] = {
            'B.1': 'Admiralties and St Matthias Islands',
            'B.2': 'Schouten (NNG) and Sarmi-Jayapura (possibly NNG)',
            'B.3': 'The Ngero-Vitiaz linkage (NNG)',
            'B.4': 'Huon Gulf (NNG)',
            'B.5': 'Papuan Tip',
            'B.6': 'New Britain and New Ireland (MM)',
            'B.7': 'Northwest Solomonic linkage (MM)',
            'B.8': 'Southeast Solomonic and Temotu',
            'B.9': 'North Vanuatu',
            'B.10': 'Central Vanuatu',
            'B.11': 'South Vanuatu',
            'B.12': 'Loyalty Islands and New Caledonia',
            'B.13': 'Micronesian languages and Yapese',
            'B.14': 'Fiji',
            'B.15': 'Polynesia',
        }

