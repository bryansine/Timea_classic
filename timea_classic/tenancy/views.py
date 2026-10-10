from .models import Tenant
from decimal import Decimal
# from decimal import Decimal
from orders.models import Order, OrderItem
from orders.models import Coupon
from chat.models import ChatMessage
from django.contrib import messages
from django.db.models import Q, Sum, F, Count
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from products.models import Product, Category, ProductVariant
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncMonth, ExtractHour, Coalesce
from django.db.models.functions import TruncMonth, ExtractHour
from django.shortcuts import render, get_object_or_404, redirect
from .forms import MerchantProductForm, CategoryForm, ProductVariantForm



def get_tenant_or_handle_inactive(request, tenant_slug):
    tenant = get_object_or_404(Tenant, slug=tenant_slug)

    if not tenant.is_active:
        return tenant, render(
            request,
            'tenancy/dashboard/store_suspended.html',
            {'tenant': tenant},
            status=403
        )

    if tenant.owner != request.user and not request.user.is_superuser:
        messages.error(
            request, 
            "Access Denied: You do not have permission to access that merchant workspace."
        )
        return tenant, redirect('home')  

    return tenant, None


User = get_user_model()

STATUS_CHOICES = [status[0] for status in Order.STATUS_CHOICES]

@login_required
def merchant_chat_dashboard(request, tenant_slug):
    tenant, error_response = get_tenant_or_handle_inactive(
        request, tenant_slug
    )
    if error_response:
        return error_response

    customers = (
        User.objects.filter(
            Q(orders__tenant=tenant) | Q(chat_messages__tenant=tenant)
        )
        .distinct()
        .exclude(id=request.user.id)
    )

    return render(
        request,
        'tenancy/dashboard/chat_dashboard.html',
        {
            'tenant': tenant,
            'customers': customers,
        },
    )



@login_required
def merchant_overview(request, tenant_slug):
    tenant, error_response = get_tenant_or_handle_inactive(request, tenant_slug)
    if error_response:
        return error_response

    tenant_orders = Order.objects.filter(tenant=tenant)
    
    total_orders = tenant_orders.count()
    completed_orders = tenant_orders.filter(status='Delivered').count()
    pending_fulfillments = tenant_orders.filter(status='Pending').count()
    
    paid_orders = tenant_orders.filter(payment_status='Paid').prefetch_related('items')
    paid_orders_count = paid_orders.count()
    
    total_revenue = sum(
        (
            Decimal(str(order.subtotal or 0)) + 
            Decimal(str(order.shipping_cost or 0)) - 
            Decimal(str(order.discount_amount or 0))
        ) for order in paid_orders
    )
    if not isinstance(total_revenue, Decimal):
        total_revenue = Decimal(str(total_revenue))
    
    aov = (total_revenue / paid_orders_count) if paid_orders_count > 0 else Decimal('0.00')

    order_total_expr = ExpressionWrapper(
        Coalesce(F('subtotal'), 0.0) + Coalesce(F('shipping_cost'), 0.0) - Coalesce(F('discount_amount'), 0.0),
        output_field=DecimalField()
    )

    monthly_sales = (
        paid_orders.annotate(
            month=TruncMonth('created_at'),
            calculated_total=order_total_expr
        )
        .values('month')
        .annotate(total=Sum('calculated_total'))
        .order_by('month')
    )
    revenue_labels = [item['month'].strftime('%b %Y') for item in monthly_sales]
    revenue_data = [float(item['total'] or 0) for item in monthly_sales]

    # 4. Top 5 Selling Products (Chart Data)
    top_products = (
        OrderItem.objects.filter(order__tenant=tenant, order__payment_status='Paid')
        .values('product__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:5]
    )
    top_product_labels = [item['product__name'] for item in top_products]
    top_product_data = [item['total_qty'] for item in top_products]

    # 5. Peak Purchasing Hours (24-Hour Distribution)
    hourly_distribution = (
        paid_orders.annotate(hour=ExtractHour('created_at'))
        .values('hour')
        .annotate(order_count=Count('id'))
        .order_by('hour')
    )
    hourly_dict = {item['hour']: item['order_count'] for item in hourly_distribution}
    peak_hours_labels = [f"{h:02d}:00" for h in range(24)]
    peak_hours_data = [hourly_dict.get(h, 0) for h in range(24)]

    recent_orders = tenant_orders.prefetch_related('items').order_by('-created_at')[:15]
    
    context = {
        'tenant': tenant,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'pending_fulfillments': pending_fulfillments,
        'total_revenue': total_revenue,
        'aov': aov,
        'revenue_labels': revenue_labels,
        'revenue_data': revenue_data,
        'top_product_labels': top_product_labels,
        'top_product_data': top_product_data,
        'peak_hours_labels': peak_hours_labels,
        'peak_hours_data': peak_hours_data,
        'recent_orders': recent_orders,
    }
    return render(request, 'tenancy/dashboard/overview.html', context)


@login_required
def merchant_chat_room(request, tenant_slug, room_name):
    tenant, error_response = get_tenant_or_handle_inactive(request, tenant_slug)
    if error_response:
        return error_response

    customer = get_object_or_404(User, username=room_name)

    customers = (
        User.objects.filter(
            Q(orders__tenant=tenant) | Q(chat_messages__tenant=tenant)
        )
        .distinct()
        .exclude(id=request.user.id)
    )

    customer_orders = (
        Order.objects.filter(user=customer, tenant=tenant)
        .prefetch_related('items')
        .order_by('-created_at')[:5]
    )

    chat_history = ChatMessage.objects.filter(
        room_name=room_name, tenant=tenant
    )

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
    tenant, error_response = get_tenant_or_handle_inactive(request, tenant_slug)
    if error_response:
        return error_response

    status_filter = request.GET.get('status', '').strip()
    search_query = request.GET.get('q', '').strip()

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


PAYMENT_STATUS_CHOICES = ['Pending', 'Paid']

@login_required
def update_payment_status(request, tenant_slug, order_id):
    tenant, error_response = get_tenant_or_handle_inactive(request, tenant_slug)
    if error_response:
        return error_response

    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, tenant=tenant)
        new_payment_status = request.POST.get('payment_status')

        if new_payment_status in PAYMENT_STATUS_CHOICES:
            order.payment_status = new_payment_status
            order.save()
            messages.success(request, f"Payment status for Order #{order.id} updated to {new_payment_status}.")
        else:
            messages.error(request, "Invalid payment status selected.")

    return redirect('tenancy:merchant_orders', tenant_slug=tenant_slug)



@login_required
def update_order_status(request, tenant_slug, order_id):
    tenant, error_response = get_tenant_or_handle_inactive(
        request, tenant_slug
    )
    if error_response:
        return error_response

    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id, tenant=tenant)
        new_status = request.POST.get('status')

        if new_status in STATUS_CHOICES:
            order.status = new_status
            order.save()
            messages.success(
                request, f"Order #{order.id} status updated to '{new_status}'."
            )
        else:
            messages.error(request, "Invalid status choice.")

    return redirect('tenancy:merchant_orders', tenant_slug=tenant.slug)


@login_required
def merchant_products(request, tenant_slug):
    tenant, error_response = get_tenant_or_handle_inactive(request, tenant_slug)
    if error_response:
        return error_response

    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')

    products = Product.objects.filter(tenant=tenant).select_related('category')
    categories = Category.objects.filter(tenant=tenant)

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(brand__icontains=query)
            | Q(description__icontains=query)
        )

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
    tenant, error_response = get_tenant_or_handle_inactive(
        request, tenant_slug
    )
    if error_response:
        return error_response

    if request.method == 'POST':
        form = MerchantProductForm(
            request.POST, request.FILES, tenant=tenant
        )
        if form.is_valid():
            product = form.save(commit=False)
            product.tenant = tenant
            product.save()
            form.save_m2m()

            messages.success(
                request, f"Product '{product.name}' created successfully!"
            )
            return redirect(
                'tenancy:merchant_products', tenant_slug=tenant.slug
            )
    else:
        form = MerchantProductForm(tenant=tenant)

    context = {
        'tenant': tenant,
        'form': form,
        'title': 'Add New Product',
    }
    return render(request, 'tenancy/dashboard/product_form.html', context)


@login_required
def merchant_product_edit(request, tenant_slug, product_id):
    tenant, error_response = get_tenant_or_handle_inactive(
        request, tenant_slug
    )
    if error_response:
        return error_response

    product = get_object_or_404(Product, id=product_id, tenant=tenant)

    if request.method == 'POST':
        form = MerchantProductForm(
            request.POST, request.FILES, instance=product, tenant=tenant
        )
        if form.is_valid():
            form.save()
            messages.success(
                request, f"Product '{product.name}' updated successfully!"
            )
            return redirect(
                'tenancy:merchant_products', tenant_slug=tenant.slug
            )
    else:
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
    tenant, error_response = get_tenant_or_handle_inactive(
        request, tenant_slug
    )
    if error_response:
        return error_response

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
    return render(
        request, 'tenancy/dashboard/product_confirm_delete.html', context
    )


@login_required
def merchant_categories(request, tenant_slug):
    tenant, error_response = get_tenant_or_handle_inactive(
        request, tenant_slug
    )
    if error_response:
        return error_response

    categories = Category.objects.filter(tenant=tenant).order_by('name')

    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if name:
            if category_id:
                cat = get_object_or_404(
                    Category, id=category_id, tenant=tenant
                )
                cat.name = name
                cat.description = description
                cat.save()
                messages.success(
                    request, f"Category '{name}' updated successfully."
                )
            else:
                Category.objects.create(
                    tenant=tenant, name=name, description=description
                )
                messages.success(
                    request, f"Category '{name}' created successfully."
                )
            return redirect(
                'tenancy:merchant_categories', tenant_slug=tenant.slug
            )

    return render(
        request,
        'tenancy/dashboard/categories.html',
        {
            'tenant': tenant,
            'categories': categories,
        },
    )

@login_required
def delete_category(request, tenant_slug, category_id):
    tenant, error_response = get_tenant_or_handle_inactive(
        request, tenant_slug
    )
    if error_response:
        return error_response

    category = get_object_or_404(Category, id=category_id, tenant=tenant)

    if request.method == 'POST':
        cat_name = category.name
        category.delete()
        messages.success(
            request, f"Category '{cat_name}' deleted successfully."
        )

    return redirect('tenancy:merchant_categories', tenant_slug=tenant.slug)


@login_required
def merchant_product_variants(request, tenant_slug, product_id):
    tenant, error_response = get_tenant_or_handle_inactive(
        request, tenant_slug
    )
    if error_response:
        return error_response

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
                variant = get_object_or_404(
                    ProductVariant, id=variant_id, product=product
                )
                variant.color_name = color_name
                variant.price = price
                variant.stock_quantity = stock_quantity
                if image:
                    variant.image = image
                variant.save()
                messages.success(
                    request, f"Variant '{color_name}' updated successfully."
                )
            else:
                ProductVariant.objects.create(
                    product=product,
                    color_name=color_name,
                    price=price,
                    stock_quantity=stock_quantity,
                    image=image,
                )
                messages.success(
                    request, f"Variant '{color_name}' created successfully."
                )

            return redirect(
                'tenancy:merchant_product_variants',
                tenant_slug=tenant.slug,
                product_id=product.id,
            )

    return render(
        request,
        'tenancy/dashboard/variants.html',
        {
            'tenant': tenant,
            'product': product,
            'variants': variants,
        },
    )

@login_required
def delete_product_variant(request, tenant_slug, product_id, variant_id):
    tenant, error_response = get_tenant_or_handle_inactive(
        request, tenant_slug
    )
    if error_response:
        return error_response

    product = get_object_or_404(Product, id=product_id, tenant=tenant)
    variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

    if request.method == 'POST':
        var_name = variant.color_name
        variant.delete()
        messages.success(
            request, f"Variant '{var_name}' deleted successfully."
        )

    return redirect(
        'tenancy:merchant_product_variants',
        tenant_slug=tenant.slug,
        product_id=product.id,
    )

@login_required
def merchant_coupons(request, tenant_slug):
    tenant, error_response = get_tenant_or_handle_inactive(request, tenant_slug)
    if error_response:
        return error_response

    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        discount_type = request.POST.get('discount_type')
        discount_value = request.POST.get('discount_value')
        min_purchase = request.POST.get('min_purchase_amount', 0.00)
        max_uses = request.POST.get('max_uses', 100)
        valid_to = request.POST.get('valid_to')

        if Coupon.objects.filter(tenant=tenant, code=code).exists():
            messages.error(request, f"Coupon code '{code}' already exists for this store.")
        else:
            Coupon.objects.create(
                tenant=tenant,
                code=code,
                discount_type=discount_type,
                discount_value=discount_value,
                min_purchase_amount=min_purchase if min_purchase else 0.00,
                max_uses=max_uses if max_uses else 100,
                valid_to=valid_to,
                is_active=True
            )
            messages.success(request, f"Coupon '{code}' created successfully!")
            return redirect('tenancy:merchant_coupons', tenant_slug=tenant.slug)

    coupons = Coupon.objects.filter(tenant=tenant).order_by('-id')
    
    return render(request, 'tenancy/dashboard/coupons.html', {
        'tenant': tenant,
        'coupons': coupons,
    })



@login_required
def toggle_coupon_status(request, tenant_slug, coupon_id):
    tenant, error_response = get_tenant_or_handle_inactive(request, tenant_slug)
    if error_response:
        return error_response

    coupon = get_object_or_404(Coupon, id=coupon_id, tenant=tenant)
    coupon.is_active = not coupon.is_active
    coupon.save()

    status_str = "activated" if coupon.is_active else "disabled"
    messages.success(request, f"Coupon '{coupon.code}' has been {status_str}.")
    
    return redirect('tenancy:merchant_coupons', tenant_slug=tenant.slug)