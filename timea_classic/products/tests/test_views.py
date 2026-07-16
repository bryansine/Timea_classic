from django.test import TestCase, Client
from django.urls import reverse
from products.models import Product, Category

class ProductViewsIntegrationTest(TestCase):

    def setUp(self):
        """Create mock categories and products for testing views."""
        self.client = Client()
        
        # Create Categories
        self.clothes = Category.objects.create(name="Clothes")
        self.toys = Category.objects.create(name="Toys")

        # Create Products assigned to different categories
        self.romper = Product.objects.create(
            name="Baby Romper", category=self.clothes, price=1200.00, image="r.jpg"
        )
        self.socks = Product.objects.create(
            name="Warm Baby Socks", category=self.clothes, price=300.00, image="s.jpg"
        )
        self.teddy = Product.objects.create(
            name="Teddy Bear", category=self.toys, price=2000.00, image="t.jpg"
        )

        # Set up URLs using the correct 'products' namespace
        self.list_url = reverse('products:list') 
        self.search_url = reverse('products:search')
        self.category_url = reverse('products:category', args=[self.clothes.id])

    def test_product_list_view_status_code(self):
        """Ensure the main products page renders successfully."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

    def test_category_page_renders_filtered_products(self):
        """Test that the category view returns only products of that category."""
        response = self.client.get(self.category_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Baby Romper")
        self.assertContains(response, "Warm Baby Socks")
        self.assertNotContains(response, "Teddy Bear")

    def test_search_functionality(self):
        """Test that searching via your product_search view returns matches."""
        response = self.client.get(self.search_url, {'q': 'Teddy'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Teddy Bear")
        self.assertNotContains(response, "Baby Romper")

    def test_pagination_logic(self):
        """Test that list view splits products into separate pages correctly."""
        for i in range(30):
            Product.objects.create(
                name=f"Extra Product {i}", category=self.clothes, price=500.00, image="ex.jpg"
            )

        # Request page 1 of the list view
        response = self.client.get(self.list_url)
        
        # Verify the paginated context is returned under the 'products' key
        self.assertTrue('products' in response.context)
        
        # Page 1 should contain exactly 24 items (your Paginator limit)
        self.assertEqual(len(response.context['products']), 24)

        # Request page 2 (total 33 products: 24 on page 1, 9 remaining on page 2)
        response_page_2 = self.client.get(self.list_url, {'page': 2})
        self.assertEqual(response_page_2.status_code, 200)
        self.assertEqual(len(response_page_2.context['products']), 9)