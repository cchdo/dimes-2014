import os
import csv
import logging

from dimesfs.views import PATH_TAG_PREFIX

from tagstore.client import TagStoreClient

TS_ENDPOINT = 'http://sui.ucsd.edu:5000/api/v1'
DIMES_FS_PATH = "/Users/myshen/Sites/dimes/datafiles/0000" #path to dir with all the numbered dirs in it
DIMES_DB_CSV = "dimes_production.csv"
"""
This only import the following attrs:
    The directory path
    If it is public or private
    filename

The following attrs are ignored:
    mimetype (can be guessed by server)
    filesize (can be checked by server)
    description

Procedure is as follows:
    1) Dump the dimes_production.uploads table to CSV
       this parser expects the first line to be the column headers
       set DIMES_DB_CSV to the path to this dump

       I used the following sequel pro settings when I dumped the table:
         Put field names in first row
         Terminate: ,
         Wrap: "
         Escape: \
         Lines: \n
         Null values: NULL
    2) Will need access to the actual fs that the dimes files are stored on
       Set the DIMES_FS_PATH to whatever the dir which contains all the
       0000 to nnnn dirs
    3) Set TS_ENDPOINT to where the tagstore is..
    4) Run this script, hope nothing goes wrong, it will take about 30 minutes
"""

def get_df_path(d):
    id = "{:0>4d}".format(int(d['id']))
    fname = d['filename']
    return os.path.join(DIMES_FS_PATH, id, fname)


def main():
    logging.basicConfig()
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    data = []
    log.info("reading data")
    with open(DIMES_DB_CSV, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"', escapechar="\\",
                doublequote=False)
        headers = reader.next()
        bool_cols = ["public", "deleted"]
        for line in reader:
            line = {k:v for k, v in zip(headers, line)}
            for col in bool_cols:
                if line[col] is '1':
                    line[col] = True
                else:
                    line[col] = False
            data.append(line)
    
    cli = TagStoreClient(TS_ENDPOINT)
    
    log.info("importing")
    for d in data:
        if not d['deleted']:
            base_tags = [
                u'website:dimes',
                ]
            dir_tag = u'{0}:{1}'.format(PATH_TAG_PREFIX, d['directory'])
            base_tags.append(dir_tag)
            fname = d['filename']
            if not d['public']:
                privacy = u'privacy:dimes'
            else:
                privacy = u'privacy:public'
            base_tags.append(privacy)
    
            with open(get_df_path(d), 'rb') as df:
                log.debug('{0}/{1}'.format(d['directory'], fname))
                cli.create(df, fname=fname, tags=base_tags)
    log.info("done")

if __name__ == "__main__":
    main()
