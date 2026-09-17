import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from dashboard.models import Booking, Movie, Payment, Theater


class Command(BaseCommand):
    help = "Generate realistic test data for the admin analytics dashboard."

    def add_arguments(self, parser):
        parser.add_argument(
            "--bookings",
            type=int,
            default=120000,
            help="Number of bookings to generate.",
        )

        parser.add_argument(
            "--users",
            type=int,
            default=5000,
            help="Number of test users to generate.",
        )

    def handle(self, *args, **options):
        booking_count = options["bookings"]
        user_count = options["users"]

        self.stdout.write(
            self.style.WARNING(
                f"Preparing {user_count} users and {booking_count} bookings..."
            )
        )

        self.create_movies()
        self.create_theaters()
        users = self.create_users(user_count)

        self.create_bookings_and_payments(
            users=users,
            booking_count=booking_count,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Test data generation completed successfully."
            )
        )

    def create_movies(self):
        movie_names = [
            ("Devara: Part 1", "Action"),
            ("RRR", "Action"),
            ("Pushpa 2: The Rule", "Action"),
            ("Kalki 2898 AD", "Sci-Fi"),
            ("Salaar", "Action"),
            ("Arjun Reddy", "Drama"),
            ("Sita Ramam", "Romance"),
            ("Hi Nanna", "Drama"),
            ("Jersey", "Sports"),
            ("Baahubali 2", "Action"),
            ("Eega", "Fantasy"),
            ("Ala Vaikunthapurramuloo", "Comedy"),
        ]

        existing_names = set(
            Movie.objects.values_list("name", flat=True)
        )

        movies_to_create = [
            Movie(name=name, genre=genre)
            for name, genre in movie_names
            if name not in existing_names
        ]

        if movies_to_create:
            Movie.objects.bulk_create(
                movies_to_create,
                batch_size=1000,
            )

        self.movies = list(Movie.objects.all())

        self.stdout.write(
            self.style.SUCCESS(
                f"Movies ready: {len(self.movies)}"
            )
        )

    def create_theaters(self):
        theater_data = [
            ("MovieMate PVR", "Bangalore", 250),
            ("INOX Garuda", "Bangalore", 300),
            ("Cinepolis Forum", "Bangalore", 220),
            ("PVR Orion Mall", "Bangalore", 280),
            ("INOX Mantri Square", "Bangalore", 240),
            ("AMB Cinemas", "Hyderabad", 320),
            ("Prasads Multiplex", "Hyderabad", 300),
            ("Asian Cinemas", "Hyderabad", 250),
        ]

        existing_names = set(
            Theater.objects.values_list("name", flat=True)
        )

        theaters_to_create = [
            Theater(
                name=name,
                location=location,
                total_seats=total_seats,
            )
            for name, location, total_seats in theater_data
            if name not in existing_names
        ]

        if theaters_to_create:
            Theater.objects.bulk_create(
                theaters_to_create,
                batch_size=1000,
            )

        self.theaters = list(Theater.objects.all())

        self.stdout.write(
            self.style.SUCCESS(
                f"Theaters ready: {len(self.theaters)}"
            )
        )

    def create_users(self, user_count):
        User = get_user_model()

        prefix = "analytics_user_"

        existing_usernames = set(
            User.objects.filter(
                username__startswith=prefix
            ).values_list("username", flat=True)
        )

        users_to_create = []

        for index in range(1, user_count + 1):
            username = f"{prefix}{index}"

            if username in existing_usernames:
                continue

            users_to_create.append(
                User(
                    username=username,
                    email=f"{username}@example.com",
                    date_joined=self.random_join_date(),
                    is_active=True,
                )
            )

        if users_to_create:
            User.objects.bulk_create(
                users_to_create,
                batch_size=2000,
            )

        users = list(
            User.objects.filter(
                username__startswith=prefix
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Users ready: {len(users)}"
            )
        )

        return users

    def random_join_date(self):
        end_date = timezone.now()
        start_date = end_date - timedelta(days=730)

        seconds = int(
            (end_date - start_date).total_seconds()
        )

        return start_date + timedelta(
            seconds=random.randint(0, seconds)
        )

    def random_booking_date(self):
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)

        day_offset = random.randint(0, 364)

        base_date = start_date + timedelta(
            days=day_offset
        )

        hour_weights = [
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            21,
            22,
        ]

        hour = random.choices(
            hour_weights,
            weights=[
                2,
                2,
                3,
                4,
                5,
                5,
                5,
                6,
                10,
                14,
                18,
                20,
                16,
                10,
            ],
            k=1,
        )[0]

        minute = random.choice(
            [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
        )

        naive_datetime = datetime(
            year=base_date.year,
            month=base_date.month,
            day=base_date.day,
            hour=hour,
            minute=minute,
        )

        return timezone.make_aware(
            naive_datetime,
            timezone.get_current_timezone(),
        )

    def create_bookings_and_payments(
        self,
        users,
        booking_count,
    ):
        booking_batch_size = 2000

        total_created = 0

        while total_created < booking_count:
            current_batch_size = min(
                booking_batch_size,
                booking_count - total_created,
            )

            bookings = []

            for _ in range(current_batch_size):
                user = random.choice(users)
                movie = random.choice(self.movies)
                theater = random.choice(self.theaters)

                booked_at = self.random_booking_date()

                seats_booked = random.randint(1, 6)

                ticket_price = Decimal(
                    random.choice(
                        [
                            "150.00",
                            "180.00",
                            "200.00",
                            "220.00",
                            "250.00",
                            "280.00",
                        ]
                    )
                )

                amount = ticket_price * seats_booked

                booking_status = random.choices(
                    [
                        Booking.CONFIRMED,
                        Booking.CANCELLED,
                    ],
                    weights=[88, 12],
                    k=1,
                )[0]

                bookings.append(
                    Booking(
                        user=user,
                        movie=movie,
                        theater=theater,
                        booked_at=booked_at,
                        seats_booked=seats_booked,
                        amount=amount,
                        status=booking_status,
                    )
                )

            with transaction.atomic():
                Booking.objects.bulk_create(
                    bookings,
                    batch_size=2000,
                )

            created_bookings = Booking.objects.order_by(
                "-id"
            )[:current_batch_size]

            created_bookings = list(
                reversed(created_bookings)
            )

            payments = []

            for booking in created_bookings:
                transaction_id = (
                    f"TXN-{booking.id}-"
                    f"{random.randint(100000, 999999)}"
                )

                if booking.status == Booking.CANCELLED:
                    payment_status = random.choices(
                        [
                            Payment.REFUNDED,
                            Payment.FAILED,
                        ],
                        weights=[85, 15],
                        k=1,
                    )[0]

                    refund_amount = (
                        booking.amount
                        if payment_status == Payment.REFUNDED
                        else Decimal("0.00")
                    )

                else:
                    payment_status = random.choices(
                        [
                            Payment.SUCCESS,
                            Payment.FAILED,
                        ],
                        weights=[95, 5],
                        k=1,
                    )[0]

                    refund_amount = Decimal("0.00")

                payments.append(
                    Payment(
                        booking=booking,
                        transaction_id=transaction_id,
                        amount=booking.amount,
                        status=payment_status,
                        refund_amount=refund_amount,
                    )
                )

            with transaction.atomic():
                Payment.objects.bulk_create(
                    payments,
                    batch_size=2000,
                )

            total_created += current_batch_size

            self.stdout.write(
                f"Bookings created: "
                f"{total_created:,}/{booking_count:,}"
            )