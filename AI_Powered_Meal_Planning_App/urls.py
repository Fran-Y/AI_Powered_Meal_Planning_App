"""
URL configuration for AI_Powered_Meal_Planning_App project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path
from mealPlanningMain import views

urlpatterns = [
    # path('', views.login),
    path('admin/', admin.site.urls),
    path('', views.landing, name='landing'),
    path('register', views.register, name='register'),
    path('login', views.login_view, name='login'),
    path('profile/', views.profile, name='profile'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('mealplan/', views.mealplan, name='mealplan'),
    path('personalInfo/', views.personalInfo, name='personalInfo'),
    path('recommendation/', views.recommend_food, name='recommendation'),
    path('test/', views.test, name='test'),
    path('about/', views.about, name='about')

]
