from django.db import models
from django.conf import settings
from django.utils.text import slugify
import uuid


class Project(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_DEPLOYED = 'DEPLOYED'
    STATUS_FAILED = 'FAILED'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_DEPLOYED, 'Deployed'),
        (STATUS_FAILED, 'Failed'),
    ]

    developer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    template = models.ForeignKey(
        'templates.Template',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects'
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, max_length=300)
    customisation_data = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    customisation_data = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            unique_id = uuid.uuid4().hex[:6]
            self.slug = f"{base}-{unique_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name