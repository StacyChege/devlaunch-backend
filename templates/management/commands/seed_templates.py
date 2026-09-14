"""Seed the curated template library (PRD F1).

Idempotent: matches on slug, so running it again refreshes metadata
without creating duplicates.

    python manage.py seed_templates
    python manage.py seed_templates --fresh   # wipe existing templates first

Only Solo Portfolio and Business Landing have real source under
template_sources/ right now (see templates/rendering.py) — they're the
only two that can actually be deployed or previewed. The rest are
metadata-only placeholders for the gallery until more source is added;
source_path is left blank for them rather than pointing at a directory
that doesn't exist.
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from templates.models import Template

TEMPLATES = [
    {
        'name': 'Solo Portfolio',
        'category': Template.PORTFOLIO,
        'tech_stack': 'HTML/CSS',
        'description': 'A clean single-page portfolio for developers and designers, '
                       'with project cards, an about section, and a contact form.',
        'source_path': 'solo-portfolio',
        'is_premium': False,
    },
    {
        'name': 'Studio Portfolio',
        'category': Template.PORTFOLIO,
        'tech_stack': 'Next.js',
        'description': 'A multi-page portfolio with case studies, an image-led work '
                       'grid, and a built-in blog. Great for creative studios.',
        'source_path': '',
        'is_premium': True,
    },
    {
        'name': 'Business Landing',
        'category': Template.BUSINESS,
        'tech_stack': 'HTML/CSS',
        'description': 'A conversion-focused landing page for small businesses: hero, '
                       'services, testimonials, pricing, and a call-to-action.',
        'source_path': 'business-landing',
        'is_premium': False,
    },
    {
        'name': 'Local Services',
        'category': Template.BUSINESS,
        'tech_stack': 'React',
        'description': 'Built for plumbers, salons, and clinics — service list, booking '
                       'enquiry form, opening hours, and a map section.',
        'source_path': '',
        'is_premium': False,
    },
    {
        'name': 'Minimal Blog',
        'category': Template.BLOG,
        'tech_stack': 'Next.js',
        'description': 'A typography-first blog with tag pages, reading time, and an '
                       'RSS feed. Markdown-driven content.',
        'source_path': '',
        'is_premium': False,
    },
    {
        'name': 'SaaS Starter',
        'category': Template.SAAS,
        'tech_stack': 'React',
        'description': 'A SaaS marketing site with feature grid, pricing tiers, FAQ, '
                       'and a newsletter capture. Pairs well with a waitlist.',
        'source_path': '',
        'is_premium': True,
    },
    {
        'name': 'Agency One',
        'category': Template.AGENCY,
        'tech_stack': 'Next.js',
        'description': 'A bold agency site with a services breakdown, team section, '
                       'client logos, and an animated hero.',
        'source_path': '',
        'is_premium': True,
    },
    {
        'name': 'Shop Starter',
        'category': Template.ECOMMERCE,
        'tech_stack': 'React',
        'description': 'A storefront starter with a product grid, product detail page, '
                       'and a cart drawer. Bring your own checkout.',
        'source_path': '',
        'is_premium': False,
    },
    {
        'name': 'Docs Site',
        'category': Template.DOCS,
        'tech_stack': 'HTML/CSS',
        'description': 'A documentation site with a sidebar nav, search, code blocks, '
                       'and a versioned layout. Ideal for open-source projects.',
        'source_path': '',
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
                # Curated templates render their own preview from source
                # (see TemplateSerializer.get_preview_url) — clear the old
                # fabricated demo.devlaunch.app URLs this seed used to set.
                # Admins can still set a real external preview_url later
                # for a template that isn't sourced here yet.
                defaults={**entry, 'is_active': True, 'preview_url': ''},
            )
            created += was_created
            updated += not was_created

        self.stdout.write(
            self.style.SUCCESS(
                f'Templates seeded: {created} created, {updated} updated.'
            )
        )
