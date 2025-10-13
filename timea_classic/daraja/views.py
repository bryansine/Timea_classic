import json
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import get_mpesa_access_token, get_timestamp, generate_password

def mpesa_token_view(request):
    token = get_mpesa_access_token()
    return JsonResponse({"access_token": token})

@csrf_exempt
def stk_push(request):
    if request.method == "POST":
        phone_number = request.POST.get("phone_number") 
        amount = request.POST.get("amount")

        access_token = get_mpesa_access_token()
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
            "PartyA": phone_number, 
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": settings.MPESA_CALLBACK_URL,
            "AccountReference": "Timea Classic",
            "TransactionDesc": "Payment for Order",
        }

        response = requests.post(endpoint, json=payload, headers=headers)

        return JsonResponse(response.json())

    return JsonResponse({"error": "Invalid request"}, status=400)
