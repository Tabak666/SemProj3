from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
import requests
from .utils import get_desk_data, pair_user_with_desk, unpair_user, mark_bookings
from .models import UserTablePairs, Users, PasswordResetRequest, BugReport, DeskBooking
from django.http import JsonResponse
from core.api_client.calls import loadDesks, get_desk_by_id, update_desk_height
from django.core.cache import cache
from .forms import RegistrationForm, LoginForm, ForgotPasswordForm
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from tableAPI.desk_store import load_desks  # ✅ Add this import
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from datetime import timedelta
import time

@require_POST
def submit_bug(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'message': 'Not logged in'}, status=401)
    
    try:
        user = Users.objects.get(id=user_id)
        desk_id = request.POST.get('desk_id')
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority', 'medium')

        if not desk_id or not title or not description:
            return JsonResponse({'success': False, 'message': 'Missing required fields'})

        # Validation: User must be paired with the desk they are reporting
        is_paired = UserTablePairs.objects.filter(
            user_id=user, 
            desk_id=desk_id, 
            end_time__isnull=True
        ).exists()

        if not is_paired:
            return JsonResponse({'success': False, 'message': 'You are not paired with this desk'}, status=403)

        BugReport.objects.create(
            user=user,
            desk_id=desk_id,
            title=title,
            description=description,
            priority=priority
        )
        return JsonResponse({'success': True, 'message': 'Bug report submitted successfully'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def admin_bugs_view(request):
    if not request.session.get('user_id') or request.session.get('role') != 'admin':
        return redirect('index')
    
    bugs = BugReport.objects.select_related('user').all().order_by('-created_at')
    
    context = {
        'bugs': bugs,
        'open_count': bugs.filter(status='open').count(),
        'high_priority_count': bugs.filter(priority='high', status__in=['open', 'in_progress']).count(),
        'resolved_count': bugs.filter(status='resolved').count(),
    }

    return render(request, 'admin_bugs.html', context)

@require_POST
def update_bug_status(request):
    if not request.session.get('user_id') or request.session.get('role') != 'admin':
        return redirect('index')
        
    bug_id = request.POST.get('bug_id')
    status = request.POST.get('status')
    notes = request.POST.get('admin_notes')
    
    try:
        bug = BugReport.objects.get(id=bug_id)
        if status:
            bug.status = status
        if notes is not None:
            bug.admin_notes = notes
        bug.save()
        messages.success(request, f"Bug #{bug.id} updated.")
    except BugReport.DoesNotExist:
        messages.error(request, "Bug report not found.")
        
    return redirect('admin_bugs')
@require_POST
def delete_bug(request):
    if not request.session.get('user_id') or request.session.get('role') != 'admin':
        return redirect('index')
    
    bug_id = request.POST.get('bug_id')
    try:
        bug = BugReport.objects.get(id=bug_id)
        if bug.status in ['resolved', 'closed']:
            bug.delete()
            messages.success(request, f"Bug #{bug_id} deleted successfully.")
        else:
            messages.warning(request, "Only Resolved or Closed bugs can be deleted.")
    except BugReport.DoesNotExist:
        messages.error(request, "Bug report not found.")
        
    return redirect('admin_bugs')

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

    # Mark which desks are booked
    for room in rooms:
        rooms[room] = mark_bookings(rooms[room])

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

    # Prevent pairing if someone else is paired
    existing = UserTablePairs.objects.filter(desk_id=desk_id, end_time__isnull=True).first()
    if existing:
        return JsonResponse({
            "success": False,
            "message": f"Desk already occupied by {existing.user_id.username}"
        })

    # Prevent pairing if someone else has booked it right now
    from django.utils import timezone
    now = timezone.now()
    booked = DeskBooking.objects.filter(
        desk_id=desk_id,
        start_time__lte=now,
        end_time__gte=now
    ).exclude(user=user).exists()
    if booked:
        return JsonResponse({
            "success": False,
            "message": "Desk is booked by another user"
        })

    # Unpair user from any previous desk
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
                current_height = int(desk.state.position_mm)
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


@require_POST
def reset_daily_metrics(request):
    """Reset all today's metrics for the user."""
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({"success": False, "message": "Not logged in"}, status=401)
    
    try:
        user = Users.objects.get(id=user_id)
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Delete all pairings from today
        UserTablePairs.objects.filter(
            user_id=user,
            start_time__gte=today_start
        ).delete()
        
        # Delete all bookings from today
        DeskBooking.objects.filter(
            user=user,
            start_time__gte=today_start
        ).delete()
        
        return JsonResponse({
            "success": True,
            "message": "Today's metrics have been reset"
        })
    except Users.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@require_GET
def health_metrics_api(request):
    """
    Calculate health metrics based on paired desks (UserTablePairs) and booked desks (DeskBooking).
    Detects REAL position changes by tracking desk height over time.
    Every real second = 1 minute for demo/testing.
    Sitting: < 850mm, Standing: >= 850mm
    """
    # Demo time scaling
    REAL_SECONDS_TO_DEMO_MINUTES = 15 / 60  # 1s real = 15s demo

    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({"success": False, "message": "Not logged in"}, status=401)
    
    try:
        user = Users.objects.get(id=user_id)
        now = timezone.now()
        
        # Position threshold
        SITTING_THRESHOLD = 850  # mm - < 850 = sitting, >= 850 = standing
        
        sitting_seconds = 0
        standing_seconds = 0
        position_changes = 0
        last_change_time = None
        
        # ============================================
        # PART 1: Process UserTablePairs (Pair Now)
        # ============================================
        # Include both active (end_time is NULL) and completed pairings from today
        from django.db.models import Q
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        paired_desks = UserTablePairs.objects.filter(
            user_id_id=user_id
        ).filter(
            Q(end_time__isnull=True) | Q(start_time__gte=today_start)
        )
        
        for pair in paired_desks:
            # Check if this is an active pairing or a completed one
            is_active = pair.end_time is None
            
            # Calculate elapsed time
            if is_active:
                # Active pairing: measure from start to now
                elapsed_seconds = (now - pair.start_time).total_seconds()
                reference_time = now
            else:
                # Completed pairing: measure from start to end
                elapsed_seconds = (pair.end_time - pair.start_time).total_seconds()
                reference_time = pair.end_time
            
            # Only fetch and record desk height for ACTIVE pairings
            if is_active:
                # Get current desk height from desk_data
                desk_data = get_desk_data(pair.desk_id)
                # Extract position_mm from state, convert to mm if needed
                position_mm = desk_data.get('state', {}).get('position_mm', 750)
                # position_mm might be in tenths of mm (e.g., 6800 = 680mm), so divide by 10 if too large
                current_height = int(position_mm)
                
                # Record this height sample with timestamp
                if not pair.height_history:
                    pair.height_history = []
                
                # Always record height periodically (baseline required for analytics)
                if not pair.height_history:
                    pair.height_history = []

                last_sample_time = pair.height_history[-1]["time_seconds"] if pair.height_history else None

                # Record a sample at least every 1 second (demo = 1 min)
                if last_sample_time is None or (elapsed_seconds - last_sample_time) >= 1:
                    pair.height_history.append({
                        "time_seconds": elapsed_seconds,
                        "height_mm": current_height
                    })
                    pair.save()

            
            # Analyze height_history for position transitions
            sitting, standing, changes, last_change = analyze_height_history(
                pair.height_history, elapsed_seconds, pair.start_time, SITTING_THRESHOLD
            )
            sitting_seconds += sitting
            standing_seconds += standing
            position_changes += changes
            if last_change and (last_change_time is None or last_change > last_change_time):
                last_change_time = last_change
        
        # ============================================
        # PART 2: Process DeskBooking (Book for Later)
        # ============================================
        # Only include bookings that are ongoing or happening today
        booked_desks = DeskBooking.objects.filter(
            user=user,
            start_time__lte=now,
            end_time__gte=now
        )
        
        for booking in booked_desks:
            # Time elapsed since booking started (or from midnight if booking started before today)
            elapsed_seconds = (now - booking.start_time).total_seconds()
            
            # Get current desk height from desk_data
            desk_data = get_desk_data(booking.desk_id)
            # Extract position_mm from state, convert to mm if needed
            position_mm = desk_data.get('state', {}).get('position_mm', 750)
            # position_mm might be in tenths of mm (e.g., 6800 = 680mm), so divide by 10 if too large
            current_height = int(position_mm)

            
            # Record this height sample with timestamp
            if not booking.height_history:
                booking.height_history = []
            
            # Always record height periodically (baseline required for analytics)
            if not booking.height_history:
                booking.height_history = []

            last_sample_time = booking.height_history[-1]["time_seconds"] if booking.height_history else None

            if last_sample_time is None or (elapsed_seconds - last_sample_time) >= 1:
                booking.height_history.append({
                    "time_seconds": elapsed_seconds,
                    "height_mm": current_height
                })
                booking.save()

            
            # Analyze height_history for position transitions
            sitting, standing, changes, last_change = analyze_height_history(
                booking.height_history, elapsed_seconds, booking.start_time, SITTING_THRESHOLD
            )
            sitting_seconds += sitting
            standing_seconds += standing
            position_changes += changes
            if last_change and (last_change_time is None or last_change > last_change_time):
                last_change_time = last_change
        
        # ============================================
        # Return results
        # ============================================
        if not paired_desks.exists() and not booked_desks.exists():
            return JsonResponse({
                "success": True,
                "sitting_time_minutes": 0,
                "standing_time_minutes": 0,
                "sitting_time_formatted": "0h / 0m",
                "standing_time_formatted": "0h / 0m",
                "sitting_percentage": 0,
                "standing_percentage": 0,
                "position_changes": 0,
                "last_change_minutes_ago": None,
                "health_score": 0,
                "total_work_minutes": 0,
                "changes_per_hour": 0
            })
        
        # Convert to minutes
        sitting_minutes = sitting_seconds * REAL_SECONDS_TO_DEMO_MINUTES
        standing_minutes = standing_seconds * REAL_SECONDS_TO_DEMO_MINUTES
        total_work_minutes = sitting_minutes + standing_minutes
        
        if total_work_minutes > 0:
            sitting_percentage = int((sitting_minutes / total_work_minutes) * 100)
            standing_percentage = int((standing_minutes / total_work_minutes) * 100)
        else:
            sitting_percentage = 0
            standing_percentage = 0
        
        # Calculate health score
        target_sitting = 60
        target_standing = 40
        sitting_diff = abs(sitting_percentage - target_sitting)
        standing_diff = abs(standing_percentage - target_standing)
        balance_score = 100 - ((sitting_diff + standing_diff) / 2)
        
        changes_per_hour = (position_changes / (total_work_minutes / 60)) if total_work_minutes > 0 else 0
        ideal_changes_per_hour = 2
        activity_score = min(100, (changes_per_hour / ideal_changes_per_hour) * 100)
        
        health_score = int((balance_score * 0.6) + (activity_score * 0.4))
        health_score = max(0, min(100, health_score))
        
        # Calculate last change time
        last_change_minutes = None
        if last_change_time:
            last_change_minutes = int((now - last_change_time).total_seconds() / 60)
        
        # Format as hours/minutes
        sitting_hours_int = int(sitting_minutes // 60)
        sitting_mins_remainder = int(sitting_minutes % 60)
        standing_hours_int = int(standing_minutes // 60)
        standing_mins_remainder = int(standing_minutes % 60)
        
        return JsonResponse({
            "success": True,
            "sitting_time_minutes": int(sitting_minutes),
            "standing_time_minutes": int(standing_minutes),
            "sitting_time_formatted": f"{sitting_hours_int}h / {sitting_mins_remainder}m",
            "standing_time_formatted": f"{standing_hours_int}h / {standing_mins_remainder}m",
            "sitting_percentage": sitting_percentage,
            "standing_percentage": standing_percentage,
            "position_changes": position_changes,
            "last_change_minutes_ago": last_change_minutes,
            "health_score": health_score,
            "total_work_minutes": int(total_work_minutes),
            "changes_per_hour": round(changes_per_hour, 2)
        })
    
    except Users.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


def analyze_height_history(height_history, elapsed_seconds, start_time, sitting_threshold):
    """
    Helper function to analyze height history and calculate sitting/standing time and position changes.
    Returns: (sitting_seconds, standing_seconds, position_changes, last_change_time)
    """
    sitting_seconds = 0
    standing_seconds = 0
    position_changes = 0
    last_change_time = None
    
    if not height_history or len(height_history) < 1:
        return sitting_seconds, standing_seconds, position_changes, last_change_time
    
    if len(height_history) < 2:
        # Only one sample, assume that position for all time
        height = height_history[0].get('height_mm', 750)
        if height < sitting_threshold:
            sitting_seconds = elapsed_seconds
        else:
            standing_seconds = elapsed_seconds
        return sitting_seconds, standing_seconds, position_changes, last_change_time
    
    # Sort history by time
    history_sorted = sorted(height_history, key=lambda x: x.get('time_seconds', 0))
    
    # Build position segments
    position_segments = []
    first_height = history_sorted[0].get('height_mm', 750)
    first_position = "sitting" if first_height < sitting_threshold else "standing"
    position_segments.append((0, first_position))
    
    # Detect position changes
    current_position = first_position
    for i in range(1, len(history_sorted)):
        height = history_sorted[i].get('height_mm', 750)
        new_position = "sitting" if height < sitting_threshold else "standing"
        
        if new_position != current_position:
            time_of_change = history_sorted[i].get('time_seconds', 0)
            position_segments.append((time_of_change, new_position))
            position_changes += 1
            last_change_time = start_time + timedelta(seconds=time_of_change)
            current_position = new_position
    
    # Calculate time in each position
    for i in range(len(position_segments)):
        seg_start_seconds = position_segments[i][0]
        seg_position = position_segments[i][1]
        
        if i + 1 < len(position_segments):
            seg_end_seconds = position_segments[i + 1][0]
        else:
            seg_end_seconds = elapsed_seconds
        
        seg_duration_demo_minutes = seg_end_seconds - seg_start_seconds
        
        if seg_position == "sitting":
            sitting_seconds += seg_duration_demo_minutes
        else:
            standing_seconds += seg_duration_demo_minutes
    
    return sitting_seconds, standing_seconds, position_changes, last_change_time


@csrf_exempt
@require_POST
def book_desk_view(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"success": False, "message": "Not logged in"}, status=401)

    desk_id = request.POST.get("desk_id")
    start = request.POST.get("start_time")
    end = request.POST.get("end_time")
    if not desk_id or not start or not end:
        return JsonResponse({"success": False, "message": "Missing parameters"}, status=400)

    try:
        start_time = parse_datetime(start)
        end_time = parse_datetime(end)
        if not start_time or not end_time:
            raise ValueError("Invalid datetime format")
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid datetime format"}, status=400)

    # Check for overlapping bookings
    overlap = DeskBooking.objects.filter(
        desk_id=desk_id,
        start_time__lt=end_time,
        end_time__gt=start_time
    ).exists()
    if overlap:
        return JsonResponse({"success": False, "message": "Desk already booked for this time"})

    user = Users.objects.get(id=user_id)
    DeskBooking.objects.create(user=user, desk_id=desk_id, start_time=start_time, end_time=end_time)
    return JsonResponse({"success": True, "message": f"Desk {desk_id} booked from {start_time} to {end_time}"})
