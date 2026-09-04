import hmac
import hashlib
import json

import razorpay

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (
    Booking,
    Payment,
    Seat,
    SeatHold,
)


def get_razorpay_client():
    """
    Create and return the Razorpay API client.
    """

    return razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET,
        )
    )


def release_payment_holds(payment):
    """
    Release all active seat holds belonging to a payment.
    """

    now = timezone.now()

    with transaction.atomic():

        locked_payment = (
            Payment.objects
            .select_for_update()
            .get(pk=payment.pk)
        )

        holds = list(
            SeatHold.objects
            .select_for_update()
            .select_related("seat")
            .filter(
                payment=locked_payment,
                status=SeatHold.STATUS_ACTIVE,
            )
        )

        for hold in holds:

            hold.status = SeatHold.STATUS_RELEASED
            hold.released_at = now

            hold.seat.status = Seat.STATUS_AVAILABLE

            hold.seat.save(
                update_fields=["status"]
            )

            hold.save(
                update_fields=[
                    "status",
                    "released_at",
                ]
            )


def confirm_payment(
    order_id,
    payment_id,
    signature,
):
    """
    Verify the Razorpay payment signature and confirm
    the associated booking exactly once.
    """

    client = get_razorpay_client()

    verification_data = {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": signature,
    }

    # Server-side signature verification.
    client.utility.verify_payment_signature(
        verification_data
    )

    with transaction.atomic():

        payment = (
            Payment.objects
            .select_for_update()
            .select_related("user", "show")
            .get(order_id=order_id)
        )

        # Idempotency:
        # If this payment was already processed successfully,
        # do not create another booking.
        if payment.status == Payment.STATUS_SUCCESS:

            if (
                payment.payment_id
                and payment.payment_id != payment_id
            ):
                raise ValueError(
                    "This order is already associated "
                    "with another payment."
                )

            return payment

        # Make sure the payment belongs to the
        # same Razorpay order being confirmed.
        payment.payment_id = payment_id
        payment.transaction_id = payment_id
        payment.status = Payment.STATUS_SUCCESS

        payment.save(
            update_fields=[
                "payment_id",
                "transaction_id",
                "status",
                "updated_at",
            ]
        )

        holds = list(
            SeatHold.objects
            .select_for_update()
            .select_related("seat")
            .filter(
                payment=payment,
                status=SeatHold.STATUS_ACTIVE,
            )
        )

        if not holds:

            # It may have already been converted to a booking
            # by a previously processed confirmation.
            existing_booking = (
                Booking.objects
                .filter(payment=payment)
                .first()
            )

            if existing_booking:
                return payment

            raise ValueError(
                "No active seat holds exist for this payment."
            )

        selected_seats = [
            hold.seat.seat_number
            for hold in holds
        ]

        # One payment can create at most one booking.
        booking, created = Booking.objects.get_or_create(
            payment=payment,
            defaults={
                "user": payment.user,
                "show": payment.show,
                "seats": sorted(selected_seats),
                "amount": payment.amount,
                "status": Booking.STATUS_CONFIRMED,
            },
        )

        if not created:

            if booking.status != Booking.STATUS_CONFIRMED:

                booking.status = Booking.STATUS_CONFIRMED

                booking.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

        # Convert held seats into booked seats.
        for hold in holds:

            hold.status = SeatHold.STATUS_BOOKED

            hold.seat.status = Seat.STATUS_BOOKED

            hold.seat.save(
                update_fields=["status"]
            )

            hold.save(
                update_fields=["status"]
            )

        return payment


def fail_payment(
    order_id,
    payment_id=None,
    reason="Payment failed.",
):
    """
    Mark payment as failed and release held seats.
    """

    with transaction.atomic():

        payment = (
            Payment.objects
            .select_for_update()
            .get(order_id=order_id)
        )

        # Never turn a successful payment back into FAILED.
        if payment.status == Payment.STATUS_SUCCESS:
            return payment

        payment.status = Payment.STATUS_FAILED

        if payment_id:
            payment.payment_id = payment_id

        payment.failure_reason = reason

        payment.save(
            update_fields=[
                "status",
                "payment_id",
                "failure_reason",
                "updated_at",
            ]
        )

    release_payment_holds(payment)

    return payment


def cancel_payment(
    order_id,
    reason="Payment cancelled.",
):
    """
    Mark payment as cancelled and release held seats.
    """

    with transaction.atomic():

        payment = (
            Payment.objects
            .select_for_update()
            .get(order_id=order_id)
        )

        # A successful payment cannot later become cancelled.
        if payment.status == Payment.STATUS_SUCCESS:
            return payment

        payment.status = Payment.STATUS_CANCELLED
        payment.failure_reason = reason

        payment.save(
            update_fields=[
                "status",
                "failure_reason",
                "updated_at",
            ]
        )

    release_payment_holds(payment)

    return payment


def verify_webhook_signature(
    raw_body,
    received_signature,
):
    """
    Verify a Razorpay webhook using the raw request body.
    """

    secret = settings.RAZORPAY_WEBHOOK_SECRET

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature,
        received_signature,
    )