import base64
import datetime
import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth

def get_mpesa_access_token():
    """Generate and return M-Pesa access token."""
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET

    response = requests.get(url, auth=HTTPBasicAuth(consumer_key, consumer_secret))

    if response.status_code == 200:
        access_token = response.json().get("access_token")
        return access_token
    else:
        raise Exception("Failed to fetch access token. Check your credentials.")

def get_timestamp():
    """Generate the current timestamp in the required format YYYYMMDDHHMMSS."""
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def generate_password():
    """Generate the STK push password using BusinessShortCode, PassKey, and Timestamp."""
    timestamp = get_timestamp()
    data = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    return base64.b64encode(data.encode()).decode()
