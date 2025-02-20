from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def room(request, room_name):  # Keep room_name parameter
    return render(request, 'chat/room.html', {})  # Empty context, relies on context processors


from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def room(request, room_name):
    return render(request, 'chat/room.html', {}) 

# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required

# @login_required
# def room(request, room_name):  # Remove the default value
#     return render(request, 'chat/room.html', {
#         'chat_room_name': room_name,  # Consistent naming
#         'username': request.user.username, #This is not used in the template, so you can remove it if you want
#     })


