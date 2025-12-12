from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from ..models import UserTablePairs, Users, DeskBooking
from ..utils import get_desk_by_id

@require_POST
def pair_desk_view(request):
    if request.method != "POST" or not request.session.get("user_id"):
        return JsonResponse({"success": False, "message": "Not logged in"})
    
    user = Users.objects.get(id=request.session["user_id"])
    desk_id = request.POST.get("desk_id")
    if not desk_id:
        return JsonResponse({"success": False, "message": "No desk selected"})

    existing = UserTablePairs.objects.filter(desk_id=desk_id, end_time__isnull=True).first()
    if existing:
        return JsonResponse({"success": False, "message": f"Desk already occupied by {existing.user_id.username}"})

    now = timezone.now()
    booked = DeskBooking.objects.filter(desk_id=desk_id, start_time__lte=now, end_time__gte=now).exclude(user=user).exists()
    if booked:
        return JsonResponse({"success": False, "message": "Desk is booked by another user"})

    UserTablePairs.objects.filter(user_id=user, end_time__isnull=True).update(end_time=now)
    UserTablePairs.objects.create(user_id=user, desk_id=desk_id, start_time=now)
    return JsonResponse({"success": True, "message": f"Paired with desk {desk_id}"})

@require_POST
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

    overlap = DeskBooking.objects.filter(desk_id=desk_id, start_time__lt=end_time, end_time__gt=start_time).exists()
    if overlap:
        return JsonResponse({"success": False, "message": "Desk already booked for this time"})

    user = Users.objects.get(id=user_id)
    DeskBooking.objects.create(user=user, desk_id=desk_id, start_time=start_time, end_time=end_time)
    return JsonResponse({"success": True, "message": f"Desk {desk_id} booked from {start_time} to {end_time}"})

@require_GET
def user_desk_status(request, desk_id):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"is_paired": False})

    is_paired = UserTablePairs.objects.filter(user_id=user_id, desk_id=desk_id, end_time__isnull=True).exists()

    current_height = None
    is_moving = False

    if is_paired:
        try:
            desk = get_desk_by_id(desk_id)
            if desk:
                current_height = int(desk.state.position_mm / 10)
                is_moving = desk.state.speed_mms != 0
        except Exception:
            pass

    return JsonResponse({"is_paired": is_paired, "current_height": current_height, "is_moving": is_moving})
