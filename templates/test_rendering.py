from django.test import SimpleTestCase

from .models import Template
from .rendering import TemplateSourceMissing, has_real_source, render_site


def make_template(**overrides):
    defaults = dict(
        name='Solo Portfolio', category=Template.PORTFOLIO,
        description='x', source_path='solo-portfolio',
    )
    return Template(**{**defaults, **overrides})


class HasRealSourceTests(SimpleTestCase):
    def test_true_for_curated_template(self):
        self.assertTrue(has_real_source(make_template()))

    def test_false_when_source_path_blank(self):
        self.assertFalse(has_real_source(make_template(source_path='')))

    def test_false_when_directory_does_not_exist(self):
        self.assertFalse(has_real_source(make_template(source_path='nope-not-real')))


class RenderSiteTests(SimpleTestCase):
    def test_renders_customisation_into_the_page(self):
        html = render_site(
            make_template(),
            'Jane Doe',
            {
                'tagline': 'Full-stack developer',
                'primary_colour': '#ff0000',
                'meta_description': 'Portfolio of Jane Doe',
            },
        )
        self.assertIn('Jane Doe', html)
        self.assertIn('Full-stack developer', html)
        self.assertIn('#ff0000', html)
        self.assertIn('Portfolio of Jane Doe', html)

    def test_falls_back_to_defaults_when_customisation_is_empty(self):
        html = render_site(make_template(), 'Jane Doe', {})
        self.assertIn('Jane Doe', html)
        self.assertIn('#3B82F6', html)  # default primary colour

    def test_customisation_data_none_is_handled(self):
        html = render_site(make_template(), 'Jane Doe', None)
        self.assertIn('Jane Doe', html)

    def test_escapes_html_in_customisation_values(self):
        html = render_site(
            make_template(), 'Jane Doe',
            {'tagline': '<script>alert(1)</script>'},
        )
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_raises_when_source_is_missing(self):
        with self.assertRaises(TemplateSourceMissing):
            render_site(make_template(source_path=''), 'Jane Doe', {})

    def test_business_landing_also_renders(self):
        html = render_site(
            make_template(name='Business Landing', source_path='business-landing'),
            'Acme Co',
            {'tagline': 'We fix things'},
        )
        self.assertIn('Acme Co', html)
        self.assertIn('We fix things', html)
