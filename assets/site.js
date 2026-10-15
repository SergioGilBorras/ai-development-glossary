/* Dependency-free search. Index HTML is server-generated for SEO and fallback. */
(() => {
  const $ = (id) => document.getElementById(id);
  const normal = (s) => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase().replace(/\s+/g, ' ').trim();
  const input = $('search'), category = $('category');
  const copy = $('copy-link');
  if (copy) {
    copy.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(location.href);
        const old = copy.textContent;
        copy.textContent = document.documentElement.lang === 'es' ? '✓ Enlace copiado' : '✓ Link copied';
        setTimeout(() => { copy.textContent = old; }, 1800);
      } catch (_) {
        window.prompt('Copy link / Copiar enlace', location.href);
      }
    });
  }
  if (!input || !category) return;
  const lang = document.documentElement.lang === 'es' ? 'es' : 'en';
  const parts = location.pathname.split('/').filter(Boolean);
  const repoBase = '/' + (parts[0] || 'ai-development-glossary') + '/';
  const termsEls = [...document.querySelectorAll('.term-row')];
  const letterEls = [...document.querySelectorAll('.letter-block')];
  const alphaLinks = [...document.querySelectorAll('.alphabet a')];
  const results = $('result-count'), clearBtn = $('clear'), noResults = $('no-results');
  let index = new Map();
  const urlState = new URLSearchParams(location.search);
  input.value = urlState.get('q') || '';
  category.value = [...category.options].some(o => o.value === urlState.get('category')) ? urlState.get('category') : 'all';
  function apply() {
    const q = normal(input.value), chosen = category.value;
    let count = 0;
    for (const row of termsEls) {
      const id = row.dataset.id;
      const term = index.get(id);
      // Always search both languages, definitions and optional aliases.
      const corpus = term ? term.search : normal(row.textContent);
      const tokens = q.split(' ').filter(Boolean);
      const show = (chosen === 'all' || row.dataset.category === chosen) && tokens.every(token => corpus.includes(token));
      row.hidden = !show;
      if (show) count++;
    }
    for (const letter of letterEls) letter.hidden = !letter.querySelector('.term-row:not([hidden])');
    for (const link of alphaLinks) {
      const target = $(link.getAttribute('href').slice(1));
      if (target) link.setAttribute('aria-disabled', String(target.hidden));
    }
    results.textContent = count + (lang === 'es' ? ' términos' : ' terms');
    noResults.hidden = count !== 0;
    clearBtn.hidden = !(q || chosen !== 'all');
    const url = new URL(location.href);
    if (input.value.trim()) url.searchParams.set('q', input.value.trim()); else url.searchParams.delete('q');
    if (chosen !== 'all') url.searchParams.set('category', chosen); else url.searchParams.delete('category');
    history.replaceState(null, '', url.pathname + url.search + url.hash);
  }
  input.addEventListener('input', apply);
  category.addEventListener('change', apply);
  function reset() { input.value = ''; category.value = 'all'; apply(); input.focus(); }
  clearBtn.addEventListener('click', reset);
  $('reset-empty').addEventListener('click', reset);
  // Fetch generated JSON; source of truth remains data/glossary.csv.
  fetch(repoBase + 'data/glossary.json')
    .then(r => { if (!r.ok) throw new Error('Glossary index unavailable'); return r.json(); })
    .then(data => {
      index = new Map(data.map(t => [t.id, { search: normal([t.term_en, t.term_es, t.definition_en, t.definition_es, ...(t.aliases || [])].join(' ')) }]));
      apply();
    })
    .catch(() => apply()); // Initial HTML remains usable even without JSON.
  apply();
})();
