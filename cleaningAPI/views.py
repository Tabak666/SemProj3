from rest_framework.decorators import api_view
from rest_framework.response import Response 
from core.api_client.calls import toggle_clean_mode

@api_view(['GET'])
def hello(request):
    name = request.GET.get('name', 'guest')
    data = {
        'name': name,
        'message': f"Hello {name}, your first API endpoint has been created successfully!"
    }
    return Response(data)

@api_view(['GET'])
def toggleCleaningMode(request):
    toggle_clean_mode()
    return Response({"kokot" : "si"})