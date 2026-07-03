from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from devlaunch_backend import settings
from django.utils.text import slugify
import uuid


class UserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None):
        user = self.create_user(email, full_name, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    DEVELOPER = 'DEVELOPER'
    ADMIN = 'ADMIN'
    ROLE_CHOICES = [
        (DEVELOPER, 'Developer'),
        (ADMIN, 'Admin'),
    ]

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=DEVELOPER)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.email

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
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects')
    
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

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
        (ECOMMERCE, 'E-commerce'),
        (DOCS, 'Documentation')
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