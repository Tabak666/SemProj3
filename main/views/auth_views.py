from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from ..models import Users, PasswordResetRequest
from ..forms import RegistrationForm, LoginForm, ForgotPasswordForm

def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                user = Users.objects.get(username=username)
                if not user.approved:
                    messages.error(request, 'Your account wasn’t approved')
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

def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            new_password = form.cleaned_data['new_password']
            try:
                user = Users.objects.get(username=username)
                existing_request = PasswordResetRequest.objects.filter(user=user, processed=False).first()
                if existing_request:
                    messages.warning(request, 'You already have a pending password reset request.')
                    return redirect('forgot_password')
                hashed_password = make_password(new_password)
                PasswordResetRequest.objects.create(
                    user=user,
                    new_password=hashed_password,
                    approved=False,
                    processed=False
                )
                messages.success(request, 'Password reset request submitted! An admin will review it shortly.')
                return redirect('login')
            except Users.DoesNotExist:
                messages.error(request, 'User does not exist.')
    else:
        form = ForgotPasswordForm()
    return render(request, 'forgot_password.html', {'form': form})
