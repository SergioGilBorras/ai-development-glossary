# AI Development Glossary · Glosario de desarrollo con IA

**An open bilingual (EN/ES) technical glossary for AI developers, engineers, legal teams and documentation specialists.**

**Un glosario técnico abierto y bilingüe (EN/ES) de desarrollo con IA, agentes, ingeniería, documentación y legaltech.**

**[🌐 Open the glossary / Abrir el glosario](https://SergioGilBorras.github.io/ai-development-glossary/)** · [English](https://SergioGilBorras.github.io/ai-development-glossary/en/) · [Español](https://SergioGilBorras.github.io/ai-development-glossary/es/)

## Features / Funcionalidades

- 542 initial terms across 15 categories. **English is the canonical term in both language versions**. Both indexes are alphabetized by English name, and the Spanish page displays the Spanish equivalent beneath each English title.
- Search in **both languages** at once, across term names, definitions and aliases; search also works without accents.
- Category dropdown filters the search; clear filters and A–Z navigation.
- Individual, shareable, indexable detail pages in `/en/term/<slug>/` and `/es/term/<slug>/`.
- Definitions and usage examples in both languages; optional **related-term links** and **external sources** are shown only when present.
- Propose new terms or corrections with **GitHub Issue Forms**. A contributor needs a GitHub account; submissions never edit the glossary automatically.
- Fully static GitHub Pages deployment with GitHub Actions, built with standard Python and vanilla JavaScript. No backend, API keys or node_modules needed.
- Downloadable [CSV](https://SergioGilBorras.github.io/ai-development-glossary/data/glossary.csv) and [JSON](https://SergioGilBorras.github.io/ai-development-glossary/data/glossary.json).

## Publishing / Publicación

In the GitHub repository, go to **Settings → Pages → Build and deployment → Source → GitHub Actions**. The workflow in `.github/workflows/pages.yml` runs on pushes to `main` and can also be started manually from Actions. Pull requests run validation and a build, but do **not** publish.

## Data and how to add a term / Datos y nuevos términos

**Source of truth:** [`data/glossary.csv`](data/glossary.csv). One row = one term. The required fields are:

`ID`, `Categoría`, `Term (EN)`, `Término (ES)`, `Meaning (EN)`, `Significado (ES)`.

`Referencia (URL)` is optional. Use a **unique ID** (`IA-543`, etc.), and an existing Spanish category spelled exactly as in the CSV. English term names are the canonical display names in **both** languages and must be unique, since they determine stable URL slugs and alphabetical order. Keep descriptions concise, technically accurate and original. A Spanish equivalent is required in the published CSV even if a GitHub suggestion comes in one language; maintainers can complete it.

**Optional enrichment:** [`data/enrichments.json`](data/enrichments.json), indexed by the same stable ID:

```json
{
  "IA-011": {
    "example_en": "The support agent transfers a billing case to another agent.",
    "example_es": "El agente de soporte transfiere una consulta al agente de facturación.",
    "related_ids": ["IA-012", "IA-013"],
    "aliases": ["agent handover"],
    "source_url": "https://example.org/reference"
  }
}
```

The `related_ids` must point to **existing IDs**. Empty `related_ids` or `source_url` values do not create empty headings or links. When an example has not yet been curated, the build uses a transparent category-based contextual example; individual examples can be improved through corrections.

## Local development / Desarrollo local

Python 3.10+ recommended; no dependencies.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 -m http.server 8000 --directory _site
```

For exact GitHub Pages paths during local preview, you can either serve `_site` at `/ai-development-glossary/` or change `BASE` in `scripts/build.py` temporarily. The generated site itself expects its project subdirectory URL.

Generated output is `_site/` (ignored by Git). The GitHub Actions deployment builds this folder from the CSV and enrichment metadata.

## Contributing / Colabora

- [📘 Propose a new term / Proponer un término](https://github.com/SergioGilBorras/ai-development-glossary/issues/new?template=new-term.yml)
- [✏️ Correct an existing term / Corregir una definición](https://github.com/SergioGilBorras/ai-development-glossary/issues/new?template=correct-term.yml)
- For data modifications, open a Pull Request. See [CONTRIBUTING.md](CONTRIBUTING.md).

All proposals are reviewed by a maintainer. Issues are public: don't include confidential client data, secrets or personal information.

## Editorial notes / Criterios editoriales

The initial 542 entries have been checked automatically for required bilingual fields, duplicate English names and IDs, link structure and safe external URL schemes. A targeted editorial pass revised 46 bilingual definitions and contributed 47 specifically written bilingual usage examples (90 curated examples in total). Remaining entries retain category-context examples pending a deeper editorial review. Selected references, aliases and related-term links were updated. The 542 entries have **not** all been individually verified against primary technical or legal sources. **Do not treat the glossary as a legal opinion, engineering sign-off or authoritative source of regulatory requirements.** Follow source links and verify professional use against applicable norms and jurisdiction.

## Licensing / Licencias

Repository software is licensed under [MIT](LICENSE). Glossary prose is provided under [CC BY 4.0](LICENSE-CONTENT.md) where the repository maintainers hold the necessary rights. External sources remain under their respective owners' terms.
