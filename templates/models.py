from django.db import models
from django.utils.text import slugify
import uuid


class Template(models.Model):
    PORTFOLIO = 'PORTFOLIO'
    BUSINESS = 'BUSINESS'
    BLOG = 'BLOG'
    SAAS = 'SAAS'
    AGENCY = 'AGENCY'
    ECOMMERCE = 'ECOMMERCE'
    DOCS = 'DOCS'

    CATEGORY_CHOICES = [
        (PORTFOLIO, 'Portfolio'),
        (BUSINESS, 'Business'),
        (BLOG, 'Blog'),
        (SAAS, 'SaaS'),
        (AGENCY, 'Agency'),
        (ECOMMERCE, 'E-Commerce'),
        (DOCS, 'Documentation'),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    tech_stack = models.CharField(max_length=100, default='React + Tailwind')
    preview_url = models.URLField(blank=True)
    source_path = models.CharField(max_length=500, blank=True)
    thumbnail = models.ImageField(
        upload_to='templates/thumbnails/',
        blank=True,
        null=True
    )
    is_premium = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name