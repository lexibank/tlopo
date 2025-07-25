"""

"""
from lexibank_tlopo import Dataset


def run(args):
    ds = Dataset()
    taxa = {}
    for row in ds.etc_dir.read_csv('species_and_genera.csv', dicts=True):
        if row['synonyms']:
            for syn in row['synonyms'].split('; '):
                taxa['_' + syn + '_'] = row['ID']
        taxa['_' + row['name'] + '_'] = row['ID']

    for gloss in ds.cldf_dir.read_csv('glosses.csv', dicts=True):
        matched = {v for k, v in taxa.items() if k in gloss['Name']}
        if len(matched) > 1:
            print(gloss['Name'] + ': ' + ', '.join(matched))
