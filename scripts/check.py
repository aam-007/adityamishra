"""Check generated HTML, local URL casing, document coverage, and catalogue data."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
import sys
import re

ROOT=Path(__file__).resolve().parents[1]
errors=[]
class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.urls=[]; self.ids=set(); self.title=False; self.main=0; self.h1=0; self.description=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        for key in ('href','src'):
            if key in a: self.urls.append(a[key])
        if 'id' in a:
            if a['id'] in self.ids: errors.append(f'{self.path}: duplicate id {a["id"]}')
            self.ids.add(a['id'])
        self.title|=tag=='title'; self.main+=tag=='main'; self.h1+=tag=='h1'
        self.description|=tag=='meta' and a.get('name')=='description'

def exact(path):
    if not path.exists(): return False
    return all(part.name in [c.name for c in part.parent.iterdir()] for part in [path,*path.parents] if part!=ROOT and ROOT in part.parents)

pages={}
for path in ROOT.rglob('*.html'):
    if any(part in path.parts for part in ('.git','templates','tmp')): continue
    parser=Page(); parser.path=path.relative_to(ROOT); parser.feed(path.read_text(encoding='utf-8')); pages[path]=parser
    legacy=path.name=='paper.html'
    if not parser.title or (not legacy and (parser.main!=1 or parser.h1!=1 or not parser.description)):
        errors.append(f'{parser.path}: missing title, description, or unique main/h1')
for path,parser in pages.items():
    for href in parser.urls:
        u=urlsplit(href)
        if u.scheme or u.netloc: continue
        target=(path.parent/unquote(u.path)).resolve() if u.path else path
        if not target.is_relative_to(ROOT): errors.append(f'{parser.path}: URL escapes project: {href}'); continue
        if not exact(target): errors.append(f'{parser.path}: missing target or wrong case: {href}')
        if u.fragment and target in pages and unquote(u.fragment) not in pages[target].ids:
            errors.append(f'{parser.path}: missing anchor: {href}')
data=json.loads((ROOT/'content.json').read_text(encoding='utf-8'))
ids=[p['id'] for p in data['papers']]
if len(ids)!=len(set(ids)): errors.append('Duplicate paper ids')
paths=[p['path'] for p in data['papers']]
if len(paths)!=len(set(paths)): errors.append('Duplicate document paths')
for p in data['papers']:
    if not exact(ROOT/p['path']): errors.append(f'Missing document: {p["path"]}')
for p in ROOT.rglob('*.pdf'):
    if 'Resume' not in p.parts and p.relative_to(ROOT).as_posix() not in paths:
        # Alternate versions remain accessible as source assets, outside the main catalogue.
        print(f'Alternate document (not catalogued): {p.relative_to(ROOT)}')
for page in data['pages']:
    for p in page['documents']:
        if p not in paths: errors.append(f'Archive page references uncatalogued document: {p}')
for featured in data['featured']:
    if featured not in ids: errors.append(f'Missing featured paper: {featured}')
for template in (ROOT/'templates').rglob('*.html'):
    relative=template.relative_to(ROOT/'templates')
    if template.name=='paper.html': continue
    original=re.search(r'<style>(.*?)</style>',template.read_text(encoding='utf-8'),re.S).group(1)
    generated=(ROOT/relative).read_text(encoding='utf-8')
    stylesheet=re.search(r'href="([^"]*original-[^"]+\.css)"',generated)
    if not stylesheet or ((ROOT/relative).parent/unquote(stylesheet[1])).read_text(encoding='utf-8')!=original:
        errors.append(f'{relative}: original design styles were altered')
if errors:
    print('\n'.join(errors)); sys.exit(1)
print(f'PASS: {len(pages)} pages; local targets, filename casing, anchors, metadata, and {len(paths)} catalogue entries checked.')
