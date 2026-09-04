from django.urls import path

from . import views


urlpatterns = [
    # Task 3 homepage
    path(
        "",
        views.home,
        name="home",
    ),

    # Create a Razorpay order and hold selected seats
    path(
        "create-order/<int:show_id>/",
        views.create_order,
        name="create_order",
    ),

    # Razorpay checkout page
    path(
        "checkout/<int:payment_id>/",
        views.checkout_page,
        name="checkout_page",
    ),

    # Payment result handlers
    path(
        "payment/success/",
        views.payment_success,
        name="payment_success",
    ),

    path(
        "payment/failed/",
        views.payment_failed,
        name="payment_failed",
    ),

    path(
        "payment/cancelled/",
        views.payment_cancelled,
        name="payment_cancelled",
    ),

    # Payment result page
    path(
        "payment/result/<str:order_id>/",
        views.payment_result,
        name="payment_result",
    ),

    # Retry a failed/cancelled payment
    path(
        "payment/retry/<int:payment_id>/",
        views.payment_retry,
        name="payment_retry",
    ),

    # User payment and booking history
    path(
        "payment-history/",
        views.payment_history,
        name="payment_history",
    ),

    # Razorpay server-to-server webhook
    path(
        "webhook/razorpay/",
        views.webhook,
        name="razorpay_webhook",
    ),
]