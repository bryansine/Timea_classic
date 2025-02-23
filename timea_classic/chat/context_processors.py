from django.conf import settings

def chat_room(request):
    if request.user.is_authenticated:
        room_name = request.user.username
        return {'chat_room_name': room_name}
    return {}