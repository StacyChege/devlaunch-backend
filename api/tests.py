from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

from .emails import make_email_verification_token

User = get_user_model()

REG = {
    'full_name': 'Test User',
    'email': 'test.user@example.com',
    'password': 'Str0ngPass!23',
    'confirm_password': 'Str0ngPass!23',
}


class AuthFlowTests(APITestCase):
    def test_register_creates_unverified_user_and_sends_two_emails(self):
        res = self.client.post('/api/auth/register/', REG, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('access', res.data)

        user = User.objects.get(email=REG['email'])
        self.assertFalse(user.is_verified)
        self.assertEqual(user.role, User.DEVELOPER)
        # welcome + verification
        self.assertEqual(len(mail.outbox), 2)

    def test_register_rejects_mismatched_passwords(self):
        bad = {**REG, 'confirm_password': 'different'}
        res = self.client.post('/api/auth/register/', bad, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_blocked_until_verified(self):
        self.client.post('/api/auth/register/', REG, format='json')
        res = self.client.post(
            '/api/auth/login/',
            {'email': REG['email'], 'password': REG['password']},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res.data['code'], 'email_not_verified')

    def test_verify_email_marks_verified_and_returns_tokens(self):
        self.client.post('/api/auth/register/', REG, format='json')
        user = User.objects.get(email=REG['email'])
        token = make_email_verification_token(user)

        res = self.client.post(
            '/api/auth/verify-email/', {'token': token}, format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        user.refresh_from_db()
        self.assertTrue(user.is_verified)

    def test_verify_email_rejects_garbage_token(self):
        res = self.client.post(
            '/api/auth/verify-email/', {'token': 'not-a-real-token'}, format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_succeeds_after_verification(self):
        self.client.post('/api/auth/register/', REG, format='json')
        user = User.objects.get(email=REG['email'])
        user.is_verified = True
        user.save(update_fields=['is_verified'])

        res = self.client.post(
            '/api/auth/login/',
            {'email': REG['email'], 'password': REG['password']},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertTrue(res.data['user']['is_verified'])

    def test_password_reset_request_does_not_leak_account_existence(self):
        res = self.client.post(
            '/api/auth/password-reset/', {'email': 'nobody@example.com'}, format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_confirm_changes_password(self):
        self.client.post('/api/auth/register/', REG, format='json')
        user = User.objects.get(email=REG['email'])
        user.is_verified = True
        user.save(update_fields=['is_verified'])

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        res = self.client.post(
            '/api/auth/password-reset/confirm/',
            {'uid': uid, 'token': token, 'new_password': 'Br4ndNew!Pass'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        login = self.client.post(
            '/api/auth/login/',
            {'email': REG['email'], 'password': 'Br4ndNew!Pass'},
            format='json',
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)

    def test_password_reset_confirm_rejects_bad_token(self):
        self.client.post('/api/auth/register/', REG, format='json')
        user = User.objects.get(email=REG['email'])
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        res = self.client.post(
            '/api/auth/password-reset/confirm/',
            {'uid': uid, 'token': 'bad-token', 'new_password': 'Br4ndNew!Pass'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_requires_auth(self):
        self.assertEqual(
            self.client.get('/api/auth/me/').status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class AccountSettingsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='dev@example.com', full_name='Old Name', password='Str0ngPass!23'
        )
        self.user.is_verified = True
        self.user.save(update_fields=['is_verified'])
        self.client.force_authenticate(self.user)

    def test_patch_me_updates_full_name(self):
        res = self.client.patch(
            '/api/auth/me/', {'full_name': 'New Name'}, format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['full_name'], 'New Name')
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'New Name')

    def test_patch_me_rejects_blank_name(self):
        res = self.client.patch('/api/auth/me/', {'full_name': '  '}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_me_ignores_email_and_role(self):
        res = self.client.patch(
            '/api/auth/me/',
            {'email': 'hacker@example.com', 'role': 'ADMIN', 'full_name': 'X'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'dev@example.com')
        self.assertEqual(self.user.role, User.DEVELOPER)

    def test_change_password_requires_correct_current(self):
        res = self.client.post(
            '/api/auth/change-password/',
            {'current_password': 'wrong', 'new_password': 'An0therPass!45'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_success_and_relogin(self):
        res = self.client.post(
            '/api/auth/change-password/',
            {'current_password': 'Str0ngPass!23', 'new_password': 'An0therPass!45'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(None)
        login = self.client.post(
            '/api/auth/login/',
            {'email': 'dev@example.com', 'password': 'An0therPass!45'},
            format='json',
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)

    def test_change_password_rejects_weak_new_password(self):
        res = self.client.post(
            '/api/auth/change-password/',
            {'current_password': 'Str0ngPass!23', 'new_password': '123'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_requires_auth(self):
        self.client.force_authenticate(None)
        res = self.client.post(
            '/api/auth/change-password/',
            {'current_password': 'x', 'new_password': 'An0therPass!45'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class HealthCheckTests(APITestCase):
    def test_healthz_ok(self):
        res = self.client.get('/healthz/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()['status'], 'ok')
        self.assertEqual(res.json()['database'], 'ok')
