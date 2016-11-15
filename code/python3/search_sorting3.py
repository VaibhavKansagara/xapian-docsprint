#!/usr/bin/env python

import json
import logging
import sys
import xapian
from support import distance_between_coords, log_matches

def search(dbpath, querystring, offset=0, pagesize=10):
    # offset - defines starting point within result set
    # pagesize - defines number of records to retrieve

    # Open the database we're going to search.
    db = xapian.Database(dbpath)

    # Set up a QueryParser with a stemmer and suitable prefixes
    queryparser = xapian.QueryParser()
    queryparser.set_stemmer(xapian.Stem("en"))
    queryparser.set_stemming_strategy(queryparser.STEM_SOME)
    queryparser.add_prefix("title", "S")
    queryparser.add_prefix("description", "XD")

    # And parse the query
    query = queryparser.parse_query(querystring)

    # Use an Enquire object on the database to run the query
    enquire = xapian.Enquire(db)
    enquire.set_query(query)
    # Start of example code.
    class DistanceKeyMaker(xapian.KeyMaker):
        def __call__(self, doc):
            # we want to return a sortable string which represents
            # the distance from Washington, DC to the middle of this
            # state.
            value = doc.get_value(4).decode('utf8')
            x, y = map(float, value.split(','))
            washington = (38.012, -77.037)
            return xapian.sortable_serialise(
                distance_between_coords((x, y), washington)
                )
    enquire.set_sort_by_key_then_relevance(DistanceKeyMaker(), False)
    # End of example code.

    # And print out something about each match
    matches = []
    for index, match in enumerate(enquire.get_mset(offset, pagesize)):
        fields = json.loads(match.document.get_data().decode('utf8'))
        print(u"%(rank)i: #%(docid)3.3i %(name)s %(date)s\n        Population %(pop)s" % {
            'rank': offset + index + 1,
            'docid': match.docid,
            'name': fields.get('name', u''),
            'date': fields.get('admitted', u''),
            'pop': fields.get('population', u''),
            'lat': fields.get('latitude', u''),
            'lon': fields.get('longitude', u''),
            })
        matches.append(match.docid)
    # Finally, make sure we log the query and displayed results
    log_matches(querystring, offset, pagesize, matches)

if len(sys.argv) < 3:
    print("Usage: %s DBPATH QUERYTERM..." % sys.argv[0])
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
search(dbpath = sys.argv[1], querystring = " ".join(sys.argv[2:]))
