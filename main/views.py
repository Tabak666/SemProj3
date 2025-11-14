from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
import requests
from .utils import get_desk_data, pair_user_with_desk, unpair_user
from .models import UserTablePairs, Users
from django.http import JsonResponse

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
    # Count currently approved users
    approved_users_count = Users.objects.filter(approved=True).count()

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
    
    context = {
        'pending_users': pending_users,
        'approved_users_count': approved_users_count
    }
    return render(request, 'approvals.html', context)


def dashboard_view(request):
    return render(request, 'dashboard.html')

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
    return render(request, "partials/desks.html")
    if not request.session.get('user_id'):
        return redirect('login')
    return render(request, 'dashboard.html')

def pair_desk_view(request):
    if request.method == "POST":
        if not request.session.get("user_id"):
            return JsonResponse({"success": False, "message": "Not logged in"})

        user = Users.objects.get(id=request.session["user_id"])
        desk_id = request.POST.get("desk_id")

        if not desk_id:
            return JsonResponse({"success": False, "message": "No desk selected"})

        pair_user_with_desk(user, desk_id)
        return JsonResponse({"success": True, "message": f"Paired with desk {desk_id}"})

def unpair_desk_view(request):
    if request.method == "POST":
        if not request.session.get("user_id"):
            return JsonResponse({"success": False, "message": "Not logged in"})

        user = Users.objects.get(id=request.session["user_id"])
        unpair_user(user)
        return JsonResponse({"success": True, "message": "Unpaired from desk"})


API_URL = "http://localhost:8001/api/v2/E9Y2LxT4g1hQZ7aD8nR3mWx5P0qK6pV7/desks"

def get_desks_api(request):
    if not request.session.get("user_id"):
        return JsonResponse({"success": False, "message": "Not logged in"}, status=401)
    
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        desks_data = response.json()  # your JSON like desk_state.json
    except requests.RequestException:
        return JsonResponse({"success": False, "message": "Failed to fetch desks"}, status=500)
    
    # Load pairing info from DB
    user_pairs = UserTablePairs.objects.filter(end_time__isnull=True).values_list("user_id", "desk_id")
    paired_desks = {desk_id: user_id for user_id, desk_id in user_pairs}

    desk_list = []
    for mac, desk in desks_data.items():
        if mac in ["current_time_s", "simulation_speed"]:
            continue  # skip metadata

        desk_info = desk.get("desk_data", {})
        config = desk_info.get("config", {})
        state = desk_info.get("state", {})

        desk_list.append({
            "id": mac,
            "name": config.get("name"),
            "status": desk.get("user", "available"),  # active/seated/standing
            "position_mm": state.get("position_mm"),
            "speed_mms": state.get("speed_mms"),
            "paired_user": paired_desks.get(mac),  # will be None if free
        })

    return JsonResponse({"success": True, "desks": desk_list})
