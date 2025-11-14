from .models import UserTablePairs, Users
from django.utils import timezone
import json, os

DATA_FILE = os.path.join("data", "desk_state.json")
def get_desk_data(desk_id):
    """Return desk data for a specific desk_id from the JSON file."""
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data.get(desk_id, {}).get("desk_data", {})
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def pair_user_with_desk(user, desk_id):
    UserTablePairs.objects.filter(user_id = user, end_time__isnull=True).update(end_time=timezone.now())#end prevoius pairings

    pair = UserTablePairs.objects.create(user_id = user, desk_id=desk_id)
    return pair

def unpair_user(user):
    UserTablePairs.objects.filter(user_id=user, end_time__isnull=True).update(end_time=timezone.now())
