"""
>>> res = species.name_usage(key=5302997)
>>> res
{
    'key': 5302997,
    'nubKey': 5302997,
    'nameKey': 3670713,
    'taxonID': 'gbif:5302997',
    'kingdom': 'Plantae',
    'phylum': 'Tracheophyta',
    'order': 'Zingiberales',
    'family': 'Marantaceae',
    'genus': 'Donax',
    'species': 'Donax canniformis',
    'genusKey': 2762131,
    'speciesKey': 5302997,
    'canonicalName': 'Donax canniformis',
    'rank': 'SPECIES',
    'taxonomicStatus': 'ACCEPTED',
    'class': 'Liliopsida'}
>>> species.name_usage(key=2650858, data='vernacularNames')
{
    'offset': 0,
    'limit': 100,
    'endOfRecords': True,
    'results': [
        {
            'taxonKey': 2650858,
            'vernacularName': 'Vegetable fern',
            'language': 'eng',
            'country': 'US',
            'area': 'Hawaii',
            'source': 'Global Register of Introduced and Invasive Species - Hawaii, United States (ver.2.0, 2022)',
            'sourceTaxonKey': 205108587},
        {
            'taxonKey': 2650858,
            'vernacularName': 'Vegetable fern',
            'language': 'eng',
            'country': 'GB', 'area': 'eng', 'source': 'TAXREF', 'sourceTaxonKey': 221952816},
        {
            'taxonKey': 2650858,
            'vernacularName': 'Vegetable fern',
            'language': 'eng',
            'country': 'US', 'area': 'conterminous 48 United States', 'source': 'Global Register of Introduced and Invasive Species - United States (Contiguous) (ver.2.0, 2022)', 'sourceTaxonKey': 205112002},
        {
            'taxonKey': 2650858,
            'vernacularName': 'kuware-shida',
            'language': '', 'source': 'GRIN Taxonomy', 'sourceTaxonKey': 101328558},
        {
            'taxonKey': 2650858,
            'vernacularName': 'paku-sayur',
            'language': 'ind',
            'source': 'GRIN Taxonomy', 'sourceTaxonKey': 101328558},
        {
            'taxonKey': 2650858,
            'vernacularName': 'vegetable fern',
            'language': 'eng', 'source': 'Integrated Taxonomic Information System (ITIS)', 'sourceTaxonKey': 102303288},
        {
            'taxonKey': 2650858,
            'vernacularName': 'vegetable fern',
            'language': 'eng', 'source': 'GRIN Taxonomy', 'sourceTaxonKey': 101328558},
        {
            'taxonKey': 2650858,
            'vernacularName': 'クワレシダ',
            'language': 'jpn', 'country': 'JP',
            'source': 'FernGreenList ver. 2.0', 'sourceTaxonKey': 243781247, 'preferred': True}]}

"""
import itertools
import collections

import pygbif
from csvw.dsv import UnicodeWriter

from lexibank_tlopo import Dataset


def eng_name(key):
    name = None
    for r in pygbif.species.name_usage(key=key, data='vernacularNames')['results']:
        if r['language'] == 'eng':
            if r.get('preferred'):
                return r['vernacularName']
            name = r['vernacularName']
    return name


def run(args):
    ds = Dataset()
    pygbif.caching(True, name='gbif.sqlite')
    taxa = []
    family_names = {
        r['Scientific_Name']: r['English_Name']
        for r in ds.etc_dir.read_csv('taxa.csv', dicts=True) if r['English_Name']}

    for key, rows in itertools.groupby(
        sorted(ds.etc_dir.read_csv('taxa.csv', dicts=True), key=lambda r: r['Key']),
        lambda r: r['Key'],
    ):
        if not key:
            continue
        rows = list(rows)
        data = collections.OrderedDict({'ID': key})
        res = pygbif.species.name_usage(key=key)
        if res['rank'] in {'SPECIES', 'GENUS'}:
            if res['taxonomicStatus'] == 'ACCEPTED':
                for row in rows:
                    sname = row['Scientific_Name'].replace('sp.', '').replace('spp.', '').strip()
                    assert res['canonicalName'] == sname, '\n"{}"\n"{}"\n{}'.format(
                        res['canonicalName'],
                        sname,
                        [(k, v) for k, v in zip(res['canonicalName'], res['canonicalName']) if k != v])
                data['name'] = res['canonicalName']
                data['name_eng'] = eng_name(key)
                data['rank'] = res['rank']
                for attr in ['kingdom', 'phylum', 'class', 'order', 'family', 'genus']:
                    if attr in res:
                        data[attr] = res[attr]

                if res['rank'] == 'SPECIES':
                    data['genus_eng'] = eng_name(res['genusKey'])
                else:
                    data['genus_eng'] = None

                if res.get('family') in family_names:
                    data['family_eng'] = family_names[res.get('family')]
                elif 'familyKey' in res:
                    data['family_eng'] = eng_name(res['familyKey'])
                else:
                    raise ValueError(rows[0])
                data['synonyms'] = "; ".join(sorted(set(r['Name_In_Text'] for r in rows))) or None
                taxa.append(data)

    with UnicodeWriter(ds.etc_dir / 'species_and_genera.csv') as w:
        for i, row in enumerate(taxa):
            if i == 0:
                w.writerow(row.keys())
            w.writerow(row.values())
