from django.conf import settings

def chat_room(request):
    if request.user.is_authenticated:
        room_name = request.user.username  # Or your logic for generating room names
        return {'chat_room_name': room_name}
    return {}