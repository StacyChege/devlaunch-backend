"""Renders a Template's static source with a site's customisation data.

No build step, no per-project containers: a template is real HTML/CSS
under template_sources/<source_path>/index.html using Django template
syntax for the handful of variables the customisation panel exposes.
This is what F3 (Deployment) actually "builds" — see projects.deploy —
and what the gallery preview (TemplatePreviewView) renders with demo data.

Deliberately takes plain values rather than a Project instance so the
templates app never has to import the projects app.
"""
import os

from django.conf import settings
from django.template import engines

SOURCE_ROOT = os.path.join(settings.BASE_DIR, 'template_sources')


class TemplateSourceMissing(Exception):
    """Raised when a Template has no renderable source on disk yet."""


def _index_path(template):
    if not template.source_path:
        return None
    return os.path.join(SOURCE_ROOT, template.source_path, 'index.html')


def has_real_source(template):
    """Whether this template can actually be deployed / previewed right now."""
    path = _index_path(template)
    return bool(path and os.path.isfile(path))


def render_site(template, site_name, customisation_data=None):
    """Render `template`'s source for a site named `site_name`.

    `customisation_data` mirrors Project.customisation_data: tagline,
    primary_colour, secondary_colour, logo_url, meta_title,
    meta_description — all optional. Returns the rendered HTML string.
    Raises TemplateSourceMissing if the template has no curated source.
    """
    path = _index_path(template)
    if not path or not os.path.isfile(path):
        raise TemplateSourceMissing(
            f'No source found for template "{template.slug}". '
            f'Add template_sources/{template.source_path or "<source_path>"}/index.html.'
        )

    with open(path, encoding='utf-8') as f:
        raw = f.read()

    custom = customisation_data or {}
    context = {
        'site_name': site_name,
        'tagline': custom.get('tagline', ''),
        'primary_colour': custom.get('primary_colour') or '#3B82F6',
        'secondary_colour': custom.get('secondary_colour') or '#1E3A5F',
        'logo_url': custom.get('logo_url', ''),
        'meta_title': custom.get('meta_title') or site_name,
        'meta_description': custom.get('meta_description', ''),
    }

    compiled = engines['django'].from_string(raw)
    return compiled.render(context)
