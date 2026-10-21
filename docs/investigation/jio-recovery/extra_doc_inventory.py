"""Read-only complete bounded inventories of additional official issue files.

Diagnostic only: no extracted number is promoted to a canonical field. Archive
paths are never extracted and spreadsheet formulae/macros are never executed.
"""
import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import traceback
import zipfile
import zlib


def inspect(raw, uri, out):
    docs = []
    if not raw.startswith(b'PK\x03\x04'):
        members = [(uri.rsplit('/', 1)[-1], raw)]
    else:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = [entry for entry in archive.infolist() if not entry.is_dir()]
            if len(entries) > 32 or sum(entry.file_size for entry in entries) > 64 * 1024 * 1024:
                raise ValueError('additional official archive exceeds bounded limits')
            members = []
            for entry in entries:
                if entry.flag_bits & 1 or entry.file_size > 32 * 1024 * 1024 or entry.file_size > max(1, entry.compress_size) * 200:
                    raise ValueError('encrypted/oversized additional archive member')
                members.append((entry.filename, archive.read(entry)))
    for name, body in members:
        digest = hashlib.sha256(body).hexdigest()
        (out / (digest + Path(name).suffix.lower())).write_bytes(body)
        row = {'name': name, 'bytes': len(body), 'sha256': digest, 'complete': True}
        try:
            if len(body) <= 512000:
                row['public_document_zlib_base64'] = base64.b64encode(zlib.compress(body)).decode()
            if body.startswith(b'%PDF-'):
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(body))
                if len(reader.pages) > 100:
                    raise ValueError('additional financial PDF exceeds 100-page diagnostic limit')
                row['pages'] = [{'page': i+1, 'text': page.extract_text() or ''}
                                for i, page in enumerate(reader.pages)]
                if not any(len(page['text'].strip()) >= 50 for page in row['pages']):
                    row['complete'] = False
                    row['gap'] = 'IMAGE_ONLY: requires original-image review/OCR; not proof of missing terms'
            elif name.lower().endswith('.xlsx'):
                from openpyxl import load_workbook
                book = load_workbook(io.BytesIO(body), read_only=True, data_only=False)
                try:
                    row['sheets'] = []
                    for sheet in book:
                        if sheet.max_row > 1000 or sheet.max_column > 100:
                            raise ValueError('additional financial sheet exceeds bounded cell grid')
                        row['sheets'].append({'sheet': sheet.title, 'rows': [
                            {'row': index, 'cells': [{'coordinate': cell.coordinate, 'value': str(cell.value),
                             'type': cell.data_type} for cell in cells if cell.value is not None]}
                            for index, cells in enumerate(sheet.iter_rows(), 1)]})
                finally:
                    book.close()
            elif name.lower().endswith('.xls'):
                import xlrd
                book = xlrd.open_workbook(file_contents=body, on_demand=True)
                try:
                    row['sheets'] = []
                    for sheet in book.sheets():
                        if sheet.nrows > 1000 or sheet.ncols > 100:
                            raise ValueError('additional financial sheet exceeds bounded cell grid')
                        row['sheets'].append({'sheet': sheet.name, 'rows': [
                            {'row': index+1, 'values': sheet.row_values(index)} for index in range(sheet.nrows)]})
                finally:
                    book.release_resources()
            elif name.lower().endswith(('.csv', '.txt')):
                row['text'] = body.decode('utf-8-sig', errors='strict')
            else:
                row['complete'] = False
                row['gap'] = 'UNSUPPORTED MEMBER TYPE; not proof of missing terms'
        except Exception:
            row['complete'] = False
            row['traceback'] = traceback.format_exc()
        docs.append(row)
    return docs
