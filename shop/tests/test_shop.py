from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from shop.models import Product

class ShopTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("buyer", "b@ex.com", "Pass123!")
        self.prod = Product.objects.create(name="P1", slug="p1", price_cents=1000, stripe_price_id="price_x")

    def test_product_list(self):
        c = Client()
        res = c.get(reverse("product_list"))
        self.assertContains(res, "P1")

    def test_checkout_requires_login(self):
        c = Client()
        res = c.get(reverse("create_checkout_session", args=["p1"]))
        self.assertEqual(res.status_code, 302)
