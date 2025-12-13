from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
import requests
from .utils import get_desk_data, pair_user_with_desk, unpair_user
from .models import UserTablePairs, Users, PasswordResetRequest
from django.http import JsonResponse
from core.api_client.calls import loadDesks, get_desk_by_id, update_desk_height
from django.core.cache import cache
from .forms import RegistrationForm, LoginForm, ForgotPasswordForm
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from tableAPI.desk_store import load_desks  # ✅ Add this import


def index(request):
    desks_api = cache.get("latest_desk_data") or []
    room_names = ["A", "B", "C", "D"]
    desks_per_room = 12
    rooms = {name: [] for name in room_names}

    desk_iter = iter(desks_api)
    desk_number = 1

    for room in room_names:
        for i in range(desks_per_room):
            try:
                desk = next(desk_iter)
            except StopIteration:
                desk = None
            rooms[room].append({
                "desk": desk,
                "number": desk_number if desk else ""
            })
            if desk:
                desk_number += 1

    default_room = {'A': rooms['A']}
    user_height = 176 
    active_desk_id = None
    
    if request.session.get('user_id'):
        try:
            user = Users.objects.get(id=request.session['user_id'])
            user_height = user.height
            active_pair = UserTablePairs.objects.filter(
                user_id=user, 
                end_time__isnull=True
            ).first()
            if active_pair:
                active_desk_id = active_pair.desk_id
        except Users.DoesNotExist:
            pass

    rec_sit = round(user_height / 2.48)
    rec_stand = round(user_height / 1.58)

    return render(request, "index.html", {
        "rooms": default_room,
        "highlight": "Room A",
        "user_height": user_height,
        "rec_sit": rec_sit,
        "rec_stand": rec_stand,
        "active_desk_id": active_desk_id
    })


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
    pending_password_resets = PasswordResetRequest.objects.filter(processed=False).select_related('user')
    approved_users_count = Users.objects.filter(approved=True).count()

    if request.method == 'POST':
        request_type = request.POST.get('request_type')
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
        elif request_type == 'password_reset':
            reset_id = request.POST.get('reset_id')
            action = request.POST.get('action')
            try:
                reset_request = PasswordResetRequest.objects.get(id=reset_id)
                user = reset_request.user
                if action == 'approve':
                    user.set_password(reset_request.new_password)
                    user.save()
                    reset_request.approved = True
                    reset_request.processed = True
                    reset_request.save()
                    messages.success(request, f'Password reset approved for {user.username}.')
                elif action == 'decline':
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

def admin_force_unpair(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"})
    if request.session.get("role") != "admin":
        return JsonResponse({"success": False, "message": "Not authorized"})
    desk_id = request.POST.get("desk_id")
    if not desk_id:
        return JsonResponse({"success": False, "message": "No desk selected"})
    UserTablePairs.objects.filter(desk_id=desk_id, end_time__isnull=True).update(end_time=timezone.now())
    return JsonResponse({"success": True, "message": f"Desk {desk_id} unpaired"})

def dashboard_view(request):
    if not request.session.get('user_id'):
        return redirect('login')
    user = Users.objects.get(id=request.session['user_id'])
    user_desk = UserTablePairs.objects.filter(user_id=user, end_time__isnull=True).first()
    metrics = {
        "desk_id": user_desk.desk_id if user_desk else "N/A",
        "sitting_hours": 3.8, 
        "standing_hours": 1.9,
        "changes": 14,
        "last_change_min_ago": 31,
        "health_score": 74
    }
    return render(request, "dashboard.html", {
        "metrics": metrics,
        "user_desk": user_desk,
    })

def load_view(request, view_name):
    # ✅ Load desks directly from JSON file, not from cache
    desks_api = load_desks()  # This returns a list of dictionaries
    room_filter = request.GET.get("room")  # e.g. "Room A"
    
    # Extract room letter from "Room A" format
    room_letter = None
    if room_filter:
        room_letter = room_filter.replace("Room ", "").strip()  # Extract "A" from "Room A"
        print(f"[load_view] Filtering desks for room: {room_letter}")
    
    room_names = ["A", "B", "C", "D"]
    desks_per_room = 12
    rooms = {name: [] for name in room_names}
    
    # Build rooms dictionary with desks filtered by room
    for desk in desks_api:
        desk_room = desk.get("room", "A")  # Default to "A" if no room specified
        if desk_room in rooms:
            rooms[desk_room].append({
                "desk": desk,
                "number": len(rooms[desk_room]) + 1
            })
    
    # If a specific room is requested, only show that room
    if room_letter and room_letter in rooms:
        filtered_rooms = {room_letter: rooms[room_letter]}
        print(f"[load_view] Returning only room {room_letter} with {len(rooms[room_letter])} desks")
    else:
        filtered_rooms = rooms
    
    context = {
        "rooms": filtered_rooms,
        "highlight": room_filter or "Room A"
    }
    
    if view_name == "desks":
        return render(request, "partials/desks.html", context)
    elif view_name == "overview":
        return render(request, "partials/overview.html", context)
    return render(request, "partials/overview.html", context)

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
    existing = UserTablePairs.objects.filter(desk_id=desk_id, end_time__isnull=True).first()
    if existing:
        return JsonResponse({
            "success": False,
            "message": f"Desk already occupied by {existing.user_id.username}"
        })
    UserTablePairs.objects.filter(user_id=user, end_time__isnull=True).update(end_time=timezone.now())
    UserTablePairs.objects.create(user_id=user, desk_id=desk_id, start_time=timezone.now())
    return JsonResponse({"success": True, "message": f"Paired with desk {desk_id}"})

def unpair_desk_view(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"})
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"success": False, "message": "Not logged in"})
    user = Users.objects.get(id=user_id)
    pairing = UserTablePairs.objects.filter(user_id=user, end_time__isnull=True).first()
    if not pairing:
        return JsonResponse({"success": False, "message": "No active desk to unpair"})
    pairing.end_time = timezone.now()
    pairing.save()
    return JsonResponse({"success": True, "message": "Unpaired from desk"})

def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            new_password = form.cleaned_data['new_password']
            try:
                user = Users.objects.get(username=username)
                existing_request = PasswordResetRequest.objects.filter(
                    user=user, 
                    processed=False
                ).first()
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

@require_GET
def user_desk_status(request, desk_id):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"is_paired": False})

    is_paired = UserTablePairs.objects.filter(
        user_id=user_id, 
        desk_id=desk_id, 
        end_time__isnull=True
    ).exists()

    current_height = None
    is_moving = False

    if is_paired:
        try:
            # Fetch real-time data to check height AND movement status
            desk = get_desk_by_id(desk_id)
            if desk:
                current_height = int(desk.state.position_mm / 10)
                is_moving = desk.state.speed_mms != 0 # Check if speed is not 0
        except Exception:
            pass

    return JsonResponse({
        "is_paired": is_paired,
        "current_height": current_height,
        "is_moving": is_moving # Return status to frontend
    })

@require_GET
def desks_status_api(request):
    active_pairs = UserTablePairs.objects.filter(end_time__isnull=True)
    data = {p.desk_id: {"user": p.user_id.username} for p in active_pairs}
    return JsonResponse(data)

@require_POST
def set_desk_height(request):
    if not request.session.get('user_id'):
        return JsonResponse({"success": False, "message": "Not logged in"}, status=401)
    user_id = request.session['user_id']
    desk_id = request.POST.get('desk_id')
    height = request.POST.get('height')
    if not desk_id or not height:
        return JsonResponse({"success": False, "message": "Missing parameters"}, status=400)
    is_paired = UserTablePairs.objects.filter(
        user_id=user_id, 
        desk_id=desk_id, 
        end_time__isnull=True
    ).exists()
    if not is_paired:
        return JsonResponse({"success": False, "message": "You are not paired with this desk"}, status=403)
    try:
        update_desk_height(desk_id, int(height))
        return JsonResponse({"success": True, "message": f"Height set to {height}cm"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)