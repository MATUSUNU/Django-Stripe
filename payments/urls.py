# payments/urls.py

from django.urls import path

from . import views

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    # 1. Get Publishable Key
    path('config/', views.stripe_config),  # new
    # 2. Create Checkout Session
    path('create-checkout-session/', views.create_checkout_session), # new
    # 3. Redirect the User Appropriately
    path('success/', views.SuccessView.as_view()), # new
    path('cancelled/', views.CancelledView.as_view()), # new
    # 4. Confirm Payment with Stripe Webhooks
    path('webhook/', views.stripe_webhook), # new
]
