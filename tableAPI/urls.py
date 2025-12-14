from django.urls import path
from django.http import HttpResponseNotAllowed
from . import views

def desks_endpoint(request):
    """Dispatch GET -> desks_list, POST -> desks_create so a single URL works for both."""
    if request.method == "GET":
        return views.desks_list(request)
    if request.method == "POST":
        return views.desks_create(request)
    return HttpResponseNotAllowed(["GET", "POST"])

urlpatterns = [
    # flexible aliases so frontends calling different paths still reach the same logic
    path("api/desks/", desks_endpoint, name="tableapi_desks_endpoint"),
    path("api/desks", desks_endpoint, name="tableapi_desks_endpoint_noslash"),
    path("desks/", desks_endpoint, name="tableapi_desks_endpoint_alt"),
    path("desks", desks_endpoint, name="tableapi_desks_endpoint_alt_noslash"),

    # delete route (with/without trailing slash)
    path("api/desks/<int:desk_id>/", views.desks_delete, name="tableapi_desks_delete"),
    path("api/desks/<int:desk_id>", views.desks_delete, name="tableapi_desks_delete_noslash"),
    path("desks/<int:desk_id>/", views.desks_delete, name="tableapi_desks_delete_alt"),
    path("desks/<int:desk_id>", views.desks_delete, name="tableapi_desks_delete_alt_noslash"),

    # compatibility endpoint used by your frontend: /load_view/desks/
    path("load_view/desks/", views.load_view_desks, name="load_view_desks"),
    path("load_view/desks", views.load_view_desks, name="load_view_desks_noslash"),
]
