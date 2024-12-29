from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/')
    featured = models.BooleanField(default=False)
    brand = models.CharField(max_length=50, default='Unknown')
    stock_quantity = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def is_in_stock(self):
        return self.stock_quantity > 0

    def get_absolute_url(self):
        return f"/products/{self.id}/"

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
