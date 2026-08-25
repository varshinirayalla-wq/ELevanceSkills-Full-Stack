# Movie Management System

A Django-based movie management application developed as part of a full-stack internship project.

The system provides an administrator interface for managing movies, genres, languages, cast members, theaters, show schedules, posters, bookings, reviews, ratings, and review reports.

## Project Overview

The Movie Management System is designed to provide two main workflows:

### Administrator

Administrators can manage:

- Movies
- Genres
- Languages
- Cast members
- Movie posters
- Theaters
- Show schedules
- Bookings
- Reviews
- Review reports

### Registered Users

Registered users can:

- Log in to the application
- Browse movies
- View movie details
- Watch embedded YouTube trailers
- View available shows
- Book a show
- Submit ratings and reviews after watching a booked show
- Edit their own reviews
- Report inappropriate reviews

## Main Features

### Movie Management

Each movie supports:

- Title
- Genre classification
- Language
- Cast members
- Age certification
- Duration
- Release date
- Detailed description
- YouTube trailer
- Multiple poster images

### Theater and Show Management

Administrators can create theaters and schedule movie shows with:

- Theater
- Movie
- Show date and time
- Ticket price
- Available seats
- Active/inactive status

### Booking System

Registered users can book available movie shows.

When a booking is created:

- The booking is associated with the logged-in user.
- The booking is associated with the selected show.
- The available seat count is reduced.
- The booking receives a confirmed status.

### Ratings and Reviews

Users cannot submit a review simply because they have opened a movie.

A review requires:

1. A confirmed booking for the movie.
2. The scheduled show to have finished.

This provides a server-side check for review eligibility.

### Verified Viewer

After a user has a confirmed booking and the corresponding show has finished, the user's review can display:

`✓ Verified Viewer`

This badge is calculated from booking information rather than being manually entered by the user.

### Automatic Rating Calculation

Movie ratings are calculated from submitted reviews.

For example:

5-star review + 4-star review

Average:

4.5 / 5

The average is calculated dynamically from the review records.

### Review Editing

Users can edit their own reviews.

The application checks ownership before allowing an edit.

### Review Reporting

Users can report another user's review by providing a reason.

Administrators can manage reported reviews using statuses such as:

- Open
- Reviewed
- Dismissed

Administrators can also hide inappropriate reviews from the public movie page.

### Trailer Embedding

Movies store the YouTube video ID rather than arbitrary iframe HTML.

The application constructs the YouTube embed URL from the validated video ID.

## Technologies Used

- Python
- Django 5.2
- SQLite
- HTML5
- CSS3
- Django Templates
- Django ORM
- Django Admin

## Project Structure

```text
ELevanceSkills-Full-Stack/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── movies/
│   ├── migrations/
│   ├── templates/
│   │   ├── movies/
│   │   │   ├── movie_list.html
│   │   │   └── movie_detail.html
│   │   └── registration/
│   │       └── login.html
│   │
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
│
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
## Installation

### 1. Clone the repository
```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd ELevanceSkills-Full-Stack

2. Create a virtual environment
Windows:
python -m venv .venv

3. Activate the environment
.venv\Scripts\activate

4. Install dependencies
pip install -r requirements.txt

5. Apply migrations
python manage.py migrate

6. Create an administrator
python manage.py createsuperuser

7. Start the server
python manage.py runserver
Then open:
http://127.0.0.1:8000/
Admin:
http://127.0.0.1:8000/admin/