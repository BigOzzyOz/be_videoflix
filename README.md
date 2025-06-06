# be_videoflix

Videoflix Backend

## Project Introduction

Videoflix is a video streaming platform. This repository contains the backend service for Videoflix, built with Django and Django REST Framework. It handles user authentication, video management, and serves data to the frontend application.

## Frontend Application

(Link to the frontend repository or deployed application will be added here)

## Docker Setup

This project uses Docker for containerization. The `dockerfile` sets up the Python 3.11 slim environment, installs dependencies, and copies the application code.

- The application exposes ports 8000 and 8002.
- The environment variable `ENV` can be set to `development` or `production`.
- The application is started using the `start.sh` script.

## Data Models

The application uses the following Django models:

### User Management (`app_users.models`)

- **`CustomUserModel`**: Extends the default Django `AbstractUser` model with additional fields like `id` (UUID), `created_at`, `updated_at`, `role`, and `user_infos`.
- **`UserProfile`**: Linked to `CustomUserModel`, this model stores user profile specific information such as `profile_name`, `profile_picture`, `is_kid`, and `preferred_language`.

### Video Management (`app_videos.models`)

(Details to be added once the models in `app_videos/models.py` are defined)

## Running the Project

The project can be run using Docker Compose.

- **Development:**

  ```bash
  docker-compose up
  ```

- **Production:**

  ```bash
  docker-compose -f docker-compose.prod.yml up -d
  ```

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
