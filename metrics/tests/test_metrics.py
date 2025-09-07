from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch

class MetricsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("u", "u@ex.com", "Pass123!")

    def test_dashboard_requires_login(self):
        c = Client()
        res = c.get(reverse("metrics_dashboard"))
        self.assertEqual(res.status_code, 302)

    @patch("api_integration.utils.fetch_metrics", return_value=({"timestamps":[],"salinity":[],"ph":[],"pollutant_index":[]}, None))
    def test_proxy_ok(self, mock_fetch):
        c = Client()
        c.login(username="u", password="Pass123!")
        res = c.get(reverse("metrics_proxy")+"?start=2025-01-01T00:00:00&end=2025-01-02T00:00:00")
        self.assertEqual(res.status_code, 200)
