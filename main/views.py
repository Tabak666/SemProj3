from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
import requests
from .utils import get_desk_data, pair_user_with_desk, unpair_user
from .models import UserTablePairs, Users, PasswordResetRequest
from django.http import JsonResponse
from core.api_client.calls import loadDesks, get_desk_by_id

from .forms import RegistrationForm, LoginForm, ForgotPasswordForm
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

    # Get both pending users and password reset requests
    pending_users = Users.objects.filter(approved=False)
    pending_password_resets = PasswordResetRequest.objects.filter(processed=False).select_related('user')
    
    # Count currently approved users
    approved_users_count = Users.objects.filter(approved=True).count()

    if request.method == 'POST':
        request_type = request.POST.get('request_type')
        
        # Handle users
        if request_type == 'user':
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
        
        # Handle password resets
        elif request_type == 'password_reset':
            reset_id = request.POST.get('reset_id')
            action = request.POST.get('action')
            try:
                reset_request = PasswordResetRequest.objects.get(id=reset_id)
                user = reset_request.user

                if action == 'approve':
                    # Update user password
                    user.set_password(reset_request.new_password)
                    user.save()
                    
                    # Mark request as processed and approved
                    reset_request.approved = True
                    reset_request.processed = True
                    reset_request.save()
                    
                    messages.success(request, f'Password reset approved for {user.username}.')

                elif action == 'decline':
                    # Mark request as processed but not approved
                    reset_request.processed = True
                    reset_request.save()
                    
                    messages.warning(request, f'Password reset declined for {user.username}.')

            except PasswordResetRequest.DoesNotExist:
                messages.error(request, "Password reset request not found")
        
        return redirect('approvals')
    
    context = {
        'pending_users': pending_users,
        'pending_password_resets': pending_password_resets,
        'approved_users_count': approved_users_count
    }
    return render(request, 'approvals.html', context)

def dashboard_view(request):
    if not request.session.get('user_id'):
        return redirect('index')  # or 'login'
    return render(request, 'dashboard.html')



def dashboard_data(request):
    if not request.session.get("user_id"):
        return JsonResponse({"success": False, "message": "Not logged in"}, status=401)

    user_id = request.session["user_id"]
    pair = UserTablePairs.objects.filter(user_id=user_id, end_time__isnull=True).first()
    desk_id = pair.desk_id if pair else None

    desk_data = None

    if desk_id:
        try:
            # ONE fast API call to get desk state
            desk = get_desk_by_id(desk_id)

            desk_data = {
                "id": desk.mac_address,
                "name": desk.config.name,
                "position_mm": desk.state.position_mm,
                "speed_mms": desk.state.speed_mms,
                "status": desk.user,
            }
        except Exception as e:
            print("Desk fetch error:", e)

    metrics = {
        "sitting_hours": 3.8,
        "standing_hours": 1.9,
        "changes": 14,
        "health_score": 74,
        "last_change_min_ago": 31,
    }

    return JsonResponse({
        "success": True,
        "desk_id": desk_id,
        "desk_data": desk_data,
        "metrics": metrics
    })


def load_view(request, view_name):
    if view_name == "desks":
        return render(request, "partials/desks.html")
    elif view_name == "overview":
        return render(request, "partials/overview.html")
    else:
        return render(request, "partials/desks.html")
def overview(request):
    return render(request, "partials/overview.html")

def desk(request):
    if not request.session.get('user_id'):
        return redirect('login')
    return render(request, "partials/desks.html")


def pair_desk_view(request):
    if request.method != "POST" or not request.session.get("user_id"):
        return JsonResponse({"success": False, "message": "Not logged in"})

    user = Users.objects.get(id=request.session["user_id"])
    desk_id = request.POST.get("desk_id")
    if not desk_id:
        return JsonResponse({"success": False, "message": "No desk selected"})

    # Check if desk is already paired
    if UserTablePairs.objects.filter(desk_id=desk_id, end_time__isnull=True).exists():
        return JsonResponse({"success": False, "message": "Desk already occupied"})

    pair_user_with_desk(user, desk_id)
    return JsonResponse({"success": True, "message": f"Paired with desk {desk_id}"})

def unpair_desk_view(request):
    if request.method == "POST":
        if not request.session.get("user_id"):
            return JsonResponse({"success": False, "message": "Not logged in"})

        user = Users.objects.get(id=request.session["user_id"])
        unpair_user(user)
        return JsonResponse({"success": True, "message": "Unpaired from desk"})

def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            new_password = form.cleaned_data['new_password']
            
            try:
                user = Users.objects.get(username=username)
                
                # Check if there's already a pending request for this user
                existing_request = PasswordResetRequest.objects.filter(
                    user=user, 
                    processed=False
                ).first()
                
                if existing_request:
                    messages.warning(request, 'You already have a pending password reset request.')
                    return redirect('forgot_password')
                
                # Create a new password reset request
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