from django.db import transaction
from uuid import uuid4

from .models import Booking
from .tasks import generate_and_email_ticket


def create_successful_booking(
    user,
    movie_title,
    theater_name,
    screen_name,
    show_time,
    booked_seats,
    payment_reference,
    amount,
):
    """
    Create a confirmed booking.

    The Celery task is queued only after the database transaction
    has successfully committed.
    """

    booking_id = (
        f"BK-{uuid4().hex[:10].upper()}"
    )

    with transaction.atomic():

        booking = Booking.objects.create(
            user=user,
            booking_id=booking_id,
            movie_title=movie_title,
            theater_name=theater_name,
            screen_name=screen_name,
            show_time=show_time,
            booked_seats=booked_seats,
            payment_reference=payment_reference,
            amount=amount,
            status=Booking.STATUS_CONFIRMED,
        )

        transaction.on_commit(
            lambda: generate_and_email_ticket.delay(
                booking.id
            )
        )

    return booking