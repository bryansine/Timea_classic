from django.test import TestCase
from products.models import Product, ProductVariant, Category

class ProductModelUnitTest(TestCase):

    def setUp(self):
        """Set up standard test data matching the actual database constraints."""
        # 1. Create Category
        self.category = Category.objects.create(name="Baby Clothes")

        # 2. Create Product with required category and stock_quantity
        self.product = Product.objects.create(
            name="Classic Baby Romper",
            description="A beautiful cotton romper for newborns.",
            category=self.category,
            price=1500.00,
            stock_quantity=10,
            image="dummy_main.jpg"
        )
        
        # 3. Create ProductVariants using your exact field names
        self.variant_blue = ProductVariant.objects.create(
            product=self.product,
            color_name="Blue",
            price=1500.00,
            stock_quantity=5,
            image="dummy_variant_blue.jpg"
        )
        self.variant_pink = ProductVariant.objects.create(
            product=self.product,
            color_name="Pink",
            price=1600.00,
            stock_quantity=0, # Out of stock
            image="dummy_variant_pink.jpg"
        )

    def test_product_creation(self):
        """Test that a product is correctly created with its base fields."""
        self.assertEqual(self.product.name, "Classic Baby Romper")
        self.assertEqual(str(self.product), "Classic Baby Romper")
        self.assertTrue(self.product.is_in_stock())

    def test_variant_associations(self):
        """Test that variants are correctly linked and match their stock logic."""
        self.assertEqual(self.product.variants.count(), 2)
        self.assertEqual(str(self.variant_blue), "Classic Baby Romper - Blue")
        
        # Test your model's stock checking method
        self.assertTrue(self.variant_blue.is_in_stock())
        self.assertFalse(self.variant_pink.is_in_stock())