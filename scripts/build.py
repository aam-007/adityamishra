"""Generate the static site while retaining its original, deliberate design."""
from pathlib import Path
from html import escape
from urllib.parse import quote
import hashlib
import json
import os
import re

ROOT=Path(__file__).resolve().parents[1]
BASE='https://aam-007.github.io/adityamishra/'
DATA=json.loads((ROOT/'content.json').read_text(encoding='utf-8'))
INTRO='<p class="introduction">I am pursuing a Master of Business Administration in Technology Management and Data Science at the engineering school of NMIMS, Mumbai. My interests span financial research, portfolio theory, and data engineering, informed by my experience as a research intern at Helios Capital.</p>'
CONTACT='<h2 class="contact-heading">Contact</h2><p class="contact"><a href="mailto:adityamishra2007mum@gmail.com">adityamishra2007mum@gmail.com</a><br><a href="mailto:aditya.mishra10@nmims.in">aditya.mishra10@nmims.in</a></p>'

def url(target,current):
    return quote(os.path.relpath(ROOT/target,(ROOT/current).parent).replace('\\','/'),safe='/')

def anchor(target,title,current):
    return f'<a href="{url(target,current)}">{escape(title)}</a>'

def collection_documents(path,ancestors=()):
    if path in ancestors:
        raise ValueError('Circular research collection: '+path)
    page=next(p for p in DATA['pages'] if p['path']==path)
    documents=set(page['documents'])
    for child,_ in page['links']:
        documents.update(collection_documents(child,(*ancestors,path)))
    return documents

def footlabel(current):
    return '<footer class="site-footlabel"><span class="footer-year" hidden><time data-current-year></time> · </span>'+anchor('sitemap.html','Sitemap',current)+'</footer>'

def paper_table(papers,current,search=False):
    rows=[]
    topics={p['topic'] for p in papers}
    years={p['year'] for p in papers}
    show_topic=search or len(topics)>1
    show_year=search or len(years)>1
    for p in sorted(papers,key=lambda p:(-int(p['year'] or '0'),p['title'].casefold())):
        size=(ROOT/p['path']).stat().st_size
        size_label=f'{size/1048576:.1f} MB' if size>=1048576 else f'{round(size/1024)} KB'
        file=f'<a href="{url(p["path"],current)}" aria-label="Open PDF: {escape(p["title"],quote=True)}">PDF</a><small>{size_label}</small>'
        metadata=('<td class="paper-topic">'+escape(p['topic'])+'</td>' if show_topic else '')+('<td class="paper-year">'+(p['year'] or '—')+'</td>' if show_year else '')
        rows.append(f'<tr class="paper" data-topic="{escape(p["topic"])}" data-year="{p["year"]}" data-search="{escape(p["summary"],quote=True)}"><th scope="row">{anchor(p["path"],p["title"],current)}</th>{metadata}<td class="paper-file">{file}</td></tr>')
    caption='Research documents; a dash indicates an unverified publication year.' if search else str(len(papers))+' documents'+(' · '+next(iter(years)) if len(years)==1 and next(iter(years)) else '')
    headers='<th scope="col">Title</th>'+('<th class="paper-topic" scope="col">Topic</th>' if show_topic else '')+('<th class="paper-year" scope="col">Year</th>' if show_year else '')+'<th class="paper-file" scope="col">File</th>'
    return '<table class="archive-table document-table"><caption'+(' class="visually-hidden"' if search else '')+'>'+escape(caption)+'</caption><thead><tr>'+headers+'</tr></thead><tbody'+(' id="catalogue"' if search else '')+'>'+''.join(rows)+'</tbody></table>'

def directory_table(page,current):
    rows=[]
    for target,label in page['links']:
        count=len(collection_documents(target))
        rows.append('<tr><th scope="row">'+anchor(target,label,current)+'</th><td>'+str(count)+'</td></tr>')
    return '<table class="archive-table directory-table"><caption class="visually-hidden">Research collections</caption><thead><tr><th scope="col">Collection</th><th scope="col">Documents</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>'

def build(current,source,title,description):
    css=re.search(r'<style>(.*?)</style>',source,re.S).group(1)
    # Identical original styles share a file; page-specific differences stay intact.
    filename='assets/original-'+hashlib.sha256(css.encode()).hexdigest()[:10]+'.css'
    (ROOT/filename).write_text(css,encoding='utf-8',newline='\n')
    source=re.sub(r'<style>.*?</style>',f'<link rel="stylesheet" href="{url(filename,current)}">\n<link rel="stylesheet" href="{url("assets/enhancements.css",current)}">',source,flags=re.S)
    source=re.sub(r'<title>.*?</title>',f'<title>{escape(title)}</title>',source)
    canonical=BASE+quote(current,safe='/')
    meta=f'<meta name="description" content="{escape(description,quote=True)}">\n<link rel="canonical" href="{canonical}">\n<meta property="og:title" content="{escape(title,quote=True)}"><meta property="og:description" content="{escape(description,quote=True)}"><meta property="og:type" content="website"><meta property="og:url" content="{canonical}"><meta name="twitter:card" content="summary">\n<script src="{url("assets/theme.js",current)}"></script><script src="{url("assets/catalogue.js",current)}" defer></script>'
    eggs=f'<script src="{url("assets/surprise.js",current)}" defer></script>'
    meta+=f'\n<link rel="stylesheet" href="{url("assets/footer.css",current)}"><script src="{url("assets/footer.js",current)}" defer></script>'
    if current=='research.html' or any(p['path']==current for p in DATA['pages']):
        meta+=f'\n<script src="{url("assets/research-view.js",current)}"></script>'
        source=source.replace('<div class="footer">','<div class="footer">\n<button class="toggle-btn legacy-toggle" id="research-view-toggle" type="button" aria-pressed="false" hidden>[ Switch to Legacy Mode ]</button>')
    source=source.replace('</head>',meta+'\n'+eggs+'\n</head>')
    source=source.replace('<body>','<body>\n<a class="skip-link" href="#main">Skip to content</a>')
    source=source.replace('<div class="content-wrapper">','<main class="content-wrapper" id="main">',1)
    # The final wrapper closing tag becomes the main landmark; original layout is unchanged.
    end=source.rfind('</div>')
    source=source[:end]+'</main>'+source[end+6:]
    source=source.replace('<div class="menu">','<nav class="menu" aria-label="Research navigation">')
    source=re.sub(r'(<nav class="menu"[^>]*>.*?)</div>',r'\1</nav>',source,flags=re.S)
    source=source.replace('<div class="sub-heading">','<h2 class="sub-heading">')
    source=re.sub(r'(<h2 class="sub-heading">.*?)</div>',r'\1</h2>',source,flags=re.S)
    source=source.replace('</body>',footlabel(current)+'\n</body>')
    source='\n'.join(line.rstrip() for line in source.splitlines())+'\n'
    (ROOT/current).parent.mkdir(parents=True,exist_ok=True)
    (ROOT/current).write_text(source,encoding='utf-8',newline='\n')

for template in sorted((ROOT/'templates').rglob('*.html')):
    current=template.relative_to(ROOT/'templates').as_posix()
    if template.name=='paper.html': continue
    source=template.read_text(encoding='utf-8')
    page=next((p for p in DATA['pages'] if p['path']==current),None)
    title='Aditya Mishra' if not page else 'Aditya Mishra - '+page['title']
    description='Aditya Mishra: financial research, portfolio theory, and data engineering. NMIMS MPSTME, Mumbai.' if not page else 'Browse '+page['title']+' in Aditya Mishra’s research repository.'
    if current=='index.html':
        source=source.replace('<h1>Aditya Mishra</h1>','<h1><a class="name-link" id="contact-open" href="contact.html" aria-haspopup="dialog" aria-controls="contact-window">Aditya Mishra</a></h1>')
        window='<dialog id="contact-window" aria-labelledby="contact-title"><header class="window-header"><h2 id="contact-title">Aditya Mishra</h2><form method="dialog"><button class="window-close" aria-label="Close contact window" autofocus>[ Close ]</button></form></header>'+INTRO+CONTACT+'</dialog>'
        source=source.replace('</body>',window+'\n<script src="assets/contact.js" defer></script>\n</body>')
    elif page:
        documents=[p for p in DATA['papers'] if p['path'] in page['documents']]
        listing=directory_table(page,current) if page['links'] else ''
        if documents:
            listing+=paper_table(documents,current)
        listing+='<p class="archive-search-link">'+anchor('research.html','Search all research',current)+'</p>'
        source=re.sub(r'<div class="menu">.*?</div>',lambda _:listing,source,count=1,flags=re.S)
    build(current,source,title,description)

# A direct link also makes the contact information available without JavaScript.
source=(ROOT/'templates/index.html').read_text(encoding='utf-8')
source=source.replace('<div class="menu">',INTRO+CONTACT+'<div class="menu">',1)
source=re.sub(r'(<div class="menu">).*?</div>',r'\1<a href="index.html">&lt;-- Back to Home</a></div>',source,count=1,flags=re.S)
build('contact.html',source,'Aditya Mishra - Contact','About Aditya Mishra and contact email addresses.')

# The search page uses the original repository page as its layout, not a new visual system.
current='research.html'
source=(ROOT/'templates/Repository of Research/repo.html').read_text(encoding='utf-8')
source=source.replace('../index.html','index.html').replace('repository of research','search research')
topics=sorted({p['topic'] for p in DATA['papers']})
years=sorted({p['year'] for p in DATA['papers'] if p['year']},reverse=True)
filters='<form id="filters" role="search" hidden><label>Search <input id="query" type="search" placeholder="Title or keyword" autocomplete="off"></label><label>Topic <select id="topic"><option value="">All topics</option>'+''.join('<option>'+escape(t)+'</option>' for t in topics)+'</select></label><label>Year <select id="year"><option value="">All years</option>'+''.join('<option>'+y+'</option>' for y in years)+'</select></label><button type="reset">Clear filters</button></form>'
catalogue=filters+f'<p id="result-count" role="status" aria-live="polite">{len(DATA["papers"])} documents</p><p id="empty" hidden>No matching documents. Try another search or clear the filters.</p>'+paper_table(DATA['papers'],current,search=True)
source=re.sub(r'<div class="menu">.*?</div>',lambda _:catalogue,source,count=1,flags=re.S)
build(current,source,'Aditya Mishra - Search Research','Search research papers and equity reports by title, topic, and year.')

# The human-readable sitemap is generated from the same catalogue as the archive.
def map_collection(path,ancestors=()):
    if path in ancestors:
        raise ValueError('Circular collection in sitemap: '+path)
    page=next(p for p in DATA['pages'] if p['path']==path)
    count=len(collection_documents(path))
    children=''.join('<li>'+map_collection(child,(*ancestors,path))+'</li>' for child,_ in page['links'])
    documents=[p for p in DATA['papers'] if p['path'] in page['documents']]
    children+=''.join('<li>'+anchor(p['path'],p['title'],'sitemap.html')+' <small>(PDF)</small></li>' for p in sorted(documents,key=lambda p:p['title'].casefold()))
    return '<details><summary>'+escape(page['title'])+f' <small>({count})</small></summary><p>'+anchor(path,'Open collection','sitemap.html')+'</p><ul>'+children+'</ul></details>'

source=(ROOT/'templates/Repository of Research/repo.html').read_text(encoding='utf-8')
source=source.replace('../index.html','index.html').replace('repository of research','sitemap')
top_pages=[('index.html','Home'),('contact.html','About & contact'),('research.html','Search research'),('Resume/AdityaMishra.pdf','Résumé (PDF)'),('cheeky.html','cheeky.html — a little surprise'),('404.html','404 page')]
sitemap='<nav class="sitemap-pages" aria-label="Site pages"><ul>'+''.join('<li>'+anchor(path,label,'sitemap.html')+'</li>' for path,label in top_pages)+'</ul></nav><section class="sitemap-tree" aria-labelledby="sitemap-research"><h3 id="sitemap-research">Research collections</h3><p class="sitemap-controls" hidden><button type="button" id="expand-map">[ Expand all ]</button> <button type="button" id="collapse-map">[ Collapse all ]</button></p>'+map_collection('Repository of Research/repo.html')+'</section><p class="sitemap-github"><a href="https://github.com/aam-007/adityamishra" target="_blank" rel="noopener noreferrer">GitHub repository ↗</a></p>'
source=re.sub(r'<div class="menu">.*?</div>',lambda _:sitemap,source,count=1,flags=re.S)
source=source.replace('</head>','<script src="assets/sitemap.js" defer></script>\n</head>')
build('sitemap.html',source,'Aditya Mishra - Sitemap','Explore all site pages, research collections, documents, and the GitHub repository.')

# Preserve old addresses while removing the obsolete broken links.
legacy='Repository of Research/Finance/Papers/paper.html'
(ROOT/legacy).write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Papers | Aditya Mishra</title><meta http-equiv="refresh" content="0;url=years.html"><link rel="canonical" href="'+BASE+'Repository%20of%20Research/Finance/Papers/years.html"></head><body><p><a href="years.html">Browse papers by year</a>.</p></body></html>',encoding='utf-8')
paths=['index.html','research.html','contact.html','sitemap.html']+[p['path'] for p in DATA['pages']]
(ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+escape(BASE+quote(p,safe='/'))+'</loc></url>' for p in paths)+'</urlset>',encoding='utf-8')
source=(ROOT/'templates/index.html').read_text(encoding='utf-8')
recovery='<section class="error-message" aria-labelledby="error-title"><h2 id="error-title">404 — Page not found</h2><p>This address does not lead to a page or document.<br>The link may be outdated, or the address may contain a typo.</p></section><form class="error-search" role="search" action="'+BASE+'research.html" method="get"><label for="error-query">Find a paper or report</label><p><input id="error-query" type="search" name="q" placeholder="Title, topic, or keyword" required><button type="submit">Search</button></p></form><div class="menu"><a href="'+BASE+'">Back to Home</a><a href="'+BASE+'Repository%20of%20Research/repo.html">Repository of Research</a><a href="'+BASE+'contact.html">Contact</a></div>'
source=re.sub(r'<div class="menu">.*?</div>',lambda _:recovery,source,count=1,flags=re.S)
source=source.replace('</head>','<meta name="robots" content="noindex, follow">\n</head>')
build('404.html',source,'Aditya Mishra - Page Not Found','Return to the homepage or search the research repository.')
# GitHub serves this document at missing nested URLs; absolute asset URLs are required.
notfound=(ROOT/'404.html').read_text(encoding='utf-8')
notfound=re.sub(r'(href|src)="(assets/[^"]+|sitemap\.html)"',lambda m:m[1]+'="'+BASE+m[2]+'"',notfound)
(ROOT/'404.html').write_text(notfound,encoding='utf-8')
print('Built original-design pages, search catalogue, redirect, sitemap, and 404 page.')

(ROOT/'cheeky.html').write_text('''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>A little surprise | Aditya Mishra</title><meta name="description" content="A little surprise."><meta name="robots" content="noindex, follow">
<script src="assets/theme.js"></script><link rel="stylesheet" href="assets/surprise.css"><link rel="stylesheet" href="assets/footer.css"><script src="assets/footer.js" defer></script></head>
<body class="surprise-page"><main><h1 id="surprise-icon">:)</h1><p id="surprise-message">a cheeky one, aren't you?</p><a href="index.html">back to site</a></main><script src="assets/surprise-message.js"></script>'''+footlabel('cheeky.html')+'''</body></html>
''',encoding='utf-8',newline='\n')
