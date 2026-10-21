from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import UserProfile


User = get_user_model()


class SignUpForm(UserCreationForm):
	email = forms.EmailField(required=True)

	class Meta(UserCreationForm.Meta):
		model = User
		fields = ('username', 'email', 'first_name', 'last_name')

	def clean_email(self):
		email = self.cleaned_data['email'].strip().lower()
		if User.objects.filter(email__iexact=email).exists():
			raise forms.ValidationError('An account with this email already exists.')
		return email


class UserDetailsForm(forms.ModelForm):
	class Meta:
		model = User
		fields = ('first_name', 'last_name', 'email')

	def clean_email(self):
		email = self.cleaned_data['email'].strip().lower()
		existing_users = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
		if existing_users.exists():
			raise forms.ValidationError('An account with this email already exists.')
		return email


class UserProfileForm(forms.ModelForm):
	class Meta:
		model = UserProfile
		fields = ('phone', 'address')
