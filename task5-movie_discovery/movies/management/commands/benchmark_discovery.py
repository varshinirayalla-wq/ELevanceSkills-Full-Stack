from time import perf_counter

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection
from django.test.utils import CaptureQueriesContext

from movies.services import (
    build_movie_queryset,
    get_matching_movie_count,
    get_recommended_movies,
    get_recently_viewed_movies,
)


class Command(BaseCommand):
    help = (
        "Benchmark movie discovery search, filtering, "
        "sorting, pagination and recommendations."
    )

    def benchmark(
        self,
        name,
        function,
    ):
        """
        Measure execution time and SQL query count.
        """

        start = perf_counter()

        with CaptureQueriesContext(
            connection
        ) as queries:
            result = function()

            # Force lazy QuerySets to execute.
            if hasattr(result, "__iter__") and not isinstance(
                result,
                (str, bytes, dict, list, tuple, set),
            ):
                result = list(result)

        elapsed = perf_counter() - start

        self.stdout.write(
            f"{name:<35} "
            f"{elapsed:.4f}s   "
            f"{len(queries)} queries"
        )

        return result

    def handle(self, *args, **options):

        self.stdout.write(
            self.style.WARNING(
                "Task 5 Movie Discovery Performance Benchmark"
            )
        )

        self.stdout.write("-" * 80)

        User = get_user_model()

        user = (
            User.objects
            .filter(
                username="demo_user"
            )
            .first()
        )

        if user is None:
            user = (
                User.objects
                .filter(
                    username__startswith="discovery_user_"
                )
                .first()
            )

        if user is None:
            self.stdout.write(
                self.style.ERROR(
                    "No test user found."
                )
            )
            return

        self.stdout.write(
            f"Test user: {user.username}"
        )

        self.stdout.write("")

        # -----------------------------------------
        # 1. Title search
        # -----------------------------------------

        self.benchmark(
            "Title Search",
            lambda: list(
                build_movie_queryset(
                    {
                        "search": "Discovery Movie 10",
                    }
                )[:12]
            ),
        )

        # -----------------------------------------
        # 2. Genre filter
        # -----------------------------------------

        self.benchmark(
            "Genre Filter",
            lambda: list(
                build_movie_queryset(
                    {
                        "genre": "1",
                    }
                )[:12]
            ),
        )

        # -----------------------------------------
        # 3. Language filter
        # -----------------------------------------

        self.benchmark(
            "Language Filter",
            lambda: list(
                build_movie_queryset(
                    {
                        "language": "1",
                    }
                )[:12]
            ),
        )

        # -----------------------------------------
        # 4. City filter
        # -----------------------------------------

        self.benchmark(
            "City Filter",
            lambda: list(
                build_movie_queryset(
                    {
                        "city": "1",
                    }
                )[:12]
            ),
        )

        # -----------------------------------------
        # 5. Theater filter
        # -----------------------------------------

        self.benchmark(
            "Theater Filter",
            lambda: list(
                build_movie_queryset(
                    {
                        "theater": "1",
                    }
                )[:12]
            ),
        )

        # -----------------------------------------
        # 6. Rating filter
        # -----------------------------------------

        self.benchmark(
            "Rating Filter",
            lambda: list(
                build_movie_queryset(
                    {
                        "minimum_rating": "8",
                    }
                )[:12]
            ),
        )

        # -----------------------------------------
        # 7. Show-time filter
        # -----------------------------------------

        self.benchmark(
            "Show Time Filter",
            lambda: list(
                build_movie_queryset(
                    {
                        "show_time_from": "18:00",
                        "show_time_to": "22:00",
                    }
                )[:12]
            ),
        )

        # -----------------------------------------
        # 8. Multi-filter query
        # -----------------------------------------

        multi_filter = {
            "search": "Discovery",
            "genre": "1",
            "language": "1",
            "city": "1",
            "minimum_rating": "7",
            "show_time_from": "18:00",
            "show_time_to": "22:00",
            "sort": "rating",
        }

        self.benchmark(
            "Multi-Filter Query",
            lambda: list(
                build_movie_queryset(
                    multi_filter
                )[:12]
            ),
        )

        # -----------------------------------------
        # 9. Popularity sorting
        # -----------------------------------------

        self.benchmark(
            "Popularity Sorting",
            lambda: list(
                build_movie_queryset(
                    {
                        "sort": "popularity",
                    }
                )[:12]
            ),
        )

        # -----------------------------------------
        # 10. Newest sorting
        # -----------------------------------------

        self.benchmark(
            "Newest Sorting",
            lambda: list(
                build_movie_queryset(
                    {
                        "sort": "newest",
                    }
                )[:12]
            ),
        )

        # -----------------------------------------
        # 11. Rating sorting
        # -----------------------------------------

        self.benchmark(
            "Rating Sorting",
            lambda: list(
                build_movie_queryset(
                    {
                        "sort": "rating",
                    }
                )[:12]
            ),
        )

        # -----------------------------------------
        # 12. Ticket price sorting
        # -----------------------------------------

        self.benchmark(
            "Price Sorting",
            lambda: list(
                build_movie_queryset(
                    {
                        "sort": "price_low",
                    }
                )[:12]
            ),
        )

        # -----------------------------------------
        # 13. Matching movie count
        # -----------------------------------------

        self.benchmark(
            "Matching Movie Count",
            lambda: get_matching_movie_count(
                {
                    "minimum_rating": "8",
                    "city": "1",
                }
            ),
        )

        # -----------------------------------------
        # 14. Pagination
        # -----------------------------------------
        #
        # We simulate retrieving page 50.
        # LIMIT/OFFSET remains database-side.

        self.benchmark(
            "Pagination Page 50",
            lambda: list(
                build_movie_queryset(
                    {
                        "sort": "popularity",
                    }
                )[588:600]
            ),
        )

        # -----------------------------------------
        # 15. Recommendations
        # -----------------------------------------

        self.benchmark(
            "Personalized Recommendations",
            lambda: get_recommended_movies(
                user,
                limit=10,
            ),
        )

        # -----------------------------------------
        # 16. Recently viewed
        # -----------------------------------------

        self.benchmark(
            "Recently Viewed",
            lambda: list(
                get_recently_viewed_movies(
                    user,
                    limit=10,
                )
            ),
        )

        # -----------------------------------------
        # Dataset information
        # -----------------------------------------

        from movies.models import (
            Booking,
            Movie,
            RecentlyViewed,
            Show,
            Theater,
        )

        self.stdout.write("")

        self.stdout.write(
            self.style.WARNING(
                "Dataset Size"
            )
        )

        self.stdout.write(
            f"Movies:          {Movie.objects.count():,}"
        )

        self.stdout.write(
            f"Shows:           {Show.objects.count():,}"
        )

        self.stdout.write(
            f"Bookings:        {Booking.objects.count():,}"
        )

        self.stdout.write(
            f"Theaters:        {Theater.objects.count():,}"
        )

        self.stdout.write(
            f"Recently Viewed: {RecentlyViewed.objects.count():,}"
        )

        # -----------------------------------------
        # Query plan
        # -----------------------------------------

        self.stdout.write("")

        self.stdout.write(
            self.style.WARNING(
                "Movie Discovery Query Plan"
            )
        )

        queryset = (
            build_movie_queryset(
                {
                    "minimum_rating": "8",
                    "city": "1",
                    "show_time_from": "18:00",
                    "show_time_to": "22:00",
                    "sort": "rating",
                }
            )
        )

        self.stdout.write(
            queryset.explain()
        )