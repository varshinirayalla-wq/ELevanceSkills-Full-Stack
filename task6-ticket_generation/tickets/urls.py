from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.home,
        name="home",
    ),

    path(
        "bookings/",
        views.booking_history,
        name="booking_history",
    ),

    path(
        "bookings/<int:booking_id>/ticket/",
        views.download_ticket,
        name="download_ticket",
    ),

    path(
        "verify/<str:booking_id>/",
        views.verify_ticket,
        name="verify_ticket",
    ),

]