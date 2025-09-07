# Risk Management Plan

| Risk | Type | Likelihood | Impact | Strategy |
|------|------|------------|--------|----------|
| Stripe misconfiguration | Technical | Medium | High | Reduce: use test mode, docs, webhooks verified |
| API downtime | External | Medium | High | Reduce: proxy with timeouts, graceful errors |
| MFA lockouts | User | Low | Medium | Accept: admin reset flow documented |
| MySQL migration issues | Technical | Medium | High | Reduce: run migrations in staging; use fixtures |
| Data privacy | Compliance | Low | High | Avoid: secure cookies, HTTPS, least‑privilege secrets |

**Ownership:** Scrum Master monitors; Devs implement mitigations.
