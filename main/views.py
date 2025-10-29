from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required


def home(request):
    """Main page view"""
    return render(request, 'main/home.html')


def about(request):
    """About us page view"""
    return render(request, 'main/about_us.html')


def education(request):
    """Education and career page view"""
    return render(request, 'main/educ.html')


def materials(request):
    """Materials page view"""
    return render(request, 'main/materials.html')


def login_view(request):
    """Login page view"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Try to find user by email
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('main:home')
            else:
                messages.error(request, 'Неверный пароль')
        except User.DoesNotExist:
            messages.error(request, 'Пользователь с такой почтой не найден')
    
    return render(request, 'main/login.html')

@login_required
def profile_view(request):
    return render(request, 'main/profile.html')