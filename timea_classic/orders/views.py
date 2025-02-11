import json
import requests
from django.conf import settings
from django.db import transaction
from django.contrib import messages
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
    cart = request.user.cart  # Ensure this is correct for your app
    if not cart.items.exists():  # Check if cart is empty
        return redirect('cart:view')  # Adjust 'cart:view' to your actual cart view

    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address')
        phone_number = request.POST.get('phone_number')

        selected_cart_items = request.POST.getlist('cart_items')  # List of selected cart item IDs

        # Ensure selected_cart_items is a list of integers
        selected_cart_item_ids = [int(item_id) for item_id in selected_cart_items]

        # Use a transaction to ensure atomicity
        with transaction.atomic():
            # Create the Order
            order = Order.objects.create(
                user=request.user,
                shipping_address=shipping_address,
                phone_number=phone_number,
                status='Pending'
            )

            # Track cart items to remove after order creation
            cart_items_to_remove = []

            # Add selected items from cart to the order
            for item in cart.items.filter(id__in=selected_cart_item_ids):
                price = item.product.price if item.product else item.variant.price
                name = item.product.name if item.product else f"{item.variant.product.name} - {item.variant.color_name}"

                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    quantity=item.quantity,
                    price=price
                )
                cart_items_to_remove.append(item.id)

            # Remove only the ordered items from the cart
            CartItem.objects.filter(id__in=cart_items_to_remove).delete()

        return redirect('orders:order_detail', order_id=order.id)

    # Render the order creation form for GET requests
    return render(request, 'orders/create_order.html', {'cart': cart})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    context = {'order': order}
    return render(request, 'orders/order_detail.html', context)  # No automatic redirect


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
        return redirect('orders:payment_waiting', order_id=order.id)  # ✅ Use the correct name

    messages.error(request, response_data.get("errorMessage", "Payment initiation failed."))
    return redirect('orders:order_detail', order_id=order.id)


def stk_push_payment(order):
    """Function to initiate M-Pesa STK Push"""
    phone_number = order.phone_number
    amount = order.total_price  # Or any amount you want to charge

    url = "http://127.0.0.1:8000/daraja/stk_push/"  # Your local or deployed endpoint
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

        if result_code == 0:  # Payment successful
            order.payment_status = "Paid"
            order.save()
            return JsonResponse({"message": "Payment successful"}, status=200)

        else:  # Payment failed
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
    # Fetch the order
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.payment_status == "Paid":
        return render(request, 'orders/payment_success.html', {'order': order})

    # If it's pending, update to paid
    if order.payment_status == "Pending":
        order.payment_status = "Paid"
        order.save()

    return render(request, 'orders/payment_success.html', {'order': order})


def payment_failed(request):
    return render(request, 'orders/payment_failed.html')