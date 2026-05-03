# SSC Education ERP

Professionalized Django-based Education ERP / CRM foundation for admissions, fees, attendance, batch operations, and operational governance.

## Current Architecture

- `core`: shared models, forms, admin, middleware, validators, utilities, audit infrastructure
- `admissions`: admission workflow views
- `finance`: fee collection workflow views
- `attendance`: attendance marking and reporting views
- `batch_management`: batch lifecycle views
- `reports`: operational health endpoint
- `Project.settings`: split `base`, `dev`, and `prod` settings

## Key Upgrades Implemented

- Service layer for admission, fee, and batch workflows
- Audit logging for admissions, fee payments, login/logout, and batch changes
- ERP role model using Django groups:
  `Super Admin`, `Admin`, `Counselor`, `Accountant`, `Attendance Manager`
- Admission `student_id` generation with a stable yearly sequence
- Soft-archive support on students, enquiries, and batches
- Login brute-force throttling and session idle timeout
- Health endpoint at `/health/`
- Batch lifecycle management with reversible end/restore flows
- Regression tests for login security, fee integrity, admission creation, and role-based batch access

## Local Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Docker

```bash
docker compose up --build
```

## Recommended Production Baseline

- PostgreSQL
- Redis cache
- Gunicorn behind Nginx
- environment-managed secrets
- TLS termination
- centralized log collection
- scheduled database and media backups

## Tests

```bash
python manage.py test core.tests
python manage.py check
```

## Batch Lifecycle

- active batches remain eligible for daily attendance
- completed, archived, or cancelled batches keep all admissions, fees, and attendance history
- batch lifecycle actions are logged in `BatchActionLog`
- restore returns a batch to attendance eligibility without recreating records
