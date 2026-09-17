from datetime import datetime, time as datetime_time, timedelta
from time import perf_counter

from django.core.management.base import BaseCommand
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from dashboard.models import Booking
from dashboard.services import (
    booking_trends,
    cancellation_statistics,
    most_booked_movies,
    peak_booking_hours,
    refund_statistics,
    revenue_summary,
    theater_occupancy,
    top_theaters,
    user_growth,
)


class Command(BaseCommand):
    help = (
        "Benchmark dashboard ORM analytics "
        "against the large test dataset."
    )

    def benchmark(self, name, function):
        """
        Measure execution time and number of SQL queries.
        """

        start = perf_counter()

        with CaptureQueriesContext(connection) as queries:
            function()

        elapsed = perf_counter() - start

        self.stdout.write(
            f"{name:<30} "
            f"{elapsed:.4f}s   "
            f"{len(queries)} queries"
        )

    def handle(self, *args, **options):

        self.stdout.write(
            self.style.WARNING(
                "Dashboard Performance Benchmark"
            )
        )

        self.stdout.write("-" * 70)

        booking_count = Booking.objects.count()

        self.stdout.write(
            f"Bookings: {booking_count:,}"
        )

        self.stdout.write("")

        tests = [
            (
                "Revenue Summary",
                revenue_summary,
            ),
            (
                "Booking Trends",
                booking_trends,
            ),
            (
                "Theater Occupancy",
                theater_occupancy,
            ),
            (
                "Most Booked Movies",
                most_booked_movies,
            ),
            (
                "Top Theaters",
                top_theaters,
            ),
            (
                "Peak Booking Hours",
                peak_booking_hours,
            ),
            (
                "Cancellation Statistics",
                cancellation_statistics,
            ),
            (
                "Refund Statistics",
                refund_statistics,
            ),
            (
                "User Growth",
                user_growth,
            ),
        ]

        for name, function in tests:
            self.benchmark(
                name,
                function,
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.WARNING(
                "Booking Query Plan"
            )
        )

        # Use timezone-aware datetimes for the query plan.

        today = timezone.localdate()

        start_date = today - timedelta(days=365)

        start_datetime = timezone.make_aware(
            datetime.combine(
                start_date,
                datetime_time.min,
            )
        )

        end_datetime = timezone.make_aware(
            datetime.combine(
                today,
                datetime_time.max,
            )
        )

        queryset = Booking.objects.filter(
            booked_at__range=(
                start_datetime,
                end_datetime,
            ),
            status=Booking.CONFIRMED,
        )

        self.stdout.write(
            f"Date range: "
            f"{start_datetime} "
            f"to "
            f"{end_datetime}"
        )

        self.stdout.write("")

        self.stdout.write(
            queryset.explain()
        )