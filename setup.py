from setuptools import setup, find_packages
import json


with open('metadata.json', encoding='utf-8') as fp:
    metadata = json.load(fp)


setup(
    name='lexibank_tlopo',
    description=metadata['title'],
    license=metadata.get('license', ''),
    url=metadata.get('url', ''),
    py_modules=['lexibank_tlopo'],
    packages=find_packages(where='.'),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'lexibank.dataset': [
            'tlopo=lexibank_tlopo:Dataset',
        ],
        'cldfbench.commands': [
            'tlopo=tlopo_commands',
        ]
    },
    install_requires=[
        'pylexibank>=3.5.1.dev0',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
