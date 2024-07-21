from warcio.warcwriter import WARCWriter
from warcio.archiveiterator import ArchiveIterator
from warcio.recordloader import ArcWarcRecord

from translate import *

import io
import gzip


with open('baidu-test-20240715021247.warc', 'rb') as instream, open('translate-baidu2.warc', 'wb') as outstream:
    writer = WARCWriter(outstream, gzip=True)
    translate_client = translate.Client()
    print("Connected to this project: ", translate_client._credentials.quota_project_id)
    record : ArcWarcRecord
    for record in ArchiveIterator(instream):
        if record.rec_type == 'response' and record.http_headers and record.http_headers.get_header('Content-Type') and 'html' in record.http_headers.get_header('Content-Type'):
            content = record.content_stream().read().decode()
            conbytes = gzip.compress(translate_html(content, translate_client).encode())
            record.raw_stream = io.BytesIO(conbytes)
            record.payload_length = len(conbytes)
            record.http_headers.replace_header('Content-Encoding', 'gzip')
        if record.rec_type == 'response' and record.http_headers and record.http_headers.get_header('Content-Type') and 'json' in record.http_headers.get_header('Content-Type'):
            content = record.content_stream().read().decode('utf-8')
            conbytes = gzip.compress(translate_json(content, translate_client).encode())
            record.raw_stream = io.BytesIO(conbytes)
            record.payload_length = len(conbytes)
            record.http_headers.replace_header('Content-Encoding', 'gzip')
        writer.write_record(record)
