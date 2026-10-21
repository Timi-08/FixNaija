from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView

from .forms import SignUpForm, UserDetailsForm, UserProfileForm
from .models import UserProfile


class SignUpView(FormView):
	template_name = 'accounts/signup.html'
	form_class = SignUpForm
	success_url = reverse_lazy('accounts:profile')

	@transaction.atomic
	def form_valid(self, form):
		user = form.save()
		UserProfile.objects.create(user=user)
		login(self.request, user)
		return super().form_valid(form)


class AccountLoginView(LoginView):
	template_name = 'accounts/login.html'
	redirect_authenticated_user = True


class AccountLogoutView(LogoutView):
	next_page = reverse_lazy('accounts:login')


@login_required
def profile(request):
	user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
	user_form = UserDetailsForm(request.POST or None, instance=request.user)
	profile_form = UserProfileForm(request.POST or None, instance=user_profile)

	if request.method == 'POST' and user_form.is_valid() and profile_form.is_valid():
		user_form.save()
		profile_form.save()
		return redirect('accounts:profile')

	return render(
		request,
		'accounts/user_profile.html',
		{'user_form': user_form, 'profile_form': profile_form},
	)
