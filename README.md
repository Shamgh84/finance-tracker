# Personal Finance Manager

A web-based system for managing and analyzing personal finances. Users register, record their income and expenses, set monthly budgets per category, and get a dashboard and automatic financial analysis of their spending habits.

Built as a graduation project with **Django**, **PostgreSQL** and **Django REST Framework**.

## Features

- **Authentication** with JWT (register, login, token refresh, profile)
- **Transactions**: create, view, edit and delete income and expenses, with search, filters (type, category, date range, amount), sorting and pagination
- **Categories**: default system categories plus personal ones per user
- **Monthly budgets** per expense category with usage tracking and alerts (warning near the limit, exceeded)
- **Dashboard**: income, expense and balance cards, category breakdown chart and monthly trend chart (Chart.js)
- **Financial analysis**:
  - month-over-month comparison per category (compared over the same days of the month)
  - end-of-month spending forecast
  - financial health score (0-100) based on savings rate, budget discipline and spending stability
  - automatic text report with insights
- **CSV export** of filtered transactions
- **Interactive API docs** (Swagger UI and ReDoc)
- Persian (RTL) interface, with dates shown in the Jalali calendar in the transaction list

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, Django, Django REST Framework |
| Database | PostgreSQL |
| Auth | JWT (`djangorestframework-simplejwt`) |
| Frontend | HTML, CSS, vanilla JavaScript, Chart.js |
| API docs | `drf-spectacular` (OpenAPI 3) |
| Tests | Django test framework (`APITestCase`) |

## Design decisions

- **Per-user data isolation**: every query is filtered by the authenticated user, and this is covered by automated tests.
- **Money as `DecimalField`**, never floats.
- **Business logic in `services.py`** (budget status, analytics, health score), separate from views, so it is easy to test. Pure functions are tested without a database.
- **Default categories** are created by a data migration, so every fresh database gets them automatically.
- **API first**: the frontend consumes the same REST API that is documented in Swagger.
- Dates are stored in the Gregorian calendar and converted for display.

## Project structure

```
config/         project settings and root URLs
accounts/       custom user model, register, login, profile
categories/     default and personal categories
transactions/   transactions API, filters, CSV export
budgets/        monthly budgets, usage and alerts
analytics/      dashboard data and financial analysis
templates/      HTML pages
static/         CSS and JavaScript
```

## Getting started (Windows)

### 1. Prerequisites

Python 3.11+, Git and PostgreSQL.

### 2. Clone and create a virtual environment

```
git clone https://github.com/Shamgh84/finance-tracker.git
cd finance-tracker
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create the database

In `psql` (or pgAdmin):

```sql
CREATE USER finance_user WITH PASSWORD 'your_password';
CREATE DATABASE finance_db OWNER finance_user;
```

### 4. Configure environment variables

```
copy .env.example .env
```

Edit `.env` and set `SECRET_KEY` and `DB_PASSWORD`. To generate a secret key:

```
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Migrate and run

```
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/ and register a new account.

## API documentation

With the server running:

- Swagger UI: http://127.0.0.1:8000/api/docs/
- ReDoc: http://127.0.0.1:8000/api/redoc/
- OpenAPI schema: http://127.0.0.1:8000/api/schema/

### Main endpoints

| Endpoint | Description |
|---|---|
| `POST /api/auth/register/` | Create an account |
| `POST /api/auth/login/` | Get access and refresh tokens |
| `GET /api/categories/` | Default and personal categories |
| `GET /api/transactions/` | List with `search`, `type`, `category`, `date_from`, `date_to`, `min_amount`, `max_amount`, `ordering` |
| `GET /api/transactions/export/` | CSV export (same filters) |
| `GET /api/budgets/` | Budgets with spent, remaining, percent and status |
| `GET /api/budgets/alerts/` | Current-month budgets near or over the limit |
| `GET /api/analytics/summary/` | Income, expense and balance |
| `GET /api/analytics/by-category/` | Category breakdown |
| `GET /api/analytics/trend/` | Monthly income and expense trend |
| `GET /api/analytics/comparison/` | Month-over-month comparison |
| `GET /api/analytics/forecast/` | End-of-month spending forecast |
| `GET /api/analytics/health-score/` | Financial health score |
| `GET /api/analytics/report/` | Full report with text insights |

## Running the tests

```
python manage.py test
```

The test database is created automatically, so the database user needs the `CREATEDB` privilege.

## Screenshots

<!-- Add screenshots to docs/screenshots and link them here -->

## Known limitations

- Budget months (and the dashboard month picker) use the Gregorian calendar; a full Jalali calendar for budgets is a possible future improvement.
- No email verification or password reset yet.

## Author

Shamim Ghadiani