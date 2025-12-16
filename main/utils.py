from .models import UserTablePairs, Users, DeskBooking
from django.utils import timezone
from django.conf import settings
import json, os
from core.api_client.calls import get_desk_by_id

def get_desk_data(desk_id):
    """
    Get LIVE desk data directly from the simulator API
    """
    try:
        desk = get_desk_by_id(desk_id)
        if not desk:
            return {}

        return {
            "state": {
                "position_mm": desk.state.position_mm,
                "speed_mms": desk.state.speed_mms
            }
        }
    except Exception as e:
        print("[get_desk_data ERROR]", e)
        return {}

# Use absolute path to ensure the file is found regardless of working directory
DATA_FILE = os.path.join(settings.BASE_DIR, "tableAPI", "data", "desks_state.json")

def pair_user_with_desk(user, desk_id):
    UserTablePairs.objects.filter(user_id = user, end_time__isnull=True).update(end_time=timezone.now())#end prevoius pairings

    pair = UserTablePairs.objects.create(user_id = user, desk_id=desk_id)
    return pair

def unpair_user(user):
    UserTablePairs.objects.filter(user_id=user, end_time__isnull=True).update(end_time=timezone.now())


def mark_bookings(desks):
    """
    Add an 'is_booked' flag to each desk based on current bookings.
    """
    now = timezone.now()
    for desk_entry in desks:
        desk_entry["is_booked"] = False
        desk = desk_entry.get("desk")
        if desk and getattr(desk, "mac_address", None):
            active_booking = DeskBooking.objects.filter(
                desk_id=desk.mac_address,
                start_time__lte=now,
                end_time__gte=now
            ).exists()
            if active_booking:
                desk_entry["is_booked"] = True
    return desks
