from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db import transaction

from .models import Article, Category, Tag
from .forms import ArticleForm, CategoryForm, TagForm, ArticleSearchForm, ArticlePublishForm



def home_page(request):
    """Home page with news content."""
    # Get featured articles
    featured_articles = Article.objects.published().filter(is_featured=True)[:3]
    
    # Get latest articles
    latest_articles = Article.objects.published()[:6]
    
    # Get categories with article counts
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'featured_articles': featured_articles,
        'latest_articles': latest_articles,
        'categories': categories,
    }
    
    return render(request, 'main/home.html', context)

def educ_page(request):
    return render(request, 'main/educ.html')

def events_page(request):
    return render(request, 'main/events.html')

def materials_page(request):
    return render(request, 'main/materials.html')

def about_us_page(request):
    return render(request, 'main/about_us.html')

def login_page(request):
    # Если пользователь уже авторизован - перенаправляем на профиль
    if request.user.is_authenticated:
        return redirect('main:profile')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('main:profile')  # Редирект на профиль
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('main:home')

@login_required
def profile_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        
        user = request.user
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
        
        messages.success(request, 'Ваш профиль был успешно обновлен!')
        return redirect('main:profile')
    
    return render(request, 'accounts/profile.html')


# Mixins for permission checking
class ContentManagerRequiredMixin(UserPassesTestMixin):
    """Mixin to require content manager permissions."""
    
    def test_func(self):
        return (self.request.user.is_authenticated and 
                (self.request.user.is_superuser or 
                 self.request.user.roles.filter(scope='content').exists()))


class ArticleAuthorOrManagerMixin(UserPassesTestMixin):
    """Mixin to require article author or content manager permissions."""
    
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        
        obj = self.get_object()
        return obj.can_edit(self.request.user)


# Article Views
class ArticleListView(ListView):
    """List view for articles."""
    model = Article
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Article.objects.published().select_related('author', 'category').prefetch_related('tags')
        
        # Handle search
        search_form = ArticleSearchForm(self.request.GET)
        if search_form.is_valid():
            query = search_form.cleaned_data.get('query')
            category = search_form.cleaned_data.get('category')
            tag = search_form.cleaned_data.get('tag')
            
            if query:
                queryset = queryset.filter(
                    Q(title__icontains=query) |
                    Q(excerpt__icontains=query) |
                    Q(content__icontains=query)
                )
            
            if category:
                queryset = queryset.filter(category=category)
                
            if tag:
                queryset = queryset.filter(tags=tag)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ArticleSearchForm(self.request.GET)
        context['categories'] = Category.objects.filter(is_active=True)
        context['featured_articles'] = Article.objects.published().filter(is_featured=True)[:3]
        return context


class ArticleDetailView(DetailView):
    """Detail view for articles."""
    model = Article
    template_name = 'articles/article_detail.html'
    context_object_name = 'article'
    
    def get_queryset(self):
        return Article.objects.published().select_related('author', 'category').prefetch_related('tags')
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Increment view count
        obj.increment_view_count()
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object
        
        # Related articles
        related_articles = Article.objects.published().filter(
            category=article.category
        ).exclude(pk=article.pk)[:3]
        
        context['related_articles'] = related_articles
        context['can_edit'] = article.can_edit(self.request.user)
        return context


class ArticleCreateView(LoginRequiredMixin, CreateView):
    """Create view for articles."""
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Статья успешно создана!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return self.object.get_absolute_url()


class ArticleUpdateView(LoginRequiredMixin, ArticleAuthorOrManagerMixin, UpdateView):
    """Update view for articles."""
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Статья успешно обновлена!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return self.object.get_absolute_url()


class ArticleDeleteView(LoginRequiredMixin, ArticleAuthorOrManagerMixin, DeleteView):
    """Delete view for articles."""
    model = Article
    template_name = 'articles/article_confirm_delete.html'
    success_url = reverse_lazy('main:article_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Soft delete
        self.object.delete(soft=True)
        messages.success(request, 'Статья успешно удалена!')
        return redirect(self.success_url)


@login_required
@require_POST
def article_publish_toggle(request, slug):
    """Toggle article publication status."""
    article = get_object_or_404(Article, slug=slug)
    
    if not article.can_publish(request.user):
        messages.error(request, 'У вас нет прав для публикации статей.')
        return redirect(article.get_absolute_url())
    
    if article.is_published:
        article.unpublish()
        messages.success(request, 'Статья снята с публикации.')
    else:
        article.publish()
        messages.success(request, 'Статья опубликована.')
    
    return redirect(article.get_absolute_url())


# Category Views
class CategoryDetailView(DetailView):
    """Detail view for categories."""
    model = Category
    template_name = 'articles/category_detail.html'
    context_object_name = 'category'
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        articles = Article.objects.published().filter(category=self.object)
        
        paginator = Paginator(articles, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['articles'] = page_obj
        return context


class CategoryListView(ListView):
    """List view for categories."""
    model = Category
    template_name = 'articles/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True)


# Tag Views
class TagDetailView(DetailView):
    """Detail view for tags."""
    model = Tag
    template_name = 'articles/tag_detail.html'
    context_object_name = 'tag'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        articles = Article.objects.published().filter(tags=self.object)
        
        paginator = Paginator(articles, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['articles'] = page_obj
        return context


# Management Views (for content managers)
class ArticleManagementListView(LoginRequiredMixin, ContentManagerRequiredMixin, ListView):
    """Management list view for articles."""
    model = Article
    template_name = 'articles/article_management.html'
    context_object_name = 'articles'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Article.objects.select_related('author', 'category').prefetch_related('tags')
        
        # Filter by status
        status = self.request.GET.get('status', 'all')
        if status == 'published':
            queryset = queryset.filter(is_published=True, is_deleted=False)
        elif status == 'draft':
            queryset = queryset.filter(is_published=False, is_deleted=False)
        elif status == 'deleted':
            queryset = queryset.filter(is_deleted=True)
        else:  # all
            queryset = queryset.filter(is_deleted=False)
        
        # Search
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(author__username__icontains=query)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', 'all')
        context['search_query'] = self.request.GET.get('q', '')
        return context


@login_required
def article_management_dashboard(request):
    """Dashboard for article management."""
    if not (request.user.is_superuser or request.user.roles.filter(scope='content').exists()):
        messages.error(request, 'У вас нет прав доступа к панели управления.')
        return redirect('main:home')
    
    # Statistics
    total_articles = Article.objects.filter(is_deleted=False).count()
    published_articles = Article.objects.filter(is_published=True, is_deleted=False).count()
    draft_articles = Article.objects.filter(is_published=False, is_deleted=False).count()
    
    # Recent articles
    recent_articles = Article.objects.filter(is_deleted=False).order_by('-created_at')[:5]
    
    context = {
        'total_articles': total_articles,
        'published_articles': published_articles,
        'draft_articles': draft_articles,
        'recent_articles': recent_articles,
    }
    
    return render(request, 'articles/management_dashboard.html', context)
