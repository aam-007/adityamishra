"""Validate the poetry collection; optionally compare it with the cited editions.

Run with --verify-sources to download the four source editions, or --source-dir
to use previously downloaded copies. Network access is never needed by the site.
"""
from pathlib import Path
from html import unescape
from urllib.request import urlopen
import argparse
import json
import re

ROOT = Path(__file__).resolve().parents[1]
AUTHORS = {
    'C. MARLOWE.': 'Christopher Marlowe',
    'W. SHAKESPEARE.': 'William Shakespeare',
    'H. CONSTABLE.': 'Henry Constable',
    'T. LODGE.': 'Thomas Lodge',
    'SIR P. SIDNEY.': 'Philip Sidney',
    'J. SYLVESTER.': 'Joshua Sylvester',
    'E. WALLER.': 'Edmund Waller',
    'B. JONSON.': 'Ben Jonson',
    'R. HERRICK.': 'Robert Herrick',
    'COLONEL LOVELACE.': 'Richard Lovelace',
    'J. GAY.': 'John Gay',
    'H. CAREY.': 'Henry Carey',
    'S. ROGERS.': 'Samuel Rogers',
    'R. BURNS.': 'Robert Burns',
    'W. COWPER.': 'William Cowper',
    'S. T. COLERIDGE.': 'Samuel Taylor Coleridge',
    'LORD BYRON.': 'Lord Byron',
    'P.B. SHELLEY.': 'Percy Bysshe Shelley',
    'P. B. SHELLEY.': 'Percy Bysshe Shelley',
    'W. WORDSWORTH.': 'William Wordsworth',
    'H. COLERIDGE.': 'Hartley Coleridge',
    'T. CAMPBELL.': 'Thomas Campbell',
    'T. MOORE.': 'Thomas Moore',
    'SIR W. SCOTT.': 'Walter Scott',
    'J. KEATS.': 'John Keats',
}


def plain(html):
    return unescape(re.sub(r'<[^>]+>', '', html))


def parse_source(source_id, text):
    if source_id == 'treasury':
        poems = {}
        for block in re.findall(r'<pre[^>]*>(.*?)</pre>', text, re.S):
            lines = [line.strip() for line in plain(block).strip().splitlines() if line.strip()]
            match = re.match(r'^(\d+)\.\s*(.*)', lines[0]) if lines else None
            if match:
                number, title = match.groups()
                credit = lines[-1]
                poems[number] = {'heading': title, 'credit': credit,
                                 'author': AUTHORS.get(credit), 'lines': lines[1:-1]}
        return poems
    if source_id in ('browning', 'shakespeare'):
        author = 'Elizabeth Barrett Browning' if source_id == 'browning' else 'William Shakespeare'
        assert f'Author: {author}' in text, f'{source_id}: author credit missing'
        text = text.split('*** END OF THE PROJECT GUTENBERG EBOOK')[0]
        blocks = re.split(r'\n\s*([IVXLCDM]+)\s*\n', text)
        return {blocks[i]: {'heading': blocks[i], 'credit': author, 'author': author,
                            'lines': [line.strip() for line in blocks[i+1].splitlines() if line.strip()]}
                for i in range(1, len(blocks)-1, 2)}
    if source_id == 'byron-beauty':
        assert 'Byron, George Gordon Lord' in plain(text), 'Byron credit missing'
        lines = [plain(line).strip() for line in re.findall(
            r'<span id="poemline-\d+" class="line-text">(.*?)</span>', text, re.S)]
        return {'1': {'heading': 'She Walks in Beauty', 'credit': 'Byron, George Gordon Lord',
                      'author': 'Lord Byron', 'lines': lines}}
    raise ValueError('Unknown source: ' + source_id)


def validate(data):
    poems, sources = data['poems'], data['sources']
    assert len(poems) == 100, 'Exactly 100 poems are required'
    assert len({p['id'] for p in poems}) == 100, 'Duplicate ids'
    assert len({p['text'] for p in poems}) == 100, 'Duplicate excerpts'
    assert len({(p['author'], p['title']) for p in poems}) == 100, 'Repeated works'
    assert len({(p['source'], p['poem']) for p in poems}) == 100, 'Repeated source poems'
    for p in poems:
        assert p['source'] in sources, p['id']
        assert p['author'] and p['title'] and p['sourceCredit'], p['id']
        assert 2 <= len(p['text'].splitlines()) <= 8, p['id']
        assert 1 <= p['lineStart'] <= p['lineEnd'], p['id']
        assert len(p['text'].splitlines()) == p['lineEnd'] - p['lineStart'] + 1, p['id']
        assert isinstance(p['excerpt'], bool), p['id']
        assert '\ufffd' not in p['text'] and '<' not in p['text'], p['id']
        assert sources[p['source']]['url'].startswith('https://'), p['id']


def verify_sources(data, source_dir=None):
    parsed = {}
    for key, source in data['sources'].items():
        if source_dir:
            raw = (Path(source_dir) / source['cacheFile']).read_bytes()
        else:
            with urlopen(source['downloadUrl'], timeout=45) as response:
                raw = response.read()
        parsed[key] = parse_source(key, raw.decode('utf-8-sig'))
    for p in data['poems']:
        original = parsed[p['source']][p['poem']]
        assert original['author'] == p['author'], f"{p['id']}: incorrect author"
        assert original['credit'] == p['sourceCredit'], f"{p['id']}: source credit changed"
        assert original['heading'] == p['sourceHeading'], f"{p['id']}: source heading changed"
        lines = original['lines'][p['lineStart']-1:p['lineEnd']]
        assert '\n'.join(lines) == p['text'], f"{p['id']}: text does not match the cited lines"
        assert p['excerpt'] == (p['lineStart'] != 1 or p['lineEnd'] != len(original['lines'])), p['id']
    print('PASS: all 100 excerpts and author credits match the four cited editions.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-sources', action='store_true')
    parser.add_argument('--source-dir', type=Path)
    args = parser.parse_args()
    collection = json.loads((ROOT / 'romantic-poems.json').read_text(encoding='utf-8'))
    validate(collection)
    if args.verify_sources or args.source_dir:
        verify_sources(collection, args.source_dir)
    else:
        print('PASS: 100 unique, attributed poetry entries; collection structure is valid.')
