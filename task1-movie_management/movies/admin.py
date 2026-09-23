from django.contrib import admin

from .models import (
    Booking,
    CastMember,
    Genre,
    Language,
    Movie,
    MoviePoster,
    Review,
    ReviewReport,
    ShowSchedule,
    Theater,
)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(CastMember)
class CastMemberAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class MoviePosterInline(admin.TabularInline):
    model = MoviePoster
    extra = 1


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "age_certification",
        "duration_minutes",
        "release_date",
        "is_active",
    )

    list_filter = (
        "age_certification",
        "is_active",
        "genres",
        "languages",
    )

    search_fields = ("title", "description")

    filter_horizontal = (
        "genres",
        "languages",
        "cast_members",
    )

    inlines = [MoviePosterInline]


@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "city",
        "total_seats",
    )

    list_filter = ("city",)
    search_fields = ("name", "city")


@admin.register(ShowSchedule)
class ShowScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "movie",
        "theater",
        "starts_at",
        "ticket_price",
        "available_seats",
        "is_active",
    )

    list_filter = (
        "theater",
        "is_active",
    )

    search_fields = (
        "movie__title",
        "theater__name",
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "show",
        "seats",
        "status",
        "booked_at",
    )

    list_filter = ("status",)
    search_fields = (
        "user__username",
        "show__movie__title",
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "movie",
        "user",
        "rating",
        "is_hidden",
        "created_at",
    )

    list_filter = (
        "rating",
        "is_hidden",
    )

    search_fields = (
        "movie__title",
        "user__username",
        "title",
        "body",
    )


@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
    list_display = (
        "review",
        "reported_by",
        "status",
        "created_at",
    )

    list_filter = ("status",)
    search_fields = (
        "review__movie__title",
        "reported_by__username",
        "reason",
    )