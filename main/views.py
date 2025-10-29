from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password

from .forms import RegistrationForm, LoginForm
from .models import Users
# Create your views here.
def index(request):
    return render(request, 'index.html')

def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                user = Users.objects.get(username=username)
                if check_password(password, user.password): #comparing password if they match
                    request.session['user_id'] = user.id
                    request.session['username'] = user.username
                    return redirect('index')
                else:
                    messages.error(request, 'Invalid password')
            except Users.DoesNotExist:
                messages.error(request, 'User does not exist')
    
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    request.session.flush()
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})

def dashboard_view(request):
    if not request.session.get('user_id'):
        return redirect('login')
    return render(request, 'dashboard.html')