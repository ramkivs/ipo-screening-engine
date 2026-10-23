"""Capture routing + governance/governance-safety extraction from a given engine tree."""
import json, sys
from pathlib import Path
tree = Path(sys.argv[1]); out = Path(sys.argv[2])
sys.path.insert(0, str(tree / 'engine'))
from ipo_screening.extraction.pdf_source import load_pdf_source
from ipo_screening.extraction.toc import TOCRouter
from ipo_screening.extraction.sections import SectionExtractor
pdf = tree / 'evidence/non-authoritative/jio/U72900GJ2019PLC110816_JIO.pdf'
doc, reader = load_pdf_source(pdf)
toc = TOCRouter.from_pdf(reader)
ranges = {k: toc.get_page_range(k) for k in toc.entries if toc.get_page_range(k)}
ex = SectionExtractor(doc, reader)
rows = []
for method, arg in (('extract_governance', ranges),):
    for x in getattr(ex, method)(arg):
        if x.field_path.startswith('governance.') and 'related_party' not in x.field_path:
            rows.append({'field': x.field_path, 'value': x.candidate_value, 'page': x.page,
                         'quote': x.quote, 'quote_is_processing': x.quote_is_processing})
obj = [x for x in ex.extract_objects_of_offer(ranges)]
uop = next((x for x in obj if x.field_path == 'use_of_proceeds'), None)
payload = {'engine_tree': str(tree), 'routing': {k: list(v) for k, v in ranges.items()},
           'governance': rows,
           'use_of_proceeds': None if uop is None else {'value': uop.candidate_value, 'page': uop.page,
               'leaves': [{'field': x.field_path, 'value': x.candidate_value, 'page': x.page} for x in obj if x.field_path != 'use_of_proceeds']},
           'capital_structure_promoter': {x.field_path: {'value': x.candidate_value, 'page': x.page}
               for x in ex.extract_capital_structure(ranges) if 'promoter_pre' in x.field_path or 'promoter_post' in x.field_path}}
out.write_text(json.dumps(payload, indent=2, default=str) + '\n')
print('written', out)
