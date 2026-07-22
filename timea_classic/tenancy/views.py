from django.db.models import Q, Sum, F, Count
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

from .models import Tenant
from .forms import MerchantProductForm, CategoryForm, ProductVariantForm
from products.models import Product, Category, ProductVariant
from orders.models import Order
from chat.models import ChatMessage

User = get_user_model()

# Extract status keys dynamically from the Order model
STATUS_CHOICES = [status[0] for status in Order.STATUS_CHOICES]

@login_required
def merchant_chat_dashboard(request, tenant_slug):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    if tenant.owner != request.user:
        return HttpResponseForbidden("Access Denied.")
        
    # Get customers who have ordered OR sent chat messages to this tenant
    customers = User.objects.filter(
        Q(orders__tenant=tenant) | Q(chat_messages__tenant=tenant)
    ).distinct().exclude(id=request.user.id)
    
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
    
    # Base QuerySet strictly filtered by the current tenant/store
    tenant_orders = Order.objects.filter(tenant=tenant)
    
    total_orders = tenant_orders.count()
    completed_orders = tenant_orders.filter(status='Delivered').count()
    pending_fulfillments = tenant_orders.filter(status='Pending').count()
    
    paid_orders = tenant_orders.filter(payment_status='Paid').prefetch_related('items')
    total_revenue = sum(order.total_price for order in paid_orders)
    
    recent_orders = tenant_orders.prefetch_related('items').order_by('-created_at')[:15]
    
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
    
    # 1. Only list customers who belong to THIS tenant
    customers = User.objects.filter(orders__tenant=tenant).distinct().exclude(id=request.user.id)
    
    # 2. Only show customer orders placed at THIS store
    customer_orders = Order.objects.filter(
        user=customer, 
        tenant=tenant
    ).prefetch_related('items').order_by('-created_at')[:5]
    
    # 3. Fetch chat history (If ChatMessage has a 'tenant' field, filter by it as well)
    if hasattr(ChatMessage, 'tenant'):
        chat_history = ChatMessage.objects.filter(room_name=room_name, tenant=tenant)
    else:
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

@login_required
def merchant_orders(request, tenant_slug):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    if tenant.owner != request.user:
        return HttpResponseForbidden("Access Denied.")

    status_filter = request.GET.get('status', '').strip()
    search_query = request.GET.get('q', '').strip()

    # Base QuerySet strictly scoped to THIS tenant/store
    orders = Order.objects.filter(tenant=tenant).prefetch_related('items__product').order_by('-created_at')

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
        # Strictly scope lookup by BOTH order_id AND tenant
        order = get_object_or_404(Order, id=order_id, tenant=tenant)
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

    # Filter products and categories strictly for THIS tenant
    products = Product.objects.filter(tenant=tenant).select_related('category')
    categories = Category.objects.filter(tenant=tenant)

    if query:
        products = products.filter(Q(name__icontains=query) | Q(brand__icontains=query) | Q(description__icontains=query))

    if category_id:
        products = products.filter(category_id=category_id)

    products = products.order_by('-created_at')

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
        # Pass tenant=tenant here 👇
        form = MerchantProductForm(request.POST, request.FILES, tenant=tenant)
        if form.is_valid():
            product = form.save(commit=False)
            product.tenant = tenant
            product.save()
            form.save_m2m()
            
            messages.success(request, f"Product '{product.name}' created successfully!")
            return redirect('tenancy:merchant_products', tenant_slug=tenant.slug)
    else:
        # Pass tenant=tenant here 👇
        form = MerchantProductForm(tenant=tenant)

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

    product = get_object_or_404(Product, id=product_id, tenant=tenant)

    if request.method == 'POST':
        # Pass tenant=tenant here 👇
        form = MerchantProductForm(request.POST, request.FILES, instance=product, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{product.name}' updated successfully!")
            return redirect('tenancy:merchant_products', tenant_slug=tenant.slug)
    else:
        # Pass tenant=tenant here 👇
        form = MerchantProductForm(instance=product, tenant=tenant)

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

    # Strictly scope the lookup by BOTH id and tenant
    product = get_object_or_404(Product, id=product_id, tenant=tenant)
    
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
    
    categories = Category.objects.filter(tenant=tenant).order_by('name')

    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if name:
            if category_id:
                cat = get_object_or_404(Category, id=category_id, tenant=tenant)
                cat.name = name
                cat.description = description
                cat.save()
                messages.success(request, f"Category '{name}' updated successfully.")
            else:
                Category.objects.create(
                    tenant=tenant,
                    name=name,
                    description=description
                )
                messages.success(request, f"Category '{name}' created successfully.")
            return redirect('tenancy:merchant_categories', tenant_slug=tenant.slug)

    return render(request, 'tenancy/dashboard/categories.html', {
        'tenant': tenant,
        'categories': categories,
    })

@login_required
def delete_category(request, tenant_slug, category_id):
    tenant = get_object_or_404(Tenant, slug=tenant_slug, is_active=True)
    if tenant.owner != request.user:
        return HttpResponseForbidden("Access Denied.")

    category = get_object_or_404(Category, id=category_id, tenant=tenant)
    
    if request.method == 'POST':
        cat_name = category.name
        category.delete()
        messages.success(request, f"Category '{cat_name}' deleted successfully.")
        
    return redirect('tenancy:merchant_categories', tenant_slug=tenant.slug)



@login_required
def merchant_product_variants(request, tenant_slug, product_id):
    tenant = get_object_or_404(Tenant, slug=tenant_slug)
    product = get_object_or_404(Product, id=product_id, tenant=tenant)
    variants = product.variants.all()

    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        color_name = request.POST.get('color_name', '').strip()
        price = request.POST.get('price', 0.0)
        stock_quantity = request.POST.get('stock_quantity', 0)
        image = request.FILES.get('image')

        if color_name:
            if variant_id:
                variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
                variant.color_name = color_name
                variant.price = price
                variant.stock_quantity = stock_quantity
                if image:
                    variant.image = image
                variant.save()
                messages.success(request, f"Variant '{color_name}' updated successfully.")
            else:
                ProductVariant.objects.create(
                    product=product,
                    color_name=color_name,
                    price=price,
                    stock_quantity=stock_quantity,
                    image=image
                )
                messages.success(request, f"Variant '{color_name}' created successfully.")
                
            return redirect('tenancy:merchant_product_variants', tenant_slug=tenant.slug, product_id=product.id)

    return render(request, 'tenancy/dashboard/variants.html', {
        'tenant': tenant,
        'product': product,
        'variants': variants,
    })

@login_required
def delete_product_variant(request, tenant_slug, product_id, variant_id):
    tenant = get_object_or_404(Tenant, slug=tenant_slug)
    product = get_object_or_404(Product, id=product_id, tenant=tenant)
    variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

    if request.method == 'POST':
        var_name = variant.color_name
        variant.delete()
        messages.success(request, f"Variant '{var_name}' deleted successfully.")

    return redirect('tenancy:merchant_product_variants', tenant_slug=tenant.slug, product_id=product.id)