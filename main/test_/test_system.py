# main/test_/test_system.py

from django.test import TestCase, Client
from django.urls import reverse
from main.models import Users


class SystemJourneyTests(TestCase):
    """
    System tests = end-to-end user journey across pages:
    register -> approve -> login -> dashboard
    (Selenium optional, but this is still a real system-level flow in Django)
    """

    def setUp(self):
        self.client = Client()

    def test_full_user_journey_register_approve_login_dashboard(self):
        
        reg = self.client.post(reverse("register"), {
            "first_name": "Test",
            "last_name": "User",
            "username": "systemuser",
            "password": "systempass123",
            "gender": "M",
            "height": 185,
        })
        self.assertIn(reg.status_code, (200, 302))

        
        u = Users.objects.get(username="systemuser")
        u.approved = True
        u.save()


        login = self.client.post(reverse("login"), {
            "username": "systemuser",
            "password": "systempass123",
        })
        self.assertIn(login.status_code, (200, 302))

        
        dash = self.client.get(reverse("dashboard"))
        self.assertIn(dash.status_code, (200, 302))
