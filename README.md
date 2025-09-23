
# Videoflix Backend (`be_videoflix`)

Backend service for Videoflix, a video streaming platform. Built with Django and Django REST Framework. Handles user authentication, video management, and serves data to the frontend.

---

## Table of Contents

- [Videoflix Backend (`be_videoflix`)](#videoflix-backend-be_videoflix)
  - [Table of Contents](#table-of-contents)
  - [Project Introduction](#project-introduction)
  - [Frontend Application](#frontend-application)
  - [Setup \& Installation](#setup--installation)
    - [1. Clone the repository](#1-clone-the-repository)
    - [2. Configure environment variables](#2-configure-environment-variables)
    - [3. Build and start the services](#3-build-and-start-the-services)
    - [4. Database migrations](#4-database-migrations)
  - [Environment Variables (.env / .env.prod)](#environment-variables-env--envprod)
  - [Docker Setup](#docker-setup)
  - [Data Models](#data-models)
    - [User Management (`app_users.models`)](#user-management-app_usersmodels)
    - [Video Management (`app_videos.models`)](#video-management-app_videosmodels)
  - [Running the Project](#running-the-project)
    - [Admin Access](#admin-access)
  - [Testing](#testing)
  - [Troubleshooting](#troubleshooting)
  - [Project Structure](#project-structure)
  - [API Endpoints](#api-endpoints)

---

## Project Introduction

Videoflix is a video streaming platform. This repository contains the backend service for Videoflix, built with Django and Django REST Framework. It handles user authentication, video management, and serves data to the frontend application.

## Frontend Application

The frontend repository can be found here: [https://github.com/BigOzzyOz/videoflix](https://github.com/BigOzzyOz/videoflix)

## Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/BigOzzyOz/be_videoflix.git
cd be_videoflix
```

### 2. Configure environment variables

Copy `.example.env` to `.env` for local development:

```bash
cp .example.env .env
```

Or for production:

```bash
cp .example.prod.env .env.prod
```

Edit the `.env` or `.env.prod` file as needed (see [Environment Variables](#environment-variables-env--envprod)).

### 3. Build and start the services

For development:

```bash
docker-compose up --build
```

For production:

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### 4. Database migrations

**Note:** The `start.sh` script (used by Docker) automatically runs migrations. However, if you need to run them manually (e.g., during development or debugging), use:

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

---

## Environment Variables (.env / .env.prod)

Environment variables are required for running the project. Example files are provided as `.example.env` and `.example.prod.env` in the repository. **Do not edit** `.example.env` or `.example.prod.env` directly—always copy them to `.env` or `.env.prod` (which are gitignored) and edit those copies.

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
- `BASE_URL`: The URL of your frontend. For local development, use your local frontend address (e.g. `http://localhost:4200/`). For production, use your deployed frontend domain (e.g. `https://videoflix.jan-holtschke.de`). This ensures that all links in emails (e.g. for verification or password reset) point to the correct frontend.

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
- The application is started using the `start.sh` script, which also runs migrations and collects static files.

You can run the project using Docker Compose (see [Setup & Installation](#setup--installation)).

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

## Testing

To run backend tests:

```bash
docker-compose exec web python manage.py test
```

## Troubleshooting

- **Migration errors:**

  ```bash
  docker-compose exec web python manage.py makemigrations
  docker-compose exec web python manage.py migrate
  ```

- **Static file issues:**

  ```bash
  docker-compose exec web python manage.py collectstatic
  ```

- **Changed environment variables?** Restart the containers.

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
