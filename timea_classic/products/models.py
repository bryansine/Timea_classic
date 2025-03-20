from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from datetime import datetime

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Discounted price, if applicable.")
    on_offer = models.BooleanField(default=False, help_text="Is this product on offer?")
    flash_sale = models.BooleanField(default=False, help_text="Is this product in a flash sale?")
    expiry_time = models.DateTimeField(null=True, blank=True, help_text="Flash sale expiration time.")
    image = models.ImageField(upload_to='product_images/')
    featured = models.BooleanField(default=False)
    brand = models.CharField(max_length=50, default='Unknown')
    stock_quantity = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    #new field
    tags = models.CharField(max_length=255, blank=True, null=True)


    def __str__(self):
        return self.name
    
    def is_in_stock(self):
        return self.stock_quantity > 0

    def get_absolute_url(self):
        return f"/products/{self.id}/"

    def is_flash_sale_active(self):
        """ Check if the flash sale is active """
        if self.flash_sale and self.expiry_time:
            return datetime.now() < self.expiry_time
        return False

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Product"
        verbose_name_plural = "Products"

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)
    color_name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='product_variants/')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    stock_quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.color_name}"

    def is_in_stock(self):
        return self.stock_quantity > 0

# 🚀 CACHE INVALIDATION WHEN PRODUCTS CHANGE
@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def clear_product_cache(sender, instance, **kwargs):
    """ Clears product-related cache when a product is added, updated, or deleted. """
    cache.delete("product_list_all")
    if instance.category:
        cache.delete(f"product_list_{instance.category.id}")
    cache.delete(f"product_{instance.id}")