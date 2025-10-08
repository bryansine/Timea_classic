# cart/utils.py

from products.models import Product, ProductVariant
from .models import Cart, CartItem
from django.shortcuts import get_object_or_404

def merge_carts(request, user):
    """
    Merges items from the Django session cart into the authenticated user's
    permanent database cart and clears the session cart.
    """
    if 'cart' not in request.session:
        return

    session_cart = request.session.get('cart', {})
    
    if session_cart:
        # 1. Get or create the user's permanent cart
        user_cart, created = Cart.objects.get_or_create(user=user)

        for item_key, quantity in session_cart.items():
            product = None
            variant = None
            
            # 2. Identify the product/variant from the session key
            if item_key.startswith('product_'):
                product_id = item_key.split('_')[1]
                product = get_object_or_404(Product, id=product_id)
            elif item_key.startswith('variant_'):
                variant_id = item_key.split('_')[1]
                variant = get_object_or_404(ProductVariant, id=variant_id)

            # 3. Look up the item in the database cart and update/create
            cart_item, item_created = CartItem.objects.get_or_create(
                cart=user_cart,
                product=product,
                variant=variant
            )
            
            # The session cart key should only contain ONE of these values
            if not item_created:
                cart_item.quantity += quantity
            else:
                cart_item.quantity = quantity

            cart_item.save()

        # 4. Clear the session cart after successful merge
        del request.session['cart']
        request.session.modified = True # Ensure the session is marked as changed