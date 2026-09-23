from io import BytesIO

import qrcode

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from django.conf import settings


def generate_ticket_pdf(booking):
    """
    Generate a professional PDF ticket in memory.

    Returns:
        bytes: PDF document contents
    """

    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=A4,
    )

    page_width, page_height = A4

    # -----------------------------
    # Header
    # -----------------------------

    pdf.setFont(
        "Helvetica-Bold",
        22,
    )

    pdf.drawString(
        25 * mm,
        page_height - 30 * mm,
        "MOVIE TICKET",
    )

    pdf.setFont(
        "Helvetica",
        10,
    )

    pdf.drawString(
        25 * mm,
        page_height - 38 * mm,
        "Electronic Booking Confirmation",
    )

    # -----------------------------
    # Ticket information
    # -----------------------------

    details = [
        (
            "Booking ID",
            booking.booking_id,
        ),
        (
            "Movie",
            booking.movie_title,
        ),
        (
            "Theater",
            booking.theater_name,
        ),
        (
            "Screen",
            booking.screen_name,
        ),
        (
            "Show Time",
            booking.show_time.strftime(
                "%d %b %Y, %I:%M %p"
            ),
        ),
        (
            "Seats",
            ", ".join(
                str(seat)
                for seat in booking.booked_seats
            ),
        ),
        (
            "Payment Reference",
            booking.payment_reference,
        ),
        (
            "Amount",
            f"INR {booking.amount}",
        ),
    ]

    y = page_height - 65 * mm

    for label, value in details:

        pdf.setFont(
            "Helvetica-Bold",
            10,
        )

        pdf.drawString(
            25 * mm,
            y,
            f"{label}:",
        )

        pdf.setFont(
            "Helvetica",
            10,
        )

        pdf.drawString(
            70 * mm,
            y,
            str(value),
        )

        y -= 9 * mm

    # -----------------------------
    # QR Code
    # -----------------------------

    qr_payload = (
    f"{settings.SITE_URL}"
    f"/verify/{booking.booking_id}/"
    )

    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=4,
    )

    qr.add_data(
        qr_payload
    )

    qr.make(
        fit=True
    )

    qr_image = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    qr_buffer = BytesIO()

    qr_image.save(
        qr_buffer,
        format="PNG",
    )

    qr_buffer.seek(0)

    from reportlab.lib.utils import ImageReader

    pdf.drawImage(
        ImageReader(qr_buffer),
        page_width - 75 * mm,
        page_height - 110 * mm,
        width=45 * mm,
        height=45 * mm,
    )

    pdf.setFont(
        "Helvetica",
        9,
    )

    pdf.drawString(
        page_width - 78 * mm,
        page_height - 118 * mm,
        "Scan to verify booking",
    )

    # -----------------------------
    # Footer
    # -----------------------------

    pdf.setFont(
        "Helvetica",
        8,
    )

    pdf.drawString(
        25 * mm,
        20 * mm,
        "Please present this ticket at the theater.",
    )

    pdf.drawString(
        25 * mm,
        15 * mm,
        "Keep your booking ID and payment reference for verification.",
    )

    pdf.showPage()

    pdf.save()

    buffer.seek(0)

    return buffer.getvalue()
