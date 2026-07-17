# tenancy/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Tenant

@login_required
def merchant_overview(request, tenant_slug):
    # Fetch the specific tenant environment by its slug
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    
    # Security Check: Ensure only the tenant owner can see this dashboard
    if tenant.owner != request.user:
        return HttpResponseForbidden("You do not have permission to manage this store.")
    
    context = {
        'tenant': tenant,
    }
    return render(request, 'tenancy/dashboard/overview.html', context)


# tenancy/views.py
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from chat.models import ChatMessage
from orders.models import Order

User = get_user_model()

@login_required
def merchant_chat_dashboard(request, tenant_slug):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    if tenant.owner != request.user:
        return HttpResponseForbidden("Access Denied.")
        
    # Exclude the merchant themselves from the customer chat lists
    customers = User.objects.exclude(id=request.user.id)
    
    context = {
        'tenant': tenant,
        'customers': customers,
    }
    return render(request, 'tenancy/dashboard/chat_dashboard.html', context)

@login_required
def merchant_chat_room(request, tenant_slug, room_name):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    if tenant.owner != request.user:
        return HttpResponseForbidden("Access Denied.")
        
    # Safely look up the specific customer by room name (username)
    customer = get_object_or_404(User, username=room_name)
    customers = User.objects.exclude(id=request.user.id)
    
    # Fetch customer's SQLite order history just like your old app did
    customer_orders = Order.objects.filter(user=customer).prefetch_related('items').order_by('-created_at')[:5]
    chat_history = ChatMessage.objects.filter(room_name=room_name)
    
    context = {
        'tenant': tenant,
        'customers': customers,
        'chat_room_name': room_name,
        'customer': customer,
        'orders': customer_orders,
        'chat_history': chat_history,
    }
    return render(request, 'tenancy/dashboard/chat_room.html', context)