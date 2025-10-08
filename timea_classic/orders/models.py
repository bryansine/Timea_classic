from django.db import models
from django.contrib.auth.models import User
from products.models import Product, ProductVariant
from django.utils import timezone
from decimal import Decimal


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    buy_now_product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    shipping_address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    order_notes = models.TextField(blank=True, null=True)

    # Shipping Fields
    shipping_option_name = models.CharField(max_length=255, blank=True, null=True)
    shipping_option_description = models.TextField(blank=True, null=True)
    shipping_option_delivery_time = models.CharField(max_length=100, blank=True, null=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # More Shipping Fields
    email = models.EmailField(default='example@example.com')
    first_name = models.CharField(max_length=100, default='First Name')
    last_name = models.CharField(max_length=100, default='Last Name')
    address = models.TextField(default='Unknown Address')
    apartment = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, default='00000')
    town_city = models.CharField(max_length=100, default='Nairobi')
    closest_town = models.CharField(max_length=100, default='Nairobi') 
    receive_emails = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Order #{self.id} - {self.status}"

    @property
    def total_price(self):
        # The total price is now simply the subtotal plus shipping cost
        return self.subtotal_price + self.shipping_cost

    @property
    def subtotal_price(self):
        return sum(item.price * item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        if self.product:
            return f"{self.product.name} - {self.quantity} pcs"
        elif self.variant:
            return f"{self.variant.product.name} ({self.variant.color_name}) - {self.quantity} pcs"
        else:
            return f"Unknown Item - {self.quantity} pcs"

    @property
    def total_price(self):
        return self.price * self.quantity