"""Seed the curated template library (PRD F1).

Idempotent: matches on slug, so running it again refreshes metadata
without creating duplicates.

    python manage.py seed_templates
    python manage.py seed_templates --fresh   # wipe existing templates first
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from templates.models import Template

TEMPLATES = [
    {
        'name': 'Solo Portfolio',
        'category': Template.PORTFOLIO,
        'tech_stack': 'React',
        'description': 'A clean single-page portfolio for developers and designers, '
                       'with project cards, an about section, and a contact form.',
        'preview_url': 'https://demo.devlaunch.app/solo-portfolio',
        'source_path': 'templates/solo-portfolio',
        'is_premium': False,
    },
    {
        'name': 'Studio Portfolio',
        'category': Template.PORTFOLIO,
        'tech_stack': 'Next.js',
        'description': 'A multi-page portfolio with case studies, an image-led work '
                       'grid, and a built-in blog. Great for creative studios.',
        'preview_url': 'https://demo.devlaunch.app/studio-portfolio',
        'source_path': 'templates/studio-portfolio',
        'is_premium': True,
    },
    {
        'name': 'Business Landing',
        'category': Template.BUSINESS,
        'tech_stack': 'HTML/CSS',
        'description': 'A conversion-focused landing page for small businesses: hero, '
                       'services, testimonials, pricing, and a call-to-action.',
        'preview_url': 'https://demo.devlaunch.app/business-landing',
        'source_path': 'templates/business-landing',
        'is_premium': False,
    },
    {
        'name': 'Local Services',
        'category': Template.BUSINESS,
        'tech_stack': 'React',
        'description': 'Built for plumbers, salons, and clinics — service list, booking '
                       'enquiry form, opening hours, and a map section.',
        'preview_url': 'https://demo.devlaunch.app/local-services',
        'source_path': 'templates/local-services',
        'is_premium': False,
    },
    {
        'name': 'Minimal Blog',
        'category': Template.BLOG,
        'tech_stack': 'Next.js',
        'description': 'A typography-first blog with tag pages, reading time, and an '
                       'RSS feed. Markdown-driven content.',
        'preview_url': 'https://demo.devlaunch.app/minimal-blog',
        'source_path': 'templates/minimal-blog',
        'is_premium': False,
    },
    {
        'name': 'SaaS Starter',
        'category': Template.SAAS,
        'tech_stack': 'React',
        'description': 'A SaaS marketing site with feature grid, pricing tiers, FAQ, '
                       'and a newsletter capture. Pairs well with a waitlist.',
        'preview_url': 'https://demo.devlaunch.app/saas-starter',
        'source_path': 'templates/saas-starter',
        'is_premium': True,
    },
    {
        'name': 'Agency One',
        'category': Template.AGENCY,
        'tech_stack': 'Next.js',
        'description': 'A bold agency site with a services breakdown, team section, '
                       'client logos, and an animated hero.',
        'preview_url': 'https://demo.devlaunch.app/agency-one',
        'source_path': 'templates/agency-one',
        'is_premium': True,
    },
    {
        'name': 'Shop Starter',
        'category': Template.ECOMMERCE,
        'tech_stack': 'React',
        'description': 'A storefront starter with a product grid, product detail page, '
                       'and a cart drawer. Bring your own checkout.',
        'preview_url': 'https://demo.devlaunch.app/shop-starter',
        'source_path': 'templates/shop-starter',
        'is_premium': False,
    },
    {
        'name': 'Docs Site',
        'category': Template.DOCS,
        'tech_stack': 'HTML/CSS',
        'description': 'A documentation site with a sidebar nav, search, code blocks, '
                       'and a versioned layout. Ideal for open-source projects.',
        'preview_url': 'https://demo.devlaunch.app/docs-site',
        'source_path': 'templates/docs-site',
        'is_premium': False,
    },
]


class Command(BaseCommand):
    help = 'Seed the curated template library.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fresh',
            action='store_true',
            help='Delete all existing templates before seeding.',
        )

    def handle(self, *args, **options):
        if options['fresh']:
            deleted, _ = Template.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} existing rows.'))

        created = updated = 0
        for entry in TEMPLATES:
            slug = slugify(entry['name'])
            _, was_created = Template.objects.update_or_create(
                slug=slug,
                defaults={**entry, 'is_active': True},
            )
            created += was_created
            updated += not was_created

        self.stdout.write(
            self.style.SUCCESS(
                f'Templates seeded: {created} created, {updated} updated.'
            )
        )
