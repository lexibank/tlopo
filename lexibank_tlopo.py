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

#
# FIXME: move all of pytlopo into pyetymdict.parser!
#
from pyetymdict.parser.models import Volume, Reflex, Protoform, Gloss, Parser
from pyetymdict.parser.util import nested_toc

GLOSS_ID = 0
POC_GRAPHEMES = "+ ŋʷ gʷ C V N M L a e i o u ā w p b m t d s n r dr l c j y k g q R ŋ ñ pʷ bʷ mʷ kʷ".split()
# Unexpected:'gʷ',  ā and kʷ
# See https://en.wikipedia.org/wiki/Proto-Oceanic_language for a mapping to BIPA
# dr: ⁿr   pre-nasalized voiced alveolar trill consonant
# R: ʀ   voiced uvular trill consonant
POC_BIPA_GRAPHEMES = {
    "dr": "ⁿr",
    "R": "ʀ",
    "ñ": "ɲ",
}
TRANSCRIPTION = POC_GRAPHEMES + [  # add POC_GRAPHEMES -> reflex_graphemes
    'C', 'L', 'F', 'N', 'M',  # CLF and NML
    '⟨', '⟩', '’', '(', ')', '[', ']', '-', '~', '=',  # enclitic boundary
    'ᵐp', 'ʷa', 'ñʰ', 'jᵐ', 'ɸ', 'ϕ', 'ɸʷ', 'h', 'vʰ', 'pʰ', 'nʰ', 'mʰ', 'tʰ', 'bˠ', 'ᵑk', 'h́',
    'ᵐb', 'ᵑr', 'lᵐ', 'lʰ',
    'á', 'ˀa', 'yʰ', 'wʷ', 'kʰ', 'oᵑ',
    'à', 'a̰', 'ä',
    'ā',  # macron
    'ã', 'ã̄', # tilde
    'â',  # circumflex
    'æ', 'ʙ', 'œ','œ̄',
    'oᵐ', 'ᴂ', 'ø̄',
    'ǣ', 'aᵐ',
    'ɒ', 'eᵐ', 'ɛᵑ',
    'ɒ̄', 'nᵐ',
    'ūᵑ', 'fʰ', 'f',
    'z', 'ẓ',
    'tᫀ', 'dᫀ', 'nᫀ',
    'ʔ',
    'ð', 'ð̼', 'ð̫', 'ðᫀ',
    'ɢ', 'g', 'gʷ', 'ᵑg', 'qʷ', 'tʷ', 'lʷ', 'ḷʷ', 'vʷ', 'ᵑgʷ', 'kʷ', 'nʷ', 'fʷ',
    'γ', 'ɣ', 'hʷ',
    'ɔ̀', 'χ', # chi
    'ɔ', 'ʊ', 'o̝',
    'ɔ̄', 'ċ',
    'v',
    'ɵ̄', 'ọ', 'öᵐ', 'ø',
    'ö', 'ō', 'õ',
    'ò', 'ó', 'ô', 'ǿ',
    'î',  # circumflex
    'ĩ',  # tilde
    'ì',  # grave
    'ī',  # macron
    'ɨ', 'ⁿ', 'ɨ̈', # stroke and diaresis
    'í',
    'I',
    'ĩ̄', 'ɨ̄',
    'ị', 'ı', 'ıː', 'ɪ',
    'ʈ', '̄t', 't̼',
    't', 'ṭ', '†',
    'x',
    'θ', 'φ',
    'b',
    'ŋ', 'ŋʷ', 'ŋʰ',
    'ñ',  # tilde
    'ɲ', 'ɳ',
    'è', 'ẽ', # tilde
    'ɛ', 'ɛ́', 'ɛ̄', 'ɛ̃', "ɛ̄", 'ɛ̃́', 'ɛ̀',
    'ə', 'ə̄', 'ɞ',
    'é',
    'ē', # macron
    'ê', 'ë', 'ẽ̄',
    'ū', 'ũ', 'ǖ', 'ú̄',
    'ü', 'û',
    'ù',
    'ú',
    'ʉ̄', 'ʉ', 'w̥',
    'm̫', 'm̥', 'm̀', 'n̼', 'n̥',
    'ṣ', 'š', 'ʃ', 'ʒ',
    'ḍ', 'ɖ', 'ɠ',
    'ũ̃', 'ʂ',
    'č',
    'c̣', 'cʰ', 'ç',
    'ɬ',
    'ʌ', 'ʌ̃', 'ʟ', 'ʌ̄̃',
    'ɭ', 'ḷ', 'ʎ',
    'ȴ', 'bʸ',
    'l̥',  # ring below
    'ʋ', 'ɓ',
    'sʸ', 'v̈', 'vʸ', 'vᫀ', 'rʰ', 'kʸ', 'ɣʷ',
    'ɯ', 'mᵚ', 'nᵚ', 'rᵚ', 'ṛᵚ', 'lᵚ', 'pᵚ',
    'ᶭ', 'lᶭ',  # FIXME: replace with ᵚ
    'mʸ', 'mᶭ', 'nᶭ', 'pᶭ', 'ᶭp',
    'β',  # LATIN SMALL LETTER TURNED M - used as superscript!
    'ṛ', 'ṛᶭ', 'ʁ', 'rᶭ',
    'r̃', 'ɹ', 'ṛʷ', 'ɾ̄',
    'ɾ',  # r with fishhook
    'ɽ', 'z̧', # z with cedilla
]

GROUPS = [  # read from etc/languages.csv!
    # Oceanic:
    "Yap",  # Yapese
    "Adm",  # Admiralty
    "NNG",  # North New Guinea
    "SJ",  # Sarmi/Jayapura
    "PT",  # Papuan Tip
    "MM",  # Meso-Melanesian
    "SES",  # Southeast Solomons
    "TM",  # Temotu
    "NCV",  # North and Central Vanuatu
    "SV",  # South Vanuatu
    "NCal",  # New Caledonia
    "Mic",  # Micronesian
    "Fij",  # Fijian
    "Pn",  # Polynesian
    # Other Austronesian:
    "CMP",  # Central Malayo-Polynesian
    "Fma",  # Formosan
    "IJ",  # Irin Jaya
    "CB",  # PEMP - Cenderawasih Bay
    "SH",  # PEMP - South Halmahera
    "RA",  # PEMP - Raja Ampat
    "Bom",  # PEMP - Bomberai
    "WMP",  # Western Malayo-Polynesian
    "SHWNG",
]
# Map proto-language ID to extra-graphemes in addition to POC_GRAPHEMES.
PROTO = {  # csvgrep -c Group -r ".+" -i etc/languages.csv | csvcut -c Name
    # Oceanic:
    "PEAd": ['f'], # Adm
    "PAdm": ['ə', 'f'], # same thing as above?
    "PWOc": ['v', 'pᵂ'],  # MM, SJ
    "PNNG": ['v'],  # NNG
    "PNGOc": ['kʷ'],  # Proto New Guinea Oceanic, i.e. PWOc without reflexes from MM
    "PPT": ['v'],  # PT
    "Proto Northwest Solomonic": ['v'],
    "PSES": ['ɣ', 'v'],  # FIXME: identify with PSS
    "PNCV": ['ʔ', 'z', 'ɣ', 'v', 'vʷ'],  # NCV
    "PNCal": ['v', 'hʷ', 'kʰ', 'ᵐb', ],
    "PMic": ['T', 'S', 'x', 'ō', 'f', 'ū', 'z', 'V', 'ī', 'ə̄', 'ə'],  # Proto Micronesian Mic
    "Proto Central Micronesian": ['f'],
    "PChk": ['ē', 'ʉ', 'ɨ', 'ō', 'f', 'ū', 'z', 'V', 'ī', 'ə̄', 'ə'],
    "PCP": ['z', 'ō', 'ī', 'ŋʷ', 'x', 'ð', 'ĩ', 'ē', 'v', 'ā', 'gʷ'],  # Proto Central Pacific, Fij
    "PPn": ['ʔ', 'h', 'ō', 'f', 'ū', 'z', 'V', 'ī', 'ə̄', 'ə'],  # PN
    "PNPn": ['f', 'ū', 'ʔ', 'ā', 'h'],
    "PEPn": ['f'],
    "PSV": ['z', 'v', 'ə', 'ɣ'],
    "PSOc": ['v'],  # Proto Southern Oceanic
    "Proto Central Vanuatu": ['v'],
    "PFij": ['v'],
    "Proto Huon Gulf": ['ɣ', ],
    "Proto Tongic": ['h'],
    "Proto Sudest-Nimoa": ['ɣ', ],
    "Proto Torres-Banks": ['v', 'ʔ', ],
    "Proto Markham": ['ɣ', ],
    "Proto Buang": ['h', 'v', 'ɣ', 'ɛ', ],
    "Proto North New Caledonia": ['ᵐb', ],
    "Proto Tanna": ['v'],
    "Proto Kilivila": ['v', 'z'],
    "Proto N Malakula": ['ɣ', ],
    "Proto CW Malakula": ['ɣ', 'v'],
    "Proto Malaita-Makira": ['ʔ', 'ɣ', 'f'],
    "PAn": ['á', 'C', 'D', 'h', 'N', 'S', 'R', 'T', 'x', 'z', 'Z', 'L', '?', 'ə', '+'],
    "PAn/PMP": ['h'],
    "PMP": ['ʔ', 'á', 'C', 'D', 'h', 'N', 'S', 'R', 'T', 'z', 'Z', 'L', '?', 'ə', '+', 'W'],
    "PWMP": ['S'],
    "PCEMP": ['ə', 'z'],
    "PEMP": ['ə', ],
    "PSS": ['v', 'ɣ'],  # all cognates are from either Northwest or Southeast Solomonic languages
    "PROc": ['v'],  # NCV, SV, Mic
    "PEOc": ['z', 'v', 'ŋʷ', 'C'],
    "Proto Central Papuan": ['ɣ', ], # Languages from PT, MM and NCV
    "PCEPn": ['ō', 'f', 'ū', 'z', 'V', 'ī', 'ə̄', 'ə'],  # Proto Central Eastern Polynesian; Hawaiian, Maori, Tuamotuan
    "Proto Hote-Buang": ['ɣ', ],  # 1
    "Proto Samoic": ['f'],  # 3
    "Proto Solomons Outlier": ['f'],  # 1
    "Proto Willaumez": ['h'],  # 2, MM and SES
}

# FIXME: Map POS patterns to lists of mormalized POS symbols.
POS = [
    'ADJ',
    'ADJ, VI',
    'ADV',
    'ADVERB OF INTENSITY',
    'adverb',
    'ADV, ADJ',
    'ADN AFFIX',
    'C',
    'DEM',
    'DIR',
    'DIR clause-final',
    'INTERJECTION',
    'IRREALIS',
    'REALIS',
    'LOC',
    'N',
    'N LOC',
    'N, N LOC',
    'N, ? N LOC',
    'N, V',
    'N. V',
    'N & V',
    'N, v',
    'N,V',
    'N,VI',
    'N, VI',
    'N, VT',
    'VI, N',
    'VI, U-verb',
    'VI, inanimate subject',
    'VT, inanimate object',
    'N LOC',
    'N, N Loc',
    'N + POSTPOSITION',
    'PLURAL SUBJECT',
    'V',
    'V, VC',
    'V, C',
    'V; C',
    'V; N',
    'VSt',
    'N,VSt',
    'N; ADJ',
    'N; V',
    'NP',
    'N, VI, VT',
    'VSt, N',
    'VT, VSt',
    'V; ADJ; N',
    'V AUX',
    'V, DIR',
    'V PERFECTIVE',
    'V PASSIVE',
    'VF',
    'v',
    'VT', 'vT',
    'VI',
    'vI', 'vi',
    'VT,VI',
    'VI,VT',
    'VTI',
    'VI, VT',
    'VT, VI',
    'V & N',
    'V, ADJ',
    '?? N LOC, V',
    'PP',
    'POSTVERBAL ADV',
    'PREPV',
    'preverbal clitic',
    'PASS',
    'postposed particle',
    'PREP',
    'PRO',
    'POSTPOSITION',
    'R-',
    'R',
    'RELATIONAL N',
]

KINSHIP = [
    '(ADDR)',
    'BD',
    'BDC',
    'BC',
    'BCC',
    'BDH',
    'BS',
    'BSSD',
    'BSW',
    'BW',
    'CC',
    'CCC',
    'CCE',
    'CD',
    'CE',
    'CS',
    'D',
    'DDC',
    'DH',
    'DSSW',
    'DSW',
    'EBS',
    'EF',
    'EFB',
    'EFZ',
    'EFZH',
    'EG',
    'eG',
    'eGE',
    'EGC',
    'EM',
    'EMByD',
    'EMM',
    'EMZ',
    'EoG',
    'EoGC',
    'EoGE',
    '{EoG}C',
    'EP',
    'EPB',
    'EPF',
    'EPG',
    'EPGE',
    'EPGoC',
    'EPGsC',
    'EPMH',
    'EPP',
    'E{PsG}',
    'E{PsG}oC',
    'ESG',
    'esG',
    '{EsG}C',
    'EsGE',
    'EZ',
    'FB',
    'FBD',
    'FBDC',
    'FBDS',
    'FBeS',
    'FBoC',
    'FBS',
    'FBSC',
    'FBsC',
    'FBW',
    'FC',
    'FEB',
    'FeBC',
    'FeBD',
    '{FeB}S',
    'FFB',
    'FFBD',
    'FFBDD',
    'FFBDH',
    'FFBS',
    'FFBW',
    'FFC',
    'FFF',
    'FFFBS',
    'FFFZ',
    'FFMBW',
    'FF{PsG}SSW',
    'FFZD',
    'FFZS',
    'FG',
    'FGCC',
    'FGS',
    'FGSC',
    'FGSCC',
    'FGSS',
    'FMB',
    'FMBS',
    'FMZS',
    'FPGSCesC',
    'F{PsG}CD',
    'F{PsG}CS',
    'F{PsG}CSS',
    'F{PsG}D',
    'F{PsG}S',
    'F{PsG}SW',
    'FW',
    '{FyB}sC',
    'FZ',
    'FZC',
    'FZCC',
    'FZCCE',
    'FZD',
    'FZDC',
    'FZDD',
    'FZDDS',
    'FZDDDS',
    'FZDH',
    'FZDS',
    'FZH',
    'FZS',
    'FZSS',
    'FZSW',
    'FZW',
    'GC',
    'GCC',
    'GCE',
    'GDH',
    'GEC',
    'GEF',
    'GEP',
    'GF',
    '{GoC}E',
    'GS',
    'GsE',
    'H',
    'HB',
    'HBC',
    'HeB',
    '{HeB}',
    '{HeB}C',
    'HeBW',
    'HF',
    'HFB',
    'HF{PsG}D',
    'HFZ',
    'HFZS',
    'HGC',
    'HGS',
    'HMB',
    'HMBS',
    'HP',
    'H{PeG}SC',
    'HPGDC',
    'HyB',
    'HZ',
    'HZC',
    'HZD',
    'HZH',
    'MB',
    'MBC',
    'MBCC',
    'MBDC',
    'MBDDD',
    'MBDS',
    '{MBeS}',
    'MBS',
    'MBSC',
    'MBSS',
    'MBW',
    'MBysC',
    'MEZH',
    'MF',
    'MFB',
    'MFBD',
    'MFBS',
    'MFF{PsG}D',
    'MFM',
    'MFMB',
    'MFMBS',
    'MFZDD',
    'MFZDS',
    'MFZS',
    'MFZSD',
    'MG',
    'MH',
    'MMB',
    'MMBC',
    'MMBDDC',
    'MMBDH',
    'MMC',
    'MMF',
    'MMM',
    'MMMB',
    'MM{PsG}DD',
    'MMyZ',
    'MMZCS',
    'MMZD',
    'MMZDDC',
    'MMZH',
    'MMZS',
    'MP',
    'MPGD',
    'MPGS',
    'M{PoG}S',
    'M{PsG}D',
    'M{PsG}S',
    'M{PsG}oG',
    'MZCC',
    'MZDC',
    'MZDoC',
    'MZDS',
    'MZH',
    'MZoC',
    'MZS',
    'MZSC',
    'MZSeC',
    'MZseC',
    'oGC',
    'PB',
    'PBS',
    'PBW',
    'PeGC',
    '{PeG}CC',
    '{PesG}sC',
    'PF',
    'PFZ',
    'PGC',
    'PGCC',
    'PGCH',
    'PGCW',
    'PGD',
    '{PG}D',
    'PGDC',
    'PGDH',
    'PGeC',
    'PGESC',
    'PGoC',
    'PGS',
    '{PG}S',
    'PGsC',
    'PGsCE',
    'PGseC',
    'PGSW',
    'PGyC',
    'PM',
    'PMH',
    '{PoG}CsE',
    '{PoG}D',
    '{PoG}DS',
    '{PoG}E',
    '{PoG}eS',
    '{PoG}oC',
    '{PoG}SC',
    '{PoG}sC',
    '{{PoG}SC}C',
    '{PoG}sCE',
    '{PoG}sCsC',
    '{PoG}SS',
    '{PoG}yD',
    '{PoG}ZDDD',
    'PP',
    'PPE',
    'P{PeG}CCC',
    'PPG',
    'PPGC',
    'PPGCD',
    'PPGCS',
    'P{PoG}S',
    'P{PoG}SC',
    'PPP',
    'P{PsG}D',
    'P{PsG}S',
    '{PsG}C',
    '{PsG}CC',
    '{PsG}CDS',
    '{PsG}D',
    '{PsG}DC',
    '{PsG}DD',
    '{PsG}eC',
    '{PsG}eS',
    '{PsG}esC',
    '{PsG}eS',
    '{PsG}oC',
    '{PsG}S',
    '{PsG}sC',
    '{PsG}sCE',
    '{PsG}SD',
    '{PsG}seC',
    '{PsG}yC',
    '{PsG}ysC',
    '{PseG}C',
    'PyGC',
    '{PyG}C',
    '{PysG}C',
    '{PysG}sC',
    'PZ',
    'PZH',
    'S',
    'SDD',
    'sG',
    'sGC',
    'sGCE',
    'sGE',
    'sGEoG',
    'sGE{PsG}oC',
    'sGsCE',
    'SSD',
    'SSS',
    'SSSS',
    'SW',
    'SWB',
    'SWBW',
    'WB',
    'WBC',
    'WBW',
    'WByW',
    '{WeZ}♀H',
    'WFB',
    'WFGyD',
    'WGS',
    'WM',
    'WMB',
    'WMZyD',
    'WPG',
    'WSZ',
    'WZ',
    'WZC',
    'WZCC',
    'WZeH',
    'WZS',
    'WZyH',
    'yG',
    'yZ',
    'ZC',
    'ZCC',
    'ZCE',
    'ZD',
    'ZDC',
    'ZDDC',
    'ZDDD',
    'ZDH',
    'ZDSW',
    'ZH',
    'ZHS',
    'ZS',
    'ZSC',
    'ZSDD',
    'ZSW',
    'ZW',
    'etc',
    'sGCC',
]


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
    Map = attr.ib(default=None)
    Icon = attr.ib(default=None)


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
    def parser(self):
        proto_graphemes, groups = {}, set()
        langs = {r['Name']: r for r in self.etc_dir.read_csv('languages.csv', dicts=True)}
        for v in list(langs.values()):
            if not v['Group']:
                proto_graphemes[v['Name']] = POC_GRAPHEMES + PROTO.get(v['Name'], []) + ['-']
            else:
                groups.add(v['Group'])
            for alt in v['Alternative_Names'].split('; '):
                if alt:
                    assert alt not in langs, alt
                    langs[alt] = v

        return Parser(
            [self.raw_dir / 'vol{}'.format(vol) for vol in range(1, 7)],
            langs,
            Source.from_bibtex(self.etc_dir.read('citation.bib')),
            Sources.from_file(self.etc_dir / 'sources.bib'),
            proto_graphemes=proto_graphemes,
            reflex_graphemes=TRANSCRIPTION,
            reflex_groups=list(groups),
            pos_map={pos: pos for pos in POS},
            kinship_tags=KINSHIP,
        )

    @functools.cached_property
    def taxa(self):
        _taxa = {}
        for row in self.etc_dir.read_csv('species_and_genera.csv', dicts=True):
            if row['synonyms']:
                for syn in row['synonyms'].split('; '):
                    _taxa['_' + syn + '_'] = row['ID']
            _taxa['_' + row['name'] + '_'] = row['ID']
        return _taxa

    #
    # FIXME: Must pass ldicts to add_form!
    #
    def add_form(self, writer, protoform_or_reflex, gloss2id, langs, lexid2fn, poc_gloss='none'):
        if poc_gloss != 'none':
            if not protoform_or_reflex.glosses:
                protoform_or_reflex.glosses.append(Gloss(gloss=poc_gloss, sources=[]))
        gloss = protoform_or_reflex.glosses[0].gloss if protoform_or_reflex.glosses else poc_gloss

        if gloss not in gloss2id:
            gloss2id[gloss] = slug(str(gloss))
            writer.add_concept(ID=slug(str(gloss)), Name=gloss)

        #
        # FIXME: add Source! either from Sources associated with glosses or from ldicts!
        #
        _source = set()
        for _gloss in protoform_or_reflex.glosses:
            if _gloss.sources:
                _source |= {ref.cldf_id for ref in _gloss.sources}

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
        if not kw['Source']:
            kw.update(Source=sorted(_source))
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
        from pycldf.ext.markdown import CLDFMarkdownLink

        def srcids(agg, m):
            if m.table_or_fname == 'Source':
                agg.add(m.objid)

        self.schema(args.writer.cldf, with_borrowings=False)
        self.local_schema(args.writer.cldf)

        args.writer.cldf.sources = Sources.from_file(self.etc_dir / 'sources.bib')
        ldicts = collections.defaultdict(list)
        for src in args.writer.cldf.sources:
            if 'dictionary' in src.get('hhtype', ''):
                for gc in src['lgcode'].split('; '):
                    assert gc.startswith('[') and gc.endswith(']')
                    ldicts[gc[1:-1]].append(src.id)

        langs = self.parser.languoids

        taxon2sections = collections.defaultdict(list)
        reconstructions, fgs, egs = [], [], []
        for vol in self.parser.volumes:
            reconstructions.extend(vol.reconstructions)
            fgs.extend(vol.formgroups)
            egs.extend(vol.igts)

            mddir = self.cldf_dir.joinpath(vol.dir.name)
            mddir.mkdir(exist_ok=True)
            for num, chapter in vol.chapters.items():  # Add chapters as CLDF Markdown docs.
                sources, source_to_sections = set(), collections.defaultdict(set)
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
                sid = None
                for sid, text in chapter.iter_sections():
                    for k, v in self.taxa.items():
                        if k in text:
                            taxon2sections[v].append(('{}-{}'.format(vol.num, num), sid))

                    sids = set()
                    CLDFMarkdownLink.replace(text, functools.partial(srcids, sids))
                    if sids:
                        sources |= sids
                        for s in sids:
                            source_to_sections[s].add(sid)
                if sid is None:  # Chapter has no sections.
                    sids = set()
                    CLDFMarkdownLink.replace(chapter.text, functools.partial(srcids, sids))
                    if sids:
                        sources |= sids

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
                    Table_Of_Contents=nested_toc(chapter.toc),
                    Source=sorted(sources),
                    Source_To_Sections={k: list(v) for k, v in source_to_sections.items()},
                ))

        for lg in langs.values():
            if not lg['Group']:
                assert any((lg[c] or 'x').split()[0] in {'Early', 'Proto'} for c in {'Alternative_Names', 'Name'})
            args.writer.add_language(
                ID=lg['ID'],
                Name=lg['Name'],
                Glottocode=lg['Glottocode'],
                Group=lg['Group'],
                Latitude=lg['Latitude'],
                Longitude=lg['Longitude'],
                Is_Proto=not bool(lg['Group']),
                Source=ldicts.get(lg['Glottocode'], []),
                Alternative_Names=lg['Alternative_Names'],
                Note=lg['Note'],
                Map=lg['Map'],
                Icon=lg['Icon'],
            )

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
                pfgloss = (pf.glosses[0].gloss or pf.glosses[0].morpheme_gloss) if pf.glosses else getattr(pf, 'comment', None)
                if isinstance(pf, Protoform):
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
                args.writer.objects['cf.csv'].append(dict(
                    ID='{}-{}'.format(rec.id, i),
                    Name=name,
                    Cognateset_ID=csid,
                    CognatesetReference_ID=rec.id,
                    Chapter_ID='-'.join(rec.id.split('-')[:2]),
                ))
                for j, w in enumerate(items, start=1):
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
            {
                'name': 'Source',
                'separator': ';',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source'},
            {'name': 'Source_To_Sections', 'datatype': 'json'},
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
