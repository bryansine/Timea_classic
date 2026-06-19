from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def room(request, room_name):
    return render(request, 'chat/room.html', {})




# chat/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model

User = get_user_model()

# Ensure only admin/staff can see the support dashboard overview
@user_passes_test(lambda u: u.is_staff)
def chat_dashboard(request):
    # Fetch all users except the current admin so you can see your clients
    customers = User.objects.exclude(id=request.user.id)
    return render(request, 'chat/dashboard.html', {'customers': customers})

@user_passes_test(lambda u: u.is_staff) # Optional: secure the room view too
def room(request, room_name):
    return render(request, 'chat/room.html', {'chat_room_name': room_name})