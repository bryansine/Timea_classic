from .models import Cart, CartItem
from products.models import Product, ProductVariant
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

@login_required
def add_to_cart(request, product_id, variant_id=None):
    cart, created = Cart.objects.get_or_create(user=request.user)
    product = get_object_or_404(Product, id=product_id)
    variant = None
    quantity = int(request.POST.get('quantity', 1))

    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product if not variant else None,
        variant=variant if variant else None,
    )
    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()

    return redirect('cart:view')


@login_required
def view_cart(request):
    cart = Cart.objects.filter(user=request.user).first()
    items = cart.items.all() if cart else []

    cart_items = []
    for item in items:
        if item.product:
            item_name = item.product.name
        elif item.variant:
            item_name = item.variant.product.name
        else:
            item_name = "Unknown Product"
        
        cart_items.append({
            'item': item,
            'item_name': item_name,
        })

    context = {
        'cart': cart,
        'cart_items': cart_items,
    }

    return render(request, 'cart/view_cart.html', context)


@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == "POST":
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('cart:view')



@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    if cart_item.cart.user == request.user:
        cart_item.delete()
    return redirect('cart:view')

