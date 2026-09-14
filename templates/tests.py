from rest_framework import status
from rest_framework.test import APITestCase

from .models import Template


class TemplateGalleryTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        Template.objects.create(
            name='Solo Portfolio', category=Template.PORTFOLIO,
            tech_stack='React', description='A clean portfolio for developers.',
            is_premium=False,
        )
        Template.objects.create(
            name='SaaS Starter', category=Template.SAAS,
            tech_stack='Next.js', description='Marketing site for a SaaS product.',
            is_premium=True,
        )
        Template.objects.create(
            name='Docs Site', category=Template.DOCS,
            tech_stack='HTML/CSS', description='Documentation with a sidebar nav.',
            is_premium=False,
        )
        Template.objects.create(
            name='Hidden Draft', category=Template.BLOG,
            tech_stack='React', description='Not ready yet.',
            is_active=False,
        )

    def test_list_is_public_and_hides_inactive(self):
        res = self.client.get('/api/templates/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        names = {t['name'] for t in res.data}
        self.assertIn('Solo Portfolio', names)
        self.assertNotIn('Hidden Draft', names)

    def test_filter_by_category(self):
        res = self.client.get('/api/templates/', {'category': 'SAAS'})
        self.assertEqual([t['name'] for t in res.data], ['SaaS Starter'])

    def test_category_all_returns_everything_active(self):
        res = self.client.get('/api/templates/', {'category': 'ALL'})
        self.assertEqual(len(res.data), 3)

    def test_filter_by_tech_stack(self):
        res = self.client.get('/api/templates/', {'tech_stack': 'Next.js'})
        self.assertEqual([t['name'] for t in res.data], ['SaaS Starter'])

    def test_filter_by_pricing_free(self):
        res = self.client.get('/api/templates/', {'pricing': 'free'})
        names = {t['name'] for t in res.data}
        self.assertEqual(names, {'Solo Portfolio', 'Docs Site'})

    def test_filter_by_pricing_premium(self):
        res = self.client.get('/api/templates/', {'pricing': 'premium'})
        self.assertEqual([t['name'] for t in res.data], ['SaaS Starter'])

    def test_search_matches_name_and_description(self):
        res = self.client.get('/api/templates/', {'search': 'sidebar'})
        self.assertEqual([t['name'] for t in res.data], ['Docs Site'])

    def test_combined_filters(self):
        res = self.client.get(
            '/api/templates/', {'tech_stack': 'React', 'pricing': 'free'}
        )
        self.assertEqual([t['name'] for t in res.data], ['Solo Portfolio'])

    def test_detail_by_slug(self):
        res = self.client.get('/api/templates/solo-portfolio/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Solo Portfolio')

    def test_detail_404_for_inactive(self):
        res = self.client.get('/api/templates/hidden-draft/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class TemplatePreviewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.real = Template.objects.create(
            name='Solo Portfolio', category=Template.PORTFOLIO,
            description='A clean portfolio.', source_path='solo-portfolio',
        )
        cls.placeholder = Template.objects.create(
            name='Agency One', category=Template.AGENCY,
            description='Coming soon.', source_path='',
        )

    def test_gallery_marks_deployable_templates(self):
        res = self.client.get('/api/templates/')
        by_name = {t['name']: t for t in res.data}
        self.assertTrue(by_name['Solo Portfolio']['is_deployable'])
        self.assertFalse(by_name['Agency One']['is_deployable'])

    def test_preview_url_only_set_for_deployable_templates(self):
        res = self.client.get('/api/templates/')
        by_name = {t['name']: t for t in res.data}
        self.assertTrue(
            by_name['Solo Portfolio']['preview_url'].endswith(
                '/api/templates/solo-portfolio/preview/'
            )
        )
        self.assertIsNone(by_name['Agency One']['preview_url'])

    def test_preview_renders_real_html(self):
        res = self.client.get('/api/templates/solo-portfolio/preview/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'text/html')
        self.assertIn(b'Solo Portfolio', res.content)

    def test_preview_404_when_no_source(self):
        res = self.client.get('/api/templates/agency-one/preview/')
        self.assertEqual(res.status_code, 404)

    def test_preview_404_for_unknown_slug(self):
        res = self.client.get('/api/templates/does-not-exist/preview/')
        self.assertEqual(res.status_code, 404)

    def test_curated_external_preview_url_is_used_when_no_local_source(self):
        self.placeholder.preview_url = 'https://example.com/agency-demo'
        self.placeholder.save(update_fields=['preview_url'])

        res = self.client.get('/api/templates/')
        by_name = {t['name']: t for t in res.data}
        self.assertEqual(by_name['Agency One']['preview_url'], 'https://example.com/agency-demo')
