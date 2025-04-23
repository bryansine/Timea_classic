from . import views
from django.urls import path
from .views import subscribe_newsletter
from django.contrib.auth import views as auth_views 


urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('refund', views.refund, name='refund'),
    path('logout/', views.logout, name='logout'),
    path('login/', views.user_login, name='login'),
    path('contact', views.contact, name='contact'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('subscribe/', subscribe_newsletter, name='subscribe_newsletter'),
    path('password/change/', views.change_password, name='change_password'),

    #password reset
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='core/password_reset.html'), name='password_reset'),
    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='core/password_change.html'), name='password_change'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='core/password_reset_done.html'), name='password_reset_done'),
    path('password-change-done/', auth_views.PasswordChangeDoneView.as_view(template_name='core/password_change_done.html'), name='password_change_done'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='core/password_reset_complete.html'), name='password_reset_complete'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='core/password_reset_confirm.html'), name='password_reset_confirm'),
]