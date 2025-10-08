from .models import Cart, CartItem
from django.core.cache import cache
from products.models import Product, ProductVariant
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

def add_to_cart(request, product_id, variant_id=None):
    product = get_object_or_404(Product, id=product_id)
    variant = None
    quantity = int(request.POST.get('quantity', 1))

    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id)

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)

        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product if not variant else None,
            variant=variant
        )
        if not item_created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        cache_key = f"cart_{request.user.id}"
        cache.delete(cache_key)

    else:
        session_cart = request.session.get('cart', {})
        
        item_key = f'product_{product_id}'
        if variant_id:
            item_key = f'variant_{variant_id}'

        session_cart[item_key] = session_cart.get(item_key, 0) + quantity
        
        request.session['cart'] = session_cart

    return redirect('cart:view')


from django.shortcuts import render, get_object_or_404
from products.models import Product, ProductVariant
from .models import Cart, CartItem
from django.core.cache import cache

def view_cart(request):
    cart = None
    raw_items = []
    cart_items = []

    if request.user.is_authenticated:
        cache_key = f"cart_{request.user.id}"
        cart_data = cache.get(cache_key)

        if not cart_data:
            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                raw_items = cart.items.all()
        
        cart_items = [
            {
                'item': item,
                'quantity': item.quantity,
                'item_name': item.product.name if item.product else item.variant.product.name
            }
            for item in raw_items
        ]

    else:
        session_cart = request.session.get('cart', {})
        
        for item_key, quantity in session_cart.items():
            if item_key.startswith('product_'):
                product_id = item_key.split('_')[1]
                product = get_object_or_404(Product, id=product_id)
                
                cart_items.append({
                    'item': product,
                    'quantity': quantity,
                    'item_name': product.name
                })
            elif item_key.startswith('variant_'):
                variant_id = item_key.split('_')[1]
                variant = get_object_or_404(ProductVariant, id=variant_id)

                cart_items.append({
                    'item': variant,
                    'quantity': quantity,
                    'item_name': variant.product.name
                })


    context = {
        'cart': cart,
        'cart_items': cart_items
    }
    
    if request.user.is_authenticated and 'cart_data' in locals():
        cache.set(cache_key, context, timeout=60)

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
            
        cache_key = f"cart_{request.user.id}"
        cache.delete(cache_key)
        
    return redirect('cart:view')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    if cart_item.cart.user == request.user:
        cart_item.delete()
        
        cache_key = f"cart_{request.user.id}"
        cache.delete(cache_key)
        
    return redirect('cart:view')
