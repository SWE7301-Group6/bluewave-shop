from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch
from accounts.models import UserProfile

class AccountsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("u1", "u1@example.com", "Pass123!")

    def test_register(self):
        c = Client()
        res = c.post(reverse("register"), {"username":"u2","email":"u2@ex.com","password":"Pass123!"})
        self.assertEqual(res.status_code, 302)

    def test_login_and_dashboard(self):
        c = Client()
        res = c.post(reverse("login"), {"username":"u1","password":"Pass123!"})
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse("dashboard"), res["Location"])

    @patch("api_integration.utils.issue_jwt_for_user", return_value=("token123", None, None))
    def test_api_token_request(self, mock_issue):
        c = Client()
        c.login(username="u1", password="Pass123!")
        prof, _ = UserProfile.objects.get_or_create(user=self.user)
        prof.is_researcher = True
        prof.save()
        res = c.post(reverse("request_api_token"))
        self.assertEqual(res.status_code, 302)
        prof.refresh_from_db()
        self.assertEqual(prof.api_jwt, "token123")
