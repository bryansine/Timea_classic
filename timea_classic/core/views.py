from .models import Promotion
from .models import UserProfile
from django.urls import reverse
from django.utils import timezone
from .forms import UserProfileForm
# from django.core.cache import cache
from django.contrib import messages
from .models import NewsletterSubscriber
from django.shortcuts import render, redirect
from products.models import Category, Product
from .forms import UserRegistrationForm, UserForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required



def about(request):
    return render(request, 'core/about.html')


def contact(request):
    return render(request, 'core/contact_us.html')


def refund(request):
    return render(request, 'core/refund.html')



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

    products = products[:8]

    # Fetch recent products
    recent_products = Product.objects.order_by('-created_at')[:8]

    # Fetch discounted products
    discounted_products = Product.objects.filter(on_offer=True) | Product.objects.filter(discount_price__isnull=False)

    # Fetch flash sale products
    flash_sale_products = Product.objects.filter(flash_sale=True, expiry_time__gt=timezone.now())

    # Get the expiry time for the flash sale
    expiry_time = None
    if flash_sale_products.exists():
        expiry_time = flash_sale_products.first().expiry_time

    # Fetch banners and pop-ups
    now = timezone.now()
    banner_locations = {
        'top_home': 'top_banners',
        'middle_home': 'middle_banners',
        'bottom_home': 'bottom_banners',
    }
      # banners logic
    banners = {}
    for location, context_name in banner_locations.items():
        banners[context_name] = Promotion.objects.filter(
            promotion_type='banner',
            is_active=True,
            start_date__lte=now,
            end_date__gte=now,
            location=location
        )
        # popup logic
    popups = Promotion.objects.filter(
        promotion_type='popup',
        is_active=True,
        start_date__lte=now,
        end_date__gte=now,
        location='homepage',
    )

    context = {
        'categories': categories,
        'products': products,
        'recent_products': recent_products,
        'discounted_products': discounted_products,
        'flash_sale_products': flash_sale_products,
        'expiry_time': expiry_time,
        **banners,
        # 'top_banners': <QuerySet of top banners>,
        # 'middle_banners': <QuerySet of middle banners>,
        # 'bottom_banners': <QuerySet of bottom banners>,
        'popups': popups,
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
            
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            
            return redirect('products:list')
    else:
        form = UserRegistrationForm()
        
    next_url = request.GET.get('next')
    return render(request, 'core/register.html', {'form': form, 'next': next_url})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            
            return redirect('products:list')
    else:
        form = AuthenticationForm()
        
    next_url = request.GET.get('next')
    return render(request, 'core/login.html', {'form': form, 'next': next_url})


def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        if NewsletterSubscriber.objects.filter(email=email).exists():
            messages.info(request, 'You are already subscribed!')
        else:
            NewsletterSubscriber.objects.create(email=email)
            messages.success(request, 'Thanks for subscribing!')

    return redirect(request.META.get('HTTP_REFERER', '/'))

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