from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages



def home_page(request):
    return render(request, 'main/home.html')

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
        return redirect('profile')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('profile')  # Редирект на профиль
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')

@login_required
def info_manager(request):
    return render(request, 'accounts/info_manager.html')