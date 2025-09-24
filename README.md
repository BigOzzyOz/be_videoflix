
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
  - [CI/CD \& Deployment](#cicd--deployment)
    - [GitHub Actions: Automated Testing \& Production Deployment](#github-actions-automated-testing--production-deployment)
      - [Production Deploy Setup](#production-deploy-setup)
  - [Troubleshooting](#troubleshooting)
  - [Project Structure](#project-structure)
  - [API Endpoints](#api-endpoints)
    - [User Endpoints](#user-endpoints)
    - [Video Endpoints](#video-endpoints)
    - [Auth \& Miscellaneous](#auth--miscellaneous)

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

Run the initial database migrations:

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

## CI/CD & Deployment

### GitHub Actions: Automated Testing & Production Deployment

This project uses GitHub Actions for CI/CD:

- **CI (main branch):** Runs tests on every push or pull request.
- **CD (prod branch):** Runs tests and deploys to your production server via SSH.

#### Production Deploy Setup

1. **Server SSH Key Setup**
   - Log in to your server as the deploy user (e.g. `jh`).
   - Add your public key to `~/.ssh/authorized_keys` (create the file if it doesn't exist).
   - Set permissions:

     ```sh
     chmod 700 ~/.ssh
     chmod 600 ~/.ssh/authorized_keys
     ```

2. **GitHub Repository Secrets**
   - Go to: GitHub → Repository → Settings → Secrets and variables → Actions → New repository secret
   - Add:
     - `PROD_HOST` = your server's hostname or IP (e.g. `backend.jan-holtschke.de`)
     - `PROD_USER` = your SSH username (e.g. `jh`)
     - `PROD_SSH_KEY` = your private SSH key (e.g. from `~/.ssh/id_ed25519`)

3. **Trigger Deployment**
   - Push or open a pull request on the `prod` branch.
   - The workflow will SSH into your server and run the deployment commands.

**Security notes:**

- Never share your private key.
- The public key must be in `~/.ssh/authorized_keys` on the server.
- GitHub secrets are used automatically by the workflow.

## Troubleshooting

- **General debugging:**

  Check the logs of your containers to find the cause of errors:

  ```bash
  docker-compose logs web
  ```

  or for all containers:

  ```bash
  docker-compose logs
  ```

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

The backend exposes a RESTful API for user and video management.

**Tip:**
Interactive API documentation is available via:

> - [Swagger UI](http://localhost:8000/swagger/) (`/swagger/`)
> - [Redoc](http://localhost:8000/redoc/) (`/redoc/`)

All endpoints are prefixed with `/api/users/` or `/api/videos/`.

---

### User Endpoints

**Base path:** `/api/users/`

```http
POST   /api/users/login/                         # Obtain JWT token (login)
POST   /api/users/register/                      # Register a new user
GET    /api/users/verify-email/<token>/          # Verify user email
POST   /api/users/logout/                        # Logout user (JWT blacklist)
POST   /api/users/password-reset/                # Request password reset
POST   /api/users/password-reset/confirm/        # Confirm password reset
GET    /api/users/me/                            # Get current user details

# User profiles
GET    /api/users/me/profiles/                   # List user profiles
POST   /api/users/me/profiles/                   # Create a new user profile
GET    /api/users/me/profiles/<profile_id>/      # Get a specific user profile
PUT    /api/users/me/profiles/<profile_id>/      # Update a user profile
PATCH  /api/users/me/profiles/<profile_id>/      # Partially update a user profile
DELETE /api/users/me/profiles/<profile_id>/      # Delete a user profile

# Video progress for profile
POST   /api/users/me/profiles/<profile_id>/progress/<video_file_id>/update/  # Update video progress
```

### Video Endpoints

**Base path:** `/api/videos/`

```http
GET    /api/videos/                  # List all videos
GET    /api/videos/<video_id>/       # Retrieve details for a video
GET    /api/videos/genre-count/      # Get count of videos per genre
```

### Auth & Miscellaneous

```http
POST   /api/token/refresh/           # Refresh JWT token
POST   /api/token/verify/            # Verify JWT token
```

- Browsable API login: `/api-auth/`
- Interactive API docs: `/swagger/` (Swagger UI), `/redoc/` (Redoc)
