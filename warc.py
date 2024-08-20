from warcio.warcwriter import WARCWriter
from warcio.archiveiterator import ArchiveIterator
from warcio.recordloader import ArcWarcRecord
from bs4 import UnicodeDammit

from translate import *

import argparse
import zipfile
import os
import io
import gzip

def translaterecords(input : ArchiveIterator, output : WARCWriter, client : translate.Client, dryrun=False, simple=False):
    record : ArcWarcRecord
    totalcount = 0
    for record in input:
        if record.rec_type == 'response' and record.http_headers and record.http_headers.get_header('Content-Type') and 'html' in record.http_headers.get_header('Content-Type'):
            a = record.content_stream().read()
            if len(a) == 0:
                print("Empty file at: ", record.rec_headers.get_header('WARC-Target-URI'))
                content = ""
            else:
                content = UnicodeDammit(a,is_html=True).unicode_markup
            count,html = translate_html(content, client,dryrun=dryrun)
            totalcount += count
            conbytes = gzip.compress(html.encode())
            record.raw_stream = io.BytesIO(conbytes)
            record.payload_length = len(conbytes)
            record.http_headers.replace_header('Content-Encoding', 'gzip')
        if record.rec_type == 'response' and record.http_headers and record.http_headers.get_header('Content-Type') and 'json' in record.http_headers.get_header('Content-Type'):
            content = UnicodeDammit(record.content_stream().read()).unicode_markup
            try:
                count,json = translate_json(content, client,dryrun=dryrun)
            except ValueError:
                print("Could not decode JSON for: " , record.rec_headers.get_header('WARC-Target-URI'))
                count = 0
                json = content
            totalcount += count
            conbytes = gzip.compress(json.encode())
            record.raw_stream = io.BytesIO(conbytes)
            record.payload_length = len(conbytes)
            record.http_headers.replace_header('Content-Encoding', 'gzip')
        output.write_record(record)
    return totalcount

def main():
    parser = argparse.ArgumentParser( prog='warcutil', description='Utility to process warc files.')
    parser.add_argument('filename', help="input filename")
    parser.add_argument('-d', '--dry-run', action='store_true', help="Diagnostic to not send data. Counts number of characters to be translated.")
    parser.add_argument('-z', '--wacz',    action='store_true', help="Outputs wacz instead of warc (overrides --gzip)")
    parser.add_argument('-g', '--gzip',    action='store_true', help="Outputs warc.gz instead of warc")
    parser.add_argument('-s', '--simple',    action='store_true', help="Converts html using a more primitive algo. Use this if not using google translate.")
    args = parser.parse_args()
    iswacz = args.filename[-4:].lower() == "wacz"
        
    filesplit = os.path.splitext(os.path.basename(args.filename))[0]
    outname = filesplit + "-english"
    if args.gzip:
        outname += ".warc.gz"
    else:
        outname += ".warc"
    if not iswacz:
        with open(args.filename, 'rb') as instream, open(outname, 'wb') as outstream:
            writer = WARCWriter(outstream, gzip=args.gzip)
            translate_client = translate.Client()
            print("Connected to this project: ", translate_client._credentials.quota_project_id)
            count = translaterecords(ArchiveIterator(instream), writer, translate_client, dryrun=args.dry_run, simple=args.simple)
            print("Characters translated: ", count)
    else:
        with zipfile.ZipFile(args.filename) as myzip, open(outname, 'wb') as outstream:
            count = 0
            writer = WARCWriter(outstream, gzip=args.gzip)
            translate_client = translate.Client()
            print("Connected to this project: ", translate_client._credentials.quota_project_id)
            archives = [x for x in myzip.namelist() if x[0:8] == "archive/"]
            for x in archives:
                with myzip.open(x) as subfile:
                    count += translaterecords(ArchiveIterator(subfile), writer, translate_client, dryrun=args.dry_run, simple=args.simple)
            print("Characters translated: ", count)
    


if __name__ == "__main__":
    main()