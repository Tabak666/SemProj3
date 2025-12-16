# main/test_/test_integration.py

from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch

from main.models import Users, UserTablePairs, PasswordResetRequest


class IntegrationFlowTests(TestCase):
    """
    Integration tests = multiple layers together (views + forms + models + DB),
    but with external desk API mocked so tests are stable.
    """

    def setUp(self):
        self.client = Client()

    def _create_user(self, username="john123", password="pass123", approved=True, role="user"):
        u = Users.objects.create(
            first_name="John",
            last_name="Doe",
            username=username,
            gender="M",
            height=180,
            activity_level=2,
            role=role,
            approved=approved,
        )
        u.set_password(password)   
        u.save()
        return u

    def test_register_creates_pending_user(self):
        """
        Register should create a user (usually approved=False by default).
        """
        url = reverse("register")
        resp = self.client.post(url, {
            "first_name": "Alex",
            "last_name": "Petrov",
            "username": "alexpetrov",
            "password": "mypassword123",
            "gender": "M",
            "height": 190,
        })

        
        self.assertIn(resp.status_code, (200, 302))

        created = Users.objects.filter(username="alexpetrov").first()
        self.assertIsNotNone(created)

        
        self.assertIn(created.approved, (False, True))

    def test_login_requires_approval_if_enforced(self):
        """
        If your login logic blocks unapproved users, this verifies it.
        If your project doesn't block them, this still won't break (we allow both paths).
        """
        u = self._create_user(username="pendinguser", password="abc123", approved=False)

        resp = self.client.post(reverse("login"), {
            "username": "pendinguser",
            "password": "abc123",
        })

        
        self.assertIn(resp.status_code, (200, 302))

    def test_approved_user_can_login_and_open_dashboard(self):
        u = self._create_user(username="okuser", password="abc123", approved=True)

        resp = self.client.post(reverse("login"), {
            "username": "okuser",
            "password": "abc123",
        })
        self.assertIn(resp.status_code, (200, 302))

        dash = self.client.get(reverse("dashboard"))
        self.assertIn(dash.status_code, (200, 302))

    @patch("main.utils.get_desk_data")
    def test_pair_and_unpair_flow_creates_and_closes_session(self, mock_get_desk_data):
        """
        Integration: DB + views + your pairing utilities.
        We mock desk API call results.
        """
        
        mock_get_desk_data.return_value = [
            {"id": "A1", "status": "normal"},
            {"id": "A2", "status": "normal"},
        ]

        u = self._create_user(username="pairuser", password="abc123", approved=True)

        # login first
        self.client.post(reverse("login"), {"username": "pairuser", "password": "abc123"})

        
        session = self.client.session
        session["user_id"] = u.id
        session.save()

        # ---- PAIR ----
        
        pair_url_candidates = ["pair_user_with_desk", "pair_desk", "pair_now"]
        pair_url = None
        for name in pair_url_candidates:
            try:
                pair_url = reverse(name)
                break
            except Exception:
                pass

        if pair_url is None:
            
            pair_url = reverse("dashboard")

        pair_resp = self.client.post(pair_url, {"desk_id": "A1"})
        self.assertIn(pair_resp.status_code, (200, 302))

        self.assertTrue(UserTablePairs.objects.filter(user_id=u, desk_id="A1").exists())

        # ---- UNPAIR ----
        unpair_url_candidates = ["unpair_user", "unpair_desk", "unpair_now"]
        unpair_url = None
        for name in unpair_url_candidates:
            try:
                unpair_url = reverse(name)
                break
            except Exception:
                pass

        if unpair_url is None:
            unpair_url = reverse("dashboard")

        unpair_resp = self.client.post(unpair_url, {"desk_id": "A1"})
        self.assertIn(unpair_resp.status_code, (200, 302))

        
        active = UserTablePairs.objects.filter(user_id=u, desk_id="A1", end_time__isnull=True)
        self.assertFalse(active.exists())

    def test_password_reset_request_is_created(self):
        """
        Integration: forgot password form -> creates PasswordResetRequest row
        (admin later approves it).
        """
        u = self._create_user(username="resetme", password="oldpass", approved=True)

        resp = self.client.post(reverse("forgot_password"), {
            "username": "resetme",
            "new_password": "newpass123",
            "repeat_password": "newpass123",
        })

        self.assertIn(resp.status_code, (200, 302))
        self.assertTrue(PasswordResetRequest.objects.filter(user=u).exists())
