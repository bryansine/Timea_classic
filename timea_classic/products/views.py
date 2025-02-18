from .models import Product, ProductVariant
from .models import Category
from django.db.models import Q
from .models import Product, Category
from django.shortcuts import redirect
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def product_list(request):
    categories = Category.objects.all()

    category_id = request.GET.get('category')
    category = None
    products = Product.objects.all()

    if category_id:
        category = get_object_or_404(Category, id=category_id)
        products = products.filter(category=category)

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
    product = get_object_or_404(Product, id=product_id)
    variants = product.variants.all()  # Fetch all variants for this product
    context = {
        'product': product,
        'variants': variants,
    }
    return render(request, 'products/product_detail.html', context)


# View to list products by category
@login_required
def product_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = category.products.all()
    return render(request, 'products/product_list.html', {'products': products, 'category': category})


# View to search products
@login_required
def product_search(request):
    query = request.GET.get('q')
    products = Product.objects.all()  # Start with all products
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    # Paginate search results
    paginator = Paginator(products, 20)  # Show 10 products per page
    page_number = request.GET.get('page')  # Get current page number from query parameters
    page_obj = paginator.get_page(page_number)  # Get the page object for the current page

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

    return redirect('products:detail', product_id=product.id)




