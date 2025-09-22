# The Newel - Biology Education Platform

A Flask-based web application for teachers to create biology prompts and for students to submit responses, get graded, and compete on a leaderboard.

## Features

- **Role-Based Authentication:** Separate sign-up and dashboards for Teachers and Students.
- **Prompt Management:** Teachers can create biology prompts.
- **Response System:** Students can view and respond to prompts.
- **Grading Interface:** Teachers can grade student responses and provide feedback.
- **Leaderboard:** Ranks students based on their average grades.

## Tech Stack

- **Backend:** Flask (Python)
- **Database:** SQLite (Development), PostgreSQL (Production)
- **ORM:** Flask-SQLAlchemy
- **Authentication:** Flask-Login
- **Frontend:** Jinja2 templates with custom CSS

## Local Development Setup

1.  **Clone the repository** and navigate into its directory.
2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```
3.  **Activate the virtual environment:**
    - On Windows: `venv\Scripts\activate`
    - On macOS/Linux: `source venv/bin/activate`
4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Set environment variable (optional for development):**
    ```bash
    # On macOS/Linux
    export SECRET_KEY='your-very-secret-random-key-here'

    # On Windows (Command Prompt)
    set SECRET_KEY=your-very-secret-random-key-here

    # On Windows (PowerShell)
    $env:SECRET_KEY='your-very-secret-random-key-here'
    ```
    *If you don't set this, the app will use a default dev key.*
6.  **Run the application:**
    ```bash
    flask run
    # or
    python app.py
    ```
7.  **Open your browser** and go to `http://localhost:5000`.

## Deployment Instructions

### Heroku / Railway

1.  **Create a `Procfile`** in your project root with the following line:
    ```procfile
    web: gunicorn app:app
    ```
2.  **Set Environment Variables** in your hosting dashboard:
    - `SECRET_KEY`: Set to a long, random string.
    - `DATABASE_URL`: (Usually added automatically by the platform when you provision a PostgreSQL database).
3.  **Update `app.py`** to use the production database (Heroku/Railway will set `DATABASE_URL`):
    ```python
    # Replace the SQLite configuration line with:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://') or 'sqlite:///merged_newel.db'
    ```
    *This ensures compatibility with Heroku's connection string.*
4.  **Deploy** your code to the platform via Git.

### PythonAnywhere

1.  **Upload** your project files.
2.  **Create a virtual environment** and install dependencies from `requirements.txt`.
3.  **In the Web App section**, point it to your `app.py` file.
4.  **Set environment variables** in the Web App configuration:
    - `SECRET_KEY`: Your secret key.
5.  **Reload** your web app.

## File Structure
