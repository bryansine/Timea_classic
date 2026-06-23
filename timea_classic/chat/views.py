from .models import ChatMessage
from orders.models import Order 
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test

User = get_user_model()

@user_passes_test(lambda u: u.is_staff)
def chat_dashboard(request):
    """Lists all registered customers for the admin support desk."""
    customers = User.objects.exclude(id=request.user.id)
    return render(request, 'chat/dashboard.html', {'customers': customers})

@user_passes_test(lambda u: u.is_staff)
def room(request, room_name):
    customer = get_object_or_404(User, username=room_name)
    customer_orders = Order.objects.filter(user=customer).prefetch_related('items').order_by('-created_at')[:5]
    
    chat_history = ChatMessage.objects.filter(room_name=room_name)
    
    context = {
        'chat_room_name': room_name,
        'customer': customer,
        'orders': customer_orders,
        'chat_history': chat_history,
    }
    return render(request, 'chat/room.html', context)