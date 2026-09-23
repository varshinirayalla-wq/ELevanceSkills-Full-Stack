import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from movies.models import (
    Booking,
    City,
    Genre,
    Language,
    Movie,
    RecentlyViewed,
    Show,
    Theater,
)


class Command(BaseCommand):
    help = "Generate realistic test data for the movie discovery module."

    def add_arguments(self, parser):
        parser.add_argument(
            "--movies",
            type=int,
            default=2000,
            help="Number of movies to create.",
        )

        parser.add_argument(
            "--users",
            type=int,
            default=1000,
            help="Number of users to create.",
        )

        parser.add_argument(
            "--shows",
            type=int,
            default=15000,
            help="Number of shows to create.",
        )

        parser.add_argument(
            "--bookings",
            type=int,
            default=30000,
            help="Number of bookings to create.",
        )

    def handle(self, *args, **options):
        movie_count = options["movies"]
        user_count = options["users"]
        show_count = options["shows"]
        booking_count = options["bookings"]

        self.stdout.write(
            self.style.WARNING(
                "Preparing Task 5 test data..."
            )
        )

        self.create_genres()
        self.create_languages()
        self.create_cities()
        self.create_theaters()

        users = self.create_users(
            user_count
        )

        movies = self.create_movies(
            movie_count
        )

        shows = self.create_shows(
            movies,
            show_count
        )

        self.create_bookings(
            users,
            shows,
            booking_count
        )

        self.create_recently_viewed(
            users,
            movies
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Task 5 test data generated successfully."
            )
        )

    def create_genres(self):
        genre_names = [
            "Action",
            "Drama",
            "Comedy",
            "Romance",
            "Thriller",
            "Horror",
            "Sci-Fi",
            "Fantasy",
            "Animation",
            "Crime",
            "Adventure",
            "Mystery",
            "Sports",
            "Historical",
            "Musical",
        ]

        existing = set(
            Genre.objects.values_list(
                "name",
                flat=True
            )
        )

        Genre.objects.bulk_create(
            [
                Genre(name=name)
                for name in genre_names
                if name not in existing
            ],
            batch_size=500,
        )

        self.genres = list(
            Genre.objects.all()
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Genres ready: {len(self.genres)}"
            )
        )

    def create_languages(self):
        language_names = [
            "Telugu",
            "English",
            "Hindi",
            "Tamil",
            "Kannada",
            "Malayalam",
        ]

        existing = set(
            Language.objects.values_list(
                "name",
                flat=True
            )
        )

        Language.objects.bulk_create(
            [
                Language(name=name)
                for name in language_names
                if name not in existing
            ],
            batch_size=500,
        )

        self.languages = list(
            Language.objects.all()
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Languages ready: {len(self.languages)}"
            )
        )

    def create_cities(self):
        city_names = [
            "Bangalore",
            "Hyderabad",
            "Chennai",
            "Mumbai",
            "Delhi",
            "Pune",
            "Kochi",
            "Mysore",
            "Vijayawada",
            "Visakhapatnam",
            "Coimbatore",
            "Mangalore",
        ]

        existing = set(
            City.objects.values_list(
                "name",
                flat=True
            )
        )

        City.objects.bulk_create(
            [
                City(name=name)
                for name in city_names
                if name not in existing
            ],
            batch_size=500,
        )

        self.cities = list(
            City.objects.all()
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Cities ready: {len(self.cities)}"
            )
        )

    def create_theaters(self):
        existing = set(
            Theater.objects.values_list(
                "name",
                "city_id"
            )
        )

        theaters = []

        for city in self.cities:
            for number in range(1, 9):
                name = f"{city.name} Cinemas {number}"

                if (name, city.id) in existing:
                    continue

                theaters.append(
                    Theater(
                        name=name,
                        city=city,
                        total_seats=random.choice(
                            [150, 180, 200, 220, 250, 300]
                        ),
                    )
                )

        Theater.objects.bulk_create(
            theaters,
            batch_size=1000,
        )

        self.theaters = list(
            Theater.objects.select_related(
                "city"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Theaters ready: {len(self.theaters)}"
            )
        )

    def create_users(self, user_count):
        User = get_user_model()

        prefix = "discovery_user_"

        existing = set(
            User.objects.filter(
                username__startswith=prefix
            ).values_list(
                "username",
                flat=True
            )
        )

        users_to_create = []

        for index in range(1, user_count + 1):
            username = f"{prefix}{index}"

            if username in existing:
                continue

            users_to_create.append(
                User(
                    username=username,
                    email=f"{username}@example.com",
                    is_active=True,
                )
            )

        if users_to_create:
            User.objects.bulk_create(
                users_to_create,
                batch_size=2000
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

    def create_movies(self, movie_count):
        existing_count = Movie.objects.count()

        if existing_count >= movie_count:
            movies = list(
                Movie.objects.all()
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Movies already available: {len(movies)}"
                )
            )

            return movies

        movies_to_create = []

        language_count = len(
            self.languages
        )

        for index in range(
            existing_count + 1,
            movie_count + 1
        ):
            language = random.choice(
                self.languages
            )

            release_date = (
                timezone.localdate()
                - timedelta(
                    days=random.randint(
                        0,
                        1500
                    )
                )
            )

            rating = Decimal(
                str(
                    round(
                        random.uniform(
                            4.5,
                            9.8
                        ),
                        1,
                    )
                )
            )

            popularity = random.randint(
                10,
                100000
            )

            movies_to_create.append(
                Movie(
                    title=f"Discovery Movie {index}",
                    language=language,
                    release_date=release_date,
                    rating=rating,
                    popularity=popularity,
                    description=(
                        "A sample movie created "
                        "for the movie discovery module."
                    ),
                )
            )

        Movie.objects.bulk_create(
            movies_to_create,
            batch_size=2000
        )

        movies = list(
            Movie.objects.all()
        )

        movie_genre_links = []

        for movie in movies:
            selected_genres = random.sample(
                self.genres,
                random.randint(1, 3)
            )

            for genre in selected_genres:
                movie_genre_links.append(
                    Movie.genres.through(
                        movie_id=movie.id,
                        genre_id=genre.id,
                    )
                )

        Movie.genres.through.objects.bulk_create(
            movie_genre_links,
            batch_size=5000,
            ignore_conflicts=True,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Movies ready: {len(movies)}"
            )
        )

        return movies

    def create_shows(self, movies, show_count):
        existing_count = Show.objects.count()

        if existing_count >= show_count:
            shows = list(
                Show.objects.select_related(
                    "movie",
                    "theater",
                )
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Shows already available: {len(shows)}"
                )
            )

            return shows

        shows_to_create = []

        now = timezone.now()

        for _ in range(
            show_count - existing_count
        ):
            movie = random.choice(
                movies
            )

            theater = random.choice(
                self.theaters
            )

            show_time = now + timedelta(
                days=random.randint(
                    -30,
                    60
                ),
                hours=random.randint(
                    9,
                    22
                ),
                minutes=random.choice(
                    [
                        0,
                        15,
                        30,
                        45
                    ]
                ),
            )

            ticket_price = Decimal(
                random.choice(
                    [
                        "150.00",
                        "180.00",
                        "200.00",
                        "220.00",
                        "250.00",
                        "300.00",
                    ]
                )
            )

            shows_to_create.append(
                Show(
                    movie=movie,
                    theater=theater,
                    show_time=show_time,
                    ticket_price=ticket_price,
                    is_active=True,
                )
            )

        Show.objects.bulk_create(
            shows_to_create,
            batch_size=2000
        )

        shows = list(
            Show.objects.select_related(
                "movie",
                "theater",
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Shows ready: {len(shows)}"
            )
        )

        return shows

    def create_bookings(
        self,
        users,
        shows,
        booking_count
    ):
        existing_count = Booking.objects.count()

        if existing_count >= booking_count:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Bookings already available: "
                    f"{existing_count}"
                )
            )
            return

        bookings_to_create = []

        now = timezone.now()

        for _ in range(
            booking_count - existing_count
        ):
            user = random.choice(
                users
            )

            show = random.choice(
                shows
            )

            booked_at = now - timedelta(
                days=random.randint(
                    0,
                    365
                ),
                hours=random.randint(
                    0,
                    23
                ),
                minutes=random.randint(
                    0,
                    59
                ),
            )

            bookings_to_create.append(
                Booking(
                    user=user,
                    show=show,
                    booked_at=booked_at,
                )
            )

        with transaction.atomic():
            Booking.objects.bulk_create(
                bookings_to_create,
                batch_size=3000
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Bookings ready: "
                f"{Booking.objects.count()}"
            )
        )

    def create_recently_viewed(
        self,
        users,
        movies
    ):
        existing_count = (
            RecentlyViewed.objects.count()
        )

        if existing_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "Recently viewed data already exists."
                )
            )
            return

        views = []

        now = timezone.now()

        for user in users:
            selected_movies = random.sample(
                movies,
                min(
                    random.randint(3, 8),
                    len(movies)
                ),
            )

            for movie in selected_movies:
                viewed_at = (
                    now
                    - timedelta(
                        days=random.randint(
                            0,
                            90
                        ),
                        hours=random.randint(
                            0,
                            23
                        ),
                    )
                )

                views.append(
                    RecentlyViewed(
                        user=user,
                        movie=movie,
                        viewed_at=viewed_at,
                    )
                )

        RecentlyViewed.objects.bulk_create(
            views,
            batch_size=3000
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Recently viewed records: "
                f"{len(views)}"
            )
        )