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
