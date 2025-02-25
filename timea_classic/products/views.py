from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .models import Product, ProductVariant, Category

@login_required
def product_list(request):
    """Fetches and displays products with caching and category filtering."""
    
    # Fetch categories from cache
    categories = cache.get("categories")
    if not categories:
        categories = list(Category.objects.all())
        cache.set("categories", categories, timeout=900)  # Cache for 15 minutes

    category_id = request.GET.get('category')
    query = request.GET.get('q')
    
    cache_key = f"product_list_{category_id or 'all'}_{query or 'none'}"
    products = cache.get(cache_key)

    if not products:
        products = Product.objects.all()
        if category_id:
            category = get_object_or_404(Category, id=category_id)
            products = products.filter(category=category)
        if query:
            products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
        
        products = list(products)  # Convert queryset to list before caching
        cache.set(cache_key, products, timeout=900)  # Cache for 15 minutes

    # Pagination
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': categories,
        'products': page_obj,
        'category': category if category_id else None,
        'query': query,
    }
    return render(request, 'products/product_list.html', context)


@login_required
def product_detail(request, product_id):
    """Fetches and displays a single product with caching."""
    
    cache_key = f"product_{product_id}"
    product = cache.get(cache_key)

    if not product:
        product = get_object_or_404(Product, id=product_id)
        cache.set(cache_key, product, timeout=3600)  # Cache for 1 hour

    # Fetch variants dynamically without caching
    variants = product.variants.all()
    
    return render(request, 'products/product_detail.html', {'product': product, 'variants': variants})


@login_required
def product_by_category(request, category_id):
    """Fetches products for a specific category using caching."""
    
    cache_key = f"category_products_{category_id}"
    products = cache.get(cache_key)

    if not products:
        category = get_object_or_404(Category, id=category_id)
        products = list(category.products.all())  # Convert to list
        cache.set(cache_key, products, timeout=900)  # Cache for 15 minutes

    return render(request, 'products/product_list.html', {'products': products, 'category': category})


@login_required
def product_search(request):
    """Handles product search with caching."""
    
    query = request.GET.get('q', '').strip()
    cache_key = f"search_results_{query or 'none'}"
    products = cache.get(cache_key)

    if not products:
        products = Product.objects.all()
        if query:
            products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
        
        products = list(products)  # Convert to list before caching
        cache.set(cache_key, products, timeout=600)  # Cache for 10 minutes

    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'products/product_list.html', {'products': page_obj, 'query': query})


@login_required
def add_variant_to_cart(request, product_id, variant_id):
    """Handles adding a product variant to the shopping cart stored in session."""
    
    product = get_object_or_404(Product, id=product_id)
    variant = get_object_or_404(ProductVariant, id=variant_id)

    # Fetch cart from session
    cart = request.session.get('cart', {})

    if str(variant.id) in cart:
        cart[str(variant.id)]['quantity'] += 1
    else:
        cart[str(variant.id)] = {
            'product_id': product.id,
            'variant_id': variant.id,
            'quantity': 1
        }

    request.session['cart'] = cart
    request.session.modified = True  # Ensure session is updated

    # Invalidate cache for product lists (since stock or availability might change)
    cache.delete(f"product_list_all")
    cache.delete(f"product_list_{product.category.id}" if product.category else None)

    return redirect('products:detail', product_id=product.id)
