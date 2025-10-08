import json
import requests
from decimal import Decimal
from django.conf import settings
from core.models import Promotion
from django.utils import timezone
from django.db import transaction
from products.models import Product
from django.contrib import messages
from django.core.cache import cache
from .models import Order, OrderItem
from cart.models import Cart, CartItem
from daraja.utils import get_mpesa_access_token
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from daraja.utils import get_mpesa_access_token, generate_password, get_timestamp

    
@login_required
def create_order(request):
    """will handle order creation for both cart checkout and Buy It Now purchases."""
    cart = request.user.cart
    buy_now_product_data = request.session.get('buy_now_product', None)

    if not cart.items.exists() and not buy_now_product_data:
        return redirect('cart:view')

    buy_now_product = None
    if buy_now_product_data:
        buy_now_product = get_object_or_404(Product, id=buy_now_product_data['id'])

    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address')
        phone_number = request.POST.get('phone_number')
        selected_cart_items = request.POST.getlist('cart_items')
        shipping_option = request.POST.get('shipping_option')

        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        apartment = request.POST.get('apartment')
        zip_code = request.POST.get('zip_code')
        town_city = request.POST.get('town_city')
        closest_town = request.POST.get('closest_town')
        receive_emails = request.POST.get('receive_emails') == 'on'
        order_notes = request.POST.get('order_notes')

        shipping_option_name = None
        shipping_option_description = None
        shipping_option_delivery_time = None
        shipping_cost = 0.00

        if shipping_option == 'pickup':
            shipping_option_name = 'Pick up from the Warehouse'
            shipping_option_description = 'To pick up Saturday 8am-5pm'
            shipping_option_delivery_time = 'Saturday'
            shipping_cost = 0.00
        elif shipping_option == 'delivery':
            shipping_option_name = 'Our own Delivery'
            shipping_option_description = 'We will deliver to your home / office'
            shipping_option_delivery_time = 'Next Day'
            shipping_cost = 250.00
        elif shipping_option == 'courier':
            shipping_option_name = 'Outside Nairobi by Courier'
            shipping_option_description = 'Courier will deliver to your town (doorstep or pick)'
            shipping_option_delivery_time = '2-3 Days'
            shipping_cost = 500.00

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                shipping_address=shipping_address,
                phone_number=phone_number,
                status='Pending',
                buy_now_product=buy_now_product,
                shipping_option_name=shipping_option_name,
                shipping_option_description=shipping_option_description,
                shipping_option_delivery_time=shipping_option_delivery_time,
                shipping_cost=shipping_cost,
                email=email,
                first_name=first_name,
                last_name=last_name,
                address=address,
                apartment=apartment,
                zip_code=zip_code,
                town_city=town_city,
                closest_town=closest_town,
                receive_emails=receive_emails,
                order_notes=order_notes,
            )

            if buy_now_product:
                OrderItem.objects.create(
                    order=order,
                    product=buy_now_product,
                    quantity=1,
                    price=buy_now_product.price
                )
                del request.session['buy_now_product']
            else:
                selected_cart_item_ids = [int(item_id) for item_id in selected_cart_items]

                for item in cart.items.filter(id__in=selected_cart_item_ids):
                    price = item.product.price if item.product else item.variant.price
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        variant=item.variant,
                        quantity=item.quantity,
                        price=price
                    )

        return redirect('orders:order_detail', order_id=order.id)

    now = timezone.now()
    popups = Promotion.objects.filter(
        promotion_type='popup',
        is_active=True,
        start_date__lte=now,
        end_date__gte=now,
        location='create_order_page',
    )

    return render(request, 'orders/create_order.html', {
        'cart': cart,
        'buy_now_product': buy_now_product,
        'popups': popups,
    })


    
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    context = {'order': order}
    return render(request, 'orders/order_detail.html', context)


@login_required
def create_order_from_cart(request):
    cart = request.user.cart 
    if not cart.items.exists():
        return redirect('cart:view')
    
    return render(request, 'orders/create_order.html', {'cart': cart})



@login_required
def initiate_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.payment_status != 'Pending':
        messages.error(request, "Payment has already been processed.")
        return redirect('orders:order_detail', order_id=order.id)

    access_token = get_mpesa_access_token()
    if not access_token:
        messages.error(request, "Failed to retrieve M-Pesa token.")
        return redirect('orders:order_detail', order_id=order.id)

    timestamp = get_timestamp()
    password = generate_password()

    phone_number = str(order.phone_number)
    if phone_number.startswith("0"):
        phone_number = "254" + phone_number[1:]

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": float(order.total_price),
        "PartyA": phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": str(order.id),
        "TransactionDesc": f"Payment for Order {order.id}"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest", 
                             headers=headers, 
                             data=json.dumps(payload))

    response_data = response.json()

    if response.status_code == 200 and response_data.get("ResponseCode") == "0":
        order.mpesa_checkout_id = response_data["CheckoutRequestID"]
        order.payment_status = "Payment Initiated"
        order.save()
        return redirect('orders:payment_waiting', order_id=order.id)

    messages.error(request, response_data.get("errorMessage", "Payment initiation failed."))
    return redirect('orders:order_detail', order_id=order.id)


def stk_push_payment(order):
    """Function to initiate M-Pesa STK Push"""
    phone_number = order.phone_number
    amount = order.total_price 

    url = "http://127.0.0.1:8000/daraja/stk_push/"
    data = {
        "phone_number": phone_number,
        "amount": amount
    }
    
    response = requests.post(url, data=data)

    return response.json()



@csrf_exempt
def mpesa_callback(request):
    try:
        data = json.loads(request.body)
        checkout_request_id = data.get("Body", {}).get("stkCallback", {}).get("CheckoutRequestID")
        result_code = data.get("Body", {}).get("stkCallback", {}).get("ResultCode")

        if not checkout_request_id:
            return JsonResponse({"error": "Invalid callback data"}, status=400)

        order = Order.objects.filter(mpesa_checkout_id=checkout_request_id).first()
        if not order:
            return JsonResponse({"error": "Order not found"}, status=404)

        if result_code == 0:
            order.payment_status = "Paid"
            order.save()
            return JsonResponse({"message": "Payment successful"}, status=200)

        else:
            order.payment_status = "Failed"
            order.save()
            return JsonResponse({"error": "Payment failed"}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def payment_waiting(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/payment_waiting.html', {'order': order})



def check_payment_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if order.payment_status == "Paid":
        return JsonResponse({"status": "success", "message": "Payment successful."})
    elif order.payment_status == "Failed":
        return JsonResponse({"status": "failed", "message": "Payment failed."})
    else:
        return JsonResponse({"status": "pending", "message": "Payment is still processing."})



@login_required
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.payment_status == "Pending":
        order.payment_status = "Paid"
        order.save()
                
        user_cart = request.user.cart
        order_items = order.items.all()
        
        product_ids_to_remove = []
        variant_ids_to_remove = []
        
        for item in order_items:
            if item.product:
                product_ids_to_remove.append(item.product.id)
            if item.variant:
                variant_ids_to_remove.append(item.variant.id)
        
        user_cart.items.filter(product__id__in=product_ids_to_remove, variant__isnull=True).delete()
        
        user_cart.items.filter(variant__id__in=variant_ids_to_remove).delete()
        
        cache_key = f"cart_{request.user.id}"
        cache.delete(cache_key)

    return render(request, 'orders/payment_success.html', {'order': order})


@login_required
def payment_failed(request):
    return render(request, 'orders/payment_failed.html')


@login_required
def buy_now(request, product_id):
    """Handles Buy Now flow by redirecting user to order creation page with a specific product"""
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        request.session['buy_now_product'] = {
            'id': product.id,
            'name': product.name,
            'price': str(product.price),
        }
        return redirect('orders:create_order')

    return redirect('products:detail', product_id=product.id)