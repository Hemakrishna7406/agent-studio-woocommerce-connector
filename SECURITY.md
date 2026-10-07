# Security

## Reporting

If you find a vulnerability, please open a private security advisory on the
repository rather than a public issue, or email the maintainer. Do not include
secrets in a report.

## Design posture

- **Read-only.** The connector exposes no write operations, and the API key is
  intended to be issued with **Read** permission to a dedicated
  least-privilege user. A leaked key cannot damage the merchant's store.
- **Transport.** Credentials are sent via **HTTP Basic over HTTPS only**, never
  in the query string. HTTPS is a hard requirement; an HTTP-only store is
  rejected rather than silently downgraded.
- **Secrets.** All credentials come from the environment. Nothing is
  hard-coded, logged, or returned in tool output. `.env` is gitignored.
- **Bounded blast radius.** Every list tool paginates and can be capped, so a
  misbehaving agent cannot exhaust the store's rate budget or its own context.
- **No PII beyond what the store exposes.** The connector returns only fields
  the merchant's own REST API already returns; field-level redaction belongs to
  the deployment host.

## Out of scope

- Write operations (refunds, fulfilment, status changes) — deliberately not
  implemented.
- Multi-tenant key management — one store per connector instance, configured by
  environment.
