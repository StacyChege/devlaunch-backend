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
    # Kept <= 255 so MySQL can index it as unique (mysql.W003).
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    customisation_data = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:200] or 'site'
            unique_id = uuid.uuid4().hex[:6]
            self.slug = f"{base}-{unique_id}"
        super().save(*args, **kwargs)

    @property
    def subdomain_url(self):
        """The intended production URL. Only really resolves once wildcard
        DNS for *.devlaunch.app points at the server — see DEPLOY.md."""
        return f"https://{self.slug}.devlaunch.app" if self.slug else None

    @property
    def site_path(self):
        """Relative path that serves the live site today, regardless of
        DNS: the backend resolves it by slug (see projects.views.SiteView)."""
        return f"/sites/{self.slug}/" if self.slug else None

    def __str__(self):
        return self.name


class Deployment(models.Model):
    STATUS_QUEUED = 'QUEUED'
    STATUS_BUILDING = 'BUILDING'
    STATUS_SUCCESS = 'SUCCESS'
    STATUS_FAILED = 'FAILED'
    STATUS_CHOICES = [
        (STATUS_QUEUED, 'Queued'),
        (STATUS_BUILDING, 'Building'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='deployments'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED
    )
    # Rendered output for a SUCCESS deployment — what /sites/<slug>/ serves.
    html = models.TextField(blank=True)
    build_log = models.TextField(blank=True)
    is_rollback = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project.name} — {self.status} ({self.created_at:%Y-%m-%d %H:%M})"


# What every custom domain must CNAME to. Verification checks the domain's
# CNAME chain resolves here; it's also the target shown in DNS instructions.
DNS_CNAME_TARGET = 'devlaunch.app'


class Domain(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_VERIFIED = 'VERIFIED'
    STATUS_FAILED = 'FAILED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_FAILED, 'Failed'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='domains'
    )
    domain_name = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    # What we told the developer to add at their registrar, and the last
    # reason a check didn't pass — shown as-is in the domain settings UI.
    record_type = models.CharField(max_length=10, default='CNAME')
    record_value = models.CharField(max_length=255, default=DNS_CNAME_TARGET)
    last_check_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.domain_name} ({self.status})"