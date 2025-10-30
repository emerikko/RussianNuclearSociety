from __future__ import annotations

import uuid
import re
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# Core Abstract Models
class UUIDPrimaryKeyModel(models.Model):
    """Abstract base model that provides a UUID primary key."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("identifier"),
    )

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """Abstract base model with creation and modification timestamps."""
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("created at"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("updated at"),
    )

    class Meta:
        abstract = True
        ordering = ("-created_at",)


class PublishableModel(TimeStampedModel):
    """Adds publication flags and helpers for content models."""
    is_published = models.BooleanField(
        default=False,
        verbose_name=_("is published"),
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("published at"),
    )

    class Meta:
        abstract = True

    def publish(self, commit: bool = True) -> None:
        self.is_published = True
        self.published_at = timezone.now()
        if commit:
            self.save(update_fields=("is_published", "published_at"))

    def unpublish(self, commit: bool = True) -> None:
        self.is_published = False
        self.published_at = None
        if commit:
            self.save(update_fields=("is_published", "published_at"))


class SoftDeletableModel(models.Model):
    """Mixin to support reversible (soft) deletion."""
    is_deleted = models.BooleanField(default=False, verbose_name=_("is deleted"))
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("deleted at"),
    )

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, soft: bool = True):
        if soft:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(update_fields=("is_deleted", "deleted_at"))
        else:
            super().delete(using=using, keep_parents=keep_parents)

    def restore(self, commit: bool = True) -> None:
        self.is_deleted = False
        self.deleted_at = None
        if commit:
            self.save(update_fields=("is_deleted", "deleted_at"))


# User Models (temporarily commented out for initial setup)
# class Role(UUIDPrimaryKeyModel, TimeStampedModel):
#     """Represents a semantic role assigned to users."""
#     class RoleScope(models.TextChoices):
#         GLOBAL = "global", _("Global")
#         CONTENT = "content", _("Content")
#         COMMUNITY = "community", _("Community")
# 
#     name = models.CharField(max_length=150, unique=True, verbose_name=_("name"))
#     slug = models.SlugField(max_length=150, unique=True, verbose_name=_("slug"))
#     description = models.TextField(blank=True, verbose_name=_("description"))
#     scope = models.CharField(
#         max_length=32,
#         choices=RoleScope.choices,
#         default=RoleScope.GLOBAL,
#         verbose_name=_("scope"),
#     )
#     is_default = models.BooleanField(
#         default=False,
#         verbose_name=_("is default"),
#         help_text=_("Automatically assign this role to newly created users."),
#     )
# 
#     class Meta:
#         verbose_name = _("role")
#         verbose_name_plural = _("roles")
#         ordering = ("name",)
# 
#     def __str__(self) -> str:
#         return self.name


# Article Models
class Category(UUIDPrimaryKeyModel, TimeStampedModel):
    """News article categories."""
    name = models.CharField(max_length=100, unique=True, verbose_name=_("name"))
    slug = models.SlugField(max_length=100, unique=True, verbose_name=_("slug"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    color = models.CharField(max_length=7, default="#007bff", verbose_name=_("color"), help_text=_("Hex color code"))
    is_active = models.BooleanField(default=True, verbose_name=_("is active"))

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("main:category_detail", kwargs={"slug": self.slug})


class Tag(UUIDPrimaryKeyModel, TimeStampedModel):
    """Tags for articles."""
    name = models.CharField(max_length=50, unique=True, verbose_name=_("name"))
    slug = models.SlugField(max_length=50, unique=True, verbose_name=_("slug"))

    class Meta:
        verbose_name = _("tag")
        verbose_name_plural = _("tags")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("main:tag_detail", kwargs={"slug": self.slug})


class ArticleQuerySet(models.QuerySet):
    """Custom queryset for articles."""
    
    def published(self):
        """Return only published articles."""
        return self.filter(is_published=True, is_deleted=False)
    
    def drafts(self):
        """Return only draft articles."""
        return self.filter(is_published=False, is_deleted=False)
    
    def by_category(self, category_slug):
        """Filter articles by category slug."""
        return self.filter(category__slug=category_slug, is_deleted=False)
    
    def by_tag(self, tag_slug):
        """Filter articles by tag slug."""
        return self.filter(tags__slug=tag_slug, is_deleted=False)
    
    def by_author(self, author):
        """Filter articles by author."""
        return self.filter(author=author, is_deleted=False)


class ArticleManager(models.Manager):
    """Custom manager for articles."""
    
    def get_queryset(self):
        return ArticleQuerySet(self.model, using=self._db)
    
    def published(self):
        return self.get_queryset().published()
    
    def drafts(self):
        return self.get_queryset().drafts()


class Article(UUIDPrimaryKeyModel, PublishableModel, SoftDeletableModel):
    """News article model."""
    title = models.CharField(max_length=200, verbose_name=_("title"))
    slug = models.SlugField(max_length=200, unique=True, verbose_name=_("slug"))
    excerpt = models.TextField(max_length=500, blank=True, verbose_name=_("excerpt"), 
                              help_text=_("Short description of the article"))
    content = models.TextField(verbose_name=_("content"))
    
    # SEO fields
    meta_description = models.CharField(
        max_length=160, 
        blank=True, 
        verbose_name=_("meta description"),
        help_text=_("SEO meta description (max 160 characters)")
    )
    meta_keywords = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name=_("meta keywords"),
        help_text=_("SEO keywords separated by commas")
    )
    
    # Media
    featured_image = models.ImageField(
        upload_to="articles/images/%Y/%m/",
        blank=True,
        null=True,
        verbose_name=_("featured image")
    )
    featured_image_alt = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("featured image alt text")
    )
    
    # Relationships
    author = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name="articles",
        verbose_name=_("author")
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
        verbose_name=_("category")
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="articles",
        verbose_name=_("tags")
    )
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0, verbose_name=_("view count"))
    
    # Priority and ordering
    is_featured = models.BooleanField(default=False, verbose_name=_("is featured"))
    order = models.IntegerField(default=0, verbose_name=_("order"), help_text=_("Higher numbers appear first"))

    objects = ArticleManager()

    class Meta:
        verbose_name = _("article")
        verbose_name_plural = _("articles")
        ordering = ("-order", "-created_at")
        indexes = [
            models.Index(fields=("is_published", "published_at")),
            models.Index(fields=("category", "is_published")),
            models.Index(fields=("author", "is_published")),
            models.Index(fields=("is_featured", "is_published")),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Auto-generate excerpt from content if not provided
        if not self.excerpt and self.content:
            # Remove HTML tags and limit to 500 characters
            clean_content = re.sub(r'<[^>]+>', '', self.content)
            self.excerpt = clean_content[:500] + "..." if len(clean_content) > 500 else clean_content
        
        # Auto-generate meta description from excerpt if not provided
        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:160]
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("main:article_detail", kwargs={"slug": self.slug})

    def get_edit_url(self):
        return reverse("main:article_edit", kwargs={"slug": self.slug})

    def get_delete_url(self):
        return reverse("main:article_delete", kwargs={"slug": self.slug})

    def increment_view_count(self):
        """Increment the view count for this article."""
        Article.objects.filter(pk=self.pk).update(view_count=models.F('view_count') + 1)

    @property
    def reading_time(self):
        """Estimate reading time in minutes."""
        word_count = len(self.content.split())
        return max(1, word_count // 200)  # Assuming 200 words per minute

    def can_edit(self, user):
        """Check if user can edit this article."""
        if not user.is_authenticated:
            return False
        
        # Author can always edit their own articles
        if self.author == user:
            return True
        
        # Staff members and superusers can edit everything
        return user.is_staff or user.is_superuser

    def can_delete(self, user):
        """Check if user can delete this article."""
        if not user.is_authenticated:
            return False
        
        # Only staff and superusers can delete
        return user.is_staff or user.is_superuser

    def can_publish(self, user):
        """Check if user can publish/unpublish this article."""
        if not user.is_authenticated:
            return False
        
        # Staff and superusers can publish
        return user.is_staff or user.is_superuser
