from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Article, Category, Tag
# Temporarily comment out complex models for initial migration
# from .models import Role, UserRole, User


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'colored_badge', 'article_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def colored_badge(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            obj.color,
            obj.name
        )
    colored_badge.short_description = 'Цвет'
    
    def article_count(self, obj):
        count = obj.articles.filter(is_deleted=False).count()
        if count > 0:
            url = reverse('admin:main_article_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}">{} статей</a>', url, count)
        return '0 статей'
    article_count.short_description = 'Статей'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'article_count', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def article_count(self, obj):
        count = obj.articles.filter(is_deleted=False).count()
        if count > 0:
            url = reverse('admin:main_article_changelist') + f'?tags__id__exact={obj.id}'
            return format_html('<a href="{}">{} статей</a>', url, count)
        return '0 статей'
    article_count.short_description = 'Статей'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'is_featured', 'view_count', 'created_at')
    list_filter = ('is_published', 'is_featured', 'is_deleted', 'category', 'created_at', 'author')
    search_fields = ('title', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('id', 'view_count', 'created_at', 'updated_at', 'published_at')
    filter_horizontal = ('tags',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'author', 'category')
        }),
        ('Содержание', {
            'fields': ('excerpt', 'content', 'tags')
        }),
        ('Медиа', {
            'fields': ('featured_image', 'featured_image_alt')
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords')
        }),
        ('Публикация', {
            'fields': ('is_published', 'is_featured', 'order')
        }),
        ('Системная информация', {
            'fields': ('id', 'view_count', 'created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        })
    )
    
    def status(self, obj):
        if obj.is_deleted:
            return format_html('<span style="color: red;">Удалена</span>')
        elif obj.is_published:
            return format_html('<span style="color: green;">Опубликована</span>')
        else:
            return format_html('<span style="color: orange;">Черновик</span>')
    status.short_description = 'Статус'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'category').prefetch_related('tags')


# Temporarily comment out User admin for initial migration
# @admin.register(User)
# class UserAdmin(admin.ModelAdmin):
#     list_display = ('username', 'email', 'display_name', 'is_active', 'is_staff', 'date_joined')
#     list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
#     search_fields = ('username', 'email', 'first_name', 'last_name', 'display_name')
#     readonly_fields = ('id', 'date_joined', 'last_login')
#     filter_horizontal = ('roles',)
#     
#     fieldsets = (
#         ('Основная информация', {
#             'fields': ('username', 'email', 'display_name')
#         }),
#         ('Личные данные', {
#             'fields': ('first_name', 'last_name', 'bio', 'avatar')
#         }),
#         ('Права доступа', {
#             'fields': ('is_active', 'is_staff', 'is_superuser', 'roles')
#         }),
#         ('Системная информация', {
#             'fields': ('id', 'date_joined', 'last_login'),
#             'classes': ('collapse',)
#         })
#     )


# Temporarily comment out Role and UserRole admin
# @admin.register(Role)
# class RoleAdmin(admin.ModelAdmin):
#     list_display = ('name', 'scope', 'is_default', 'user_count', 'created_at')
#     list_filter = ('scope', 'is_default', 'created_at')
#     search_fields = ('name', 'description')
#     prepopulated_fields = {'slug': ('name',)}
#     readonly_fields = ('id', 'created_at', 'updated_at')
#     
#     def user_count(self, obj):
#         count = obj.users.count()
#         if count > 0:
#             url = reverse('admin:main_user_changelist') + f'?roles__id__exact={obj.id}'
#             return format_html('<a href="{}">{} пользователей</a>', url, count)
#         return '0 пользователей'
#     user_count.short_description = 'Пользователей'


# @admin.register(UserRole)
# class UserRoleAdmin(admin.ModelAdmin):
#     list_display = ('user', 'role', 'assigned_by', 'created_at')
#     list_filter = ('role', 'created_at')
#     search_fields = ('user__username', 'role__name')
#     readonly_fields = ('id', 'created_at', 'updated_at')
