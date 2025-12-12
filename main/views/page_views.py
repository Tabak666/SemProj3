from django.shortcuts import render, redirect
from django.core.cache import cache
from ..models import Users, UserTablePairs
from ..utils import mark_bookings

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
            rooms[room].append({"desk": desk, "number": desk_number if desk else ""})
            if desk:
                desk_number += 1

    for room in rooms:
        rooms[room] = mark_bookings(rooms[room])

    default_room = {'A': rooms['A']}
    user_height = 176 
    active_desk_id = None
    if request.session.get('user_id'):
        try:
            user = Users.objects.get(id=request.session['user_id'])
            user_height = user.height
            active_pair = UserTablePairs.objects.filter(user_id=user, end_time__isnull=True).first()
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
    return render(request, "dashboard.html", {"metrics": metrics, "user_desk": user_desk})
