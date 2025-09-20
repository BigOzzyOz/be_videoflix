# be_videoflix

Videoflix Backend

## Project Introduction

Videoflix is a video streaming platform. This repository contains the backend service for Videoflix, built with Django and Django REST Framework. It handles user authentication, video management, and serves data to the frontend application.

## Frontend Application

The frontend repository can be found here: [https://github.com/BigOzzyOz/videoflix](https://github.com/BigOzzyOz/videoflix)

## Quick Start

1. Copy `.example.env` to `.env` for local development.
2. Run `docker-compose up` to start all services.
3. Access the backend at [http://localhost:8000/](http://localhost:8000/) and the admin at [http://localhost:8000/admin/](http://localhost:8000/admin/).

For production, use `.example.prod.env` and `docker-compose -f docker-compose.prod.yml up -d`.

## Environment Variables (.env / .env.prod)

Environment variables are required for running the project. Example files are provided as `.example.env` and `.example.prod.env` in the repository. Do not edit `.example.env` or `.example.prod.env` directly—always copy them to `.env` or `.env.prod` (which are gitignored) and edit those copies.

**How to use:**

1. Copy `.example.env` to `.env` for local development, or `.example.prod.env` to `.env.prod` for production.
2. Adjust the values as needed (e.g. SECRET_KEY, database, email, etc.).
3. The Docker Compose files will automatically load the appropriate .env file.

**Important variables:**

- `SECRET_KEY`: Django secret key (should be unique and secret)
- `DEBUG`: `True` for development, `False` for production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `EMAIL_HOST`, `EMAIL_PORT`, ...: SMTP configuration
- `FORCE_SCRIPT_NAME`, `STATIC_URL`, `MEDIA_URL`: Path configuration for deployment

**.example.env (for local development):**

```env
SECRET_KEY=django-insecure-...your-key...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
EMAIL_HOST=localhost
EMAIL_PORT=1025
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=False
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=webmaster@localhost
RQ_URL=redis://localhost:6379/0
RQ_DEFAULT_TIMEOUT=360
```

**.example.prod.env (for production):**

```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourserver.com
EMAIL_HOST=smtp.yourserver.com
EMAIL_PORT=587
EMAIL_HOST_USER=youruser
EMAIL_HOST_PASSWORD=yourpassword
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=admin@yourserver.com
RQ_URL=redis://redis:6379/0
RQ_DEFAULT_TIMEOUT=360
FORCE_SCRIPT_NAME=/be-videoflix
STATIC_URL=/be-videoflix/static/
MEDIA_URL=/be-videoflix/media/
```

## Docker Setup

This project uses Docker for containerization. The `dockerfile` sets up the Python 3.11 slim environment, installs dependencies, and copies the application code.

- The application exposes ports 8000 and 8002.
- The environment variable `ENV` can be set to `development` or `production`.
- The application is started using the `start.sh` script.

The project can be run using Docker Compose.

- **Development:**

  ```bash
  docker-compose up
  ```

- **Production:**

  ```bash
  docker-compose -f docker-compose.prod.yml up -d
  ```

## Data Models

The application uses the following Django models:

### User Management (`app_users.models`)

- **`CustomUserModel`**: Extends the default Django `AbstractUser` model with additional fields like `id` (UUID), `created_at`, `updated_at`, `role`, and `user_infos`.
- **`UserProfile`**: Linked to `CustomUserModel`, this model stores user profile specific information such as `profile_name`, `profile_picture`, `is_kid`, and `preferred_language`.

### Video Management (`app_videos.models`)

(Details to be added once the models in `app_videos/models.py` are defined)

## Running the Project

### Admin Access

To create a Django admin user, run:

```bash
docker-compose exec web python manage.py createsuperuser
```

Then log in at [http://localhost:8000/admin/](http://localhost:8000/admin/)

### Testing

To run backend tests:

```bash
docker-compose exec web python manage.py test
```

## Troubleshooting

- If you see migration errors, run:

  ```bash
  docker-compose exec web python manage.py migrate
  ```

- For static file issues, run:

  ```bash
  docker-compose exec web python manage.py collectstatic
  ```

- If you change environment variables, restart the containers.

## Project Structure

The project follows a standard Django structure:

- `core/`: Contains the main project settings, ASGI/WSGI configurations, and root URL configurations.
- `app_users/`: Django app for user management, including models, views, and API serializers/URLs.
- `app_videos/`: Django app for video management (details to be added).
- `media/`: Stores user-uploaded files, like profile pictures.
- `static/`: For static files (CSS, JavaScript, images).
- `dockerfile`: Defines the Docker image for the application.
- `docker-compose.yml`: Docker Compose configuration for development.
- `docker-compose.prod.yml`: Docker Compose configuration for production.
- `manage.py`: Django's command-line utility.
- `requirements.txt`: Lists Python dependencies.
- `start.sh`: Script to start the application inside the Docker container.

## API Endpoints

The application provides API endpoints for interacting with user and video data. These are defined within the `api/` subdirectories of `app_users` and `app_videos`. (Specific endpoint documentation can be added here later).
