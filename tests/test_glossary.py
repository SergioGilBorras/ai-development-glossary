import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('glossary_builder',ROOT/'scripts/build.py')
b=importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

class GlossaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.terms=b.read_data()
    def test_terms_are_complete_and_unique(self):
        self.assertGreaterEqual(len(self.terms),500)
        self.assertEqual(len(self.terms),len({t['id'] for t in self.terms}))
        self.assertEqual(len(self.terms),len({t['slug'] for t in self.terms}))
        for t in self.terms:
            for key in ('term_en','term_es','definition_en','definition_es','example_en','example_es'):
                self.assertTrue(t[key],msg=(t['id'],key))
    def test_related_links_resolve_and_are_optional(self):
        ids={t['id'] for t in self.terms}
        for t in self.terms:
            self.assertTrue(set(t['related_ids']) <= ids)
            self.assertNotIn(t['id'],t['related_ids'])
    def test_urls_are_safe(self):
        for t in self.terms:
            self.assertTrue(t['source_url']=='' or t['source_url'].startswith('https://'))
    def test_detail_only_shows_optional_fields_when_present(self):
        sample=next(t for t in self.terms if t['term_en']=='Handoff')
        page=b.detail('es',sample,0,[sample],{t['id']:t for t in self.terms})
        self.assertIn('Ejemplo de uso',page)
        self.assertIn('Relacionado con',page)
        self.assertIn('Fuente externa',page)
        plain=next(t for t in self.terms if not t['source_url'] and not t['related_ids'])
        page2=b.detail('en',plain,0,[plain],{plain['id']:plain})
        self.assertNotIn('Related terms</h2>',page2)
        self.assertNotIn('External source',page2)
    def test_english_term_is_primary_in_both_languages(self):
        # Listings and detail headings always use the English canonical name.
        handoff=next(t for t in self.terms if t['term_en']=='Handoff')
        for lang in ('en','es'):
            listing=b.entry_list(lang,[handoff])
            self.assertIn('class="term-name"',listing)
            self.assertIn('>Handoff <span',listing)
            self.assertNotIn('>Traspaso de control o contexto <span',listing)
            if lang=='es':
                self.assertIn('lang="es">Traspaso de control o contexto',listing)
            else:
                self.assertNotIn('class="term-translation"',listing)
            page=b.detail(lang,handoff,0,[handoff],{t['id']:t for t in self.terms})
            self.assertIn('<h1>Handoff</h1>',page)
            self.assertNotIn('<h1>Traspaso de control o contexto</h1>',page)
            self.assertIn('"name": "Handoff"',page)
            if lang=='es': self.assertIn('Término en español',page)
            else: self.assertNotIn('class="translation"',page)

    def test_alphabetical_order_is_english_in_spanish_too(self):
        # Spanish alphabetization previously placed a translated term under its ES initial.
        first=next(t for t in self.terms if t['term_en']=='AI (Artificial Intelligence)')
        handoff=next(t for t in self.terms if t['term_en']=='Handoff')
        for lang in ('en','es'):
            page=b.entry_list(lang,[handoff,first])
            self.assertLess(page.index('>AI (Artificial Intelligence) <span'),page.index('>Handoff <span'))
            self.assertIn('id="letter-A"',page)
            self.assertIn('id="letter-H"',page)

    def test_related_names_are_english_even_in_spanish(self):
        handoff=next(t for t in self.terms if t['term_en']=='Handoff')
        page=b.detail('es',handoff,0,[handoff],{t['id']:t for t in self.terms})
        self.assertIn('>Agent handoff <span',page)
        self.assertNotIn('>Traspaso entre agentes <span',page)

    def test_generated_index_and_json(self):
        b.build()
        for path in ('en/index.html','es/index.html','es/term/handoff/index.html','en/term/handoff/index.html','data/glossary.json','sitemap.xml'):
            self.assertTrue((b.OUT/path).exists(),path)
        contents=json.loads((b.OUT/'data/glossary.json').read_text(encoding='utf-8'))
        self.assertEqual(len(contents),len(self.terms))
        self.assertEqual((b.OUT/'sitemap.xml').read_text().count('<url>'),2*(len(self.terms)+1))

if __name__=='__main__': unittest.main()
