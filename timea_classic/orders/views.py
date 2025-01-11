from django.shortcuts import render, get_object_or_404, redirect
from .models import Order, OrderItem
from django.contrib.auth.decorators import login_required
from cart.models import Cart, CartItem
from django.http import HttpResponse
from django.db import transaction




@login_required
def create_order(request):
    cart = request.user.cart  # Ensure this is correct for your app
    if not cart.items.exists():  # Check if cart is empty
        return redirect('cart:view')  # Adjust 'cart:view' to your actual cart view

    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address')
        phone_number = request.POST.get('phone_number')

        selected_cart_items = request.POST.getlist('cart_items')  # List of selected cart item IDs

        # Ensure selected_cart_items is a list of integers
        selected_cart_item_ids = [int(item_id) for item_id in selected_cart_items]

        # Use a transaction to ensure atomicity
        with transaction.atomic():
            # Create the Order
            order = Order.objects.create(
                user=request.user,
                shipping_address=shipping_address,
                phone_number=phone_number,
                status='Pending'
            )

            # Track cart items to remove after order creation
            cart_items_to_remove = []

            # Add selected items from cart to the order
            for item in cart.items.filter(id__in=selected_cart_item_ids):
                price = item.product.price if item.product else item.variant.price
                name = item.product.name if item.product else f"{item.variant.product.name} - {item.variant.color_name}"

                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    quantity=item.quantity,
                    price=price
                )
                cart_items_to_remove.append(item.id)

            # Remove only the ordered items from the cart
            CartItem.objects.filter(id__in=cart_items_to_remove).delete()

        # Redirect to order detail page
        return redirect('orders:order_detail', order_id=order.id)

    # Render the order creation form for GET requests
    return render(request, 'orders/create_order.html', {'cart': cart})



@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {'order': order}
    return render(request, 'orders/order_detail.html', context)

@login_required
def create_order_from_cart(request):
    cart = request.user.cart 
    if not cart.items.exists():
        return redirect('cart:view')
    
    return render(request, 'orders/create_order.html', {'cart': cart})


@login_required
def initiate_payment(request, order_id):
    # Fetch the order
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.payment_status == "Paid":
        # If the payment is already complete
        return HttpResponse("Payment has already been completed for this order.")

    # Process payment (for now, we're simulating this step)
    # Example: Call a payment API or redirect to a payment gateway
    order.payment_status = "Pending"  # Update the payment status
    order.save()

    # Redirect to a payment confirmation or success page
    return redirect('orders:payment_success', order_id=order.id)


@login_required
def payment_success(request, order_id):
    # Fetch the order
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.payment_status != "Pending":
        return HttpResponse("Invalid payment status.")

    # Simulate successful payment
    order.payment_status = "Paid"
    order.save()

    return render(request, 'orders/payment_success.html', {'order': order})
