#!/usr/bin/env python3
"""Build a bilingual, SEO-friendly static glossary for GitHub Pages.

Only Python 3 standard library is required. Data is sourced from data/glossary.csv;
optional additions live in data/enrichments.json.
"""
import csv
import html
import json
import re
import shutil
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote, urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '_site'
REPO = 'https://github.com/SergioGilBorras/ai-development-glossary'
ORIGIN = 'https://SergioGilBorras.github.io'
BASE = '/ai-development-glossary/'
SITE = ORIGIN + BASE
CATS = {
 'Fundamentos y flujo de trabajo': ('foundations','Foundations & workflows'),
 'Prompts y gestión del contexto': ('prompts','Prompts & context'),
 'Modelos y entrenamiento': ('models','Models & training'),
 'RAG y conocimiento': ('rag','RAG & knowledge'),
 'Agentes y orquestación': ('agents','Agents & orchestration'),
 'Programación asistida por IA': ('coding','AI-assisted programming'),
 'Evaluación y calidad': ('evaluation','Evaluation & quality'),
 'Seguridad y privacidad': ('security','Security & privacy'),
 'Datos, MLOps y observabilidad': ('data','Data, MLOps & observability'),
 'Infraestructura y rendimiento': ('infrastructure','Infrastructure & performance'),
 'Documentación de ingeniería': ('engineering','Engineering documentation'),
 'Ámbito jurídico y legaltech': ('legal','Legal & legaltech'),
 'Gobernanza y cumplimiento': ('governance','Governance & compliance'),
 'Multimodalidad y documentos': ('multimodal','Multimodality & documents'),
 'Producto y experiencia de usuario': ('product','Product & user experience'),
}
T = {
 'es': {'tag':'Glosario abierto de desarrollo con IA','hero':'Entiende el lenguaje de la inteligencia artificial.','sub':'Términos técnicos explicados con claridad. Del desarrollo de software a los agentes, la ingeniería y el ámbito jurídico.', 'browse':'Explorar glosario','search':'Buscar término, sigla o definición…','cat':'Categoría','all':'Todas las categorías','result':'términos','details':'Ver detalle','suggest':'Proponer término','correct':'Sugerir corrección','definition':'Definición','example':'Ejemplo de uso','related':'Relacionado con','sources':'Más información','source':'Fuente externa','back':'Volver al glosario','english':'Término en inglés','spanish':'Término en español','empty':'No se han encontrado términos. Prueba otra búsqueda o categoría.','clear':'Limpiar filtros','allalpha':'Índice alfabético','intro':'El glosario en pocas palabras','contribute':'Este es un proyecto abierto. ¿Echas en falta un concepto?','contributeText':'Ayúdanos a mantener las definiciones útiles, verificables y actuales. Las propuestas se revisan antes de publicarse.','copy':'Copiar enlace','copied':'Enlace copiado','next':'Siguiente','prev':'Anterior','github':'Código en GitHub','other':'Ver en inglés','home':'Inicio','jump':'Ir al listado','skip':'Saltar al contenido'},
 'en': {'tag':'Open glossary for AI development','hero':'Understand the language of artificial intelligence.','sub':'Technical terms, clearly explained. From software development and agents to engineering and legal workflows.','browse':'Browse glossary','search':'Search for a term, acronym or definition…','cat':'Category','all':'All categories','result':'terms','details':'View details','suggest':'Suggest a term','correct':'Suggest a correction','definition':'Definition','example':'Usage example','related':'Related terms','sources':'Learn more','source':'External source','back':'Back to glossary','english':'English term','spanish':'Spanish term','empty':'No matching terms. Try a different search or category.','clear':'Clear filters','allalpha':'Alphabetical index','intro':'A glossary made for real projects','contribute':'This is an open project. Missing a concept?','contributeText':'Help us keep definitions useful, verifiable and up to date. Suggestions are reviewed before publication.','copy':'Copy link','copied':'Link copied','next':'Next','prev':'Previous','github':'Source on GitHub','other':'Ver en español','home':'Home','jump':'Jump to terms','skip':'Skip to content'},
}
# Curated context-sensitive fallback. Individual enrichments always take priority.
CONTEXT = {
'foundations': ('In a project kickoff, the team explicitly discusses {term} to align expectations before starting the AI work.', 'En la reunión de inicio, el equipo analiza {term} para alinear expectativas antes de comenzar el trabajo con IA.'),
'prompts': ('While configuring an assistant, the team tests {term} to improve how the model responds to instructions.', 'Al configurar un asistente, el equipo prueba {term} para mejorar cómo responde el modelo a las instrucciones.'),
'models': ('While adapting a language model for a new task, engineers evaluate the impact of {term} on its behavior.', 'Al adaptar un modelo de lenguaje a otra tarea, los ingenieros evalúan cómo influye {term} en su comportamiento.'),
'rag': ('A support assistant built on company documentation considers {term} when retrieving information for its answers.', 'Un asistente basado en documentación interna tiene en cuenta {term} al recuperar información para responder.'),
'agents': ('In a multi-agent workflow, the team decides how to use {term} while coordinating tasks and tools.', 'En un flujo con varios agentes, el equipo decide cómo utilizar {term} para coordinar tareas y herramientas.'),
'coding': ('Before merging a change suggested by an AI coding assistant, the developer checks {term} in the repository workflow.', 'Antes de incorporar un cambio propuesto por un asistente de programación, el desarrollador comprueba {term} en el flujo del repositorio.'),
'evaluation': ('During an assistant quality review, the team uses {term} to analyze results before a release.', 'Durante una revisión de calidad de un asistente, el equipo utiliza {term} para analizar los resultados antes de publicar.'),
'security': ('During a security review of an AI application, the team assesses {term} before granting production access.', 'Durante una revisión de seguridad de una aplicación de IA, el equipo evalúa {term} antes de habilitar su uso en producción.'),
'data': ('In the model operations dashboard, engineers monitor {term} to identify problems early.', 'En el panel de operación de modelos, los ingenieros supervisan {term} para identificar problemas a tiempo.'),
'infrastructure': ('When deploying a model endpoint, the operations team reviews {term} to estimate capacity and reliability.', 'Al desplegar un endpoint de modelos, operaciones revisa {term} para estimar capacidad y fiabilidad.'),
'engineering': ('When preparing an AI-assisted engineering deliverable, the team reviews {term} with the responsible engineer before approval.', 'Al preparar un entregable de ingeniería con asistencia de IA, el equipo revisa {term} con el ingeniero responsable antes de aprobarlo.'),
'legal': ('When using AI in a legal matter, the legal team checks {term} before relying on the output in a client deliverable.', 'Al utilizar IA en un asunto jurídico, el equipo legal comprueba {term} antes de incorporar resultados a un entregable para el cliente.'),
'governance': ('Before approving an AI system for organizational use, the governance team documents {term} in its assessment.', 'Antes de aprobar un sistema de IA en la organización, el equipo de gobernanza documenta {term} en su evaluación.'),
'multimodal': ('When processing mixed text and media documents, the team tests {term} as part of the extraction pipeline.', 'Al procesar documentos con texto y otros medios, el equipo prueba {term} como parte del proceso de extracción.'),
'product': ('During a usability session for an AI product, the team observes how {term} affects the user experience.', 'Durante una sesión de usabilidad de un producto de IA, el equipo observa cómo afecta {term} a la experiencia de usuario.'),
}

def esc(value): return html.escape(str(value or ''), quote=True)
def slugify(value):
    value = unicodedata.normalize('NFKD', value.lower())
    value = ''.join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r'[^a-z0-9]+', '-', value).strip('-')
    return value[:85] or 'term'
def clean_url(url):
    url = (url or '').strip()
    p = urlparse(url)
    return url if p.scheme == 'https' and p.netloc and not p.username and not p.password else ''
def a_link(lang, slug): return f'{BASE}{lang}/term/{quote(slug)}/'
def index_link(lang): return f'{BASE}{lang}/'
def issue_url(kind, term=''):
    fname = 'correct-term.yml' if kind == 'correct' else 'new-term.yml'
    base = f'{REPO}/issues/new?template={fname}'
    return base + ('&title=' + quote('[Correction] ' + term) if kind == 'correct' and term else '')

def read_data():
    with (ROOT/'data/glossary.csv').open(encoding='utf-8-sig', newline='') as f: original=list(csv.DictReader(f))
    extras_path=ROOT/'data/enrichments.json'
    extras=json.loads(extras_path.read_text(encoding='utf-8')) if extras_path.exists() else {}
    if not isinstance(extras,dict): raise ValueError('data/enrichments.json must contain a JSON object')
    ids=set(); en_names=set(); terms=[]; errors=[]
    for n,row in enumerate(original,2):
        id=(row.get('ID') or '').strip()
        en=(row.get('Term (EN)') or '').strip()
        es=(row.get('Término (ES)') or '').strip()
        den=(row.get('Meaning (EN)') or '').strip()
        des=(row.get('Significado (ES)') or '').strip()
        cat=(row.get('Categoría') or '').strip()
        if not all((id,en,es,den,des)) or cat not in CATS: errors.append(f'Row {n}: empty mandatory field or invalid category')
        if id in ids or en.casefold() in en_names: errors.append(f'Row {n}: duplicated ID or English term: {id} / {en}')
        ids.add(id); en_names.add(en.casefold())
        e=extras.get(id,{})
        if not isinstance(e,dict): errors.append(f'Invalid enrichment for {id}');e={}
        k,cat_en=CATS.get(cat,('other',cat))
        terms.append({'id':id,'term_en':en,'term_es':es,'definition_en':den,'definition_es':des,'category':k,'category_en':cat_en,'category_es':cat,'slug':slugify(en),'example_en':e.get('example_en') or CONTEXT[k][0].format(term=en), 'example_es':e.get('example_es') or CONTEXT[k][1].format(term=es.lower()), 'aliases':e.get('aliases',[]), 'related_ids':e.get('related_ids',[]), 'source_url':clean_url(e.get('source_url') or row.get('Referencia (URL)'))})
    slugs=Counter(t['slug'] for t in terms)
    for slug,count in slugs.items():
        if count>1: errors.append(f'Duplicate URL slug: {slug}')
    for t in terms:
        if not isinstance(t['aliases'],list) or not isinstance(t['related_ids'],list): errors.append('aliases and related_ids must be lists: '+t['id']);continue
        for rel in t['related_ids']:
            if rel not in ids: errors.append(f'Unknown related ID: {t["id"]} -> {rel}')
            if rel==t['id']: errors.append(f'Self-referential related ID: {rel}')
    if errors: raise ValueError('\n'.join(errors))
    return terms

def navbar(lang,t=None):
    other='en' if lang=='es' else 'es'
    lang_url=a_link(other,t['slug']) if t else index_link(other)
    navlabel='ESPAÑOL' if lang=='en' else 'ENGLISH'
    return f'''<header class="header"><div class="wrap nav"><a class="brand" href="{index_link(lang)}" aria-label="AI Development Glossary"><span class="brand-icon">AI<span class="brand-dot">.</span></span><span>Development <b>Glossary</b></span></a><nav class="nav-actions" aria-label="Navigation"><a class="nav-repo" href="{REPO}" target="_blank" rel="noopener noreferrer"><svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .8a11.2 11.2 0 0 0-3.54 21.83c.56.1.76-.24.76-.54v-1.9c-3.09.67-3.74-1.31-3.74-1.31-.5-1.28-1.23-1.62-1.23-1.62-1-.68.08-.67.08-.67 1.11.08 1.7 1.14 1.7 1.14.98 1.68 2.57 1.2 3.2.92.1-.71.38-1.2.7-1.48-2.47-.28-5.06-1.24-5.06-5.52 0-1.22.44-2.22 1.14-3-.11-.28-.5-1.42.11-2.96 0 0 .93-.3 3.07 1.15a10.6 10.6 0 0 1 5.59 0c2.14-1.45 3.07-1.15 3.07-1.15.61 1.54.22 2.68.11 2.96.71.78 1.13 1.78 1.13 3 0 4.29-2.6 5.24-5.08 5.52.39.34.74 1 .74 2.02v3c0 .3.2.65.77.54A11.2 11.2 0 0 0 12 .8Z"/></svg><span>GitHub</span></a><a class="language" href="{lang_url}" lang="{other}" hreflang="{other}">{navlabel} <span aria-hidden="true">↗</span></a><a class="nav-suggest" href="{issue_url('new')}" target="_blank" rel="noopener noreferrer">＋ {esc(T[lang]['suggest'])}</a></nav></div></header>'''
def head(lang,title,description,url,alt_url):
    return f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0b1826"><meta name="description" content="{esc(description)}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(url)}"><meta property="og:site_name" content="AI Development Glossary"><link rel="canonical" href="{esc(url)}"><link rel="alternate" hreflang="{lang}" href="{esc(url)}"><link rel="alternate" hreflang="{'en' if lang=='es' else 'es'}" href="{esc(alt_url)}"><link rel="icon" href="{BASE}assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{BASE}assets/site.css"><title>{esc(title)}</title></head><body><a class="skip" href="#main">{esc(T[lang]['skip'])}</a>'''
def footer(lang):
    t=T[lang]
    return f'''<footer class="footer"><div class="wrap foot-grid"><div><div class="footer-brand">AI<span>.</span> Development Glossary</div><p>{esc(t['tag'])} · EN / ES</p></div><div class="footer-links"><a href="{REPO}" target="_blank" rel="noopener noreferrer">{esc(t['github'])} ↗</a><a href="{issue_url('new')}" target="_blank" rel="noopener noreferrer">{esc(t['suggest'])} ↗</a><a href="{BASE}data/glossary.csv" download>CSV ↓</a><a href="{BASE}data/glossary.json" download>JSON ↓</a></div></div></footer><script src="{BASE}assets/site.js" defer></script></body></html>'''
def entry_list(lang,terms):
    sections=defaultdict(list)
    for t in sorted(terms,key=lambda r: unicodedata.normalize('NFKD',r['term_es' if lang=='es' else 'term_en']).casefold()):
        title=t['term_es' if lang=='es' else 'term_en']; letter=slugify(title)[:1].upper()
        if not letter.isalpha():letter='#'
        sections[letter].append(t)
    out=[]
    for letter in sorted(sections):
        rows=[]
        for t in sections[letter]:
            title=t['term_es' if lang=='es' else 'term_en']; gloss=t['definition_es' if lang=='es' else 'definition_en']
            cat=t['category_es' if lang=='es' else 'category_en']
            rows.append(f'''<article class="term-row" data-id="{esc(t['id'])}" data-category="{esc(t['category'])}"><div class="term-body"><a class="term-name" href="{a_link(lang,t['slug'])}">{esc(title)} <span aria-hidden="true">↗</span></a><p>{esc(gloss)}</p></div><span class="term-tag">{esc(cat)}</span></article>''')
        out.append(f'''<section class="letter-block" id="letter-{letter}" data-letter="{letter}"><h2 class="letter-title">{letter}</h2><div class="term-rows">{''.join(rows)}</div></section>''')
    return ''.join(out)
def landing(lang, terms):
    t=T[lang]
    title='Glosario de IA para desarrolladores | AI Development Glossary' if lang=='es' else 'AI Development Glossary | Bilingual technical terminology'
    desc=t['sub']
    # CATS value is (slug, english label)
    opts=''.join(f'<option value="{slug}">{esc(english if lang=="en" else spanish)}</option>' for spanish,(slug,english) in CATS.items())
    buttons=''.join(f'<a href="#letter-{a}">{a}</a>' for a in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    return head(lang,title,desc,SITE+lang+'/', SITE+('en' if lang=='es' else 'es')+'/')+navbar(lang)+f'''<main id="main"><div class="hero-outer"><section class="wrap hero"><div class="eyebrow"><span class="eyebrow-line"></span>{esc(t['tag'])}</div><h1>{esc(t['hero'])}</h1><p>{esc(t['sub'])}</p><div class="hero-stats"><span><b>{len(terms)}</b> {esc(t['result'])}</span><i></i><span><b>{len(CATS)}</b> {'categories' if lang=='en' else 'categorías'}</span><i></i><span><b>02</b> {'languages' if lang=='en' else 'idiomas'}</span></div><a class="jump" href="#glossary">{esc(t['browse'])} ↓</a></section></div><section class="wrap catalog" id="glossary" aria-labelledby="catalog-title"><div class="catalog-heading"><div><div class="section-kicker">01 / {'GLOSSARY' if lang=='en' else 'GLOSARIO'}</div><h2 id="catalog-title">{esc(t['allalpha'])}</h2></div><p>{esc(t['intro'])}</p></div><div class="filters"><label class="search-label"><span class="field-title">{'SEARCH' if lang=='en' else 'BUSCAR'}</span><span class="search-field"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m16 16 5 5"/></svg><input type="search" id="search" autocomplete="off" placeholder="{esc(t['search'])}" aria-label="{esc(t['search'])}"></span></label><label class="category-label"><span class="field-title">{esc(t['cat']).upper()}</span><select id="category" aria-label="{esc(t['cat'])}"><option value="all">{esc(t['all'])}</option>{opts}</select></label></div><div class="resultsbar"><span id="result-count" role="status" aria-live="polite">{len(terms)} {esc(t['result'])}</span><button type="button" id="clear" class="clear" hidden>{esc(t['clear'])} ↺</button></div><nav class="alphabet" aria-label="{esc(t['allalpha'])}">{buttons}</nav><div id="term-list">{entry_list(lang,terms)}</div><div id="no-results" class="empty" hidden><strong>{esc(t['empty'])}</strong><button id="reset-empty" type="button">{esc(t['clear'])} ↺</button></div></section><section class="contribute"><div class="wrap contribute-inner"><div><div class="section-kicker">02 / {'CONTRIBUTE' if lang=='en' else 'COLABORA'}</div><h2>{esc(t['contribute'])}</h2><p>{esc(t['contributeText'])}</p></div><a class="primary-button" href="{issue_url('new')}" target="_blank" rel="noopener noreferrer">{esc(t['suggest'])} ↗</a></div></section></main>'''+footer(lang)
def detail(lang,t,idx,order,byid):
    tr=T[lang];other='en' if lang=='es' else 'es'
    title=t['term_es' if lang=='es' else 'term_en']
    secondary=t['term_en' if lang=='es' else 'term_es']
    desc=t['definition_es' if lang=='es' else 'definition_en']
    example=t['example_es' if lang=='es' else 'example_en']
    related=[byid[i] for i in t['related_ids'] if i in byid and i!=t['id']]
    related_html=''
    if related:
        pills=''.join(f'<a class="related-pill" href="{a_link(lang,r["slug"])}">{esc(r["term_es" if lang=="es" else "term_en"])} <span aria-hidden="true">↗</span></a>' for r in related)
        related_html=f'<section class="detail-section"><h2>{esc(tr["related"])}</h2><div class="related-list">{pills}</div></section>'
    source_html=f'<section class="detail-section"><h2>{esc(tr["sources"])}</h2><a class="source-link" href="{esc(t["source_url"])}" target="_blank" rel="noopener noreferrer">{esc(tr["source"])} <span aria-hidden="true">↗</span></a></section>' if t['source_url'] else ''
    prev=order[idx-1] if idx>0 else None; nxt=order[idx+1] if idx<len(order)-1 else None
    controls=''.join(f'<a class="pager-link {klass}" href="{a_link(lang,item["slug"])}"><small>{esc(tr[label])}</small><strong>{esc(item["term_es" if lang=="es" else "term_en"])}</strong></a>' for item,klass,label in [(prev,'previous','prev'),(nxt,'following','next')] if item)
    alt_url=SITE+other+'/term/'+quote(t['slug'])+'/'
    url=SITE+lang+'/term/'+quote(t['slug'])+'/'
    structured=json.dumps({'@context':'https://schema.org','@type':'DefinedTerm','name':title,'description':desc,'url':url,'inDefinedTermSet':SITE+lang+'/','alternateName':secondary},ensure_ascii=False).replace('<','\\u003c')
    return head(lang,title+' | AI Development Glossary',desc,url,alt_url)+navbar(lang,t)+f'''<main id="main"><div class="wrap detail-wrap"><nav class="breadcrumbs" aria-label="Breadcrumb"><a href="{index_link(lang)}">{esc(tr['home'])}</a><span aria-hidden="true">/</span><span>{esc(t['category_es'] if lang=='es' else t['category_en'])}</span></nav><div class="detail-grid"><article class="detail-content"><div class="detail-kicker">{esc(t['category_es'] if lang=='es' else t['category_en'])} <span>·</span> {esc(t['id'])}</div><h1>{esc(title)}</h1><div class="translation"><span>{esc(tr['english' if lang=='es' else 'spanish'])}:</span> <strong>{esc(secondary)}</strong></div><section class="detail-section definition"><h2>{esc(tr['definition'])}</h2><p>{esc(desc)}</p></section><section class="detail-section example"><h2>{esc(tr['example'])}</h2><p>{esc(example)}</p></section>{related_html}{source_html}<nav class="pager" aria-label="Term navigation">{controls}</nav></article><aside class="detail-aside"><div class="aside-card"><span class="aside-eyebrow">AI DEVELOPMENT GLOSSARY</span><p>{esc(tr['contributeText'])}</p><button id="copy-link" class="aside-action" type="button">⧉ {esc(tr['copy'])}</button><a class="aside-action" href="{issue_url('correct',t['term_en'])}" target="_blank" rel="noopener noreferrer">↗ {esc(tr['correct'])}</a><a class="aside-action" href="{issue_url('new')}" target="_blank" rel="noopener noreferrer">＋ {esc(tr['suggest'])}</a></div><a href="{index_link(lang)}" class="backlink">← {esc(tr['back'])}</a></aside></div></div></main><script type="application/ld+json">{structured}</script>'''+footer(lang)
def build():
    terms=read_data();byid={t['id']:t for t in terms}
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT/'assets').mkdir()
    for p in (ROOT/'assets').iterdir():
        if p.is_file(): shutil.copy2(p, OUT/'assets'/p.name)
    (OUT/'data').mkdir()
    shutil.copy2(ROOT/'data/glossary.csv',OUT/'data/glossary.csv')
    light=[{k:t[k] for k in ('id','slug','term_en','term_es','definition_en','definition_es','category','category_en','category_es','aliases')} for t in terms]
    (OUT/'data/glossary.json').write_text(json.dumps(light,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    root=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={BASE}en/"><title>AI Development Glossary</title><link rel="canonical" href="{SITE}en/"></head><body><p><a href="{BASE}en/">English</a> · <a href="{BASE}es/">Español</a></p><script>location.replace('{BASE}'+(navigator.language.toLowerCase().startsWith('es')?'es/':'en/'))</script></body></html>'''
    (OUT/'index.html').write_text(root,encoding='utf8')
    (OUT/'.nojekyll').write_text('',encoding='utf8')
    sitemap=[]
    for lang in ('en','es'):
        directory=OUT/lang;directory.mkdir()
        (directory/'index.html').write_text(landing(lang,terms),encoding='utf8')
        sitemap.append(SITE+lang+'/')
        order=sorted(terms,key=lambda x:unicodedata.normalize('NFKD',x['term_es' if lang=='es' else 'term_en']).casefold())
        for idx,term in enumerate(order):
            dirname=directory/'term'/term['slug'];dirname.mkdir(parents=True,exist_ok=True)
            (dirname/'index.html').write_text(detail(lang,term,idx,order,byid),encoding='utf8')
            sitemap.append(SITE+lang+'/term/'+quote(term['slug'])+'/')
    from xml.sax.saxutils import escape as xml_esc
    sitemap_text='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join('<url><loc>'+xml_esc(x)+'</loc></url>\n' for x in sitemap)+'</urlset>'
    (OUT/'sitemap.xml').write_text(sitemap_text,encoding='utf8')
    (OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+SITE+'sitemap.xml\n',encoding='utf8')
    print(f'Built {len(terms)} terms, {len(sitemap)} indexable URLs -> {OUT}')
if __name__ == '__main__':
    try: build()
    except (ValueError,OSError,csv.Error) as e:
        print('Build error:',e,file=sys.stderr);sys.exit(1)
