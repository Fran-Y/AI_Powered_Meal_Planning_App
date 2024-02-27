from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

from mealPlanningMain.forms import SignUpForm, LoginForm
from django.db import connection
from .models import User
from django.contrib.auth.decorators import login_required



# Create your views here.
def landing(request):
    return render(request, "landing.html")


def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            try:
                user = User.objects.get(username=username)
                if user.password == password:
                    login(request, user)
                    return redirect('profile')
                else:
                    messages.error(request, 'Password is incorrect')
            except User.DoesNotExist:
                messages.error(request, 'Username does not exist')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


@login_required
def profile(request):
    user = request.user
    context = {
        'user': user
    }
    return render(request, 'profile.html', context)


# def logout(request):
#

@login_required
def mealplan(request):
    return render(request, 'meal-plans.html')

def personalInfo(request):
    return render(request, 'personal-info.html')
