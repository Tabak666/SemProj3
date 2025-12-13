from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

from .desk_store import load_desks, add_desk, remove_desk

@require_http_methods(["GET"])
def desks_list(request):
    """Return desks from JSON file as a list. Public endpoint."""
    try:
        desks = load_desks()
        return JsonResponse(desks, safe=False)
    except Exception as e:
        print(f"[desks_list] Error: {e}")
        return JsonResponse([], safe=False)

@require_http_methods(["POST"])
def desks_create(request):
    """Add a desk. Accepts JSON body {'name':..., 'floor':..., 'room':..., 'mac':...}"""
    print(f"[desks_create] POST request - User authenticated: {request.user.is_authenticated}")
    
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception as e:
        print(f"[desks_create] JSON decode error: {e}")
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    name = payload.get("name", "").strip()
    if not name:
        return JsonResponse({"error": "Name is required"}, status=400)
    
    extra = {}
    if payload.get("floor"):
        extra["floor"] = payload.get("floor").strip()
    if payload.get("room"):
        extra["room"] = payload.get("room").strip()
    if payload.get("mac"):
        extra["mac"] = payload.get("mac").strip()
    
    try:
        new_desk = add_desk(name=name, extra=extra)
        print(f"[desks_create] Successfully added desk: {new_desk}")
        return JsonResponse(new_desk, status=201)
    except Exception as e:
        print(f"[desks_create] Error adding desk: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@require_http_methods(["DELETE"])
def desks_delete(request, desk_id):
    """Remove a desk by ID."""
    print(f"[desks_delete] DELETE request for desk {desk_id}")
    print(f"[desks_delete] User authenticated: {request.user.is_authenticated}")
    print(f"[desks_delete] User: {request.user}")
    
    try:
        success = remove_desk(desk_id)
        if success:
            print(f"[desks_delete] Successfully deleted desk {desk_id}")
            return JsonResponse({"detail": "Deleted"})
        else:
            print(f"[desks_delete] Desk {desk_id} not found")
            return JsonResponse({"error": "Desk not found"}, status=404)
    except Exception as e:
        print(f"[desks_delete] Error deleting desk {desk_id}: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@require_http_methods(["GET"])
def load_view_desks(request):
    """Compatibility endpoint for /load_view/desks/"""
    try:
        desks = load_desks()
        room = request.GET.get("room", "").strip()  # e.g. "Room A"
        
        if room:
            # Extract just the letter (A, B, C, D) from "Room A"
            room_letter = room.replace("Room ", "").strip()
            print(f"[load_view_desks] Filtering by room: '{room}' -> '{room_letter}'")
            desks = [d for d in desks if (d.get("room") or "A") == room_letter]
            print(f"[load_view_desks] Found {len(desks)} desks in room {room_letter}")
        
        return JsonResponse(desks, safe=False)
    except Exception as e:
        print(f"[load_view_desks] Error: {e}")
        return JsonResponse([], safe=False)
