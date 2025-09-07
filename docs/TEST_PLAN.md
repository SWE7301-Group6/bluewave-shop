# Test Plan (TDD)

- **Accounts**
  - Registration/login validation
  - 2FA flow: setup, verify, login
- **Shop/Payments**
  - Create checkout session (mock Stripe)
  - Webhook handling creates Orders and Subscriptions
- **Metrics**
  - Proxy validates params & passes data (mock API)
- **API Access**
  - JWT issuance stores token & expiry (mock API)
- **Security**
  - CSRF & auth on protected routes

Run: `python manage.py test`
