from django.shortcuts import render, get_object_or_404, redirect
from .models import Order, OrderItem
from django.contrib.auth.decorators import login_required
from cart.models import Cart

@login_required
def create_order(request):
    cart = Cart(request)
    if not cart:
        return redirect('cart:cart_detail')

    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address')
        phone_number = request.POST.get('phone_number')

        order = Order.objects.create(
            user=request.user,
            status='Pending',
            shipping_address=shipping_address,
            phone_number=phone_number
        )
        for item in cart:
            product = item['product']
            variant = item['variant']
            price = item['price']
            quantity = item['quantity']

            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                quantity=quantity,
                price=price
            )

        cart.clear()
        return redirect('orders:order_detail', order_id=order.id)

    return render(request, 'orders/create_order.html', {'cart': cart})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {'order': order}
    return render(request, 'orders/order_detail.html', context)

@login_required
def create_order_from_cart(request):
    return redirect('orders:create_order')
