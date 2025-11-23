# main/tests/test_all_django.py

from django.test import TestCase, Client
from django.urls import reverse, resolve
from unittest.mock import patch, mock_open
from main.models import Users, UserTablePairs, PasswordResetRequest
from main.forms import RegistrationForm, LoginForm, ForgotPasswordForm
from main.utils import get_desk_data, pair_user_with_desk, unpair_user

class MainAppTests(TestCase):

    def setUp(self):
        self.client = Client()

    # ============================================================
    # FORMS TESTS
    # ============================================================

    def test_registration_form_valid(self):
        form = RegistrationForm(data={
            "first_name": "John",
            "last_name": "Doe",
            "username": "john123",
            "password": "mypassword",
            "gender": "M",
            "height": 180
        })
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertIsNotNone(user.pk)
        self.assertNotEqual(user.password, "mypassword")

    def test_registration_form_negative_height(self):
        form = RegistrationForm(data={
            "first_name": "John",
            "last_name": "Doe",
            "username": "john123",
            "password": "pwd",
            "gender": "M",
            "height": -1
        })
        self.assertFalse(form.is_valid())
        self.assertIn("height", form.errors)

    def test_registration_form_height_too_large(self):
        form = RegistrationForm(data={
            "first_name": "John",
            "last_name": "Doe",
            "username": "john123",
            "password": "pwd",
            "gender": "M",
            "height": 500
        })
        self.assertFalse(form.is_valid())
        self.assertIn("height", form.errors)

    def test_login_form_valid(self):
        form = LoginForm(data={"username": "john", "password": "secret"})
        self.assertTrue(form.is_valid())

    def test_login_form_missing_username(self):
        form = LoginForm(data={"password": "secret"})
        self.assertFalse(form.is_valid())

    def test_forgot_password_valid(self):
        Users.objects.create(
            first_name="Test", last_name="User", username="john",
            password="xxx", gender="M", height=170
        )
        form = ForgotPasswordForm(data={
            "username": "john",
            "new_password": "123",
            "repeat_password": "123"
        })
        self.assertTrue(form.is_valid())

    def test_forgot_password_user_not_found(self):
        form = ForgotPasswordForm(data={
            "username": "ghost",
            "new_password": "a",
            "repeat_password": "a"
        })
        self.assertFalse(form.is_valid())

    def test_forgot_password_password_mismatch(self):
        Users.objects.create(
            first_name="A", last_name="B", username="john",
            password="xxx", gender="M", height=170
        )
        form = ForgotPasswordForm(data={
            "username": "john",
            "new_password": "a",
            "repeat_password": "b"
        })
        self.assertFalse(form.is_valid())

    # ============================================================
    # MODELS TESTS
    # ============================================================

    def test_user_set_password_hashes(self):
        user = Users(
            first_name="A", last_name="B", username="abc",
            password="plain", gender="M", height=170
        )
        user.set_password("newpass")
        self.assertNotEqual(user.password, "newpass")

    def test_user_table_pairs_str(self):
        user = Users.objects.create(
            first_name="A", last_name="B", username="abc",
            password="xxx", gender="M", height=170
        )
        pair = UserTablePairs.objects.create(user_id=user, desk_id="A1")
        self.assertIn(user.username, str(pair))

    # ============================================================
    # UTILS TESTS
    # ============================================================

    def test_get_desk_data_success(self):
        fake_json = '{"A1": {"desk_data": {"height": 120}}}'
        with patch("builtins.open", mock_open(read_data=fake_json)):
            data = get_desk_data("A1")
            self.assertEqual(data, {"height": 120})

    def test_get_desk_data_file_not_found(self):
        with patch("builtins.open", side_effect=FileNotFoundError):
            data = get_desk_data("A1")
            self.assertEqual(data, {})

    def test_pair_user_with_desk(self):
        user = Users.objects.create(
            first_name="A", last_name="B", username="abc",
            password="x", gender="M", height=170
        )
        pair = pair_user_with_desk(user, "D1")
        self.assertEqual(pair.desk_id, "D1")
        self.assertEqual(pair.user_id, user)

    def test_unpair_user(self):
        user = Users.objects.create(
            first_name="A", last_name="B", username="abc",
            password="x", gender="M", height=170
        )
        UserTablePairs.objects.create(user_id=user, desk_id="D1")
        unpair_user(user)
        self.assertEqual(UserTablePairs.objects.filter(user_id=user, end_time__isnull=True).count(), 0)

    # ============================================================
    # VIEWS TESTS
    # ============================================================

    def create_test_user(self, approved=True, role="user"):
        user = Users.objects.create(
            first_name="John", last_name="Doe", username="john",
            password="", gender="M", height=180,
            approved=approved, role=role
        )
        user.set_password("secret")  # hash correcto
        user.save()
        return user

    def test_login_view_success(self):
        user = self.create_test_user()
        response = self.client.post(reverse("login"), {
            "username": "john",
            "password": "secret"
        })
        self.assertIn(response.status_code, [200, 302])

    def test_login_view_user_not_exist(self):
        response = self.client.post(reverse("login"), {
            "username": "ghost",
            "password": "x"
        })
        self.assertEqual(response.status_code, 200)

    def test_logout_view(self):
        user = self.create_test_user()
        session = self.client.session
        session["user_id"] = user.id
        session.save()
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)

    def test_register_view_get(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_logged_in(self):
        user = self.create_test_user()
        session = self.client.session
        session["user_id"] = user.id
        session.save()
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_pair_desk_no_login(self):
        response = self.client.post(reverse("pair_desk"))
        self.assertFalse(response.json()["success"])

    def test_pair_desk_success(self):
        user = self.create_test_user()
        session = self.client.session
        session["user_id"] = user.id
        session.save()
        response = self.client.post(reverse("pair_desk"), {"desk_id": "A1"})
        self.assertTrue(response.json()["success"])

    def test_unpair_desk_success(self):
        user = self.create_test_user()
        UserTablePairs.objects.create(user_id=user, desk_id="A1")
        session = self.client.session
        session["user_id"] = user.id
        session.save()
        response = self.client.post(reverse("unpair_desk"))
        self.assertTrue(response.json()["success"])

    def test_forgot_password_submit(self):
        self.create_test_user()
        response = self.client.post(reverse("forgot_password"), {
            "username": "john", "new_password": "abc", "repeat_password": "abc"
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertEqual(PasswordResetRequest.objects.count(), 1)

    def test_user_desk_status(self):
        user = self.create_test_user()
        session = self.client.session
        session["user_id"] = user.id
        session.save()
        UserTablePairs.objects.create(user_id=user, desk_id="A1")
        response = self.client.get(reverse("user_desk_status", args=["A1"]))
        self.assertTrue(response.json()["is_paired"])

    # ============================================================
    # URL ROUTING
    # ============================================================

    def test_urls_exist(self):
        self.assertEqual(resolve(reverse("login")).view_name, "login")
        self.assertEqual(resolve(reverse("logout")).view_name, "logout")
        self.assertEqual(resolve(reverse("index")).view_name, "index")
        self.assertEqual(resolve(reverse("register")).view_name, "register")
        self.assertEqual(resolve(reverse("dashboard")).view_name, "dashboard")
