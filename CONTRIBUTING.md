# Contributing / Cómo colaborar

Thanks for improving the AI Development Glossary. / Gracias por mejorar el glosario.

The easiest way to contribute is through GitHub Issue Forms, available from the website:

- [Propose a new term / Proponer un término](https://github.com/SergioGilBorras/ai-development-glossary/issues/new?template=new-term.yml)
- [Suggest a correction / Sugerir una corrección](https://github.com/SergioGilBorras/ai-development-glossary/issues/new?template=correct-term.yml)

For a Pull Request:

1. Add a row to `data/glossary.csv` with a unique `IA-###` ID, an existing category, names and definitions in both languages, and an optional HTTPS reference.
2. Add optional usage examples (`example_en`, `example_es`), aliases, valid related IDs, or a reference override to `data/enrichments.json` under that ID.
3. Run `python3 -m unittest discover -s tests -v` and `python3 scripts/build.py`.
4. Open a Pull Request with the reason for the addition, sources and any terminology ambiguity.

**Editorial rules:** Cite reliable references when available; explain terms in your own words, avoid reproducing copyrighted definitions, and distinguish legal/jurisdictional meanings where applicable. Write understandable and specific examples. Do not submit proprietary or confidential material. Relations should only point to genuinely relevant existing terms.

**Security:** Do not include credentials, access tokens or sensitive personal data in issues or PRs. Proposed changes are only published after review and merge into `main`.
