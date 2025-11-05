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
                if not user.approved:
                    messages.error(request, 'Your account wasnt approved')
                    return redirect('login')
                
                if check_password(password, user.password):
                    request.session['user_id'] = user.id
                    request.session['username'] = user.username
                    request.session['role'] = user.role
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
            user = form.save(commit=False)
            user.approved = False
            user.save()
            return redirect('login')
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})

def approvals_view(request):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('role') != 'admin':
        return redirect('index')

    pending_users = Users.objects.filter(approved=False)

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        try:
            user = Users.objects.get(id=user_id)

            if action == 'approve':
                user.approved = True
                user.save()
                messages.success(request, f'{user.username} has been approved.')

            elif action == 'decline':
                user.delete()
                messages.warning(request, f'{user.username} has been declined and removed.')

        except Users.DoesNotExist:
            messages.error(request, "User not Found")
        return redirect('approvals')
    
    return render(request, 'approvals.html', {'pending_users': pending_users})


def dashboard_view(request):
    if not request.session.get('user_id'):
        return redirect('login')
    return render(request, 'dashboard.html')