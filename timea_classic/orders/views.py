from django.shortcuts import render, get_object_or_404, redirect
from .models import Order, OrderItem
from django.contrib.auth.decorators import login_required
from cart.models import Cart, CartItem
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
import json


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

    # If payment status is Pending, show the "Place Order & Pay" button
    if order.payment_status == 'Pending':
        # Logic to initiate M-Pesa payment if clicked
        return redirect('orders:initiate_payment', order_id=order.id)

    context = {'order': order}
    return render(request, 'orders/order_detail.html', context)

@login_required
def create_order_from_cart(request):
    cart = request.user.cart 
    if not cart.items.exists():
        return redirect('cart:view')
    
    return render(request, 'orders/create_order.html', {'cart': cart})


import base64
import requests
from django.conf import settings
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse
from .models import Order

# M-Pesa credentials from settings
MPESA_LIPA_NA_MPESA_SHORTCODE = settings.MPESA_SHORTCODE
MPESA_LIPA_NA_MPESA_PASSKEY = settings.MPESA_PASSKEY
MPESA_LIPA_NA_MPESA_CONSUMER_KEY = settings.MPESA_CONSUMER_KEY
MPESA_LIPA_NA_MPESA_CONSUMER_SECRET = settings.MPESA_CONSUMER_SECRET

def get_mpesa_access_token():
    """
    Function to get M-Pesa access token from Safaricom
    """
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    
    # Combine Consumer Key and Secret in the required format for Basic Authentication
    credentials = f'{MPESA_LIPA_NA_MPESA_CONSUMER_KEY}:{MPESA_LIPA_NA_MPESA_CONSUMER_SECRET}'
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(credentials.encode()).decode('utf-8')
    }
    
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        json_response = response.json()
        return json_response.get('access_token')
    else:
        return None

def initiate_payment(request, order_id):
    """
    Function to initiate M-Pesa payment via STK Push
    """
    # Get the order object based on the order_id
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Ensure payment status is Pending
    if order.payment_status != 'Pending':
        return HttpResponse("Payment has already been made.")

    # Get the access token for authorization
    access_token = get_mpesa_access_token()
    if not access_token:
        return HttpResponse("Failed to retrieve access token from M-Pesa. Please try again later.")
    
    # M-Pesa STK Push request headers
    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json"
    }
    
    # Prepare the STK Push payload
    payload = {
        "BusinessShortcode": MPESA_LIPA_NA_MPESA_SHORTCODE,
        "LipaNaMpesaOnlineShortcode": MPESA_LIPA_NA_MPESA_SHORTCODE,
        "LipaNaMpesaOnlineShortcodePasskey": MPESA_LIPA_NA_MPESA_PASSKEY,
        "PhoneNumber": order.phone_number,  # From the order's phone number
        "Amount": order.total_price,  # Amount to pay
        "AccountReference": str(order.id),  # The order id
        "TransactionDesc": f"Payment for Order {order.id}"
    }
    
    # URL for initiating the STK Push request
    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    
    # Send the STK Push request to Safaricom's API
    response = requests.post(url, json=payload, headers=headers)

    # Handle the response
    if response.status_code == 200:
        return redirect('orders:mpesa_callback', order_id=order.id)
    else:
        return HttpResponse(f"Payment initiation failed: {response.text}")



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


@login_required
def payment_success(request, order_id):
    # Fetch the order
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.payment_status != "Pending":
        return HttpResponse("Invalid payment status.")

    # Simulate successful payment
    order.payment_status = "Paid"
    order.save()

    return render(request, 'orders/payment_success.html', {'order': order})





@csrf_exempt
def mpesa_callback(request):
    # Safaricom returns the response in JSON format
    data = json.loads(request.body)

    # Extract the OrderID from the callback data
    order_id = data.get("OrderID")
    
    # Ensure the order exists and belongs to the user
    order = get_object_or_404(Order, id=order_id)

    # Check the result code returned by Safaricom
    if data.get("ResultCode") == "0":
        # Successful payment
        order.payment_status = "Paid"
        order.save()

        # Redirect to the payment success page
        return redirect('orders:payment_success', order_id=order.id)
    else:
        # Payment failure
        order.payment_status = "Failed"
        order.save()

        # Return failure message
        return HttpResponse("Payment Failed", status=400)




def get_mpesa_access_token():
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    
    # Ensure that these keys are defined in settings.py
    lipa_key = settings.MPESA_CONSUMER_SECRET 
    lipa_secret = settings.MPESA_CONSUMER_KEY

    # Use the settings values to create the Authorization header
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(f'{lipa_key}:{lipa_secret}'.encode()).decode('utf-8')
    }

    # Send the request to get the access token
    response = requests.get(api_url, headers=headers)
    json_response = response.json()

    # Return the access token from the response
    return json_response.get('access_token')  
