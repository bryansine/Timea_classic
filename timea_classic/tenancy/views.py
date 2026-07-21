# tenancy/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Tenant
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Sum, Count
from orders.models import Order

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Sum, F
from .models import Tenant
from orders.models import Order

@login_required
def merchant_overview(request, tenant_slug):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    
    if tenant.owner != request.user:
        return HttpResponseForbidden("You do not have permission to manage this store.")
    
    # 📊 Counts
    total_orders = Order.objects.count()
    completed_orders = Order.objects.filter(status='Delivered').count() # or 'Completed' based on STATUS_CHOICES
    pending_fulfillments = Order.objects.filter(status='Pending').count()
    
    # 💰 Calculate Total Revenue safely for Paid orders
    paid_orders = Order.objects.filter(payment_status='Paid').prefetch_related('items')
    total_revenue = sum(order.total_price for order in paid_orders)
    
    # 🛒 Recent 5 store orders
    recent_orders = Order.objects.prefetch_related('items').order_by('-created_at')[:5]
    
    context = {
        'tenant': tenant,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'pending_fulfillments': pending_fulfillments,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
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

# tenancy/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from .models import Tenant
from orders.models import Order

@login_required
def merchant_orders(request, tenant_slug):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    if tenant.owner != request.user:
        return HttpResponseForbidden("Access Denied.")
        
    # 🔄 Handle Inline Merchant Updates (Fulfillment & Payment Status)
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        new_payment_status = request.POST.get('payment_status')
        
        order = get_object_or_404(Order, id=order_id)
        
        # Update fulfillment status if provided
        if new_status in [c[0] for c in Order.STATUS_CHOICES]:
            order.status = new_status
            
        # Update payment status if provided
        if new_payment_status in [c[0] for c in Order.PAYMENT_STATUS_CHOICES]:
            order.payment_status = new_payment_status
            
        order.save()
        messages.success(request, f"Order #{order.id} updated successfully!")
        return redirect('tenancy:merchant_orders', tenant_slug=tenant.slug)

    # Fetch all orders prefetching line items
    orders = Order.objects.prefetch_related('items__product').order_by('-created_at')
    
    context = {
        'tenant': tenant,
        'orders': orders,
        'status_choices': Order.STATUS_CHOICES,
        'payment_choices': Order.PAYMENT_STATUS_CHOICES,
    }
    return render(request, 'tenancy/dashboard/orders.html', context)