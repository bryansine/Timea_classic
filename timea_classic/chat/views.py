from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# @login_required
# def room(request, room_name):
#     return render(request, 'chat/room.html', {
#         'room_name': room_name,
#         'username': request.user.username,
#     })
@login_required
def room(request, room_name=None):
    if not room_name:
        room_name = "defaultroom"  # Set a fallback room name
    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'username': request.user.username,
    })