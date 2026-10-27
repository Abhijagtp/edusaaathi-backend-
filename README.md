# EduSaathi Backend API (Django + Docker + Neon PostgreSQL + JWT)

Modern, containerized Django REST Framework backend designed for **EduSaathi** with separate **`website`** and **`admin_app`** applications, PostgreSQL hosted on Neon with SSL connection pooling, and JWT authentication.

---

## 🚀 Quick Start with Docker

### 1. Build and Run the Container
From the `backend` directory (or the project root):
```bash
docker compose up --build
```

The container automatically:
- Tests and waits for the **Neon PostgreSQL** database connection.
- Applies all database migrations for `admin_app` and `website`.
- Automatically ensures the **Admin Superuser** exists.
- Collects static files.
- Starts the development server at `http://localhost:8000`.

To run in the background (detached mode):
```bash
docker compose up -d
```

To stop:
```bash
docker compose down
```

---

## 🔑 Default Admin Superuser Credentials

The initial administrator account is automatically provisioned on startup:

- **Email**: `edusaathi@gmail.com`
- **Password**: `edusaathi9897@!`
- **Role**: `ADMIN` (Superuser & Staff permissions enabled)

---

## 🗄️ Database Configuration (Neon PostgreSQL)

The backend connects directly to your Neon PostgreSQL pooler database configured in `.env`:
```env
DATABASE_URL=postgresql://neondb_owner:npg_EO6dPImaTV1b@ep-royal-fire-aou535vk-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

---

## 🔐 JWT Authentication & APIs

### 1. Obtain JWT Tokens (Login)
- **POST** `/api/auth/login/` (or `/api/admin/auth/login/`)
- **Payload**:
```json
{
  "email": "edusaathi@gmail.com",
  "password": "edusaathi9897@!"
}
```
- **Response**:
```json
{
  "refresh": "eyJhbGciOiJIUzI1Ni...",
  "access": "eyJhbGciOiJIUzI1Ni...",
  "user": {
    "id": 1,
    "email": "edusaathi@gmail.com",
    "first_name": "EduSaathi",
    "last_name": "Admin",
    "role": "ADMIN",
    "is_staff": true,
    "is_superuser": true
  }
}
```

### 2. Refresh JWT Token
- **POST** `/api/auth/token/refresh/`
- **Payload**:
```json
{
  "refresh": "<your_refresh_token>"
}
```

### 3. Verify JWT Token
- **POST** `/api/auth/token/verify/`
- **Payload**:
```json
{
  "token": "<your_access_token>"
}
```

### 4. Authenticated User Profile
- **GET** `/api/auth/me/` (Send header `Authorization: Bearer <access_token>`)
- **PATCH** `/api/auth/me/`

---

## 🛠️ Applications Architecture

### 1. `admin_app`
- **Custom User Model**: Uses `email` as `USERNAME_FIELD` with roles (`ADMIN`, `STAFF`, `CONSULTANT`, `COUNSELOR`, `USER`).
- **Dashboard Metrics**: `GET /api/admin/dashboard/stats/` (aggregated user counts, new signups, website leads, contact queries).
- **Consultant Management (Admin)**:
  - `GET /api/admin/consultants/`: List all consultants with referral links and live lead conversion metrics.
  - `POST /api/admin/consultants/`: Create a new consultant (automatically generates unique referral code & share link).
  - `POST /api/admin/consultants/<id>/regenerate-link/`: Generate a new referral code/link.
- **Consultant Self-Service & Lead Management**:
  - `GET /api/consultant/dashboard/`: Consultant profile, unique referral link, and conversion rates (`NEW`, `CONTACTED`, `ENROLLED`).
  - `GET /api/consultant/leads/`: Returns only student leads assigned to the logged-in consultant.
  - `PATCH /api/consultant/leads/<id>/`: Consultant updates status and counselor notes for their assigned lead.
- **User Management**: `GET/POST/PUT/DELETE /api/admin/users/` (staff/admin only).
- **Admin Audit Logs**: `GET /api/admin/logs/`.
- **Site Settings**: `GET/POST/PUT /api/admin/settings/`.

### 2. `website`
- **Student Inquiry Form & Referral Tracking**:
  - `GET /api/website/student-form/options/`: Returns dynamic dropdown options for active courses (with "Other" option) and 33+ Indian cities (with "Other" option).
  - `POST /api/website/student-form/submit/` (or `/api/website/enquiries/`): Submits inquiry. Accepts optional `referral_code` (or query param `?ref=...`).
    - If a valid referral code is present, **the lead is automatically assigned to that consultant**!
    - Validates 10-digit Indian Mobile Number (`^[6-9]\d{9}$`).
- **Indian Cities**:
  - `GET /api/website/cities/` (search & list Indian cities)
- **Course Content Management (Admin & Website)**:
  - `POST /api/admin/courses/` (or `/api/website/admin/courses/`): Add a new course with full rich content (name, slug, duration, fees, image, alt, descriptions, eligibility, highlights array/text, admission info, published status).
  - `GET /api/admin/courses/`: List all courses (including draft/unpublished courses).
  - `GET /api/admin/courses/<id_or_slug>/`: Retrieve course details for editing.
  - `PATCH /api/admin/courses/<id_or_slug>/` (or `PUT`): Update existing course content.
  - `DELETE /api/admin/courses/<id_or_slug>/`: Remove course guide.
  - `GET /api/courses/` (or `/api/website/courses/`): Public listing of all published courses for frontend cards.
  - `GET /api/courses/<slug>/` (or `/api/website/courses/<slug>/`): Public detailed course guide.
- **Contact Inquiries**:
  - `POST /api/website/contact/submit/`
- **FAQs**:
  - `GET /api/website/faqs/`
- **Health Check**:
  - `GET /api/website/health/`
- **Admin Inquiries Management**:
  - `GET /api/website/admin/leads/` (Filter by status, search by name/mobile/city)
  - `PATCH /api/website/admin/leads/<id>/` (Update status and counselor notes)

---

## 📖 Interactive API Documentation

Interactive Swagger and Redoc pages are available:
- **Swagger UI**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **ReDoc**: [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)
- **OpenAPI Schema**: [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)
- **Django Admin**: [http://localhost:8000/admin/](http://localhost:8000/admin/)
