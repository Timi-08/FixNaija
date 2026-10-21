from django.urls import path

from . import views


app_name = 'accounts'

urlpatterns = [
	path('signup/', views.SignUpView.as_view(), name='signup'),
	path('login/', views.AccountLoginView.as_view(), name='login'),
	path('logout/', views.AccountLogoutView.as_view(), name='logout'),
	path('profile/', views.profile, name='profile'),
]
