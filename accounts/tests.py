from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import UserProfile


User = get_user_model()


class AccountFlowTests(TestCase):
	def test_signup_creates_profile_and_authenticates_user(self):
		response = self.client.post(
			reverse('accounts:signup'),
			{
				'username': 'ada',
				'email': 'ada@example.com',
				'first_name': 'Ada',
				'last_name': 'Okafor',
				'password1': 'Strong-pass-583!',
				'password2': 'Strong-pass-583!',
			},
		)

		user = User.objects.get(username='ada')
		self.assertRedirects(response, reverse('accounts:profile'))
		self.assertTrue(UserProfile.objects.filter(user=user).exists())
		self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

	def test_signup_rejects_duplicate_email(self):
		User.objects.create_user(
			username='existing',
			email='ada@example.com',
			password='Strong-pass-583!',
		)

		response = self.client.post(
			reverse('accounts:signup'),
			{
				'username': 'ada',
				'email': 'ADA@example.com',
				'password1': 'Strong-pass-583!',
				'password2': 'Strong-pass-583!',
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertFalse(User.objects.filter(username='ada').exists())

	def test_profile_requires_login_and_saves_profile_data(self):
		user = User.objects.create_user(
			username='ada',
			email='ada@example.com',
			password='Strong-pass-583!',
		)

		response = self.client.get(reverse('accounts:profile'))
		self.assertRedirects(
			response,
			f"{reverse('accounts:login')}?next={reverse('accounts:profile')}",
		)

		self.client.force_login(user)
		response = self.client.post(
			reverse('accounts:profile'),
			{
				'first_name': 'Ada',
				'last_name': 'Okafor',
				'email': 'ada@example.com',
				'phone': '+2348000000000',
				'address': 'Lagos',
			},
		)

		self.assertRedirects(response, reverse('accounts:profile'))
		user.profile.refresh_from_db()
		self.assertEqual(user.profile.phone, '+2348000000000')
		self.assertEqual(user.profile.address, 'Lagos')

	def test_login_and_logout(self):
		User.objects.create_user(
			username='ada',
			email='ada@example.com',
			password='Strong-pass-583!',
		)

		response = self.client.post(
			reverse('accounts:login'),
			{'username': 'ada', 'password': 'Strong-pass-583!'},
		)
		self.assertRedirects(response, reverse('accounts:profile'))

		response = self.client.post(reverse('accounts:logout'))
		self.assertRedirects(response, reverse('accounts:login'))
		self.assertNotIn('_auth_user_id', self.client.session)
