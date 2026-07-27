from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from products.models import Product, ProductVariant

from django.db import models
from django.utils import timezone
from tenancy.models import Tenant 


class Coupon(models.Model):
    DISCOUNT_TYPES = (
        ('percentage', 'Percentage Off (%)'),
        ('fixed', 'Fixed Amount Off (KES)'),
    )

    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='coupons'
    )
    code = models.CharField(max_length=50)
    discount_type = models.CharField(
        max_length=10, 
        choices=DISCOUNT_TYPES, 
        default='percentage'
    )
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Percentage (e.g. 10.00 for 10%) or fixed KES amount"
    )
    min_purchase_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Minimum cart subtotal required to apply coupon"
    )
    max_discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Maximum cap for percentage discounts (optional)"
    )
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()
    max_uses = models.PositiveIntegerField(
        default=100, 
        help_text="Total allowed redemptions across all users"
    )
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        # Prevents duplicate codes within the SAME tenant/store,
        # but allows different stores to use the same code (e.g., WELCOME10).
        unique_together = ('tenant', 'code')

    def __str__(self):
        return f"[{self.tenant.name}] {self.code}"

    def is_valid(self, subtotal):
        """Validates if the coupon can be applied to the given subtotal."""
        now = timezone.now()
        if not self.is_active:
            return False, "This promo code is inactive."
        if now < self.valid_from or now > self.valid_to:
            return False, "This promo code has expired or is not active yet."
        if self.used_count >= self.max_uses:
            return False, "This promo code has reached its maximum redemptions."
        if subtotal < self.min_purchase_amount:
            return False, f"Minimum purchase of KES {self.min_purchase_amount:,.2f} required."
        return True, "Valid"

    def calculate_discount(self, subtotal):
        """Calculates discount amount without exceeding the subtotal."""
        subtotal = float(subtotal)
        value = float(self.discount_value)

        if self.discount_type == 'percentage':
            discount = (value / 100.0) * subtotal
            if self.max_discount_amount and discount > float(self.max_discount_amount):
                discount = float(self.max_discount_amount)
        else:
            discount = value

        # Discount cannot exceed the subtotal
        return min(discount, subtotal)

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
    
    tenant = models.ForeignKey(
        'tenancy.Tenant', 
        on_delete=models.CASCADE, 
        related_name='orders', 
        null=True, 
        blank=True
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    mpesa_checkout_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
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
    
    # COUPON TRACKING
    subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Cart total before discount"
    )
    discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Amount deducted via coupon"
    )
    coupon = models.ForeignKey(
        Coupon, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='orders'
    )
    
    def __str__(self):
        return f"Order #{self.id} - {self.status}"

    @property
    def total_price(self):
        base_amount = self.subtotal if self.subtotal > 0 else self.subtotal_price
        payable = (base_amount - self.discount_amount) + self.shipping_cost
        return max(0.00, payable)

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
    
