from celery import shared_task
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.utils import timezone

from .models import Booking, Ticket
from .pdf_service import generate_ticket_pdf


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
)
def generate_and_email_ticket(
    self,
    booking_id,
):
    """
    Generate the ticket PDF and email it asynchronously.

    Celery automatically retries the task if PDF generation
    or email delivery raises an exception.
    """

    booking = (
        Booking.objects
        .select_related("user")
        .get(
            id=booking_id
        )
    )

    if booking.status != Booking.STATUS_CONFIRMED:
        return (
            "Booking is not confirmed. "
            "Ticket generation skipped."
        )

    ticket, created = Ticket.objects.get_or_create(
        booking=booking,
        defaults={
            "qr_value": (
                f"BOOKING:{booking.booking_id}|"
                f"PAYMENT:{booking.payment_reference}"
            ),
        },
    )

    # ------------------------------------
    # Generate PDF only if not already saved
    # ------------------------------------

    if not ticket.pdf_file:

        pdf_data = generate_ticket_pdf(
            booking
        )

        filename = (
            f"ticket_{booking.booking_id}.pdf"
        )

        ticket.pdf_file.save(
            filename,
            ContentFile(pdf_data),
            save=False,
        )

        ticket.generated_at = (
            timezone.now()
        )

        ticket.email_status = (
            Ticket.EMAIL_PENDING
        )

        ticket.save()

    # ------------------------------------
    # Send email
    # ------------------------------------

    ticket.email_attempts += 1
    ticket.save(
        update_fields=["email_attempts"]
    )

    recipient = booking.user.email

    if not recipient:
        raise ValueError(
            "The booking user does not have an email address."
        )

    email = EmailMessage(
        subject=(
            f"Your Movie Ticket - "
            f"{booking.booking_id}"
        ),
        body=(
            f"Hello {booking.user.username},\n\n"
            f"Your booking has been confirmed.\n\n"
            f"Movie: {booking.movie_title}\n"
            f"Theater: {booking.theater_name}\n"
            f"Screen: {booking.screen_name}\n"
            f"Booking ID: {booking.booking_id}\n"
            f"Payment Reference: "
            f"{booking.payment_reference}\n\n"
            f"Your PDF ticket is attached.\n\n"
            f"Thank you."
        ),
        to=[recipient],
    )

    email.attach_file(
        ticket.pdf_file.path
    )

    try:

        email.send(
            fail_silently=False
        )

    except Exception as exc:

        ticket.email_status = (
            Ticket.EMAIL_FAILED
        )

        ticket.last_email_error = str(
            exc
        )

        ticket.save(
            update_fields=[
                "email_status",
                "last_email_error",
            ]
        )

        raise

    ticket.email_status = (
        Ticket.EMAIL_SENT
    )

    ticket.emailed_at = (
        timezone.now()
    )

    ticket.last_email_error = ""

    ticket.save(
        update_fields=[
            "email_status",
            "emailed_at",
            "last_email_error",
        ]
    )

    return (
        f"Ticket emailed successfully "
        f"for {booking.booking_id}"
    )