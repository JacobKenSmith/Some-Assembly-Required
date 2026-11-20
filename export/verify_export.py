"""Verify the exact exported source snapshot using Python's standard library."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import hashlib, json
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'export/SOURCE_SHA256.json').read_text())
errors=[]
for name,digest in manifest.items():
    path=ROOT/name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        errors.append('Missing or changed original file: '+name)
web=ROOT/'dist'
class LinkChecker(HTMLParser):
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key not in ('href','src') or not value: continue
            parsed=urlsplit(value)
            if parsed.scheme or parsed.netloc or not parsed.path: continue
            target=(web/unquote(parsed.path.lstrip('/'))) if parsed.path.startswith('/') else self.path.parent/unquote(parsed.path)
            if not target.exists(): errors.append('Broken local link: '+str(self.path.relative_to(ROOT))+' -> '+value)
for path in web.rglob('*.html'):
    parser=LinkChecker(); parser.path=path; parser.feed(path.read_text(encoding='utf-8'))
data=json.loads((web/'edition-data.json').read_text(encoding='utf-8'))
sources={s['id']:s for s in data['sources']}
for source in sources.values():
    for key in ('postData','url','image'):
        value=source.get(key)
        if value and not urlsplit(value).scheme and not urlsplit(value).netloc and not (web/value).is_file():
            errors.append('Missing source file: '+value)
for annotation in data['annotations']:
    if annotation['source'] not in sources: errors.append('Missing annotation source: '+annotation['id'])
annotation_ids={a['id'] for a in data['annotations']}
for expected in ('4chan-250550578-response-1','usenet-post-20601-8faa2e13-engagement-1'):
    if expected not in annotation_ids: errors.append('Missing deep-link annotation: '+expected)
if len(data['paragraphs'])!=232: errors.append('Unexpected primary-text paragraph count')
if errors:
    print('\n'.join(errors)); raise SystemExit(1)
print(f"PASS: {len(manifest):,} original files match SHA-256; local HTML/source references resolve.")
print(f"Preserved: {len(data['paragraphs'])} primary paragraphs, {len(data['annotations'])} annotations, {len(data['additionalResponses'])} additional responses.")
print('Example passage-specific annotation IDs are present.')
