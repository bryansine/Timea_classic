import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from orders.models import Order
from orders.views import stk_push_payment

class MpesaCallbackIntegrationTest(TestCase):

    def setUp(self):
        """Set up standard user, order, and client data before each test."""
        self.client = Client()
        
        # 1. Create a dummy user
        self.user = User.objects.create_user(username="customer1", password="securepassword123")
        
        # 2. Define a mock Safaricom Checkout Request ID
        self.checkout_id = "ws_CO_15072026_XYZ"
        
        # 3. Create a pending order with our checkout ID linked
        self.order = Order.objects.create(
            user=self.user,
            status='Pending',
            payment_status='Pending',
            mpesa_checkout_id=self.checkout_id,
            first_name="Bryan",
            last_name="Sine",
            phone_number="254712345678",
            shipping_cost=250.00
        )
        
        # For testing total price in our initiation function:
        if not hasattr(self.order, 'total_price'):
            self.order.total_price = 1000.00
        
        # 4. Resolve the URL (using the correct namespace)
        self.callback_url = reverse('orders:mpesa_callback')

    @patch('orders.views.requests.post')
    def test_stk_push_payment_sends_correct_payload(self, mock_post):
        """Test that stk_push_payment correctly formats and sends data to Daraja."""
        
        # 1. Mock the API response from your Daraja view
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "MerchantRequestID": "12345-6789-10",
            "CheckoutRequestID": self.checkout_id,
            "ResponseCode": "0",
            "ResponseDescription": "Success. Request accepted for processing"
        }
        mock_post.return_value = mock_response

        # 2. Call the function with our test order
        result = stk_push_payment(self.order)

        # Check that the network request was actually made once
        mock_post.assert_called_once()
        
        # Check that the correct URL and payload data were sent
        called_args, called_kwargs = mock_post.call_args
        self.assertEqual(called_args[0], "http://127.0.0.1:8000/daraja/stk_push/")
        self.assertEqual(called_kwargs['data']['phone_number'], "254712345678")
        self.assertEqual(called_kwargs['data']['amount'], self.order.total_price)

        # Check that the function returns the expected JSON response dictionary
        self.assertEqual(result["ResponseCode"], "0")
        self.assertEqual(result["CheckoutRequestID"], self.checkout_id)

    def test_successful_mpesa_callback_updates_to_paid(self):
        """Test that a ResultCode of 0 updates the order payment_status to Paid."""
        
        successful_payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "12345-6789-10",
                    "CheckoutRequestID": self.checkout_id,
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 1.00},
                            {"Name": "MpesaReceiptNumber", "Value": "RAG7UX89LP"},
                            {"Name": "TransactionDate", "Value": 20260715180000},
                            {"Name": "PhoneNumber", "Value": 254712345678}
                        ]
                    }
                }
            }
        }

        response = self.client.post(
            self.callback_url,
            data=json.dumps(successful_payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("message"), "Payment successful")

        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, "Paid")

    def test_failed_mpesa_callback_updates_to_failed(self):
        """Test that a non-zero ResultCode updates the order payment_status to Failed."""
        
        failed_payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "12345-6789-10",
                    "CheckoutRequestID": self.checkout_id,
                    "ResultCode": 1032,
                    "ResultDesc": "Request cancelled by user.",
                }
            }
        }

        response = self.client.post(
            self.callback_url,
            data=json.dumps(failed_payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("error"), "Payment failed")

        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, "Failed")