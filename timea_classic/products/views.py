from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .models import Product, ProductVariant, Category

@login_required
def product_list(request):
    categories = cache.get("categories")  # Try getting categories from cache
    if not categories:
        categories = list(Category.objects.all())
        cache.set("categories", categories, timeout=60 * 15)  # Cache for 15 minutes

    category_id = request.GET.get('category')
    category = None
    cache_key = f"product_list_{category_id}" if category_id else "product_list_all"
    
    products = cache.get(cache_key)  # Try fetching cached products
    if not products:
        products = Product.objects.all()
        if category_id:
            category = get_object_or_404(Category, id=category_id)
            products = products.filter(category=category)
        cache.set(cache_key, list(products), timeout=60 * 15)  # Cache for 15 minutes

    query = request.GET.get('q')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': categories,
        'products': page_obj,
        'category': category,
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'products/product_list.html', context)

@login_required
def product_detail(request, product_id):
    cache_key = f"product_{product_id}"  # Unique cache key per product
    product = cache.get(cache_key)

    if not product:
        product = get_object_or_404(Product, id=product_id)
        cache.set(cache_key, product, timeout=60 * 60)  # Cache for 1 hour

    variants = product.variants.all()  # Fetch variants separately (not cached)
    
    context = {
        'product': product,
        'variants': variants,
    }
    return render(request, 'products/product_detail.html', context)

@login_required
def product_by_category(request, category_id):
    cache_key = f"category_products_{category_id}"
    products = cache.get(cache_key)

    if not products:
        category = get_object_or_404(Category, id=category_id)
        products = list(category.products.all())  # Convert queryset to list
        cache.set(cache_key, products, timeout=60 * 15)  # Cache for 15 minutes

    return render(request, 'products/product_list.html', {'products': products, 'category': category})

@login_required
def product_search(request):
    query = request.GET.get('q')
    cache_key = f"search_results_{query}" if query else "search_results_all"
    products = cache.get(cache_key)

    if not products:
        products = Product.objects.all()
        if query:
            products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
        cache.set(cache_key, list(products), timeout=60 * 10)  # Cache for 10 minutes

    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'query': query,
        'page_obj': page_obj,
    }
    return render(request, 'products/product_list.html', context)

@login_required
def add_variant_to_cart(request, product_id, variant_id):
    product = get_object_or_404(Product, id=product_id)
    variant = get_object_or_404(ProductVariant, id=variant_id)

    cart = request.session.get('cart', {})

    if str(variant.id) in cart:
        cart[str(variant.id)]['quantity'] += 1
    else:
        cart[str(variant.id)] = {'product_id': product.id, 'variant_id': variant.id, 'quantity': 1}

    request.session['cart'] = cart

    # Invalidate cache for product list since cart is updated
    cache.delete("product_list_all")

    return redirect('products:detail', product_id=product.id)
