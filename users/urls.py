from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('verify-email/<str:token>/', views.verify_email_view, name='verify_email'),
    
    # Machine ID
    path('set-machine-id/', views.set_machine_id_view, name='set_machine_id'),
    
    # Password Reset
    path('password-reset/', views.password_reset_request_view, name='password_reset_request'),
    path('password-reset/<str:token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    
    # Profile & Settings
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
]

