# BlueWave Shop (Django)

An e-commerce and subscription website for selling micro-desalination units, managing researcher subscriptions,
displaying environmental impact metrics pulled from the existing BlueWave API, issuing JWTs for API access,
and enforcing MFA (password + TOTP). Built with Django 5, Bootstrap 5 (Bootswatch), and Stripe Checkout.

> **Sprint 2 deliverable** built to integrate with your existing **BlueWave API** from Sprint 1.

---

## Quick Start

```bash
# 1) Create & activate a virtualenv (recommended)
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Configure environment
cp .env.sample .env
# Edit .env: set STRIPE keys, BLUEWAVE_API_BASE (point it at your running API), etc.

# 4) Run Django setup
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_demo  # creates demo data and a superuser

# 5) Run the dev server
python manage.py runserver 0.0.0.0:8000
```

### Demo accounts
Created by `seed_demo`:
- **Admin**: `admin@example.com` / `Admin123!` (staff)
- **Customer**: `customer@example.com` / `Customer123!`
- **Researcher (with active subscription)**: `researcher@example.com` / `Researcher123!`

After first login for any user, set up TOTP from **Dashboard → Security → Set up Authenticator App**.

---

## Linking to the existing BlueWave API

1. Ensure your BlueWave API (from Sprint 1) is running and reachable. Set in `.env`:
   - `BLUEWAVE_API_BASE` (e.g., `http://localhost:5000`)
   - `BLUEWAVE_API_JWT_ENDPOINT` (e.g., `/auth/jwt` if your API exposes it)
   - `BLUEWAVE_API_METRICS_ENDPOINT` (e.g., `/v1/metrics` or similar)

2. From the website:
   - **JWT issuance**: On **Dashboard → API Access**, click **Request API Token**. The Django server calls
     the API's JWT endpoint with your configured client creds and the requesting user's email as the subject.
     The token is stored with expiry and displayed.
   - **Metrics dashboard**: **Environmental Dashboard** queries the BlueWave API via a Django proxy
     (`/metrics/proxy`) to avoid CORS issues. You can choose a time window and see salinity, pH, pollutants.

> If your API uses different parameter names, adjust `api_integration/utils.py` accordingly. The defaults assume
> `start` and `end` ISO-8601 timestamps, as in your earlier OpenAPI docs.

---

## Payments (Stripe) & Subscriptions

- **Products** are created in Django admin (or via the demo seed). Each product can be:
  - `ONE_TIME` (e.g., hardware unit purchase)
  - `SUBSCRIPTION` (for BlueWave data access)
- Put your Stripe Price IDs on the product (`stripe_price_id`).
- Checkout is handled with Stripe Checkout Sessions. Webhooks (`/payments/webhook/`) record successful
  payments, create `Order`s, and for subscriptions create/activate `Subscription` rows.
- Admins can **approve purchases** (to reflect fulfillment) via **Admin → Orders** or the custom screen
  **/admin-panel/pending-orders/**.

> Use **Stripe test mode** for real card testing (e.g., 4242 4242 4242 4242).

---

## Security & MFA

- MFA implemented with **password + TOTP** (using `pyotp`).
- Users set up TOTP by scanning a QR code. Then each login requires the 6-digit code.
- Standard Django security middleware is enabled; production settings recommend HTTPS and secure cookies.

---

## Databases

- **Dev**: SQLite (default)
- **Prod**: MySQL — set `DB_ENGINE=mysql` and MySQL env vars in `.env`. Then:
  ```bash
  pip install mysqlclient
  python manage.py migrate
  ```
- Schemas are the same via Django migrations. To migrate data from SQLite to MySQL in prod, use `dumpdata/loaddata` or a tool like `pgloader` (for MySQL use `mysqldump`-like tools) after clearing auth tokens.

---

## Tests (TDD-friendly)

- Unit tests exist under each app's `tests/` package.
- Run with:
  ```bash
  python manage.py test
  ```
- External calls (Stripe, BlueWave API) are mocked so tests run offline.

---

## Scrum Process Artefacts

See the `/docs` folder:
- `MOSCOW.md`: Prioritisation for this sprint.
- `RISK_PLAN.md`: Risk register with strategies.
- `SCRUM_BOARD.md`: Suggested Jira/Trello column layout and sample cards.
- `TEST_PLAN.md`: TDD workflow and coverage targets.

---

## Swagger / OpenAPI (from Sprint 1)

In this sprint we **consume** your API. If you host its OpenAPI at `/docs` or `/openapi.json`, add that URL to the
**Dashboard → API Access** page so researchers can discover endpoints easily.

---

## Running with Gunicorn (prod-ish)
```bash
DJANGO_DEBUG=False gunicorn bluewave_shop.wsgi:application --bind 0.0.0.0:8000
```
Behind Nginx with TLS; set secure cookie settings in `settings.py` as instructed there.
