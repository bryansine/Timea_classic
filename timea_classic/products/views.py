from django.db.models import Q
from django.core.cache import cache
from .forms import ProductReviewForm
from django.http import JsonResponse
from .models import Product, ProductReview
from django.core.paginator import Paginator
from .models import Product, ProductVariant, Category
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

@login_required
def product_list(request):
    categories = cache.get("categories")
    if not categories:
        categories = list(Category.objects.all())
        cache.set("categories", categories, timeout=900)

    category_id = request.GET.get('category')
    query = request.GET.get('q')

    category = None

    cache_key = f"product_list_{category_id or 'all'}_{query or 'none'}"
    products = cache.get(cache_key)

    if not products:
        products = Product.objects.all()

        if category_id:
            category = get_object_or_404(Category, id=category_id)
            products = products.filter(category=category)

        if query:
            products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
        
        products = list(products)
        cache.set(cache_key, products, timeout=900)

    paginator = Paginator(products, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': categories,
        'products': page_obj,
        'category': category,
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
        cache.set(cache_key, product, timeout=3600)

    variants = product.variants.all()

    # Get related products (same category, excluding the current product)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

    return render(request, 'products/product_detail.html', {'product': product, 'variants': variants, 'related_products': related_products})


@login_required
def product_by_category(request, category_id):
    """Fetches products for a specific category using caching."""
    
    cache_key = f"category_products_{category_id}"
    products = cache.get(cache_key)

    if not products:
        category = get_object_or_404(Category, id=category_id)
        products = list(category.products.all())
        cache.set(cache_key, products, timeout=900)

    return render(request, 'products/product_list.html', {'products': products, 'category': category})



@login_required
def product_search(request):
    query = request.GET.get('q', '').strip()
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort_by', 'created_at_desc')

    products = Product.objects.all()

    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    if query:
        products = products.filter(name__icontains=query)

    # Sorting logic
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'name_asc':
        products = products.order_by('name')
    elif sort_by == 'name_desc':
        products = products.order_by('-name')
    elif sort_by == 'created_at_asc':
        products = products.order_by('created_at')
    elif sort_by == 'created_at_desc':
        products = products.order_by('-created_at')

    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'products/product_list.html', {'products': page_obj, 'query': query})


def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = []
    if query:
        products = Product.objects.filter(name__icontains=query)[:5]
        suggestions = [product.name for product in products]
    return JsonResponse(suggestions, safe=False)


@login_required
def add_variant_to_cart(request, product_id, variant_id):    
    product = get_object_or_404(Product, id=product_id)
    variant = get_object_or_404(ProductVariant, id=variant_id)

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
    request.session.modified = True 

    cache.delete(f"product_list_all")
    cache.delete(f"product_list_{product.category.id}" if product.category else None)

    return redirect('products:detail', product_id=product.id)




@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        form = ProductReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            return redirect('products:detail', product_id=product_id)  # Redirect to product detail page
    else:
        form = ProductReviewForm()
    return render(request, 'products/add_review.html', {'form': form, 'product': product})