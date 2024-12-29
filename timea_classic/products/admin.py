from django.contrib import admin
from .models import Product, Category, ProductVariant

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock_quantity', 'is_in_stock')
    list_filter = ('category', 'featured')
    search_fields = ('name', 'category__name')
    list_editable = ('stock_quantity',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'color_name', 'stock_quantity', 'is_in_stock')
    list_filter = ('color_name',)
    search_fields = ('product__name', 'color_name')
