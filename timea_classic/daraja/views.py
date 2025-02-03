import json
import requests
from django.conf import settings
from django.http import JsonResponse
from .utils import get_mpesa_access_token, get_timestamp, generate_password
from django.views.decorators.csrf import csrf_exempt

def mpesa_token_view(request):
    # Get the access token
    token = get_mpesa_access_token()
    return JsonResponse({"access_token": token})

@csrf_exempt
def stk_push(request):
    if request.method == "POST":
        phone_number = request.POST.get("phone_number")  # Get user phone number
        amount = request.POST.get("amount")  # Get amount to pay

        # Use your credentials from the sandbox
        access_token = get_mpesa_access_token()  # Corrected function name here
        endpoint = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": generate_password(),
            "Timestamp": get_timestamp(),
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,  # Customer phone number
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": settings.MPESA_CALLBACK_URL,
            "AccountReference": "Timea Classic",
            "TransactionDesc": "Payment for Order",
        }

        # Sending the payment request to Safaricom's STK Push API
        response = requests.post(endpoint, json=payload, headers=headers)

        # Returning the response from the STK Push request as a JSON response
        return JsonResponse(response.json())

    return JsonResponse({"error": "Invalid request"}, status=400)
