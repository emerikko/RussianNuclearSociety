from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
<<<<<<< HEAD
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('education/', views.education, name='education'),
    path('materials/', views.materials, name='materials'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
=======

    path('', views.home_page, name='home'),
    path('educ.html', views.educ_page, name='educ'),
    path('events.html', views.events_page, name='events'),
    path('materials.html', views.materials_page, name='materials'),
    path('about_us.html', views.about_us_page, name='about_us'),
    path('login.html', views.login_page, name='login'),
    path('profile', views.profile_view, name="profile"),

>>>>>>> 624e864 (Registration system is done)
]
