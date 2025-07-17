"""

"""
import sqlite3

from pycldf.db import Database
from lexibank_tlopo import Dataset


class DB(Database):
    def query(self, sql: str, params=None) -> list:
        """
        Run `sql` on the database, returning the list of results.
        """
        with self.connection() as conn:
            cu = conn.cursor()
            cu.row_factory = sqlite3.Row
            cu.execute(sql, params or ())

            return list(cu.fetchall())


def run(args):
    ds = Dataset()
    out = ds.dir / 'out'
    if not out.exists():
        out.mkdir()
    cldf = ds.cldf_reader()
    #
    # Must precompute data for cognatesetreferences and store with cldf!
    #
    # create in-memory sqlite db!


    db = DB(cldf, fname='tlopo.sqlite')
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
                   gs.context, \
                    c.footnote_number
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
    for row in db.query(q, ('1-3-3-4-56-POc-bou-a',)):
        print(row.keys())
        return
