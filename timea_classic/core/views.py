# views.py
from django.urls import reverse
from django.shortcuts import render, redirect
from .forms import UserProfileForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import UserRegistrationForm, UserForm  # Keep these imports here

from products.models import Product, Category
from django.contrib import messages
from .models import UserProfile

def about(request):
    return render(request, 'core/about.html')

def home(request):
    categories = Category.objects.all()
    category_id = request.GET.get('category')

    if category_id:
        try:
            category = Category.objects.get(id=category_id)
            products = Product.objects.filter(category=category)
        except Category.DoesNotExist:
            products = Product.objects.all()
    else:
        products = Product.objects.all()
        
    context = {
        'categories': categories,
        'products': products,
    }
    return render(request, 'core/home.html', context)

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('products:list')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'core/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('products:list')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})


def logout(request):
    logout(request)
    return redirect('home')

@login_required
def profile_view(request):
    from .forms import UserProfileForm

    user_form = UserForm(instance=request.user)
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    profile_form = UserProfileForm(request.POST, instance=profile)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'core/profile.html', context)

@login_required
def profile_edit(request):
    # Your logic to handle the profile editing form goes here
    user_form = UserForm(instance=request.user)
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')

    else:
        profile_form = UserProfileForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'core/profile_edit.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('profile')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'core/change_password.html', {'form': form})






# from django.core.cache import cache
# from django.urls import reverse
# from django.shortcuts import render, redirect
# from django.contrib.auth import login, authenticate, logout
# from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth import update_session_auth_hash
# from django.contrib import messages
# from django.views.decorators.cache import cache_page

# from .forms import UserProfileForm, UserRegistrationForm, UserForm
# from products.models import Product, Category
# from .models import UserProfile

# @cache_page(60 * 15)  # Cache for 15 minutes
# def about(request):
#     return render(request, 'core/about.html')

# @cache_page(60 * 5)  # Cache for 5 minutes
# def home(request):
#     category_id = request.GET.get('category')

#     # Try to get cached products based on category filter
#     cache_key = f'products_category_{category_id}' if category_id else 'products_all'
#     products = cache.get(cache_key)
    
#     if not products:
#         categories = Category.objects.all()
#         if category_id:
#             try:
#                 category = Category.objects.get(id=category_id)
#                 products = Product.objects.filter(category=category)
#             except Category.DoesNotExist:
#                 products = Product.objects.all()
#         else:
#             products = Product.objects.all()
        
#         cache.set(cache_key, products, 300)  # Cache for 5 minutes

#     context = {
#         'categories': Category.objects.all(),
#         'products': products,
#     }
#     return render(request, 'core/home.html', context)

# def register(request):
#     if request.method == 'POST':
#         form = UserRegistrationForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.set_password(form.cleaned_data['password'])
#             user.save()
#             login(request, user)
#             return redirect('products:list')
#     else:
#         form = UserRegistrationForm()
    
#     return render(request, 'core/register.html', {'form': form})

# def user_login(request):
#     if request.method == 'POST':
#         form = AuthenticationForm(data=request.POST)
#         if form.is_valid():
#             user = form.get_user()
#             login(request, user)
#             return redirect('products:list')
#     else:
#         form = AuthenticationForm()
#     return render(request, 'core/login.html', {'form': form})

# def logout_view(request):
#     logout(request)
#     return redirect('home')

# @login_required
# def profile_view(request):
#     user_form = UserForm(instance=request.user)
#     profile, created = UserProfile.objects.get_or_create(user=request.user)
#     profile_form = UserProfileForm(request.POST, instance=profile)

#     if request.method == 'POST':
#         user_form = UserForm(request.POST, instance=request.user)
#         profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)

#         if user_form.is_valid() and profile_form.is_valid():
#             user_form.save()
#             profile_form.save()
#             return redirect('profile')

#     context = {
#         'user_form': user_form,
#         'profile_form': profile_form,
#     }
#     return render(request, 'core/profile.html', context)

# @login_required
# def profile_edit(request):
#     user_form = UserForm(instance=request.user)
#     profile, created = UserProfile.objects.get_or_create(user=request.user)

#     if request.method == 'POST':
#         user_form = UserForm(request.POST, instance=request.user)
#         profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
#         if user_form.is_valid() and profile_form.is_valid():
#             user_form.save()
#             profile_form.save()
#             return redirect('profile')
#     else:
#         profile_form = UserProfileForm(instance=profile)

#     context = {
#         'user_form': user_form,
#         'profile_form': profile_form,
#     }
#     return render(request, 'core/profile_edit.html', context)

# @login_required
# def change_password(request):
#     if request.method == 'POST':
#         form = PasswordChangeForm(user=request.user, data=request.POST)
#         if form.is_valid():
#             user = form.save()
#             update_session_auth_hash(request, user)
#             return redirect('profile')
#     else:
#         form = PasswordChangeForm(user=request.user)

#     return render(request, 'core/change_password.html', {'form': form})
