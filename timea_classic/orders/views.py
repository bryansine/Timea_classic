from django.shortcuts import render, get_object_or_404, redirect
from .models import Order, OrderItem
from django.contrib.auth.decorators import login_required
from cart.models import Cart
from django.http import HttpResponse


@login_required
def create_order(request):
    cart = request.user.cart
    if not cart.items.exists():
        return redirect('cart:view')

    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address')
        phone_number = request.POST.get('phone_number')

        # Create Order
        order = Order.objects.create(
            user=request.user,
            shipping_address=shipping_address,
            phone_number=phone_number,
            status='Pending'
        )

        # Add items from cart to order
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                quantity=item.quantity,
                price=item.product.price if item.product else item.variant.price
            )

        # Clear the cart
        cart.items.all().delete()

        return redirect('orders:order_detail', order_id=order.id)

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
