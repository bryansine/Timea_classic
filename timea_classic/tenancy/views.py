from .models import Tenant
from django.db.models import Q
from orders.models import Order
from chat.models import ChatMessage
from django.db.models import Sum, F
from django.contrib import messages
from products.models import Product
from .forms import MerchantProductForm
from django.db.models import Sum, Count
from django.http import HttpResponseForbidden
from django.contrib.auth import get_user_model
from .forms import CategoryForm, ProductVariantForm
from products.models import Category, ProductVariant
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

User = get_user_model()
@login_required
def merchant_chat_dashboard(request, tenant_slug):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    if tenant.owner != request.user:
        return HttpResponseForbidden("Access Denied.")
        
    customers = User.objects.exclude(id=request.user.id)
    
    context = {
        'tenant': tenant,
        'customers': customers,
    }
    return render(request, 'tenancy/dashboard/chat_dashboard.html', context)


@login_required
def merchant_overview(request, tenant_slug):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    
    if tenant.owner != request.user:
        return HttpResponseForbidden("You do not have permission to manage this store.")
    
    total_orders = Order.objects.count()
    completed_orders = Order.objects.filter(status='Delivered').count()
    pending_fulfillments = Order.objects.filter(status='Pending').count()
    
    paid_orders = Order.objects.filter(payment_status='Paid').prefetch_related('items')
    total_revenue = sum(order.total_price for order in paid_orders)
    
    recent_orders = Order.objects.prefetch_related('items').order_by('-created_at')[:15]
    
    context = {
        'tenant': tenant,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'pending_fulfillments': pending_fulfillments,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
    }
    return render(request, 'tenancy/dashboard/overview.html', context)


@login_required
def merchant_chat_room(request, tenant_slug, room_name):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    if tenant.owner != request.user:
        return HttpResponseForbidden("Access Denied.")
        
    customer = get_object_or_404(User, username=room_name)
    customers = User.objects.exclude(id=request.user.id)
    
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


STATUS_CHOICES = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']

@login_required
def merchant_orders(request, tenant_slug):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    if tenant.owner != request.user:
        return HttpResponseForbidden("Access Denied.")

    status_filter = request.GET.get('status', '').strip()
    search_query = request.GET.get('q', '').strip()

    orders = Order.objects.prefetch_related('items__product').order_by('-created_at')

    if status_filter in STATUS_CHOICES:
        orders = orders.filter(status=status_filter)

    if search_query:
        if search_query.startswith('#'):
            search_query = search_query[1:]
        orders = orders.filter(
            Q(id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    context = {
        'tenant': tenant,
        'orders': orders,
        'status_choices': STATUS_CHOICES,
        'selected_status': status_filter,
        'search_query': search_query,
    }
    return render(request, 'tenancy/dashboard/orders_list.html', context)


@login_required
def update_order_status(request, tenant_slug, order_id):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    if tenant.owner != request.user:
        return HttpResponseForbidden("Access Denied.")

    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')

        if new_status in STATUS_CHOICES:
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.id} status updated to '{new_status}'.")
        else:
            messages.error(request, "Invalid status choice.")

    return redirect('tenancy:merchant_orders', tenant_slug=tenant.slug)


@login_required
def merchant_products(request, tenant_slug):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    if tenant.owner != request.user:
        return HttpResponseForbidden("Access Denied.")

    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')

    products = Product.objects.select_related('category').all()

    if query:
        products = products.filter(Q(name__icontains=query) | Q(brand__icontains=query) | Q(description__icontains=query))

    if category_id:
        products = products.filter(category_id=category_id)

    products = products.order_by('-created_at')
    categories = Category.objects.all()

    context = {
        'tenant': tenant,
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
    }
    return render(request, 'tenancy/dashboard/products_list.html', context)


@login_required
def merchant_product_create(request, tenant_slug):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    if tenant.owner != request.user:
        return HttpResponseForbidden("Access Denied.")

    if request.method == 'POST':
        form = MerchantProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product '{product.name}' created successfully!")
            return redirect('tenancy:merchant_products', tenant_slug=tenant.slug)
    else:
        form = MerchantProductForm()

    context = {
        'tenant': tenant,
        'form': form,
        'title': 'Add New Product',
    }
    return render(request, 'tenancy/dashboard/product_form.html', context)


@login_required
def merchant_product_edit(request, tenant_slug, product_id):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    if tenant.owner != request.user:
        return HttpResponseForbidden("Access Denied.")

    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = MerchantProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{product.name}' updated successfully!")
            return redirect('tenancy:merchant_products', tenant_slug=tenant.slug)
    else:
        form = MerchantProductForm(instance=product)

    context = {
        'tenant': tenant,
        'form': form,
        'product': product,
        'title': f"Edit: {product.name}",
    }
    return render(request, 'tenancy/dashboard/product_form.html', context)


@login_required
def merchant_product_delete(request, tenant_slug, product_id):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    if tenant.owner != request.user:
        return HttpResponseForbidden("Access Denied.")

    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f"Product '{product_name}' was deleted.")
        return redirect('tenancy:merchant_products', tenant_slug=tenant.slug)

    context = {
        'tenant': tenant,
        'product': product,
    }
    return render(request, 'tenancy/dashboard/product_confirm_delete.html', context)


@login_required
def merchant_categories(request, tenant_slug):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    if tenant.owner != request.user:
        return HttpResponseForbidden("Access Denied.")

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "New category added successfully!")
            return redirect('tenancy:merchant_categories', tenant_slug=tenant.slug)
    else:
        form = CategoryForm()

    categories = Category.objects.all()
    
    context = {
        'tenant': tenant,
        'form': form,
        'categories': categories,
    }
    return render(request, 'tenancy/dashboard/categories.html', context)


@login_required
def merchant_product_variants(request, tenant_slug, product_id):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    if tenant.owner != request.user:
        return HttpResponseForbidden("Access Denied.")

    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductVariantForm(request.POST, request.FILES)
        if form.is_valid():
            variant = form.save(commit=False)
            variant.product = product
            variant.save()
            messages.success(request, f"Variant '{variant.color_name}' added to {product.name}!")
            return redirect('tenancy:merchant_product_variants', tenant_slug=tenant.slug, product_id=product.id)
    else:
        form = ProductVariantForm()

    variants = product.variants.all()

    context = {
        'tenant': tenant,
        'product': product,
        'variants': variants,
        'form': form,
    }
    return render(request, 'tenancy/dashboard/variants.html', context)