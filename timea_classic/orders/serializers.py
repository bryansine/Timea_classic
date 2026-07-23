from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'status', 'payment_status', 'mpesa_checkout_id', 'phone_number', 'shipping_cost', 'created_at']