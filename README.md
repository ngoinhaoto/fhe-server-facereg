# FHE Server for Face Recognition Attendance

This is the main application server for the Face Recognition Attendance System. It provides RESTful APIs for user management, class/session scheduling, attendance tracking, face registration and verification (including privacy-preserving FHE operations), and integrates with a PostgreSQL database and SMTP email system.

---

## Features

- FastAPI-based REST API
- Modular routers for users, classes, attendance, authentication, FHE, and admin dashboard
- PostgreSQL database with SQLAlchemy ORM
- Homomorphic encryption (CKKS via TenSEAL) for privacy-preserving face verification
- Integrated email system for password reset, onboarding, and notifications
- JWT authentication and role-based access control

---

## Installation Guide

### 1. Clone the Repository

```sh
git clone https://github.com/ngoinhaoto/fhe-server-facereg.git
cd fhe-server-facereg
```

### 2. Create and Activate a Python Environment

```sh
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```sh
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and edit as needed:

```sh
cp .env.example .env
```

Set your database, email, and service URLs in `.env`:

```
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
DB_NAME=facereg_fhe_db

EMAIL_SENDER=your_email@gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

FRONTEND_URL=http://localhost:3000
MICROSERVICE_URL=http://localhost:8002
CONTEXT_DIR=context
```

### 5. Initialize the Database

Make sure PostgreSQL is running and accessible.

Run the database initialization script:

```sh
python scripts/init_db.py
```

### 6. Run the Server

```sh
python main.py
```

The API will be available at [http://localhost:8000](http://localhost:8000).

---

## Usage

- See the OpenAPI docs at `/docs` for all available endpoints.
- Integrate with the React frontend and FHE microservice as described in the system documentation.

---

## Email System

The application server integrates a robust email system for password reset, account recovery, and user notifications.

- **Password Reset & Account Recovery:**  
  When a user forgets their password, they can request a reset link via the frontend. The backend generates a secure, time-limited token and sends a password reset email to the user’s registered address using SMTP. The user clicks the link, sets a new password, and the backend verifies the token before updating the password in the database.

- **Welcome & Notification Emails:**  
  When a user is created via the `/users/` endpoint, a welcome email is sent asynchronously using FastAPI’s `BackgroundTasks` and the email service. The system can also send attendance confirmations, session reminders, and absence notifications.

- **Implementation:**

  - SMTP credentials are configured in `.env`:
    ```
    EMAIL_SENDER=your_email@gmail.com
    SMTP_USERNAME=your_email@gmail.com
    SMTP_PASSWORD=your_app_password
    SMTP_SERVER=smtp.gmail.com
    SMTP_PORT=587
    ```
  - Email templates are rendered using Jinja2 and stored in `templates/email/`.
  - All email sending is performed in the background to avoid blocking API responses.

- **Security:**
  - Password reset tokens are securely generated and expire after a set time.
  - Passwords are hashed before storage and never sent via email.

**Summary:**  
The email system ensures secure, automated communication for password resets, onboarding, and attendance notifications, improving both usability and security for all users.

---

## Development

- Routers are in the `routers/` directory.
- Database models are in `models/database.py`.
- Email templates are in `templates/email/`.
- FHE context files are in the `context/` directory.

---

## Troubleshooting

- Ensure PostgreSQL is running and credentials in `.env` are correct.
- For email, use an app password if using Gmail and enable "less secure apps" if needed.
- If FHE context files are missing, they will be generated automatically on first run.

---

## License

MIT (or your chosen license)
