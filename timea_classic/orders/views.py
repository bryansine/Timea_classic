from django.shortcuts import render, get_object_or_404, redirect
from .models import Order, OrderItem
from django.contrib.auth.decorators import login_required
from cart.models import Cart, CartItem
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
import json
from daraja.utils import get_mpesa_access_token

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



import json
import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse
from .models import Order
from daraja.utils import get_mpesa_access_token, generate_password, get_timestamp

def initiate_payment(request, order_id):
    """
    Function to initiate M-Pesa payment via STK Push.
    """
    # Get the order object based on the order_id
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Ensure payment status is Pending
    if order.payment_status != 'Pending':
        return HttpResponse("Payment has already been made.", status=400)

    # Get the access token for authorization
    access_token = get_mpesa_access_token()
    if not access_token:
        return HttpResponse("Failed to retrieve access token from M-Pesa. Please try again later.", status=500)
    
    # Generate timestamp & password for STK push
    timestamp = get_timestamp()
    password = generate_password()

    # M-Pesa STK Push request headers
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # STK Push API endpoint
    stk_push_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    phone_number = str(order.phone_number)
    if phone_number.startswith("0"):
        phone_number = "254" + phone_number[1:]
    elif phone_number.startswith("+"):
        phone_number = phone_number[1:]

    # STK Push payload (update PhoneNumber field)
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


    # # Payload for STK Push request
    # payload = {
    #     "BusinessShortCode": settings.MPESA_SHORTCODE,  # Corrected field name
    #     "Password": password,  # Correctly generated password
    #     "Timestamp": timestamp,  # Correct timestamp format
    #     "TransactionType": "CustomerPayBillOnline",
    #     "Amount": float(order.total_price),  # Convert Decimal to float
    #     "PartyA": str(order.phone_number),  # Ensure it's a string
    #     "PartyB": settings.MPESA_SHORTCODE,  # The PayBill/Till number
    #     "PhoneNumber": str(order.phone_number),  # Ensure it's a string
    #     "CallBackURL": settings.MPESA_CALLBACK_URL,  # Use a callback URL from settings
    #     "AccountReference": str(order.id),
    #     "TransactionDesc": f"Payment for Order {order.id}"
    # }

    # Send request to M-Pesa STK Push API
    response = requests.post(stk_push_url, headers=headers, data=json.dumps(payload))

    # Return response from Safaricom API
    return JsonResponse(response.json(), status=response.status_code)

    


    
    
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






# @csrf_exempt
# def mpesa_callback(request):
#     # Safaricom returns the response in JSON format
#     data = json.loads(request.body)

#     # Extract the OrderID from the callback data
#     order_id = data.get("OrderID")
    
#     # Ensure the order exists and belongs to the user
#     order = get_object_or_404(Order, id=order_id)

#     # Check the result code returned by Safaricom
#     if data.get("ResultCode") == "0":
#         # Successful payment
#         order.payment_status = "Paid"
#         order.save()

#         # Redirect to the payment success page
#         return redirect('orders:payment_success', order_id=order.id)
#     else:
#         # Payment failure
#         order.payment_status = "Failed"
#         order.save()

#         # Return failure message
#         return HttpResponse("Payment Failed", status=400)

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Order

@csrf_exempt
def mpesa_callback(request):
    try:
        data = json.loads(request.body)

        # Extract Order ID from the callback data
        order_id = data.get("OrderID")
        order = get_object_or_404(Order, id=order_id)

        # Check payment result
        result_code = data.get("ResultCode")

        if result_code == "0":
            # Successful payment
            order.payment_status = "Paid"
            order.transaction_id = data.get("TransactionID", "N/A")  # Store M-Pesa transaction ID
            order.amount_paid = data.get("Amount", 0)  # Store paid amount
            order.phone_number = data.get("PhoneNumber", "Unknown")  # Store phone number
            order.save()

            return redirect(f'/orders/payment-success/{order.id}/')  # Redirect to success page
        
        else:
            # Payment failure
            order.payment_status = "Failed"
            order.save()

            return redirect('/orders/payment-failed/')  # Redirect to failure page

    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON format", status=400)

    except Exception as e:
        return HttpResponse(f"Error processing payment: {str(e)}", status=500)

# def payment_success(request, order_id):
#     order = get_object_or_404(Order, id=order_id)
#     return render(request, 'orders/payment_success.html', {'order': order})


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



def payment_failed(request):
    return render(request, 'orders/payment_failed.html')